"""
Celery task: index an admin Knowledge Base document into Qdrant.

Enqueued by the API when an admin uploads a document via
POST /api/v1/admin/knowledge-bases/{id}/documents.

Unlike process_file (user files), this task:
  - targets a named KB Qdrant collection (not a user namespace)
  - uses the KB's own chunking config
  - updates KB stats in MongoDB after indexing
"""
from loguru import logger
from pymongo import MongoClient
from bson import ObjectId

from app.celery_app import celery_app
from app.core.config import settings
from app.db import qdrant as qdrant_db
from app.storage.s3 import download_file_to_tmp


@celery_app.task(bind=True, name="index_kb_document", max_retries=3)
def index_kb_document(
    self,
    *,
    file_id: str,
    s3_key: str,
    kb_id: str,
    vector_collection: str,
    tenant_id: str,
    chunking_strategy: str = "recursive",
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
):
    logger.info(
        f"index_kb_document | kb_id={kb_id} file_id={file_id} "
        f"collection={vector_collection} strategy={chunking_strategy}"
    )

    try:
        # 1. Download file from S3
        tmp_path = _download_by_s3_key(s3_key)

        # 2. Extract text based on file type
        text = _extract_text(tmp_path)

        # 3. Chunk with KB-specific config
        chunks = _chunk(text, chunking_strategy, chunk_size, chunk_overlap)

        # 4. Embed + upsert into KB's Qdrant collection
        metadata = {
            "file_id": file_id,
            "kb_id": kb_id,
            "tenant_id": tenant_id,
            "s3_key": s3_key,
        }
        count = qdrant_db.index_chunks(
            collection=vector_collection,
            chunks=chunks,
            metadata=metadata,
        )

        # 5. Update KB stats in MongoDB
        _update_kb_stats(kb_id, count)

        logger.info(f"index_kb_document done — {count} chunks in collection={vector_collection}")

    except Exception as exc:
        logger.exception(f"index_kb_document failed: {exc}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _download_by_s3_key(s3_key: str):
    import tempfile
    from pathlib import Path
    import boto3

    suffix = Path(s3_key).suffix or ".bin"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)

    s3 = boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    s3.download_fileobj(settings.AWS_S3_BUCKET, s3_key, tmp)
    tmp.flush()
    return Path(tmp.name)


def _extract_text(path) -> str:
    from pathlib import Path
    ext = Path(path).suffix.lower()

    if ext == ".pdf":
        from app.processors.pdf.extractor import PDFProcessor
        # Inline extraction without full processor run
        import boto3
        import re
        textract = boto3.client("textract", region_name=settings.AWS_REGION)
        with open(path, "rb") as f:
            resp = textract.detect_document_text(Document={"Bytes": f.read()})
        return "\n".join(
            b["Text"] for b in resp["Blocks"] if b["BlockType"] == "LINE"
        )

    elif ext in (".docx", ".doc"):
        from docx import Document
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    elif ext in (".txt", ".md"):
        return Path(path).read_text(encoding="utf-8", errors="ignore")

    elif ext == ".html":
        import re
        html = Path(path).read_text(encoding="utf-8", errors="ignore")
        return re.sub(r"<[^>]+>", " ", html).strip()

    elif ext in (".xlsx", ".xls"):
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True)
        rows = []
        for sheet in wb.worksheets:
            for row in sheet.iter_rows(values_only=True):
                rows.append("\t".join(str(c) for c in row if c is not None))
        return "\n".join(rows)

    else:
        return Path(path).read_text(encoding="utf-8", errors="ignore")


def _chunk(text: str, strategy: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return splitter.split_text(text)


def _update_kb_stats(kb_id: str, new_chunks: int) -> None:
    from datetime import datetime
    client = MongoClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB]
    db["knowledge_bases"].update_one(
        {"_id": ObjectId(kb_id)},
        {
            "$inc": {
                "stats.total_documents": 1,
                "stats.total_chunks": new_chunks,
            },
            "$set": {"stats.last_indexed_at": datetime.utcnow()},
        },
    )
    client.close()

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel

from app.core.admin_auth import require_admin
from app.core.auth import TokenPayload
from app.core.config import settings
from app.models.knowledge_base import KnowledgeBase
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository

router = APIRouter(prefix="/admin/knowledge-bases", tags=["admin:knowledge-bases"])

Tenant = Annotated[TokenPayload, Depends(require_admin)]


class KBCreateRequest(BaseModel):
    name: str
    description: str = ""
    type: str = "document"
    embedding_model: str = "text-embedding-3-large"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    chunking_strategy: str = "recursive"


class KBUpdateRequest(KBCreateRequest):
    pass


@router.get("/")
async def list_kbs(payload: Tenant):
    repo = KnowledgeBaseRepository()
    return await repo.list_for_tenant(payload.tenant)


@router.get("/{kb_id}")
async def get_kb(kb_id: str, payload: Tenant):
    repo = KnowledgeBaseRepository()
    kb = await repo.get_by_id(kb_id, payload.tenant)
    if not kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found")
    return kb


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_kb(body: KBCreateRequest, payload: Tenant):
    # Collection name derived from a unique slug to avoid collisions
    collection = f"kb_{payload.tenant}_{uuid.uuid4().hex[:8]}"
    kb = KnowledgeBase(
        id="",
        tenant=payload.tenant,
        vector_collection=collection,
        **body.model_dump(),
    )
    repo = KnowledgeBaseRepository()
    new_id = await repo.upsert(kb)
    return {"id": new_id, "vector_collection": collection}


@router.put("/{kb_id}")
async def update_kb(kb_id: str, body: KBUpdateRequest, payload: Tenant):
    repo = KnowledgeBaseRepository()
    existing = await repo.get_by_id(kb_id, payload.tenant)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found")
    updated = existing.model_copy(update={**body.model_dump(), "updated_at": datetime.utcnow()})
    await repo.upsert(updated)
    return {"id": kb_id}


@router.post("/{kb_id}/documents", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    kb_id: str,
    payload: Tenant,
    file: UploadFile = File(...),
    title: str = Form(""),
):
    """
    Uploads a document to S3 and enqueues it for indexing into the KB's Qdrant collection.
    Indexing is performed asynchronously by the file-processor worker.
    """
    repo = KnowledgeBaseRepository()
    kb = await repo.get_by_id(kb_id, payload.tenant)
    if not kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found")

    import boto3
    file_id = uuid.uuid4().hex
    s3_key = f"kbs/{kb_id}/{file_id}_{file.filename}"

    s3 = boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    s3.upload_fileobj(file.file, settings.AWS_S3_BUCKET, s3_key)

    # Enqueue indexing task for file-processor
    from app.core.queue import enqueue_kb_indexing
    await enqueue_kb_indexing(
        file_id=file_id,
        s3_key=s3_key,
        kb_id=kb_id,
        vector_collection=kb.vector_collection,
        tenant_id=payload.tenant,
        chunking_strategy=kb.chunking_strategy,
        chunk_size=kb.chunk_size,
        chunk_overlap=kb.chunk_overlap,
    )

    return {
        "file_id": file_id,
        "s3_key": s3_key,
        "status": "queued",
        "message": "Document upload received. Indexing started asynchronously.",
    }


@router.post("/{kb_id}/search-test")
async def test_search(kb_id: str, payload: Tenant, query: str):
    """Runs a semantic search against the KB for admin testing."""
    from app.services.knowledge_bases.builder import build_admin_kb_source
    from app.repositories.knowledge_base_repository import KnowledgeBaseRepository

    repo = KnowledgeBaseRepository()
    kb = await repo.get_by_id(kb_id, payload.tenant)
    if not kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found")

    source = build_admin_kb_source(kb)
    results = await source.asearch(query, num_documents=5)
    return {"query": query, "results": [r.model_dump() for r in results]}


@router.delete("/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_kb(kb_id: str, payload: Tenant):
    repo = KnowledgeBaseRepository()
    deleted = await repo.delete(kb_id, payload.tenant)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found")

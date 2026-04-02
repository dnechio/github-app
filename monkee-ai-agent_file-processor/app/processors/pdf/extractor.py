from app.processors.base import BaseProcessor
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger
import re


class PDFProcessor(BaseProcessor):
    """Extracts text from PDFs using AWS Textract (OCR)."""

    def extract_text(self) -> str:
        import boto3
        from app.storage.s3 import get_s3_key
        from app.core.config import settings

        textract = boto3.client("textract", region_name=settings.AWS_REGION)
        s3_key = get_s3_key(self.file_id)

        logger.info(f"Starting Textract OCR for file_id={self.file_id}")
        response = textract.detect_document_text(
            Document={"S3Object": {"Bucket": settings.AWS_S3_BUCKET, "Name": s3_key}}
        )

        lines = [
            block["Text"]
            for block in response["Blocks"]
            if block["BlockType"] == "LINE"
        ]
        return "\n".join(lines)

    def chunk_text(self, text: str) -> list[str]:
        # Legal document chunking: split by "Art.", "§", "Inciso" first
        legal_pattern = r"(?=Art\.\s+\d+|§\s+\d+|Inciso\s+[IVX]+)"
        legal_chunks = re.split(legal_pattern, text)

        result = []
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        for chunk in legal_chunks:
            if len(chunk) > 1200:
                result.extend(splitter.split_text(chunk))
            elif chunk.strip():
                result.append(chunk.strip())

        return result

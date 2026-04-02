from loguru import logger
from app.celery_app import celery_app


@celery_app.task(bind=True, name="process_file", max_retries=3)
def process_file(self, file_id: str, tenant_id: str, user_id: str, file_type: str):
    """
    Main task: routes file to the appropriate processor based on file_type.

    file_type: audio | video | pdf | document | image | json
    """
    logger.info(f"Processing file {file_id} | type={file_type} | tenant={tenant_id}")

    try:
        from app.processors.audio.transcriber import AudioProcessor
        from app.processors.pdf.extractor import PDFProcessor
        from app.processors.document.extractor import DocumentProcessor
        from app.processors.image.analyzer import ImageProcessor

        processor_map = {
            "audio": AudioProcessor,
            "video": AudioProcessor,
            "pdf": PDFProcessor,
            "document": DocumentProcessor,
            "image": ImageProcessor,
        }

        processor_cls = processor_map.get(file_type)
        if not processor_cls:
            raise ValueError(f"Unsupported file type: {file_type}")

        processor = processor_cls(file_id=file_id, tenant_id=tenant_id, user_id=user_id)
        processor.run()

    except Exception as exc:
        logger.error(f"Failed to process file {file_id}: {exc}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))

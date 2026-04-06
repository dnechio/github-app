from abc import ABC, abstractmethod

from loguru import logger

from app.db import mongodb, qdrant as qdrant_db


class BaseProcessor(ABC):
    def __init__(self, file_id: str, tenant_id: str, user_id: str):
        self.file_id = file_id
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.vector_namespace = f"user_{tenant_id}_{user_id}"

    @abstractmethod
    def extract_text(self) -> str:
        """Extract raw text from the file."""
        ...

    @abstractmethod
    def chunk_text(self, text: str) -> list[str]:
        """Split text into chunks for indexing."""
        ...

    def run(self) -> None:
        logger.info(f"[{self.__class__.__name__}] Starting — file_id={self.file_id}")

        try:
            self._update_status("processing")
            text = self.extract_text()

            self._update_status("indexing")
            chunks = self.chunk_text(text)
            count = self._index_chunks(chunks)

            self._update_status("ready", {"chunks_count": count})
            logger.info(f"[{self.__class__.__name__}] Done — {count} chunks indexed")

        except Exception as exc:
            logger.exception(f"[{self.__class__.__name__}] Failed — file_id={self.file_id}: {exc}")
            mongodb.increment_file_retry(self.file_id, str(exc))
            raise

    def _update_status(self, status: str, extra: dict | None = None) -> None:
        logger.debug(f"file_id={self.file_id} status → {status}")
        mongodb.update_file_status(self.file_id, status, extra)

    def _index_chunks(self, chunks: list[str]) -> int:
        """Embeds and upserts chunks into the user's private Qdrant namespace."""
        if not chunks:
            return 0

        metadata = {
            "file_id": self.file_id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
        }

        count = qdrant_db.index_chunks(
            collection=self.vector_namespace,
            chunks=chunks,
            metadata=metadata,
        )
        logger.debug(
            f"Indexed {count} chunks in collection={self.vector_namespace}"
        )
        return count

from app.processors.base import BaseProcessor
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger


class AudioProcessor(BaseProcessor):
    """Transcribes audio/video files using OpenAI Whisper API."""

    def extract_text(self) -> str:
        from openai import OpenAI
        from app.storage.s3 import download_file_to_tmp

        client = OpenAI()
        tmp_path = download_file_to_tmp(self.file_id)

        logger.info(f"Transcribing audio file_id={self.file_id}")
        with open(tmp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
            )

        return transcript.text

    def chunk_text(self, text: str) -> list[str]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
        )
        return splitter.split_text(text)

from app.processors.base import BaseProcessor
from langchain_text_splitters import RecursiveCharacterTextSplitter
import base64
from loguru import logger


class ImageProcessor(BaseProcessor):
    """Analyzes images using OpenAI Vision API."""

    def extract_text(self) -> str:
        from openai import OpenAI
        from app.storage.s3 import download_file_to_tmp

        client = OpenAI()
        tmp_path = download_file_to_tmp(self.file_id)

        image_data = base64.b64encode(tmp_path.read_bytes()).decode("utf-8")
        ext = tmp_path.suffix.lower().lstrip(".")
        mime = f"image/{ext}" if ext != "jpg" else "image/jpeg"

        logger.info(f"Analyzing image with Vision API — file_id={self.file_id}")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime};base64,{image_data}"},
                        },
                        {
                            "type": "text",
                            "text": "Descreva detalhadamente o conteúdo desta imagem, incluindo qualquer texto visível.",
                        },
                    ],
                }
            ],
            max_tokens=1000,
        )
        return response.choices[0].message.content or ""

    def chunk_text(self, text: str) -> list[str]:
        splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
        return splitter.split_text(text)

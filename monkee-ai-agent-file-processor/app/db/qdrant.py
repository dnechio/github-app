from functools import lru_cache

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
)
from openai import OpenAI

from app.core.config import settings

EMBEDDING_MODEL = "text-embedding-3-large"
VECTOR_SIZE = 3072   # text-embedding-3-large output dimension


@lru_cache(maxsize=1)
def _qdrant() -> QdrantClient:
    return QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY or None,
    )


@lru_cache(maxsize=1)
def _openai() -> OpenAI:
    return OpenAI(api_key=settings.OPENAI_API_KEY)


def ensure_collection(collection: str) -> None:
    """Creates the Qdrant collection if it doesn't exist."""
    client = _qdrant()
    existing = {c.name for c in client.get_collections().collections}
    if collection not in existing:
        client.create_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Batch-embeds texts via OpenAI. Splits into chunks of 100 to stay within limits."""
    client = _openai()
    all_vectors: list[list[float]] = []
    batch_size = 100
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        all_vectors.extend([item.embedding for item in response.data])
    return all_vectors


def index_chunks(
    collection: str,
    chunks: list[str],
    metadata: dict,
    start_id: int = 0,
) -> int:
    """
    Embeds and upserts chunks into Qdrant.

    metadata is attached as payload to every point (e.g. user_id, file_id, s3_key).
    Returns the number of points indexed.
    """
    if not chunks:
        return 0

    ensure_collection(collection)
    vectors = embed_texts(chunks)

    points = [
        PointStruct(
            id=start_id + i,
            vector=vector,
            payload={**metadata, "text": chunk, "chunk_index": start_id + i},
        )
        for i, (chunk, vector) in enumerate(zip(chunks, vectors))
    ]

    _qdrant().upsert(collection_name=collection, points=points)
    return len(points)


def delete_file_chunks(collection: str, file_id: str) -> None:
    """Removes all chunks belonging to a specific file_id from the collection."""
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    _qdrant().delete(
        collection_name=collection,
        points_selector=Filter(
            must=[FieldCondition(key="file_id", match=MatchValue(value=file_id))]
        ),
    )

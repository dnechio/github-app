from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime


class KnowledgeBaseStats(BaseModel):
    total_documents: int = 0
    total_chunks: int = 0
    last_indexed_at: datetime | None = None


class KnowledgeBase(BaseModel):
    id: str
    name: str
    description: str
    tenant: str
    type: Literal["document", "jurisprudence", "legislation", "custom"] = "document"

    vector_collection: str
    embedding_model: str = "text-embedding-3-large"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    chunking_strategy: Literal["fixed", "semantic", "recursive"] = "recursive"

    linked_agents: list[str] = Field(default_factory=list)
    stats: KnowledgeBaseStats = Field(default_factory=KnowledgeBaseStats)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

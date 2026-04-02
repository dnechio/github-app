from agno.knowledge.combined import CombinedKnowledgeBase
from agno.vectordb.qdrant import Qdrant
from agno.embedder.openai import OpenAIEmbedder

from app.core.config import settings
from app.models.knowledge_base import KnowledgeBase
from app.services.agents.context import UserContext


def _make_qdrant(collection: str, embedder=None) -> Qdrant:
    return Qdrant(
        collection=collection,
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY or None,
        embedder=embedder or OpenAIEmbedder(id="text-embedding-3-large"),
    )


def build_admin_kb_source(kb: KnowledgeBase):
    """Returns an Agno knowledge source for an admin Knowledge Base."""
    from agno.knowledge.qdrant import QdrantKnowledgeBase

    return QdrantKnowledgeBase(
        collection=kb.vector_collection,
        vector_db=_make_qdrant(kb.vector_collection),
        num_documents=10,
    )


def build_user_kb_source(user_ctx: UserContext):
    """Returns an Agno knowledge source scoped to the user's private namespace."""
    from agno.knowledge.qdrant import QdrantKnowledgeBase

    return QdrantKnowledgeBase(
        collection=user_ctx.vector_namespace,
        vector_db=_make_qdrant(user_ctx.vector_namespace),
        num_documents=8,
        # Filter applied at query time to ensure namespace isolation
        search_kwargs={"filter": {"must": [{"key": "user_id", "match": {"value": user_ctx.user_id}}]}},
    )


def build_knowledge(
    kb_configs: list[KnowledgeBase],
    user_ctx: UserContext,
    can_use_user_files: bool,
) -> CombinedKnowledgeBase | None:
    sources = [build_admin_kb_source(kb) for kb in kb_configs]

    if can_use_user_files:
        sources.append(build_user_kb_source(user_ctx))

    if not sources:
        return None

    return CombinedKnowledgeBase(sources=sources)

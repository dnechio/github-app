from agno.memory.db.mongodb import MongoDbMemory
from agno.memory.summarizer import SessionSummarizer

from app.core.config import settings
from app.services.agents.context import UserContext
from app.services.agents.models import SUMMARIZER_MODEL


def build_memory(user_ctx: UserContext) -> MongoDbMemory:
    """
    Builds Agno persistent memory for a user.

    - Summaries and user profile are stored in MongoDB under
      collection  memory_{tenant_id}, partitioned by user_id.
    - create_user_memories=True extracts preference facts after each run.
    - update_user_memories_after_run=True keeps the profile fresh.
    """
    return MongoDbMemory(
        db_url=settings.MONGODB_URI,
        db_name=settings.MONGODB_DB,
        collection_name=f"memory_{user_ctx.tenant_id}",
        user_id=user_ctx.user_id,
        create_user_memories=True,
        update_user_memories_after_run=True,
        summarizer=SessionSummarizer(model=SUMMARIZER_MODEL()),
    )

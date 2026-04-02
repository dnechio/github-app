from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.admin_auth import require_admin
from app.core.auth import TokenPayload
from app.core.database import get_db

router = APIRouter(prefix="/admin/monitoring", tags=["admin:monitoring"])

Tenant = Annotated[TokenPayload, Depends(require_admin)]


@router.get("/usage")
async def usage_summary(
    payload: Tenant,
    period: str = Query("day", pattern="^(day|week|month)$"),
):
    """
    Aggregated token/call usage per agent for the given period.
    Reads from the usage_records collection.
    """
    db = get_db()
    since = {
        "day": datetime.utcnow() - timedelta(days=1),
        "week": datetime.utcnow() - timedelta(weeks=1),
        "month": datetime.utcnow() - timedelta(days=30),
    }[period]

    pipeline = [
        {"$match": {"tenant": payload.tenant, "created_at": {"$gte": since}}},
        {"$group": {
            "_id": "$agent_id",
            "total_calls": {"$sum": 1},
            "total_input_tokens": {"$sum": "$input_tokens"},
            "total_output_tokens": {"$sum": "$output_tokens"},
            "unique_users": {"$addToSet": "$user_id"},
        }},
        {"$project": {
            "agent_id": "$_id",
            "total_calls": 1,
            "total_input_tokens": 1,
            "total_output_tokens": 1,
            "unique_users": {"$size": "$unique_users"},
        }},
        {"$sort": {"total_calls": -1}},
    ]
    cursor = db["usage_records"].aggregate(pipeline)
    return [doc async for doc in cursor]


@router.get("/logs")
async def recent_logs(
    payload: Tenant,
    limit: int = Query(50, le=200),
    agent_id: str | None = None,
    user_id: str | None = None,
    level: str | None = Query(None, pattern="^(info|warning|error)$"),
):
    """Returns recent agent execution logs for the tenant."""
    db = get_db()
    query: dict = {"tenant": payload.tenant}
    if agent_id:
        query["agent_id"] = agent_id
    if user_id:
        query["user_id"] = user_id
    if level:
        query["level"] = level

    cursor = db["agent_logs"].find(query).sort("created_at", -1).limit(limit)
    return [
        {**doc, "_id": str(doc["_id"])}
        async for doc in cursor
    ]


@router.get("/errors")
async def recent_errors(
    payload: Tenant,
    limit: int = Query(20, le=100),
):
    """Returns recent errors across all agents for the tenant."""
    db = get_db()
    cursor = (
        db["agent_logs"]
        .find({"tenant": payload.tenant, "level": "error"})
        .sort("created_at", -1)
        .limit(limit)
    )
    return [{**doc, "_id": str(doc["_id"])} async for doc in cursor]


@router.get("/stats")
async def global_stats(payload: Tenant):
    """Quick summary: total agents, KBs, pipelines, users."""
    db = get_db()
    tenant = payload.tenant

    agents_count, kb_count, pipeline_count, user_count = await _multi_count(
        db, tenant,
        ("agents", "knowledge_bases", "pipelines", "users"),
    )
    return {
        "agents": agents_count,
        "knowledge_bases": kb_count,
        "pipelines": pipeline_count,
        "users": user_count,
    }


async def _multi_count(db, tenant: str, collections: tuple) -> list[int]:
    return [
        await db[col].count_documents({"tenant": tenant})
        for col in collections
    ]

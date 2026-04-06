#!/usr/bin/env python3
"""
Cria um agente de teste básico para validar o chat.

Usage:
    python scripts/seed_agent.py
"""
import asyncio
import sys
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, ".")
from app.core.config import settings


async def main():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB]

    existing = await db["agents"].find_one({"slug": "assistente-geral", "tenant": "default"})
    if existing:
        print("Agente 'assistente-geral' já existe.")
        client.close()
        return

    result = await db["agents"].insert_one({
        "tenant": "default",
        "name": "Assistente Geral",
        "slug": "assistente-geral",
        "description": "Assistente jurídico generalista para testes",
        "enabled": True,
        "model": "claude-sonnet-4-6",
        "provider": "anthropic",
        "instructions": (
            "Você é um assistente jurídico especializado em direito brasileiro. "
            "Responda de forma clara, objetiva e sempre cite as bases legais relevantes. "
            "Quando não tiver certeza, indique explicitamente."
        ),
        "temperature": 0.7,
        "max_tokens": 4096,
        "reasoning_effort": None,
        "tools": [],
        "knowledge_bases": [],
        "can_use_user_files": False,
        "can_use_memory": True,
        "show_citations": False,
        "routing_tags": ["geral", "direito", "juridico"],
        "routing_description": "Assistente jurídico generalista — responde dúvidas gerais de direito brasileiro",
        "day_limit": 100,
        "week_limit": 500,
        "month_limit": 2000,
        "allowed_groups": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    })

    client.close()
    print(f"✓ Agente criado (id={result.inserted_id})")


if __name__ == "__main__":
    asyncio.run(main())

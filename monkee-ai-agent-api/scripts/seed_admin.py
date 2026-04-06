#!/usr/bin/env python3
"""
Seed script — creates the first admin user and tenant.

Usage:
    python scripts/seed_admin.py

The raw API key is printed once. Store it securely.
"""
import asyncio
import hashlib
import secrets
import sys
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, ".")

from app.core.config import settings


TENANT_ID = "default"


async def main():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB]

    # Create tenant if not exists
    existing_tenant = await db["tenants"].find_one({"_id": TENANT_ID})
    if not existing_tenant:
        await db["tenants"].insert_one({
            "_id": TENANT_ID,
            "name": "Default",
            "enabled": True,
            "created_at": datetime.utcnow(),
        })
        print(f"✓ Tenant '{TENANT_ID}' criado")
    else:
        print(f"  Tenant '{TENANT_ID}' já existe")

    # Create admin group
    existing_group = await db["user_groups"].find_one({"name": "admin", "tenant": TENANT_ID})
    if not existing_group:
        await db["user_groups"].insert_one({
            "name": "admin",
            "description": "Administradores do sistema",
            "tenant": TENANT_ID,
            "created_at": datetime.utcnow(),
        })
        print("✓ Grupo 'admin' criado")

    # Check if admin user already exists
    existing_admin = await db["users"].find_one({"email": "admin@criminal-player.local"})
    if existing_admin:
        print("\n⚠ Usuário admin já existe. Use /admin/users/{id}/rotate-key para gerar nova API key.")
        client.close()
        return

    # Create admin user
    raw_key = secrets.token_urlsafe(32)
    api_key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    result = await db["users"].insert_one({
        "tenant": TENANT_ID,
        "name": "Admin",
        "email": "admin@criminal-player.local",
        "api_key_hash": api_key_hash,
        "groups": ["admin"],
        "enabled": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    })

    client.close()

    print(f"\n✓ Usuário admin criado (id={result.inserted_id})")
    print("\n" + "="*60)
    print("  API KEY (copie agora — não será exibida novamente):")
    print(f"\n  {raw_key}\n")
    print("="*60)
    print("\nUse essa key no frontend para fazer login:")
    print(f"  POST /api/v1/auth/session  {{\"api_key\": \"<key>\"}}")
    print("\nO JWT retornado deve ser enviado como: Authorization: Bearer <jwt>")


if __name__ == "__main__":
    asyncio.run(main())

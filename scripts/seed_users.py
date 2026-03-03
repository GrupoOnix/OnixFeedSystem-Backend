"""
Seed script: crea 3 usuarios demo en la base de datos.

Uso:
    python scripts/seed_users.py                   # Solo crear usuarios
    python scripts/seed_users.py --assign-orphans   # Crear usuarios + asignar datos huerfanos a demo1
"""

import asyncio
import argparse
import sys
from pathlib import Path
from uuid import UUID

# Agregar src/ al path para importar modulos del proyecto
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import text
from infrastructure.persistence.database import get_session_context
from infrastructure.persistence.models.user_model import UserModel
from application.services.auth_service import AuthService

# Usuarios demo
DEMO_USERS = [
    {
        "username": "demo1",
        "password": "demo123",
        "name": "Usuario Demo 1",
        "role": "admin",
        "email": "demo1@onix.com",
    },
    {
        "username": "demo2",
        "password": "demo123",
        "name": "Usuario Demo 2",
        "role": "admin",
        "email": "demo2@onix.com",
    },
    {
        "username": "demo3",
        "password": "demo123",
        "name": "Usuario Demo 3",
        "role": "admin",
        "email": "demo3@onix.com",
    },
]

# Tablas raiz que tienen columna user_id
ROOT_TABLES = [
    "feeding_lines",
    "cages",
    "cage_groups",
    "silos",
    "feeding_sessions",
    "system_config",
    "foods",
    "alerts",
    "scheduled_alerts",
    "feedback",
    "slot_assignments",
]


async def seed_users() -> dict[str, UUID]:
    """Crea los usuarios demo si no existen. Retorna {username: user_id}."""
    created: dict[str, UUID] = {}

    async with get_session_context() as session:
        for user_data in DEMO_USERS:
            # Verificar si ya existe
            result = await session.execute(
                text("SELECT id FROM users WHERE username = :username"),
                {"username": user_data["username"]},
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"  [skip] '{user_data['username']}' ya existe (id: {existing})")
                created[user_data["username"]] = existing
                continue

            # Crear usuario
            password_hash, salt = AuthService.hash_password(user_data["password"])
            from datetime import datetime, timezone
            from uuid import uuid4

            user_id = uuid4()
            user_model = UserModel(
                id=user_id,
                username=user_data["username"],
                password_hash=password_hash,
                password_salt=salt,
                name=user_data["name"],
                role=user_data["role"],
                email=user_data["email"],
                created_at=datetime.now(timezone.utc),
            )
            session.add(user_model)
            created[user_data["username"]] = user_id
            print(f"  [created] '{user_data['username']}' (id: {user_id})")

        await session.commit()

    return created


async def assign_orphans(demo1_id: UUID) -> None:
    """Asigna registros sin user_id al usuario demo1."""
    async with get_session_context() as session:
        total = 0
        for table in ROOT_TABLES:
            # Verificar si la tabla existe y tiene columna user_id
            try:
                result = await session.execute(
                    text(f"UPDATE {table} SET user_id = :uid WHERE user_id IS NULL"),  # noqa: S608
                    {"uid": demo1_id},
                )
                count = result.rowcount
                if count > 0:
                    print(f"  [assign] {table}: {count} registro(s) asignados a demo1")
                    total += count
            except Exception as e:
                print(f"  [warn] {table}: {e}")

        await session.commit()

        if total == 0:
            print("  [info] No se encontraron registros huerfanos")
        else:
            print(f"  [done] Total: {total} registro(s) asignados a demo1")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Seed de usuarios demo")
    parser.add_argument(
        "--assign-orphans",
        action="store_true",
        help="Asignar datos existentes sin user_id al usuario demo1",
    )
    args = parser.parse_args()

    print("=== Seed de usuarios demo ===\n")

    print("Creando usuarios...")
    users = await seed_users()

    if args.assign_orphans:
        demo1_id = users.get("demo1")
        if demo1_id:
            print("\nAsignando datos huerfanos a demo1...")
            await assign_orphans(demo1_id)
        else:
            print("\n[error] No se pudo obtener el ID de demo1")

    print("\n=== Seed completado ===")
    print("\nUsuarios disponibles:")
    for user_data in DEMO_USERS:
        uid = users.get(user_data["username"], "?")
        print(f"  {user_data['username']} / {user_data['password']}  (id: {uid})")


if __name__ == "__main__":
    asyncio.run(main())

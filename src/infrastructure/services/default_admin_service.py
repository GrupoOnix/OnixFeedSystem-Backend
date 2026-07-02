"""Servicio para crear el administrador por defecto al iniciar la aplicación."""

import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from domain.aggregates.user import User, UserRole
from infrastructure.persistence.repositories import UserRepository
from infrastructure.security.password_service import PasswordService

logger = logging.getLogger(__name__)

DEFAULT_ADMIN_USERNAME = "adminOnix"
DEFAULT_ADMIN_PASSWORD = "OnixServicios"
DEFAULT_ADMIN_FULL_NAME = "Administrador Onix"


async def seed_default_admin_if_needed(session: AsyncSession) -> None:
    """
    Crea el usuario administrador por defecto si no existe.

    El admin por defecto tiene:
    - username: adminOnix
    - password: OnixServicios
    - role: admin
    - is_superadmin: True
    - is_active: True

    La operación es idempotente: si otro worker ya creó el usuario, el
    IntegrityError del unique constraint se captura y se ignora, evitando
    race conditions al levantar la app con multiples workers.
    """
    user_repository = UserRepository(session)

    existing_admin = await user_repository.find_by_username(DEFAULT_ADMIN_USERNAME)
    if existing_admin:
        logger.info("El administrador por defecto ya existe: %s", DEFAULT_ADMIN_USERNAME)
        return

    hashed_password = PasswordService.hash_password(DEFAULT_ADMIN_PASSWORD)
    admin_user = User.create(
        username=DEFAULT_ADMIN_USERNAME,
        full_name=DEFAULT_ADMIN_FULL_NAME,
        hashed_password=hashed_password,
        role=UserRole.ADMIN,
        is_superadmin=True,
        is_active=True,
    )

    try:
        await user_repository.save(admin_user)
        await session.commit()
        logger.info("Administrador por defecto creado: %s", DEFAULT_ADMIN_USERNAME)
    except IntegrityError:
        await session.rollback()
        logger.info(
            "El administrador por defecto ya fue creado por otro proceso: %s",
            DEFAULT_ADMIN_USERNAME,
        )

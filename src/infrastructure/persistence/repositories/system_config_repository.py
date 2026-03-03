from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.aggregates.system_config import SystemConfig
from domain.repositories import ISystemConfigRepository
from domain.value_objects.identifiers import UserId
from infrastructure.persistence.models.system_config_model import SystemConfigModel


class SystemConfigRepository(ISystemConfigRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: UserId) -> SystemConfig:
        stmt = select(SystemConfigModel).where(SystemConfigModel.user_id == user_id.value)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            default = SystemConfig.create_default()
            default._user_id = user_id
            model = SystemConfigModel.from_domain(default)
            self.session.add(model)
            await self.session.flush()
        return model.to_domain()

    async def save(self, config: SystemConfig) -> None:
        stmt = select(SystemConfigModel).where(SystemConfigModel.user_id == config.user_id.value)  # type: ignore[union-attr]
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            existing.feeding_start_time = config.feeding_start_time
            existing.feeding_end_time = config.feeding_end_time
            existing.timezone_id = config.timezone_id
            existing.selector_positioning_time_seconds = config.selector_positioning_time_seconds
        else:
            self.session.add(SystemConfigModel.from_domain(config))
        await self.session.flush()

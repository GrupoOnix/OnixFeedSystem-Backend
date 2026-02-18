from sqlalchemy.ext.asyncio import AsyncSession

from domain.aggregates.system_config import SystemConfig
from domain.repositories import ISystemConfigRepository
from infrastructure.persistence.models.system_config_model import SystemConfigModel


class SystemConfigRepository(ISystemConfigRepository):

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self) -> SystemConfig:
        model = await self.session.get(SystemConfigModel, SystemConfig._SINGLETON_ID)
        if model is None:
            default = SystemConfig.create_default()
            model = SystemConfigModel.from_domain(default)
            self.session.add(model)
            await self.session.flush()
        return model.to_domain()

    async def save(self, config: SystemConfig) -> None:
        existing = await self.session.get(SystemConfigModel, config.id)
        if existing:
            existing.feeding_start_time = config.feeding_start_time
            existing.feeding_end_time = config.feeding_end_time
            existing.timezone_id = config.timezone_id
        else:
            self.session.add(SystemConfigModel.from_domain(config))
        await self.session.flush()

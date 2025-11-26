from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.aggregates.cage import Cage
from domain.repositories import ICageRepository
from domain.value_objects import CageId, CageName, LineId, SlotNumber
from infrastructure.persistence.models.cage_model import CageModel
from infrastructure.persistence.models.slot_assignment_model import SlotAssignmentModel
from infrastructure.persistence.models.feeding_line_model import FeedingLineModel


class CageRepository(ICageRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, cage: Cage) -> None:
        existing = await self.session.get(CageModel, cage.id.value)

        if existing:
            # Básicos
            existing.name = str(cage.name)
            existing.status = cage.status.value
            existing.created_at = cage.created_at
            
            # Población
            existing.current_fish_count = cage.current_fish_count.value if cage.current_fish_count else None
            
            # Biometría (convertir a miligramos)
            existing.avg_fish_weight_mg = cage.avg_fish_weight.as_miligrams if cage.avg_fish_weight else None
            
            # Configuración
            existing.fcr = float(cage.fcr) if cage.fcr else None
            existing.total_volume_m3 = cage.total_volume.as_cubic_meters if cage.total_volume else None
            existing.max_density_kg_m3 = float(cage.max_density) if cage.max_density else None
            existing.feeding_table_id = str(cage.feeding_table_id) if cage.feeding_table_id else None
            existing.transport_time_sec = cage.transport_time.value if cage.transport_time else None
        else:
            cage_model = CageModel.from_domain(cage)
            self.session.add(cage_model)
        
        await self.session.flush()

    async def find_by_id(self, cage_id: CageId) -> Optional[Cage]:
        cage_model = await self.session.get(CageModel, cage_id.value)
        return cage_model.to_domain() if cage_model else None

    async def find_by_name(self, name: CageName) -> Optional[Cage]:
        result = await self.session.execute(
            select(CageModel).where(CageModel.name == str(name))
        )
        cage_model = result.scalar_one_or_none()
        return cage_model.to_domain() if cage_model else None

    async def list(self) -> List[Cage]:
        """Lista todas las jaulas sin información adicional."""
        result = await self.session.execute(select(CageModel))
        cage_models = result.scalars().all()
        return [model.to_domain() for model in cage_models]

    async def list_with_line_info(self, line_id: Optional['LineId'] = None) -> List[Tuple[Cage, Optional[str]]]:
        """
        Lista jaulas con información de línea (nombre).
        Retorna tuplas de (Cage, line_name).
        """
        if line_id:
            # Join con slot_assignments y feeding_lines para obtener nombre
            query = (
                select(CageModel, SlotAssignmentModel.slot_number, FeedingLineModel.name)
                .join(SlotAssignmentModel, CageModel.id == SlotAssignmentModel.cage_id)
                .join(FeedingLineModel, SlotAssignmentModel.line_id == FeedingLineModel.id)
                .where(SlotAssignmentModel.line_id == line_id.value)
            )
            result = await self.session.execute(query)
            rows = result.all()
            
            cages_with_info = []
            for cage_model, slot_number, line_name in rows:
                cage = cage_model.to_domain()
                cage._line_id = line_id
                cage._slot_number = SlotNumber(slot_number)
                cages_with_info.append((cage, line_name))
            
            return cages_with_info
        else:
            # Sin filtro, traer todas las jaulas con left join
            query = (
                select(
                    CageModel, 
                    SlotAssignmentModel.line_id, 
                    SlotAssignmentModel.slot_number,
                    FeedingLineModel.name
                )
                .outerjoin(SlotAssignmentModel, CageModel.id == SlotAssignmentModel.cage_id)
                .outerjoin(FeedingLineModel, SlotAssignmentModel.line_id == FeedingLineModel.id)
            )
            result = await self.session.execute(query)
            rows = result.all()
            
            cages_with_info = []
            for cage_model, line_id_value, slot_number_value, line_name in rows:
                cage = cage_model.to_domain()
                if line_id_value:
                    cage._line_id = LineId(line_id_value)
                if slot_number_value is not None:
                    cage._slot_number = SlotNumber(slot_number_value)
                cages_with_info.append((cage, line_name))
            
            return cages_with_info

    async def delete(self, cage_id: CageId) -> None:
        cage_model = await self.session.get(CageModel, cage_id.value)
        if cage_model:
            await self.session.delete(cage_model)
            await self.session.flush()

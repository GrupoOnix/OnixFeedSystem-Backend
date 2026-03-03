from dataclasses import dataclass
from typing import Dict, List, Set, Any
from domain.repositories import IFeedingLineRepository, ISiloRepository, ICageRepository
from domain.value_objects import SiloId, CageId, LineId
from domain.value_objects.identifiers import UserId


@dataclass
class Delta:
    """Representa las diferencias entre el estado deseado y el actual."""

    silos_to_create: List[Any]
    silos_to_update: Dict[SiloId, Any]
    silos_to_delete: Set[SiloId]

    cages_to_create: List[Any]
    cages_to_update: Dict[CageId, Any]
    cages_to_delete: Set[CageId]

    lines_to_create: List[Any]
    lines_to_update: Dict[LineId, Any]
    lines_to_delete: Set[LineId]


class DeltaCalculator:
    """Calcula diferencias entre estado deseado y actual."""

    @staticmethod
    async def calculate(
        request: Any,
        line_repo: IFeedingLineRepository,
        silo_repo: ISiloRepository,
        cage_repo: ICageRepository,
        user_id: UserId,
    ) -> Delta:
        """Calcula qué crear, actualizar y eliminar."""

        # Cargar todos los IDs reales de la BD
        db_lines = await line_repo.get_all(user_id)
        db_silos = await silo_repo.get_all(user_id)
        db_cages = await cage_repo.list(user_id)

        db_line_ids_set = {line.id for line in db_lines}
        db_silo_ids_set = {silo.id for silo in db_silos}
        db_cage_ids_set = {cage.id for cage in db_cages}

        # Separar objetos en "Crear" vs "Actualizar"
        silos_to_update: Dict[SiloId, Any] = {}
        silos_to_create: List[Any] = []

        for item in request.silos:
            if DeltaCalculator._is_uuid(item.id):
                silo_id = SiloId.from_string(item.id)
                if silo_id in db_silo_ids_set:
                    silos_to_update[silo_id] = item
                else:
                    silos_to_create.append(item)
            else:
                silos_to_create.append(item)

        cages_to_update: Dict[CageId, Any] = {}
        cages_to_create: List[Any] = []

        for item in request.cages:
            if DeltaCalculator._is_uuid(item.id):
                cage_id = CageId.from_string(item.id)
                if cage_id in db_cage_ids_set:
                    cages_to_update[cage_id] = item
                else:
                    cages_to_create.append(item)
            else:
                cages_to_create.append(item)

        lines_to_update: Dict[LineId, Any] = {}
        lines_to_create: List[Any] = []

        for item in request.feeding_lines:
            if DeltaCalculator._is_uuid(item.id):
                line_id = LineId.from_string(item.id)
                if line_id in db_line_ids_set:
                    lines_to_update[line_id] = item
                else:
                    lines_to_create.append(item)
            else:
                lines_to_create.append(item)

        # Calcular IDs a eliminar
        silo_ids_to_delete = db_silo_ids_set - set(silos_to_update.keys())
        cage_ids_to_delete = db_cage_ids_set - set(cages_to_update.keys())
        line_ids_to_delete = db_line_ids_set - set(lines_to_update.keys())

        return Delta(
            silos_to_create=silos_to_create,
            silos_to_update=silos_to_update,
            silos_to_delete=silo_ids_to_delete,
            cages_to_create=cages_to_create,
            cages_to_update=cages_to_update,
            cages_to_delete=cage_ids_to_delete,
            lines_to_create=lines_to_create,
            lines_to_update=lines_to_update,
            lines_to_delete=line_ids_to_delete,
        )

    @staticmethod
    def _is_uuid(id_str: str) -> bool:
        """Verifica si un string es un UUID válido."""
        import uuid

        try:
            uuid.UUID(id_str)
            return True
        except ValueError:
            return False

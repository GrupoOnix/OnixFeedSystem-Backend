from domain.exceptions import SiloInUseError, SiloNotFoundError
from domain.repositories import ISiloRepository
from domain.value_objects import SiloId


class DeleteSiloUseCase:
    """Caso de uso para eliminar un silo."""

    def __init__(self, silo_repository: ISiloRepository):
        self._silo_repository = silo_repository

    async def execute(self, silo_id: str) -> None:
        """
        Ejecuta el caso de uso para eliminar un silo.

        Args:
            silo_id: ID del silo a eliminar

        Raises:
            SiloNotFoundError: Si el silo no existe
            SiloInUseError: Si el silo está asignado a un dosificador
        """
        # Buscar el silo
        silo_id_vo = SiloId.from_string(silo_id)
        silo = await self._silo_repository.find_by_id(silo_id_vo)

        if not silo:
            raise SiloNotFoundError(f"Silo con ID {silo_id} no encontrado")

        # Validar que no esté asignado a un dosificador
        if silo.is_assigned:
            raise SiloInUseError(
                f"No se puede eliminar el silo '{silo.name}' porque está asignado a un dosificador"
            )

        # Eliminar el silo
        await self._silo_repository.delete(silo_id_vo)

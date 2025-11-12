"""
Caso de Uso: Obtener Layout del Sistema

Responsabilidad:
- Cargar todos los agregados del sistema desde los repositorios
- Convertir entidades de dominio a DTOs (usando DomainToDTOMapper)
- Retornar el layout completo con IDs reales
"""

from application.dtos import SystemLayoutDTO
from application.mappers import DomainToDTOMapper
from domain.repositories import (
    IFeedingLineRepository,
    ISiloRepository,
    ICageRepository
)


class GetSystemLayoutUseCase:
    """
    Caso de uso para obtener el layout completo del sistema.
    
    Carga todos los agregados desde los repositorios y los convierte
    a DTOs para ser consumidos por la capa de presentación.
    """

    def __init__(self,
                 line_repo: IFeedingLineRepository,
                 silo_repo: ISiloRepository,
                 cage_repo: ICageRepository):
        self.line_repo = line_repo
        self.silo_repo = silo_repo
        self.cage_repo = cage_repo

    async def execute(self) -> SystemLayoutDTO:
        """
        Ejecuta el caso de uso para obtener el layout del sistema.
        
        Returns:
            SystemLayoutDTO con todos los agregados del sistema
        """
        # Cargar todos los agregados desde BD
        all_silos = await self.silo_repo.get_all()
        all_cages = await self.cage_repo.get_all()
        all_lines = await self.line_repo.get_all()
        
        # Convertir entidades de dominio a DTOs usando el mapper
        silos_dtos = [
            DomainToDTOMapper.silo_to_dto(silo)
            for silo in all_silos
        ]
        
        cages_dtos = [
            DomainToDTOMapper.cage_to_dto(cage)
            for cage in all_cages
        ]
        
        lines_dtos = [
            DomainToDTOMapper.feeding_line_to_dto(line)
            for line in all_lines
        ]
        
        return SystemLayoutDTO(
            silos=silos_dtos,
            cages=cages_dtos,
            feeding_lines=lines_dtos,
            presentation_data={"lines": {}}
        )

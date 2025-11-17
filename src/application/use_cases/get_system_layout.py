"""
Caso de Uso: Obtener Layout del Sistema

Responsabilidad:
- Cargar todos los agregados del sistema desde los repositorios
- Retornar entidades de dominio puras
"""

from typing import List, Tuple
from domain.repositories import (
    IFeedingLineRepository,
    ISiloRepository,
    ICageRepository
)
from domain.aggregates.silo import Silo
from domain.aggregates.cage import Cage
from domain.aggregates.feeding_line.feeding_line import FeedingLine


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

    async def execute(self) -> Tuple[List[Silo], List[Cage], List[FeedingLine]]:
        """
        Ejecuta el caso de uso para obtener el layout del sistema.
        
        Returns:
            Tupla con (silos, cages, lines) - entidades de dominio puras
        """
        # Cargar todos los agregados desde BD
        all_silos = await self.silo_repo.get_all()
        all_cages = await self.cage_repo.get_all()
        all_lines = await self.line_repo.get_all()
        
        return (all_silos, all_cages, all_lines)

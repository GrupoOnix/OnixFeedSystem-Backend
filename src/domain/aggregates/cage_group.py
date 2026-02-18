"""Aggregate Root para Grupos de Jaulas."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from domain.aggregates.cage import Cage
from domain.value_objects.identifiers import CageGroupId, CageId
from domain.value_objects.names import CageGroupName


@dataclass
class CageGroupMetrics:
    """Métricas calculadas para un grupo de jaulas."""

    total_population: int
    total_biomass: float
    avg_weight: float
    total_volume: float
    avg_density: float


class CageGroup:
    """
    Aggregate Root que representa un grupo de jaulas.

    Responsabilidades:
    - Identidad y metadatos del grupo
    - Gestión de membresía de jaulas
    - Cálculo de métricas agregadas

    NO es responsable de:
    - Validar que las jaulas existan (lo hace el repositorio/use case)
    - Almacenar datos de jaulas (solo referencias por ID)
    """

    def __init__(
        self,
        name: CageGroupName,
        cage_ids: List[CageId],
        description: Optional[str] = None,
    ):
        """
        Crea un nuevo grupo de jaulas.

        Args:
            name: Nombre único del grupo
            cage_ids: Lista de IDs de jaulas (debe tener al menos 1)
            description: Descripción opcional del grupo

        Raises:
            ValueError: Si cage_ids está vacío
        """
        if not cage_ids or len(cage_ids) == 0:
            raise ValueError("Un grupo debe contener al menos una jaula")

        self._id = CageGroupId.generate()
        self._name = name
        self._description = description
        self._cage_ids = list(set(cage_ids))  # Eliminar duplicados
        self._created_at = datetime.now(timezone.utc)
        self._updated_at = datetime.now(timezone.utc)

    # =========================================================================
    # PROPIEDADES DE IDENTIDAD
    # =========================================================================

    @property
    def id(self) -> CageGroupId:
        """ID único del grupo."""
        return self._id

    @property
    def name(self) -> CageGroupName:
        """Nombre del grupo."""
        return self._name

    @property
    def description(self) -> Optional[str]:
        """Descripción del grupo."""
        return self._description

    @property
    def cage_ids(self) -> List[CageId]:
        """Lista de IDs de jaulas en el grupo."""
        return self._cage_ids.copy()  # Retornar copia para evitar modificación externa

    @property
    def created_at(self) -> datetime:
        """Fecha de creación del grupo."""
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        """Fecha de última actualización del grupo."""
        return self._updated_at

    # =========================================================================
    # MÉTODOS DE GESTIÓN DE JAULAS
    # =========================================================================

    def add_cage(self, cage_id: CageId) -> None:
        """
        Agrega una jaula al grupo.

        Args:
            cage_id: ID de la jaula a agregar

        Note:
            Si la jaula ya existe en el grupo, no hace nada (idempotente).
        """
        if cage_id not in self._cage_ids:
            self._cage_ids.append(cage_id)
            self._updated_at = datetime.now(timezone.utc)

    def remove_cage(self, cage_id: CageId) -> None:
        """
        Remueve una jaula del grupo.

        Args:
            cage_id: ID de la jaula a remover

        Raises:
            ValueError: Si es la última jaula del grupo
        """
        if cage_id not in self._cage_ids:
            return  # No hacer nada si no está

        if len(self._cage_ids) == 1:
            raise ValueError(
                "No se puede remover la última jaula del grupo. "
                "Un grupo debe contener al menos una jaula."
            )

        self._cage_ids.remove(cage_id)
        self._updated_at = datetime.now(timezone.utc)

    def set_cages(self, cage_ids: List[CageId]) -> None:
        """
        Reemplaza todas las jaulas del grupo.

        Args:
            cage_ids: Nueva lista de IDs de jaulas

        Raises:
            ValueError: Si la lista está vacía
        """
        if not cage_ids or len(cage_ids) == 0:
            raise ValueError("Un grupo debe contener al menos una jaula")

        self._cage_ids = list(set(cage_ids))  # Eliminar duplicados
        self._updated_at = datetime.now(timezone.utc)

    def has_cage(self, cage_id: CageId) -> bool:
        """
        Verifica si una jaula pertenece al grupo.

        Args:
            cage_id: ID de la jaula a verificar

        Returns:
            True si la jaula está en el grupo, False en caso contrario
        """
        return cage_id in self._cage_ids

    # =========================================================================
    # MÉTODOS DE ACTUALIZACIÓN DE METADATOS
    # =========================================================================

    def update_name(self, new_name: CageGroupName) -> None:
        """
        Actualiza el nombre del grupo.

        Args:
            new_name: Nuevo nombre del grupo
        """
        self._name = new_name
        self._updated_at = datetime.now(timezone.utc)

    def update_description(self, description: Optional[str]) -> None:
        """
        Actualiza la descripción del grupo.

        Args:
            description: Nueva descripción (puede ser None)
        """
        self._description = description
        self._updated_at = datetime.now(timezone.utc)

    # =========================================================================
    # MÉTODOS DE CÁLCULO DE MÉTRICAS
    # =========================================================================

    def calculate_metrics(self, cages: List[Cage]) -> CageGroupMetrics:
        """
        Calcula métricas agregadas a partir de las jaulas del grupo.

        Args:
            cages: Lista de jaulas cargadas desde el repositorio

        Returns:
            CageGroupMetrics con las métricas calculadas

        Note:
            Las jaulas que no se encuentren en la lista (por ID) serán ignoradas.
            Esto permite calcular métricas incluso si algunas jaulas fueron eliminadas.
        """
        # Filtrar solo las jaulas que pertenecen al grupo
        relevant_cages = [
            cage for cage in cages if cage.id in self._cage_ids
        ]

        if not relevant_cages:
            return CageGroupMetrics(
                total_population=0,
                total_biomass=0.0,
                avg_weight=0.0,
                total_volume=0.0,
                avg_density=0.0,
            )

        # Calcular totales
        total_population = sum(cage.fish_count for cage in relevant_cages)
        total_biomass = sum(cage.biomass_kg for cage in relevant_cages)
        total_volume = sum(
            cage.config.volume_m3 or 0.0 for cage in relevant_cages
        )

        # Calcular promedios
        avg_weight = (
            (total_biomass / total_population * 1000)  # kg to grams
            if total_population > 0
            else 0.0
        )
        avg_density = (
            total_biomass / total_volume if total_volume > 0 else 0.0
        )

        return CageGroupMetrics(
            total_population=total_population,
            total_biomass=round(total_biomass, 2),
            avg_weight=round(avg_weight, 2),
            total_volume=round(total_volume, 2),
            avg_density=round(avg_density, 2),
        )

    # =========================================================================
    # MÉTODOS DE RECONSTRUCCIÓN (para repositorio)
    # =========================================================================

    def _set_id(self, group_id: CageGroupId) -> None:
        """Solo para uso del repositorio al reconstruir desde BD."""
        self._id = group_id

    def _set_created_at(self, created_at: datetime) -> None:
        """Solo para uso del repositorio al reconstruir desde BD."""
        self._created_at = created_at

    def _set_updated_at(self, updated_at: datetime) -> None:
        """Solo para uso del repositorio al reconstruir desde BD."""
        self._updated_at = updated_at

    # =========================================================================
    # FACTORY METHOD
    # =========================================================================

    @classmethod
    def create(
        cls,
        name: str,
        cage_ids: List[str],
        description: Optional[str] = None,
    ) -> "CageGroup":
        """
        Factory method para crear un nuevo grupo de jaulas.

        Args:
            name: Nombre del grupo
            cage_ids: Lista de IDs de jaulas como strings
            description: Descripción opcional

        Returns:
            Nueva instancia de CageGroup

        Raises:
            ValueError: Si los parámetros son inválidos
        """
        cage_id_objects = [CageId.from_string(id_str) for id_str in cage_ids]

        return cls(
            name=CageGroupName(name),
            cage_ids=cage_id_objects,
            description=description,
        )

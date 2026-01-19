"""Value Object para la configuración de una jaula."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CageConfiguration:
    """
    Configuración inmutable de una jaula.

    Agrupa todos los parámetros configurables de alimentación y físicos.
    Al ser inmutable, cualquier cambio retorna una nueva instancia.
    """

    fcr: Optional[float] = None  # Feed Conversion Ratio (0.5 - 3.0)
    volume_m3: Optional[float] = None  # Volumen en metros cúbicos
    max_density_kg_m3: Optional[float] = None  # Densidad máxima en kg/m³
    transport_time_seconds: Optional[int] = None  # Tiempo de transporte en segundos

    def __post_init__(self) -> None:
        """Valida los valores de configuración."""
        if self.fcr is not None:
            if not (0.5 <= self.fcr <= 3.0):
                raise ValueError("FCR debe estar entre 0.5 y 3.0")

        if self.volume_m3 is not None:
            if self.volume_m3 <= 0:
                raise ValueError("El volumen debe ser mayor a 0")

        if self.max_density_kg_m3 is not None:
            if self.max_density_kg_m3 <= 0:
                raise ValueError("La densidad máxima debe ser mayor a 0")

        if self.transport_time_seconds is not None:
            if self.transport_time_seconds < 0:
                raise ValueError("El tiempo de transporte no puede ser negativo")

    def with_fcr(self, fcr: Optional[float]) -> "CageConfiguration":
        """Retorna una nueva configuración con el FCR actualizado."""
        return CageConfiguration(
            fcr=fcr,
            volume_m3=self.volume_m3,
            max_density_kg_m3=self.max_density_kg_m3,
            transport_time_seconds=self.transport_time_seconds,
        )

    def with_volume(self, volume_m3: Optional[float]) -> "CageConfiguration":
        """Retorna una nueva configuración con el volumen actualizado."""
        return CageConfiguration(
            fcr=self.fcr,
            volume_m3=volume_m3,
            max_density_kg_m3=self.max_density_kg_m3,
            transport_time_seconds=self.transport_time_seconds,
        )

    def with_max_density(
        self, max_density_kg_m3: Optional[float]
    ) -> "CageConfiguration":
        """Retorna una nueva configuración con la densidad máxima actualizada."""
        return CageConfiguration(
            fcr=self.fcr,
            volume_m3=self.volume_m3,
            max_density_kg_m3=max_density_kg_m3,
            transport_time_seconds=self.transport_time_seconds,
        )

    def with_transport_time(
        self, transport_time_seconds: Optional[int]
    ) -> "CageConfiguration":
        """Retorna una nueva configuración con el tiempo de transporte actualizado."""
        return CageConfiguration(
            fcr=self.fcr,
            volume_m3=self.volume_m3,
            max_density_kg_m3=self.max_density_kg_m3,
            transport_time_seconds=transport_time_seconds,
        )

    @classmethod
    def empty(cls) -> "CageConfiguration":
        """Crea una configuración vacía (todos los valores en None)."""
        return cls()

    def is_empty(self) -> bool:
        """Verifica si todos los valores son None."""
        return (
            self.fcr is None
            and self.volume_m3 is None
            and self.max_density_kg_m3 is None
            and self.transport_time_seconds is None
        )

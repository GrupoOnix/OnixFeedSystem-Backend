"""
Entidad Comida (Feeding Operation).

Representa una operación completa de alimentación de inicio a fin.
Una comida puede ser MANUAL, CICLICA o PROGRAMADA, y contiene una o más visitas.
"""

from datetime import datetime
from typing import Optional

from ..enums import EstadoComida, TipoComida
from ..value_objects import ComidaId, LineId, Weight


# ============================================================================
# Entidad Comida
# ============================================================================


class Comida:
    """
    Entidad que representa una operación completa de alimentación.

    Una comida representa "ocupar la tubería bajo una programación de inicio a fin".
    Contiene una o más visitas a jaulas y mantiene el estado global de la operación.

    Reglas de negocio:
    - RN-06: No se puede iniciar si el tiempo estimado excede el día operativo restante
    - Puede pausarse y reanudarse
    - Se puede modificar tasa y potencia de blower en tiempo real durante la ejecución
    - Al interrumpirse, queda registro de qué visitas se completaron y cuáles no
    """

    def __init__(
        self,
        tipo: TipoComida,
        linea_id: LineId,
        operador_nombre: str,
        cantidad_total_programada: Weight,
        fecha_hora_inicio_programada: Optional[datetime] = None,
    ):
        """
        Crea una nueva comida.

        Args:
            tipo: Tipo de comida (MANUAL, CICLICA, PROGRAMADA)
            linea_id: ID de la línea de alimentación
            operador_nombre: Nombre del operador que inició la comida
            cantidad_total_programada: Cantidad total de alimento programada (kg)
            fecha_hora_inicio_programada: Fecha/hora programada (requerida para PROGRAMADA)
        """
        self._id = ComidaId.generate()
        self._tipo = tipo
        self._estado = EstadoComida.PROGRAMADA
        self._linea_id = linea_id
        self._operador_nombre = operador_nombre
        self._fecha_hora_inicio_programada = fecha_hora_inicio_programada
        self._fecha_hora_inicio_real: Optional[datetime] = None
        self._fecha_hora_fin: Optional[datetime] = None
        self._cantidad_total_programada = cantidad_total_programada
        self._created_at = datetime.utcnow()

        # Validaciones
        if not operador_nombre or not operador_nombre.strip():
            raise ValueError("El nombre del operador no puede estar vacío")

        if tipo == TipoComida.PROGRAMADA and not fecha_hora_inicio_programada:
            raise ValueError(
                "Las comidas PROGRAMADAS requieren fecha_hora_inicio_programada"
            )

    # =========================================================================
    # PROPIEDADES
    # =========================================================================

    @property
    def id(self) -> ComidaId:
        """ID único de la comida."""
        return self._id

    @property
    def tipo(self) -> TipoComida:
        """Tipo de comida."""
        return self._tipo

    @property
    def estado(self) -> EstadoComida:
        """Estado actual de la comida."""
        return self._estado

    @property
    def linea_id(self) -> LineId:
        """ID de la línea de alimentación asociada."""
        return self._linea_id

    @property
    def operador_nombre(self) -> str:
        """Nombre del operador que inició la comida."""
        return self._operador_nombre

    @property
    def fecha_hora_inicio_programada(self) -> Optional[datetime]:
        """Fecha/hora de inicio programada (para tipo PROGRAMADA)."""
        return self._fecha_hora_inicio_programada

    @property
    def fecha_hora_inicio_real(self) -> Optional[datetime]:
        """Fecha/hora de inicio real."""
        return self._fecha_hora_inicio_real

    @property
    def fecha_hora_fin(self) -> Optional[datetime]:
        """Fecha/hora de finalización."""
        return self._fecha_hora_fin

    @property
    def cantidad_total_programada(self) -> Weight:
        """Cantidad total de alimento programada."""
        return self._cantidad_total_programada

    @property
    def created_at(self) -> datetime:
        """Timestamp de creación."""
        return self._created_at

    # =========================================================================
    # MÉTODOS DE NEGOCIO - TRANSICIONES DE ESTADO
    # =========================================================================

    def iniciar(self) -> None:
        """
        Inicia la comida.

        Transición: PROGRAMADA -> EN_CURSO

        Raises:
            ValueError: Si el estado no permite iniciar
        """
        if self._estado != EstadoComida.PROGRAMADA:
            raise ValueError(
                f"No se puede iniciar una comida en estado {self._estado.value}"
            )

        self._estado = EstadoComida.EN_CURSO
        self._fecha_hora_inicio_real = datetime.utcnow()

    def pausar(self) -> None:
        """
        Pausa la comida.

        Transición: EN_CURSO -> PAUSADA

        Raises:
            ValueError: Si el estado no permite pausar
        """
        if self._estado != EstadoComida.EN_CURSO:
            raise ValueError(
                f"No se puede pausar una comida en estado {self._estado.value}"
            )

        self._estado = EstadoComida.PAUSADA

    def reanudar(self) -> None:
        """
        Reanuda la comida.

        Transición: PAUSADA -> EN_CURSO

        Raises:
            ValueError: Si el estado no permite reanudar
        """
        if self._estado != EstadoComida.PAUSADA:
            raise ValueError(
                f"No se puede reanudar una comida en estado {self._estado.value}"
            )

        self._estado = EstadoComida.EN_CURSO

    def completar(self) -> None:
        """
        Marca la comida como completada.

        Transición: EN_CURSO -> COMPLETADA

        Raises:
            ValueError: Si el estado no permite completar
        """
        if self._estado != EstadoComida.EN_CURSO:
            raise ValueError(
                f"No se puede completar una comida en estado {self._estado.value}"
            )

        self._estado = EstadoComida.COMPLETADA
        self._fecha_hora_fin = datetime.utcnow()

    def cancelar(self) -> None:
        """
        Cancela la comida.

        Transición: EN_CURSO | PAUSADA -> CANCELADA

        Raises:
            ValueError: Si el estado no permite cancelar
        """
        if self._estado not in [EstadoComida.EN_CURSO, EstadoComida.PAUSADA]:
            raise ValueError(
                f"No se puede cancelar una comida en estado {self._estado.value}"
            )

        self._estado = EstadoComida.CANCELADA
        self._fecha_hora_fin = datetime.utcnow()

    def interrumpir(self, motivo: str) -> None:
        """
        Interrumpe la comida por límite horario o alarma.

        Transición: EN_CURSO -> INTERRUMPIDA

        Args:
            motivo: Razón de la interrupción

        Raises:
            ValueError: Si el estado no permite interrumpir
        """
        if self._estado != EstadoComida.EN_CURSO:
            raise ValueError(
                f"No se puede interrumpir una comida en estado {self._estado.value}"
            )

        if not motivo or not motivo.strip():
            raise ValueError("El motivo de interrupción no puede estar vacío")

        self._estado = EstadoComida.INTERRUMPIDA
        self._fecha_hora_fin = datetime.utcnow()
        # El motivo se guardará como evento del sistema

    # =========================================================================
    # MÉTODOS DE CONSULTA
    # =========================================================================

    def esta_activa(self) -> bool:
        """Retorna True si la comida está en curso o pausada."""
        return self._estado in [EstadoComida.EN_CURSO, EstadoComida.PAUSADA]

    def esta_finalizada(self) -> bool:
        """Retorna True si la comida está completada, cancelada o interrumpida."""
        return self._estado in [
            EstadoComida.COMPLETADA,
            EstadoComida.CANCELADA,
            EstadoComida.INTERRUMPIDA,
        ]

    def puede_modificarse(self) -> bool:
        """Retorna True si se pueden modificar parámetros en tiempo real."""
        return self._estado == EstadoComida.EN_CURSO

    def duracion_total_segundos(self) -> Optional[float]:
        """
        Calcula la duración total en segundos.

        Returns:
            Duración en segundos si la comida finalizó, None si aún está en curso
        """
        if not self._fecha_hora_inicio_real:
            return None

        fecha_fin = self._fecha_hora_fin or datetime.utcnow()
        delta = fecha_fin - self._fecha_hora_inicio_real
        return delta.total_seconds()

    # =========================================================================
    # MÉTODOS DE RECONSTRUCCIÓN (para repositorio)
    # =========================================================================

    def _set_id(self, comida_id: ComidaId) -> None:
        """Solo para uso del repositorio al reconstruir desde BD."""
        self._id = comida_id

    def _set_estado(self, estado: EstadoComida) -> None:
        """Solo para uso del repositorio al reconstruir desde BD."""
        self._estado = estado

    def _set_fecha_hora_inicio_real(self, fecha_hora: Optional[datetime]) -> None:
        """Solo para uso del repositorio al reconstruir desde BD."""
        self._fecha_hora_inicio_real = fecha_hora

    def _set_fecha_hora_fin(self, fecha_hora: Optional[datetime]) -> None:
        """Solo para uso del repositorio al reconstruir desde BD."""
        self._fecha_hora_fin = fecha_hora

    def _set_created_at(self, created_at: datetime) -> None:
        """Solo para uso del repositorio al reconstruir desde BD."""
        self._created_at = created_at

    # =========================================================================
    # FACTORY METHODS
    # =========================================================================

    @classmethod
    def crear_manual(
        cls,
        linea_id: LineId,
        operador_nombre: str,
        cantidad_total_kg: float,
    ) -> "Comida":
        """
        Factory method para crear una comida manual.

        Args:
            linea_id: ID de la línea de alimentación
            operador_nombre: Nombre del operador
            cantidad_total_kg: Cantidad total en kg

        Returns:
            Nueva instancia de Comida tipo MANUAL
        """
        return cls(
            tipo=TipoComida.MANUAL,
            linea_id=linea_id,
            operador_nombre=operador_nombre,
            cantidad_total_programada=Weight.from_kg(cantidad_total_kg),
        )

    @classmethod
    def crear_ciclica(
        cls,
        linea_id: LineId,
        operador_nombre: str,
        cantidad_total_kg: float,
    ) -> "Comida":
        """
        Factory method para crear una comida cíclica.

        Args:
            linea_id: ID de la línea de alimentación
            operador_nombre: Nombre del operador
            cantidad_total_kg: Cantidad total en kg

        Returns:
            Nueva instancia de Comida tipo CICLICA
        """
        return cls(
            tipo=TipoComida.CICLICA,
            linea_id=linea_id,
            operador_nombre=operador_nombre,
            cantidad_total_programada=Weight.from_kg(cantidad_total_kg),
        )

    @classmethod
    def crear_programada(
        cls,
        linea_id: LineId,
        operador_nombre: str,
        cantidad_total_kg: float,
        fecha_hora_inicio: datetime,
    ) -> "Comida":
        """
        Factory method para crear una comida programada.

        Args:
            linea_id: ID de la línea de alimentación
            operador_nombre: Nombre del operador
            cantidad_total_kg: Cantidad total en kg
            fecha_hora_inicio: Fecha/hora programada de inicio

        Returns:
            Nueva instancia de Comida tipo PROGRAMADA
        """
        return cls(
            tipo=TipoComida.PROGRAMADA,
            linea_id=linea_id,
            operador_nombre=operador_nombre,
            cantidad_total_programada=Weight.from_kg(cantidad_total_kg),
            fecha_hora_inicio_programada=fecha_hora_inicio,
        )

from datetime import datetime
from typing import List, Optional

from ..enums import EstadoVisita
from ..value_objects import CageId, CambioTasa, ComidaId, TasaAlimentacion, VisitaId, Weight


class Visita:

    def __init__(
        self,
        comida_id: ComidaId,
        jaula_id: CageId,
        numero_visita: int,
        orden_ejecucion: int,
        cantidad_programada: Weight,
        tasa_inicial: TasaAlimentacion,
        potencia_blower: int,
    ):
        self._id = VisitaId.generate()
        self._comida_id = comida_id
        self._jaula_id = jaula_id
        self._numero_visita = numero_visita
        self._orden_ejecucion = orden_ejecucion
        self._cantidad_programada = cantidad_programada
        self._cantidad_dispensada = Weight.zero()
        self._tasa_inicial = tasa_inicial
        self._tasa_actual = tasa_inicial
        self._potencia_blower = potencia_blower
        self._estado = EstadoVisita.PENDIENTE
        self._fecha_hora_inicio: Optional[datetime] = None
        self._fecha_hora_fin: Optional[datetime] = None
        self._historial_cambios_tasa: List[CambioTasa] = []
        self._created_at = datetime.utcnow()

        if numero_visita <= 0:
            raise ValueError("El número de visita debe ser mayor a 0")
        if orden_ejecucion <= 0:
            raise ValueError("El orden de ejecución debe ser mayor a 0")
        if not (0 <= potencia_blower <= 100):
            raise ValueError("La potencia del blower debe estar entre 0 y 100%")

    @property
    def id(self) -> VisitaId:
        return self._id

    @property
    def comida_id(self) -> ComidaId:
        return self._comida_id

    @property
    def jaula_id(self) -> CageId:
        return self._jaula_id

    @property
    def numero_visita(self) -> int:
        return self._numero_visita

    @property
    def orden_ejecucion(self) -> int:
        return self._orden_ejecucion

    @property
    def cantidad_programada(self) -> Weight:
        return self._cantidad_programada

    @property
    def cantidad_dispensada(self) -> Weight:
        return self._cantidad_dispensada

    @property
    def tasa_inicial(self) -> TasaAlimentacion:
        return self._tasa_inicial

    @property
    def tasa_actual(self) -> TasaAlimentacion:
        return self._tasa_actual

    @property
    def potencia_blower(self) -> int:
        return self._potencia_blower

    @property
    def estado(self) -> EstadoVisita:
        return self._estado

    @property
    def fecha_hora_inicio(self) -> Optional[datetime]:
        return self._fecha_hora_inicio

    @property
    def fecha_hora_fin(self) -> Optional[datetime]:
        return self._fecha_hora_fin

    @property
    def historial_cambios_tasa(self) -> List[CambioTasa]:
        return list(self._historial_cambios_tasa)

    @property
    def created_at(self) -> datetime:
        return self._created_at

    def iniciar(self) -> None:
        if self._estado != EstadoVisita.PENDIENTE:
            raise ValueError(
                f"No se puede iniciar una visita en estado {self._estado.value}"
            )

        self._estado = EstadoVisita.EN_CURSO
        self._fecha_hora_inicio = datetime.utcnow()

    def completar(self) -> None:
        if self._estado != EstadoVisita.EN_CURSO:
            raise ValueError(
                f"No se puede completar una visita en estado {self._estado.value}"
            )

        self._estado = EstadoVisita.COMPLETADA
        self._fecha_hora_fin = datetime.utcnow()

    def cancelar(self) -> None:
        if self._estado not in [EstadoVisita.EN_CURSO, EstadoVisita.PENDIENTE]:
            raise ValueError(
                f"No se puede cancelar una visita en estado {self._estado.value}"
            )

        self._estado = EstadoVisita.CANCELADA
        if self._estado == EstadoVisita.EN_CURSO:
            self._fecha_hora_fin = datetime.utcnow()

    def cambiar_tasa(
        self, nueva_tasa: TasaAlimentacion, operador_nombre: str
    ) -> CambioTasa:
        if self._estado != EstadoVisita.EN_CURSO:
            raise ValueError(
                f"No se puede cambiar la tasa en una visita en estado {self._estado.value}"
            )

        cambio = CambioTasa(
            timestamp=datetime.utcnow(),
            tasa_anterior=self._tasa_actual,
            tasa_nueva=nueva_tasa,
            operador_nombre=operador_nombre,
        )

        self._tasa_actual = nueva_tasa
        self._historial_cambios_tasa.append(cambio)

        return cambio

    def registrar_alimento_dispensado(self, cantidad: Weight) -> None:
        if self._estado != EstadoVisita.EN_CURSO:
            raise ValueError(
                f"No se puede registrar alimento en una visita en estado {self._estado.value}"
            )

        self._cantidad_dispensada = self._cantidad_dispensada + cantidad

    def esta_activa(self) -> bool:
        return self._estado == EstadoVisita.EN_CURSO

    def esta_finalizada(self) -> bool:
        return self._estado in [EstadoVisita.COMPLETADA, EstadoVisita.CANCELADA]

    def porcentaje_completado(self) -> float:
        if self._cantidad_programada.as_kg == 0:
            return 0.0

        return (
            self._cantidad_dispensada.as_kg / self._cantidad_programada.as_kg
        ) * 100.0

    def duracion_total_segundos(self) -> Optional[float]:
        if not self._fecha_hora_inicio:
            return None

        if not self._fecha_hora_fin:
            if self._estado == EstadoVisita.EN_CURSO:
                delta = datetime.utcnow() - self._fecha_hora_inicio
                return delta.total_seconds()
            return None

        delta = self._fecha_hora_fin - self._fecha_hora_inicio
        return delta.total_seconds()

    def tasa_promedio_real(self) -> Optional[TasaAlimentacion]:
        duracion = self.duracion_total_segundos()
        if not duracion or duracion == 0:
            return None

        duracion_minutos = duracion / 60.0
        kg_dispensados = self._cantidad_dispensada.as_kg

        tasa_kg_min = kg_dispensados / duracion_minutos
        return TasaAlimentacion(kg_por_minuto=tasa_kg_min)

    def tiempo_estimado_restante_minutos(self) -> Optional[float]:
        if self._estado != EstadoVisita.EN_CURSO:
            return None

        cantidad_restante = self._cantidad_programada - self._cantidad_dispensada
        if cantidad_restante.as_kg <= 0:
            return 0.0

        tasa_kg_min = self._tasa_actual.kg_por_minuto
        if tasa_kg_min == 0:
            return None

        return cantidad_restante.as_kg / tasa_kg_min

    def _set_id(self, visita_id: VisitaId) -> None:
        self._id = visita_id

    def _set_estado(self, estado: EstadoVisita) -> None:
        self._estado = estado

    def _set_cantidad_dispensada(self, cantidad: Weight) -> None:
        self._cantidad_dispensada = cantidad

    def _set_tasa_actual(self, tasa: TasaAlimentacion) -> None:
        self._tasa_actual = tasa

    def _set_fecha_hora_inicio(self, fecha_hora: Optional[datetime]) -> None:
        self._fecha_hora_inicio = fecha_hora

    def _set_fecha_hora_fin(self, fecha_hora: Optional[datetime]) -> None:
        self._fecha_hora_fin = fecha_hora

    def _set_historial_cambios_tasa(self, historial: List[CambioTasa]) -> None:
        self._historial_cambios_tasa = historial

    def _set_created_at(self, created_at: datetime) -> None:
        self._created_at = created_at

    @classmethod
    def crear(
        cls,
        comida_id: ComidaId,
        jaula_id: CageId,
        numero_visita: int,
        orden_ejecucion: int,
        cantidad_programada_kg: float,
        tasa_kg_min: float,
        potencia_blower: int,
    ) -> "Visita":
        return cls(
            comida_id=comida_id,
            jaula_id=jaula_id,
            numero_visita=numero_visita,
            orden_ejecucion=orden_ejecucion,
            cantidad_programada=Weight.from_kg(cantidad_programada_kg),
            tasa_inicial=TasaAlimentacion(kg_por_minuto=tasa_kg_min),
            potencia_blower=potencia_blower,
        )

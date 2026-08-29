from domain.interfaces import IBlower

SELECTOR_POSITIONING_SECONDS = 5.0


def calculate_visit_duration(
    quantity_kg: float,
    rate_kg_per_min: float,
    transport_time_seconds: int,
    blower: IBlower,
    selector_positioning_seconds: float = SELECTOR_POSITIONING_SECONDS,
    include_blow_before: bool = True,
    include_blow_after: bool = True,
) -> float:
    """
    Calcula la duración estimada de una visita de alimentación en segundos.

    Flujo y fórmula:
        T_visita = T_selector [+ T_soplado_previo] + T_dosificacion + T_transporte [+ T_soplado_posterior]

    Donde:
        T_selector          = selector_positioning_seconds (configurable, posicionamiento mecánico)
        T_soplado_previo    = blow_before_feeding_time — solo en la primera visita de la sesión
        T_dosificacion      = (quantity_kg / rate_kg_per_min) * 60
        T_transporte        = transport_time_seconds (garantiza que el último pellet llega a la jaula)
        T_soplado_posterior = blow_after_feeding_time — solo en la última visita de la sesión

    Args:
        quantity_kg: Cantidad a dispensar en kg.
        rate_kg_per_min: Tasa de dosificación en kg/min.
        transport_time_seconds: Tiempo de transporte del pellet hasta la jaula (seg).
        blower: Entidad blower de la línea (provee tiempos de soplado).
        selector_positioning_seconds: Tiempo de posicionamiento de la selectora (seg).
        include_blow_before: Si True, incluye T_soplado_previo en el total.
        include_blow_after: Si True, incluye T_soplado_posterior en el total.

    Returns:
        Duración estimada total en segundos.
    """
    dispensing_time = (quantity_kg / rate_kg_per_min) * 60
    blow_before = blower.blow_before_feeding_time.value if include_blow_before else 0.0
    blow_after = blower.blow_after_feeding_time.value if include_blow_after else 0.0
    return selector_positioning_seconds + blow_before + dispensing_time + transport_time_seconds + blow_after


def calculate_paused_visit_duration(
    quantity_kg: float,
    rate_kg_per_min: float,
    transport_time_seconds: float,
    selector_positioning_seconds: float = SELECTOR_POSITIONING_SECONDS,
) -> float:
    """Calcula una espera simulada sin accionar selector, blower ni dosificador."""
    if quantity_kg < 0:
        raise ValueError("La cantidad simulada no puede ser negativa")
    if quantity_kg > 0 and rate_kg_per_min <= 0:
        raise ValueError("La tasa debe ser mayor a 0 cuando la pausa tiene cantidad simulada")
    dispensing_time = (quantity_kg / rate_kg_per_min) * 60 if quantity_kg > 0 else 0.0
    return selector_positioning_seconds + dispensing_time + transport_time_seconds


def calculate_cyclic_wait_duration(
    *,
    total_rounds: int,
    active_cage_count: int,
    wait_after_visit_seconds: float,
) -> float:
    total_visit_executions = total_rounds * active_cage_count
    waits_between_visits = max(total_visit_executions - 1, 0)
    return waits_between_visits * wait_after_visit_seconds

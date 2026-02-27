from domain.interfaces import IBlower

SELECTOR_POSITIONING_SECONDS = 5.0


def calculate_visit_duration(
    quantity_kg: float,
    rate_kg_per_min: float,
    transport_time_seconds: int,
    blower: IBlower,
    selector_positioning_seconds: float = SELECTOR_POSITIONING_SECONDS,
) -> float:
    """
    Calcula la duración estimada de una visita de alimentación en segundos.

    Flujo y fórmula:
        T_visita = T_selector + T_soplado_previo + T_dosificacion + T_transporte + T_soplado_posterior

    Donde:
        T_selector          = selector_positioning_seconds (configurable, posicionamiento mecánico)
        T_soplado_previo    = blow_before_feeding_time (prepara la línea)
        T_dosificacion      = (quantity_kg / rate_kg_per_min) * 60
        T_transporte        = transport_time_seconds (garantiza que el último pellet llega a la jaula)
        T_soplado_posterior = blow_after_feeding_time (limpieza final de la línea)

    Args:
        quantity_kg: Cantidad a dispensar en kg.
        rate_kg_per_min: Tasa de dosificación en kg/min.
        transport_time_seconds: Tiempo de transporte del pellet hasta la jaula (seg).
        blower: Entidad blower de la línea (provee tiempos de soplado).
        selector_positioning_seconds: Tiempo de posicionamiento de la selectora (seg).

    Returns:
        Duración estimada total en segundos.
    """
    dispensing_time = (quantity_kg / rate_kg_per_min) * 60
    return (
        selector_positioning_seconds
        + blower.blow_before_feeding_time.value
        + dispensing_time
        + transport_time_seconds
        + blower.blow_after_feeding_time.value
    )

"""Reglas temporales de planes diarios de alimentación."""


def calculate_window_seconds(start_time: str, end_time: str) -> float:
    """Calcula una ventana de una misma jornada; no admite cruzar medianoche."""
    start_hours, start_minutes = map(int, start_time.split(":"))
    end_hours, end_minutes = map(int, end_time.split(":"))
    start = start_hours * 3600 + start_minutes * 60
    end = end_hours * 3600 + end_minutes * 60
    if end <= start:
        raise ValueError("La alimentación debe comenzar y terminar durante el mismo día")
    return float(end - start)


def calculate_remaining_seconds(window_seconds: float, estimated_total_seconds: float) -> float:
    return round(window_seconds - estimated_total_seconds, 3)

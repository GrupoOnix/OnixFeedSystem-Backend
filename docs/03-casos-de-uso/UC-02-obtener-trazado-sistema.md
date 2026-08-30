# UC-02: Obtener el trazado del sistema

## Objetivo

Obtener la configuración física completa utilizada por el editor de trazado y
por las pantallas que necesitan reconstruir líneas, componentes y asignaciones.
Es una operación de solo lectura.

## Entradas HTTP

```http
GET /api/system-layout
GET /api/system-layout/export
Authorization: Bearer <token>
```

Ambos endpoints requieren un usuario autenticado y devuelven el mismo contrato.

## Flujo

1. Se cargan todos los silos, jaulas y líneas desde sus repositorios.
2. Para cada línea se cargan sus asignaciones de slots.
3. El mapper transforma los agregados de dominio a `SystemLayoutModel`.
4. La API devuelve el layout completo.

## Respuesta

```text
SystemLayoutModel
├── silos[]
│   ├── id
│   ├── name
│   └── capacity
├── cages[]
│   ├── id
│   └── name
└── feeding_lines[]
    ├── id, line_name y status
    ├── locked_by, locked_reason y locked_at
    ├── blower_config
    ├── cooler_config opcional
    ├── sensors_config[]
    ├── dosers_config[]
    ├── selector_config
    └── slot_assignments[]
```

Cada dosificador incluye sus parámetros de tasa y calibración, además de
`assigned_silo_ids`. `pulse_speed` sigue siendo un campo opcional por
compatibilidad y no debe retirarse sin migración.

## Límites del contrato

El layout solo representa configuración física. No incluye:

- stock total, reservado o disponible;
- partidas FIFO;
- alimento de un silo;
- historial de alimentación.

Esa información se obtiene mediante los endpoints específicos de silos y
alimentación.

Un sistema vacío devuelve listas vacías. El endpoint no modifica estado. Los
errores inesperados siguen el manejo estándar de FastAPI.

## Fuente autoritativa

- Contrato: `src/api/models/system_layout.py`.
- Mapper: `src/api/mappers/response_mapper.py`.
- Endpoint: `src/api/routers/system_layout.py`.
- Consulta: `src/application/use_cases/get_system_layout.py`.
- Contrato HTTP generado: `/docs` u `/openapi.json` con la API en ejecución.

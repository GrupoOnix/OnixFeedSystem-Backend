# UC-01: Sincronizar el trazado del sistema

## Objetivo

Persistir el estado deseado completo del editor de trazado. El caso de uso
calcula diferencias respecto de la base de datos, elimina recursos ausentes,
crea recursos nuevos, actualiza los existentes y devuelve el layout reconstruido
con identificadores reales.

## Entrada HTTP

```http
POST /api/system-layout
Authorization: Bearer <token>
Content-Type: application/json
```

Cualquier usuario autenticado puede ejecutar actualmente esta operación.

El body usa `SystemLayoutModel` y contiene:

- `silos`: `id`, `name` y `capacity`.
- `cages`: `id` y `name`.
- `feeding_lines`: configuración física completa de cada línea:
  - blower obligatorio;
  - uno o más dosificadores, cada uno con uno o más silos asignados;
  - selector obligatorio y sus asignaciones de slots;
  - sensores opcionales;
  - cooler opcional;
  - estado y datos de bloqueo de la línea.

El inventario FIFO no pertenece al layout. No se aceptan `food_id`, nivel de
stock ni partidas dentro de la configuración de un silo.

## Flujo

1. Se comparan los IDs recibidos con silos, jaulas y líneas persistidos.
2. Se eliminan asignaciones y entidades que ya no aparecen en el request.
3. Se crean primero silos y jaulas; sus IDs temporales se mapean a UUID reales.
4. Se crean líneas y se resuelven referencias a silos y jaulas.
5. Se actualizan las entidades existentes y sus componentes.
6. Se vuelve a leer el layout y se entrega el estado persistido al cliente.

## Identificadores temporales

El frontend puede enviar IDs no UUID para elementos nuevos. El backend los usa
solo durante la sincronización y devuelve UUID reales. Una referencia temporal
debe apuntar a otro elemento nuevo incluido en el mismo request.

## Reglas relevantes

- Los nombres de silos, jaulas y líneas deben ser únicos.
- Cada línea requiere blower, selector y al menos un dosificador.
- Un dosificador no puede repetir un silo dentro de `assigned_silo_ids`.
- Los IDs referenciados deben existir o ser creados en la misma sincronización.
- Los tipos de sensores y componentes deben estar soportados por sus factories.
- La eliminación puede rechazarse cuando las reglas del dominio indican que un
  recurso está en uso.

## Resultado

`200 OK` devuelve el mismo contrato `SystemLayoutModel`, ya con IDs persistidos
y referencias resueltas.

Los errores de validación, nombres duplicados o reglas de dominio se devuelven
como `400 Bad Request`. Los errores no contemplados se devuelven actualmente
como `500 Internal Server Error`.

## Fuente autoritativa

- Contrato: `src/api/models/system_layout.py`.
- Endpoint: `src/api/routers/system_layout.py`.
- Orquestación: `src/application/use_cases/sync_system_layout.py`.
- Contrato HTTP generado: `/docs` u `/openapi.json` con la API en ejecución.

# Endpoints

## System
- GET `/system/status`

## System Layout
- POST `/system-layout`
- GET `/system-layout/export`

## Cages
- GET `/cages`
- POST `/cages/{cage_id}/biometry`
- GET `/cages/{cage_id}/biometry`
- POST `/cages/{cage_id}/mortality`
- GET `/cages/{cage_id}/mortality`
- PATCH `/cages/{cage_id}/config`
- GET `/cages/{cage_id}/config-changes`

## Feeding Operations
- POST `/feeding/start`
- POST `/feeding/lines/{line_id}/stop`
- POST `/feeding/lines/{line_id}/pause`
- POST `/feeding/lines/{line_id}/resume`
- PATCH `/feeding/lines/{line_id}/parameters`

## Silos
- GET `/silos`
- GET `/silos/{silo_id}`
- POST `/silos`
- PATCH `/silos/{silo_id}`
- DELETE `/silos/{silo_id}`

## Foods
- GET `/foods`
- GET `/foods/{food_id}`
- POST `/foods`
- PATCH `/foods/{food_id}`
- PATCH `/foods/{food_id}/toggle-active`
- DELETE `/foods/{food_id}`

## Feeding Lines
- GET `/feeding-lines`
- GET `/feeding-lines/{line_id}`
- PATCH `/feeding-lines/{line_id}/selector`
- POST `/feeding-lines/{line_id}/selector/move-to-slot/{slot_number}`
- POST `/feeding-lines/{line_id}/selector/reset-position`
- PATCH `/feeding-lines/{line_id}/blower`
- PATCH `/feeding-lines/{line_id}/dosers/{doser_id}`
- GET `/feeding-lines/{line_id}/sensors/readings`

## Device Control

### Blower Control
- POST `/device-control/blowers/{blower_id}/on`
- POST `/device-control/blowers/{blower_id}/off`
- POST `/device-control/blowers/{blower_id}/set-power`

### Doser Control
- POST `/device-control/dosers/{doser_id}/on`
- POST `/device-control/dosers/{doser_id}/off`
- POST `/device-control/dosers/{doser_id}/set-rate`

### Selector Control
- POST `/device-control/selectors/{selector_id}/move`
- POST `/device-control/selectors/{selector_id}/reset`

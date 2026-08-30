# Deuda técnica vigente

Este documento contiene únicamente riesgos confirmados contra el código actual.
Los planes ejecutados y hallazgos ya resueltos se conservan en el historial de
Git, no en la documentación activa.

## Seguridad y configuración

### Credenciales iniciales hardcodeadas

`src/infrastructure/services/default_admin_service.py` mantiene el usuario y la
contraseña iniciales como constantes conocidas. Deben trasladarse a variables de
entorno y exigirse un cambio de contraseña durante el primer acceso.

### CORS abierto

`src/main.py` utiliza `allow_origins=["*"]`. Es adecuado para desarrollo local,
pero los orígenes permitidos deben configurarse explícitamente antes de un
despliegue fuera de una red controlada.

### Variables no propagadas por Docker Compose

`docker-compose.yml` transmite actualmente solo las variables de base de datos
al contenedor backend. La configuración JWT y los intervalos de alimentación
programada definidos en `.env.template` no se propagan y el contenedor utiliza
los defaults del código. Deben incorporarse explícitamente al servicio.

### Login sin rate limiting

`POST /api/auth/login` no limita intentos por IP o usuario. El riesgo es menor
en la red privada prevista, pero debe revisarse si el sistema se expone a otras
redes.

## Modelo y migraciones

### Modelo de actividad especializado por entidad

Existen value objects separados para actividad de jaulas y grupos de jaulas.
Antes de agregar auditoría para más tipos de entidad conviene evaluar un modelo
común basado en `source_entity_type` y `source_entity_id`.

### Alineación de la migración de usuarios

La migración inicial de `users` expresa la unicidad de `username` mediante una
constraint y un índice separado, mientras el modelo SQLModel declara el campo
como único e indexado. El esquema funciona, pero puede producir diferencias
ruidosas al usar autogenerate.

## Compatibilidad pendiente de retirar

`pulse_speed` continúa presente en el dominio, persistencia, contrato del layout
y fallback de calibración. Su retiro requiere auditar datos existentes y crear
una migración coordinada con el frontend; no debe tratarse como código muerto.

## Criterio de cierre

Cada punto debe eliminarse de este documento cuando el cambio esté implementado,
cubierto por pruebas y, cuando corresponda, aplicado mediante migración.

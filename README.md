# Feeding System API

API de control y monitoreo para el sistema de alimentación acuícola Onix.
Expone autenticación, configuración del trazado, inventario FIFO de silos,
alimentaciones manuales, cíclicas y programadas, historial, alertas y gestión
de usuarios.

## Requisitos

- Docker con Docker Compose, o Python 3.11+ para desarrollo local.
- PostgreSQL.
- Un archivo `.env` basado en `.env.template`.

## Inicio con Docker

```bash
cp .env.template .env
docker compose up -d --build
```

Servicios disponibles:

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- PostgreSQL: `localhost:5432`

Comandos habituales:

```bash
docker compose logs -f backend
docker compose exec backend alembic upgrade head
docker compose down
```

`docker compose down -v` elimina también el volumen y todos los datos locales.

## Desarrollo local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
cd src
uvicorn main:app --reload --port 8000
```

La configuración disponible se describe en `.env.template`.
`JWT_SECRET_KEY` debe cambiarse fuera de desarrollo. El Compose actual solo
propaga las variables de base de datos; la propagación del resto está registrada
en [deuda técnica](docs/deuda-tecnica.md).

## Autenticación

La API utiliza JWT Bearer. Salvo health y OpenAPI, los endpoints bajo `/api`
requieren el header:

```http
Authorization: Bearer <access_token>
```

El token dura 24 horas por defecto y no existe refresh token. Endpoints
principales:

| Método | Endpoint | Acceso |
| --- | --- | --- |
| `POST` | `/api/auth/login` | Público |
| `GET` | `/api/auth/me` | Usuario autenticado |
| `PATCH` | `/api/auth/me/password` | Usuario autenticado |
| `POST` | `/api/users` | Admin o superadmin |
| `GET` | `/api/users` | Admin o superadmin |
| `PATCH` | `/api/users/{id}/status` | Admin o superadmin |
| `PATCH` | `/api/users/{id}/role` | Superadmin |
| `PATCH` | `/api/users/{id}/password` | Superadmin |

En una base nueva, el servicio crea el superadministrador definido actualmente
en `src/infrastructure/services/default_admin_service.py`. Es una facilidad de
bootstrap pendiente de migrar a configuración externa; la contraseña debe
cambiarse antes de operar fuera de un entorno controlado.

## Calidad y pruebas

Desde la raíz del backend:

```bash
ruff check src
pytest -q --ignore=src/test/api/integration
pytest -q src/test/api/integration
```

Las pruebas de integración requieren una API y una base de datos disponibles.

## Migraciones

```bash
alembic upgrade head
alembic history
alembic revision --autogenerate -m "descripcion"
alembic downgrade -1
```

No se deben eliminar migraciones históricas aunque una tabla o modelo haya
dejado de existir: son necesarias para reconstruir bases desde cero.

## Documentación mantenida

- [UC-01: sincronizar el trazado](docs/03-casos-de-uso/UC-01-sincronizar-trazado-sistema.md)
- [UC-02: obtener el trazado](docs/03-casos-de-uso/UC-02-obtener-trazado-sistema.md)
- [Deuda técnica vigente](docs/deuda-tecnica.md)

Para contratos HTTP exactos, Swagger/OpenAPI es la fuente autoritativa.

# Feeding System API

Sistema de gestión de alimentación para acuicultura.

## 🚀 Inicio Rápido con Docker

### Prerrequisitos

- Docker y Docker Compose instalados
- Archivo `.env` configurado (ver `.env.template`)

### Levantar el sistema

```bash
docker-compose up -d
```

Esto iniciará:

- **PostgreSQL** en `localhost:5432`
- **API Backend** en `http://localhost:8000`

### Verificar que está funcionando

```bash
# Ver logs
docker-compose logs -f backend

# Verificar salud de la base de datos
docker-compose ps
```

### Acceder a la API

- **Documentación interactiva**: http://localhost:8000/docs
- **API alternativa**: http://localhost:8000/redoc

## 🔐 Autenticación

La API usa tokens JWT. Casi todos los endpoints requieren autenticación; los únicos abiertos son los de health (`/`, `/health`) y la documentación OpenAPI (`/docs`, `/openapi.json`).

### Usuario administrador por defecto

Al iniciar la aplicación se crea automáticamente un superadministrador si no existe:

- **username**: `adminOnix`
- **password**: `OnixServicios`
- **role**: `admin`
- **superadmin**: `true`

### Obtener un token

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "adminOnix", "password": "OnixServicios"}'
```

Respuesta:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "...",
    "username": "adminOnix",
    "full_name": "Administrador Onix",
    "role": "admin",
    "is_superadmin": true,
    "is_active": true
  }
}
```

### Usar el token

Incluye el header `Authorization: Bearer <token>` en cada petición protegida:

```bash
curl http://localhost:8000/api/cages \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

### Roles y permisos

| Rol | Permisos |
|-----|----------|
| `user` | Operar el sistema: alimentaciones, consultar estados, configuraciones operativas. No puede gestionar usuarios. |
| `admin` | Todo lo de `user`, más crear/listar/desactivar usuarios con rol `user`. Puede cambiar su propia contraseña. |
| `superadmin` | Todo lo de `admin`, más crear/modificar/desactivar otros admins, cambiar roles y resetear contraseñas de cualquier usuario. |

### Endpoints de autenticación y usuarios

| Método | Endpoint | Descripción | Permiso |
|--------|----------|-------------|---------|
| POST | `/api/auth/login` | Iniciar sesión y obtener JWT | Público |
| GET | `/api/auth/me` | Obtener usuario actual | Autenticado |
| PATCH | `/api/auth/me/password` | Cambiar contraseña propia | Autenticado |
| POST | `/api/users` | Crear usuario | Admin o superadmin |
| GET | `/api/users` | Listar usuarios | Admin o superadmin |
| PATCH | `/api/users/{id}/status` | Activar/desactivar usuario | Admin (solo `user`) / superadmin (todos) |
| PATCH | `/api/users/{id}/role` | Cambiar rol de usuario | Superadmin |
| PATCH | `/api/users/{id}/password` | Resetear contraseña | Superadmin |

### Comandos útiles

```bash
# Detener servicios
docker-compose down

# Detener y eliminar volúmenes (⚠️ borra la base de datos)
docker-compose down -v

# Reconstruir imágenes
docker-compose up -d --build

# Ver logs en tiempo real
docker-compose logs -f

# Ejecutar migraciones manualmente
docker-compose exec backend alembic upgrade head
```

## 📝 Configuración

Crea un archivo `.env` basado en `.env.template`:

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=tu_password_seguro
DB_NAME=feeding_system
DB_ECHO=false

JWT_SECRET_KEY=cambia-esto-en-produccion
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=120
```

## 🗄️ Base de Datos

La base de datos PostgreSQL persiste en un volumen Docker. Los datos se mantienen entre reinicios.

Para resetear completamente:

```bash
docker-compose down -v
docker-compose up -d
```

## 📚 Documentación Adicional

- [API de Jaulas](docs/API_CAGES.md)
- [Comandos Alembic](docs/comandos-alembic.md)
- [Análisis de Requerimientos](docs/Analisis-de-Requerimientos.md)

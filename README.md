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

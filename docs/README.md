# 📚 Documentación del Sistema de Alimentación de Peces

Bienvenido a la documentación completa del sistema de alimentación automatizada para piscicultura.

---

## 🗂️ Estructura de la Documentación

### [📦 02-Dominio](02-dominio/README.md)

Documentación del modelo de dominio (Aggregate Roots y Value Objects).

**Contenido**:

- 3 Aggregate Roots (FeedingLine, Silo, Cage)
- 20+ Value Objects (IDs, Nombres, Medidas, etc.)
- Reglas de negocio FA1-FA7
- Arquitectura del dominio

**Cuándo consultar**: Para entender conceptos de negocio, reglas que nunca se rompen, y estructura del dominio.

---

### [🎯 03-Casos de Uso](03-casos-de-uso/README.md)

Documentación de todos los casos de uso del sistema.

**Contenido**:

- UC-01: Sincronizar Trazado del Sistema ⭐⭐⭐ (Implementado)
- UC-02: Obtener Trazado del Sistema ⭐⭐⭐ (Implementado)

**Cuándo consultar**: Para entender qué hace el sistema, quién lo usa, y cómo fluyen las operaciones.

---

### [🧪 05-Testing](05-testing/estrategia.md)

Estrategia completa de testing del proyecto.

**Contenido**:

- Qué se prueba (Casos de uso, Dominio, Infraestructura)
- Reglas clave de testing
- Patrones y buenas prácticas
- Cobertura de reglas FA1-FA7
- Cómo ejecutar tests

**Cuándo consultar**: Para entender la estrategia de testing y escribir nuevos tests.

---

### [✅ Cobertura de Tests](test-coverage-summary.md)

Resumen completo de la cobertura de tests del sistema.

**Contenido**:

- 33 tests implementados (100% pasando)
- Cobertura de reglas FA2-FA7
- Validaciones de rangos
- Tests de integración

**Cuándo consultar**: Para verificar qué está testeado específicamente.

---

## 🎯 Guías Rápidas

### Para Nuevos Desarrolladores

1. **Entender el negocio**: Lee [02-Dominio](02-dominio/README.md)
2. **Entender los casos de uso**: Lee [03-Casos de Uso](03-casos-de-uso/README.md)
3. **Ver la implementación**: Revisa el código en `src/`
4. **Ejecutar tests**: Consulta [Cobertura de Tests](test-coverage-summary.md)

### Para Product Owners / Analistas

1. **Casos de uso**: [03-Casos de Uso](03-casos-de-uso/README.md)
2. **Reglas de negocio**: [02-Dominio - Reglas](02-dominio/README.md#-reglas-de-negocio-principales)
3. **Actores del sistema**: [Actores](03-casos-de-uso/README.md#-actores-del-sistema)

### Para QA / Testers

1. **Cobertura de tests**: [Test Coverage](test-coverage-summary.md)
2. **Casos de prueba**: Basados en [Casos de Uso](03-casos-de-uso/README.md)
3. **Reglas a validar**: [Reglas FA1-FA7](02-dominio/README.md#-reglas-de-negocio-principales)

---

## 🏗️ Arquitectura del Sistema

### Capas de la Aplicación

```
┌─────────────────────────────────────┐
│         API Layer (FastAPI)         │  ← Endpoints REST
├─────────────────────────────────────┤
│      Application Layer (Use Cases)  │  ← UC-01, UC-02, etc.
├─────────────────────────────────────┤
│       Domain Layer (Aggregates)     │  ← FeedingLine, Silo, Cage
├─────────────────────────────────────┤
│   Infrastructure Layer (Repos)      │  ← Persistencia
└─────────────────────────────────────┘
```

### Flujo de una Operación

```
1. Usuario → API Endpoint
2. API → Use Case (UC-01, UC-02, etc.)
3. Use Case → Domain (valida reglas FA1-FA7)
4. Domain → Repository (persiste)
5. Repository → Base de Datos
6. Respuesta ← Usuario
```

---

## 📊 Reglas de Negocio Principales

| Regla   | Descripción                 | Dónde se valida                              |
| ------- | --------------------------- | -------------------------------------------- |
| **FA1** | Composición mínima de línea | FeedingLine.create()                         |
| **FA2** | Nombres únicos              | SyncSystemLayoutUseCase                      |
| **FA3** | Jaula en una línea          | Cage.assign_to_line()                        |
| **FA4** | Slots únicos                | FeedingLine.assign_cage_to_slot()            |
| **FA5** | Silo 1-a-1                  | Silo.assign_to_doser()                       |
| **FA6** | Referencias válidas         | SyncSystemLayoutUseCase                      |
| **FA7** | Sensores únicos por tipo    | FeedingLine.\_validate_unique_sensor_types() |

Ver [Documentación del Dominio](02-dominio/README.md) para detalles completos.

---

## 🧪 Testing

### Ejecutar Tests

```bash
# Todos los tests
python -m pytest src/test/application/use_cases/ -v

# Solo un archivo
python -m pytest src/test/application/use_cases/test_sync_business_rules.py -v

# Con cobertura
python -m pytest src/test/application/use_cases/ --cov=src/application --cov-report=html
```

### Cobertura Actual

- **33 tests** implementados
- **100%** de tests pasando
- Cobertura de reglas FA2-FA7
- Tests de integración con repositorios mock

Ver [Cobertura Completa](test-coverage-summary.md)

---

## 📝 Convenciones

### Nomenclatura

- **Aggregate Roots**: PascalCase (FeedingLine, Silo, Cage)
- **Value Objects**: PascalCase (LineId, LineName, Weight)
- **Use Cases**: PascalCase + "UseCase" (SyncSystemLayoutUseCase)
- **Reglas de negocio**: FA1, FA2, FA3, etc.

### Estructura de Archivos

```
docs/
├── 02-dominio/           # Modelo de dominio
│   ├── aggregates/       # Aggregate Roots
│   └── value-objects/    # Value Objects
├── 03-casos-de-uso/      # Casos de uso
└── test-coverage-summary.md  # Cobertura de tests

src/
├── domain/               # Capa de dominio
│   ├── aggregates/       # Aggregate Roots
│   └── value_objects.py  # Value Objects
├── application/          # Capa de aplicación
│   └── use_cases/        # Casos de uso
├── infrastructure/       # Capa de infraestructura
└── api/                  # Capa de API
```

---

## 🔍 Búsqueda Rápida

### Por Concepto

- **Línea de alimentación**: [FeedingLine](02-dominio/aggregates/feeding-line.md)
- **Silo**: [Silo](02-dominio/aggregates/silo.md)
- **Jaula**: [Cage](02-dominio/aggregates/cage.md)
- **Peso**: [Weight](02-dominio/value-objects/weight.md)
- **Dosificación**: [Dosing](02-dominio/value-objects/dosing.md)

### Por Caso de Uso

- **Guardar configuración**: [UC-01](03-casos-de-uso/UC-01-sincronizar-trazado-sistema.md)
- **Cargar configuración**: [UC-02](03-casos-de-uso/UC-02-obtener-trazado-sistema.md)

### Por Regla de Negocio

- **FA1**: [Composición mínima](02-dominio/aggregates/feeding-line.md)
- **FA2**: [Nombres únicos](03-casos-de-uso/UC-01-sincronizar-trazado-sistema.md)
- **FA3**: [Jaula en una línea](02-dominio/aggregates/cage.md)
- **FA4**: [Slots únicos](02-dominio/value-objects/selector.md)
- **FA5**: [Silo 1-a-1](02-dominio/aggregates/silo.md)
- **FA6**: [Referencias válidas](03-casos-de-uso/UC-01-sincronizar-trazado-sistema.md)
- **FA7**: [Sensores únicos](02-dominio/aggregates/feeding-line.md)

---

## 🚀 Inicio Rápido

### 1. Configurar el entorno

```bash
# Crear entorno virtual
python -m venv .venv

# Activar entorno
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Ejecutar el servidor

```bash
fastapi dev src/main.py
```

### 3. Acceder a la documentación interactiva

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 4. Ejecutar tests

```bash
python -m pytest src/test/application/use_cases/ -v
```

---

## 📞 Contacto y Soporte

Para preguntas sobre:

- **Negocio y reglas**: Consulta [02-Dominio](02-dominio/README.md)
- **Casos de uso**: Consulta [03-Casos de Uso](03-casos-de-uso/README.md)
- **Tests**: Consulta [Cobertura de Tests](test-coverage-summary.md)
- **Implementación**: Revisa el código en `src/`

---

**Última actualización**: 2025-11-12  
**Versión del sistema**: 1.0.0  
**Estado de la documentación**: ✅ Completa

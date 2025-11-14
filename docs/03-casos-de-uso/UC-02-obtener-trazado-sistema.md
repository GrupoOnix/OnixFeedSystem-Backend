# UC-02: Obtener Trazado del Sistema

## Qué logra

Obtiene el estado completo actual del trazado del sistema desde la base de datos para mostrarlo en el canvas del frontend.

## Quién lo inicia

**Técnico de planta** o **Sistema** (al cargar la pantalla de trazado)

## Precondiciones

- Usuario autenticado con permisos de lectura
- Sistema de trazado configurado (puede estar vacío)

## Pasos principales

1. **Usuario abre la pantalla de trazado**

   - Frontend solicita el layout completo al backend
   - Envía petición GET al endpoint de sistema

2. **Sistema carga todos los agregados**

   - Obtiene todos los silos de la base de datos
   - Obtiene todas las jaulas de la base de datos
   - Obtiene todas las líneas de alimentación con sus componentes

3. **Sistema convierte entidades a DTOs**

   - Transforma silos del dominio a DTOs de configuración
   - Transforma jaulas del dominio a DTOs de configuración
   - Transforma líneas con todos sus componentes a DTOs

4. **Sistema mapea referencias**

   - Asegura que dosificadores tengan IDs reales de silos
   - Asegura que slots tengan IDs reales de jaulas
   - Mantiene la integridad referencial

5. **Sistema devuelve el layout completo**
   - Envía JSON con silos, jaulas y líneas
   - Incluye todas las configuraciones y asignaciones
   - Frontend renderiza el canvas con los datos

## Qué pasa si falla

### Base de datos no disponible

- **Qué**: Error de conexión a la base de datos
- **Resultado**: Error 503 Service Unavailable
- **Mensaje**: "El sistema no está disponible temporalmente"

### Datos corruptos

- **Qué**: Referencias rotas en base de datos (silo/jaula eliminada pero referenciada)
- **Resultado**: Error 500 Internal Server Error
- **Mensaje**: "Error al cargar el trazado del sistema"
- **Acción**: Log del error para investigación

### Usuario sin permisos

- **Qué**: Usuario no autenticado o sin permisos de lectura
- **Resultado**: Error 401 Unauthorized o 403 Forbidden
- **Mensaje**: "No tiene permisos para ver el trazado"

## Resultado final

### Si tiene éxito

- ✅ Frontend recibe el layout completo del sistema
- ✅ Todas las entidades tienen IDs reales
- ✅ Todas las referencias están correctamente mapeadas
- ✅ Canvas se renderiza con el estado actual

### Datos devueltos

**Silos**:

- ID real
- Nombre
- Capacidad
- Nivel de stock actual
- Estado de asignación

**Jaulas**:

- ID real
- Nombre
- Estado (disponible/en uso)

**Líneas de alimentación**:

- ID real
- Nombre de la línea
- **Blower**: nombre, potencia, tiempos de soplado
- **Dosificadores**: nombre, tipo, rango de dosificación, tasa actual, silo asignado
- **Selector**: nombre, capacidad, velocidades
- **Sensores**: nombre, tipo (opcional)
- **Asignaciones**: slot → jaula

### Casos especiales

**Sistema vacío (primera vez)**:

- Devuelve listas vacías para silos, jaulas y líneas
- Frontend muestra canvas en blanco listo para configurar

**Sistema parcialmente configurado**:

- Devuelve solo lo que existe (ej: solo silos, sin líneas)
- Frontend permite completar la configuración

## Notas importantes

- **Solo lectura**: Este caso de uso no modifica datos
- **Consistencia garantizada**: Los datos devueltos son consistentes (no hay referencias rotas)
- **Idempotente**: Llamar múltiples veces devuelve el mismo resultado
- **Rápido**: Optimizado para carga inicial del canvas
- **Completo**: Devuelve todo lo necesario para renderizar el canvas

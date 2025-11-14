# UC-01: Sincronizar Trazado del Sistema

## Qué logra

Sincroniza el estado completo del canvas de trazado (frontend) con la base de datos, aplicando todas las creaciones, actualizaciones y eliminaciones en una sola transacción.

## Quién lo inicia

**Técnico de planta** (usuario con permisos de configuración)

## Precondiciones

- Usuario autenticado con rol de "Técnico"
- Canvas de trazado cargado en el frontend

## Pasos principales

1. **Técnico modifica el canvas**

   - Crea nuevos silos, jaulas o líneas de alimentación
   - Actualiza nombres, capacidades o configuraciones
   - Elimina elementos arrastrándolos fuera del canvas
   - Conecta componentes (silos→dosificadores, slots→jaulas)

2. **Técnico presiona "Guardar"**

   - El frontend recopila el estado completo del canvas
   - Genera IDs temporales para entidades nuevas
   - Mantiene IDs reales para entidades existentes

3. **Sistema calcula diferencias (Delta)**

   - Compara IDs del canvas con IDs en base de datos
   - Identifica qué crear, qué actualizar y qué eliminar

4. **Sistema elimina entidades obsoletas**

   - Elimina líneas, silos y jaulas que ya no están en el canvas
   - Valida que no estén en uso antes de eliminar

5. **Sistema crea nuevas entidades**

   - Crea silos y jaulas independientes primero
   - Mapea IDs temporales → IDs reales
   - Crea líneas de alimentación con sus componentes
   - Resuelve referencias usando el mapa de IDs

6. **Sistema actualiza entidades existentes**

   - Actualiza nombres, capacidades y configuraciones
   - Actualiza componentes de líneas
   - Actualiza asignaciones de slots

7. **Sistema confirma transacción**
   - Persiste todos los cambios
   - Devuelve el layout completo con IDs reales

## Qué pasa si falla

### FA1: Composición de línea inválida

- **Qué**: Línea sin blower, sin dosificadores o sin selector
- **Resultado**: Transacción rechazada, canvas no se guarda
- **Mensaje**: "La línea debe tener un blower, al menos un dosificador y un selector"

### FA2: Nombres duplicados

- **Qué**: Dos silos, jaulas o líneas con el mismo nombre
- **Resultado**: Transacción rechazada
- **Mensaje**: "Ya existe un [silo/jaula/línea] con el nombre '[nombre]'"

### FA3: Jaula ya asignada a otra línea

- **Qué**: Intento de asignar una jaula que ya está en uso
- **Resultado**: Transacción rechazada
- **Mensaje**: "La jaula '[nombre]' ya está asignada a otra línea"

### FA4: Slot duplicado o inválido

- **Qué**: Dos jaulas en el mismo slot, o slot fuera de capacidad
- **Resultado**: Transacción rechazada
- **Mensaje**: "Slot [número] ya está asignado" o "Slot [número] excede la capacidad del selector"

### FA5: Silo ya asignado a otro dosificador

- **Qué**: Intento de asignar un silo que ya está en uso
- **Resultado**: Transacción rechazada
- **Mensaje**: "El silo '[nombre]' ya está asignado a otro dosificador"

### FA6: Referencia rota (ID inexistente)

- **Qué**: Dosificador referencia silo inexistente, o slot referencia jaula inexistente
- **Resultado**: Transacción rechazada
- **Mensaje**: "El [silo/jaula] con ID '[id]' no existe"

### FA7: Sensores duplicados por tipo

- **Qué**: Dos sensores del mismo tipo en una línea
- **Resultado**: Transacción rechazada
- **Mensaje**: "Ya existe un sensor de tipo '[tipo]' en la línea"

### Error de validación de rangos

- **Qué**: Valores fuera de rango (min > max, capacidad negativa, etc.)
- **Resultado**: Transacción rechazada
- **Mensaje**: Descripción específica del error de validación

## Resultado final

### Si tiene éxito

- ✅ Base de datos refleja exactamente el estado del canvas
- ✅ Todas las entidades tienen IDs reales (no temporales)
- ✅ Todas las referencias están correctamente mapeadas
- ✅ Metadatos de presentación guardados (posiciones, conexiones visuales)
- ✅ Frontend recibe el layout actualizado con IDs reales

### Datos devueltos

- Lista de silos con IDs reales
- Lista de jaulas con IDs reales
- Lista de líneas de alimentación con:
  - Componentes (blower, dosers, selector, sensors)
  - Asignaciones de slots actualizadas
  - Referencias correctas a silos y jaulas

## Notas importantes

- **Operación atómica**: Todo se guarda o nada se guarda (transaccional)
- **Sincronización declarativa**: El canvas define el estado deseado completo
- **Mapeo automático de IDs**: El sistema resuelve IDs temporales automáticamente
- **Validación exhaustiva**: Todas las reglas FA1-FA7 se validan antes de persistir

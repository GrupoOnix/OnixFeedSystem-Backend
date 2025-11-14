# FeedingLine (Línea de Alimentación)

## Qué representa

Una línea de alimentación completa que transporta alimento desde silos hasta jaulas de peces, compuesta por un soplador, dosificadores, selectora y sensores opcionales.

## Reglas que nunca se rompen

1. **FA1 - Composición mínima**: Debe tener obligatoriamente un Blower, al menos un Doser y un Selector
2. **FA4 - Slots únicos**: No puede haber dos jaulas asignadas al mismo slot
3. **FA4 - Jaulas únicas**: Una jaula no puede estar asignada a dos slots diferentes en la misma línea
4. **FA4 - Slots válidos**: Los slots asignados deben estar dentro de la capacidad del Selector (1 a N)
5. **FA7 - Sensores únicos por tipo**: Solo puede haber un sensor de cada tipo (temperatura, presión, flujo)
6. **Nombre único**: El nombre de la línea debe ser único en el sistema

## Qué puede hacer

### Creación

- **Crear línea completa**: Crea una nueva línea validando composición mínima y sensores únicos

### Gestión de componentes

- **Actualizar componentes**: Reemplaza blower, dosers, selector y sensores validando reglas FA1 y FA7

### Gestión de asignaciones

- **Asignar jaula a slot**: Asigna una jaula a un slot específico validando disponibilidad
- **Remover asignación de slot**: Libera un slot para que pueda ser reasignado
- **Actualizar todas las asignaciones**: Reemplaza todas las asignaciones validando duplicados

### Consultas

- **Obtener jaula de un slot**: Devuelve qué jaula está asignada a un slot
- **Obtener slot de una jaula**: Devuelve en qué slot está una jaula
- **Obtener dosificador por ID**: Busca un dosificador específico dentro de la línea
- **Obtener todas las asignaciones**: Lista todas las asignaciones slot→jaula

## Eventos que lanza

- `SlotAssigned`: Cuando se asigna una jaula a un slot
- `SlotUnassigned`: Cuando se libera un slot
- `ComponentsUpdated`: Cuando se actualizan los componentes de la línea
- `AssignmentsUpdated`: Cuando se actualizan todas las asignaciones

## Entidades hijas

- **Blower** (1): Soplador que impulsa el alimento
- **Doser** (1..N): Dosificadores que controlan la cantidad de alimento
- **Selector** (1): Selectora que dirige el alimento a diferentes slots
- **Sensor** (0..N): Sensores opcionales de medición (máximo uno por tipo)

## Referencias externas

- **Silo**: Cada Doser referencia un Silo del cual obtiene alimento
- **Cage**: Cada SlotAssignment referencia una Jaula destino

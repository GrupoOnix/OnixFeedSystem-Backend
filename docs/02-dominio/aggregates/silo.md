# Silo

## Qué representa

Un contenedor de almacenamiento de alimento con capacidad definida y control de stock.

## Reglas que nunca se rompen

1. **Stock no excede capacidad**: El nivel de stock nunca puede ser mayor que la capacidad del silo
2. **FA5 - Asignación 1-a-1**: Un silo solo puede estar asignado a un dosificador a la vez
3. **Capacidad no menor al stock**: Al actualizar la capacidad, no puede ser menor al stock actual
4. **Peso no negativo**: Ni la capacidad ni el stock pueden ser negativos
5. **Nombre único**: El nombre del silo debe ser único en el sistema

## Qué puede hacer

### Gestión de asignación

- **Asignar a dosificador**: Marca el silo como asignado a un dosificador (valida FA5)
- **Liberar de dosificador**: Libera el silo para que pueda ser asignado a otro dosificador

### Actualización de atributos

- **Cambiar nombre**: Actualiza el nombre del silo
- **Cambiar capacidad**: Actualiza la capacidad validando que no sea menor al stock actual

### Consultas

- **Verificar si está asignado**: Indica si el silo ya está en uso por un dosificador
- **Obtener capacidad**: Devuelve la capacidad máxima del silo
- **Obtener stock actual**: Devuelve el nivel de stock actual

## Eventos que lanza

- `SiloAssignedToDoser`: Cuando el silo es asignado a un dosificador
- `SiloReleasedFromDoser`: Cuando el silo es liberado
- `SiloCapacityUpdated`: Cuando se actualiza la capacidad
- `SiloNameUpdated`: Cuando se actualiza el nombre

## Relaciones

- **Dosificador**: Un silo puede estar asignado a máximo un dosificador (relación 1-a-1)

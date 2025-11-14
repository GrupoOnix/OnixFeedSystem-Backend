# Cage (Jaula)

## Qué representa

Una jaula de peces que puede recibir alimento a través de una línea de alimentación.

## Reglas que nunca se rompen

1. **FA3 - Una línea a la vez**: Una jaula solo puede estar asignada a una línea de alimentación a la vez
2. **Estado coherente**: Solo puede ser asignada a una línea si está en estado AVAILABLE
3. **Nombre único**: El nombre de la jaula debe ser único en el sistema

## Qué puede hacer

### Gestión de asignación

- **Asignar a línea**: Marca la jaula como EN USO y la vincula a una línea (valida FA3)
- **Liberar de línea**: Marca la jaula como DISPONIBLE para ser asignada a otra línea

### Actualización de atributos

- **Cambiar nombre**: Actualiza el nombre de la jaula
- **Cambiar estado**: Actualiza el estado de la jaula (AVAILABLE, IN_USE)

### Consultas

- **Verificar disponibilidad**: Indica si la jaula está disponible para ser asignada
- **Obtener estado**: Devuelve el estado actual de la jaula

## Eventos que lanza

- `CageAssignedToLine`: Cuando la jaula es asignada a una línea
- `CageReleasedFromLine`: Cuando la jaula es liberada
- `CageNameUpdated`: Cuando se actualiza el nombre
- `CageStatusChanged`: Cuando cambia el estado

## Estados posibles

- **AVAILABLE**: Jaula disponible para ser asignada
- **IN_USE**: Jaula actualmente asignada a una línea de alimentación

## Relaciones

- **Línea de alimentación**: Una jaula puede estar asignada a máximo una línea a la vez

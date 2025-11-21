# Cage (Jaula)

## Qué representa

Una jaula de cultivo de peces que contiene población, tiene parámetros de biometría y configuración operacional, y puede recibir alimento a través de una línea de alimentación.

## Reglas que nunca se rompen

1. **Población no negativa**: El conteo de peces nunca puede ser negativo
2. **Peso positivo**: El peso promedio de los peces debe ser mayor a 0
3. **Población inicial inmutable**: Una vez establecida la población inicial, no puede ser modificada
4. **Nombre único**: El nombre de la jaula debe ser único en el sistema
5. **Conteo coherente**: El conteo actual no puede exceder la población inicial

## Qué puede hacer

### Gestión de población

- **Establecer población inicial**: Define la siembra inicial (cantidad de peces y peso promedio)
- **Actualizar conteo de peces**: El operador puede modificar el conteo actual libremente (recuentos físicos, ajustes)
- **Registrar mortalidad**: Registra peces muertos para reportes (NO modifica el conteo actual)

### Gestión de biometría

- **Actualizar biometría**: Actualiza el peso promedio de los peces
- **Calcular biomasa**: Calcula automáticamente la biomasa (cantidad × peso promedio)
- **Calcular densidad**: Calcula la densidad actual si hay volumen configurado

### Configuración operacional

- **Actualizar FCR**: Factor de conversión alimenticia
- **Configurar volumen**: Volumen total de la jaula en m³
- **Configurar densidad máxima**: Umbral de densidad para alarmas
- **Asignar tabla de alimentación**: Referencia a tabla de alimentación
- **Configurar tiempo de transporte**: Tiempo de transporte del alimento

### Actualización de atributos básicos

- **Cambiar nombre**: Actualiza el nombre de la jaula
- **Cambiar estado**: Actualiza el estado de la jaula (AVAILABLE, IN_USE, MAINTENANCE)

### Consultas y propiedades calculadas

- **Tasa de supervivencia**: Porcentaje de peces vivos respecto a la población inicial
- **Conteo de mortalidad**: Diferencia entre población inicial y actual
- **Densidad actual**: Biomasa / volumen (si está configurado)
- **Biomasa**: Peso total de peces en la jaula

## Atributos

### Identificación

- `id`: Identificador único (CageId)
- `name`: Nombre de la jaula (CageName)
- `status`: Estado actual (CageStatus)
- `created_at`: Fecha de creación

### Población

- `initial_fish_count`: Población inicial sembrada (inmutable)
- `current_fish_count`: Conteo actual de peces (mutable por operador)

### Biometría

- `avg_fish_weight`: Peso promedio actual de los peces
- `biomass`: Biomasa calculada (propiedad)

### Configuración

- `fcr`: Factor de conversión alimenticia
- `total_volume`: Volumen de la jaula en m³
- `max_density`: Densidad máxima permitida (umbral de alarma)
- `feeding_table_id`: Referencia a tabla de alimentación
- `transport_time`: Tiempo de transporte del alimento

### Relaciones (referencias de conveniencia)

- `line_id`: Línea de alimentación asignada (la verdad la tiene FeedingLine)
- `slot_number`: Ranura asignada en la selectora

## Estados posibles

- **AVAILABLE**: Jaula disponible para ser asignada
- **IN_USE**: Jaula actualmente asignada a una línea de alimentación
- **MAINTENANCE**: Jaula en mantenimiento

## Relaciones

- **Línea de alimentación**: Una jaula puede estar asignada a máximo una línea a la vez (referencia de conveniencia, FeedingLine tiene la verdad)
- **Tabla de mortalidad**: Registros de mortalidad en tabla separada `cage_mortality_log`
- **Tabla de biometría**: Registros de biometría en tabla separada `cage_biometry_log`

## Notas de diseño

### Gestión de población (similar a AKVA)

- La mortalidad se registra en tabla separada para reportes y NO modifica `current_fish_count`
- El operador actualiza `current_fish_count` libremente cuando hace recuentos físicos
- Esto permite flexibilidad para ajustes por escapes, robos, correcciones, etc.
- La diferencia entre `initial_fish_count` y `current_fish_count` menos la mortalidad registrada indica pérdidas no explicadas

### Relaciones con FeedingLine

- `line_id` y `slot_number` son referencias de conveniencia para consultas rápidas
- La fuente de verdad de la asignación está en FeedingLine (SlotAssignment)
- El repositorio sincroniza ambos lados al persistir

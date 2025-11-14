# Identificadores (IDs)

## Qué representan

Identificadores únicos e inmutables para cada entidad del dominio, basados en UUID.

## Reglas que nunca se rompen

1. **Inmutabilidad**: Una vez creado, un ID nunca cambia
2. **Unicidad**: Cada ID es único en todo el sistema
3. **Formato UUID**: Todos los IDs son UUIDs válidos

## Tipos de identificadores

### Aggregate Roots

- **LineId**: Identifica una línea de alimentación
- **SiloId**: Identifica un silo de almacenamiento
- **CageId**: Identifica una jaula de peces

### Entidades hijas de FeedingLine

- **BlowerId**: Identifica un soplador
- **DoserId**: Identifica un dosificador
- **SelectorId**: Identifica una selectora
- **SensorId**: Identifica un sensor

## Qué pueden hacer

### Creación

- **Generar nuevo ID**: Crea un nuevo UUID único
- **Desde string**: Crea un ID desde una representación de texto UUID

### Conversión

- **A string**: Convierte el ID a su representación textual
- **Comparación**: Compara dos IDs para verificar igualdad

## Características

- Son **Value Objects**: Se comparan por valor, no por referencia
- Son **inmutables**: No pueden modificarse después de crearse
- Son **serializables**: Pueden convertirse a string para persistencia

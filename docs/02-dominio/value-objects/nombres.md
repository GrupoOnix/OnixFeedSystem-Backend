# Nombres (Names)

## Qué representan

Nombres validados para entidades del dominio con reglas de formato consistentes.

## Reglas que nunca se rompen

1. **No vacío**: El nombre no puede estar vacío (después de quitar espacios)
2. **Longitud máxima**: No puede exceder 100 caracteres
3. **Caracteres válidos**: Solo letras (con tildes y ñ), números, espacios, guiones (-) y guiones bajos (\_)
4. **Tipo string**: Debe ser una cadena de texto

## Tipos de nombres

### Aggregate Roots

- **LineName**: Nombre de línea de alimentación
- **SiloName**: Nombre de silo
- **CageName**: Nombre de jaula

### Componentes

- **BlowerName**: Nombre de soplador
- **DoserName**: Nombre de dosificador
- **SelectorName**: Nombre de selectora
- **SensorName**: Nombre de sensor

## Qué pueden hacer

### Validación

- **Validar formato**: Verifica que el nombre cumple todas las reglas al crearse
- **Normalizar**: Elimina espacios al inicio y final

### Conversión

- **A string**: Devuelve el valor del nombre como texto

## Ejemplos válidos

- "Línea Principal"
- "Silo_A-01"
- "Jaula Norte 123"
- "Dosificador-Proteína"

## Ejemplos inválidos

- "" (vacío)
- " " (solo espacios)
- "Nombre con más de 100 caracteres..." (excede límite)
- "Nombre@Inválido" (carácter @ no permitido)
- "Nombre#123" (carácter # no permitido)

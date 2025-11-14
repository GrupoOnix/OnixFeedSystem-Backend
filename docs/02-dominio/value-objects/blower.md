# Blower (Soplador)

## Qué representan

Value Objects relacionados con la configuración del soplador.

---

## BlowerPowerPercentage (Potencia del Soplador)

### Qué representa

La potencia del soplador expresada como porcentaje (0-100%).

### Reglas que nunca se rompen

1. **Rango válido**: Debe estar entre 0.0 y 100.0
2. **Valor numérico**: Debe ser un número (int o float)

### Qué puede hacer

- **Crear potencia**: `BlowerPowerPercentage(value=75.0)`
- **Convertir a string**: Muestra valor con símbolo % (ej: "75.0 %")

---

## BlowDurationInSeconds (Duración de Soplado)

### Qué representa

El tiempo en segundos que el soplador debe operar antes o después de la alimentación.

### Reglas que nunca se rompen

1. **No negativo**: No puede ser negativo
2. **Límite superior**: No puede exceder 600 segundos (10 minutos)
3. **Valor entero**: Debe ser un número entero de segundos

### Qué puede hacer

- **Crear duración**: `BlowDurationInSeconds(value=5)`
- **Convertir a string**: Muestra valor con unidad (ej: "5 s")

## Uso en Blower

El soplador usa estos VOs para:

- **non_feeding_power**: Potencia cuando no está alimentando
- **blow_before_feeding_time**: Tiempo de soplado antes de alimentar
- **blow_after_feeding_time**: Tiempo de soplado después de alimentar

## Ejemplos de uso

```python
# Configuración típica de soplador
potencia = BlowerPowerPercentage(value=50.0)  # 50% de potencia
antes = BlowDurationInSeconds(value=5)        # 5 segundos antes
despues = BlowDurationInSeconds(value=3)      # 3 segundos después

blower = Blower(
    name=BlowerName("Soplador Principal"),
    non_feeding_power=potencia,
    blow_before_time=antes,
    blow_after_time=despues
)
```

## Validaciones

- Potencia fuera de rango: `BlowerPowerPercentage(150.0)` → Error
- Duración negativa: `BlowDurationInSeconds(-5)` → Error
- Duración excesiva: `BlowDurationInSeconds(700)` → Error

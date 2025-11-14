# Dosing (Dosificación)

## Qué representan

Value Objects relacionados con la dosificación de alimento: tasas y rangos válidos.

---

## DosingRate (Tasa de Dosificación)

### Qué representa

La velocidad a la que un dosificador entrega alimento, expresada en kg/min.

### Reglas que nunca se rompen

1. **No negativa**: La tasa no puede ser negativa
2. **Límite superior**: No puede exceder 1000 kg/min
3. **Unidad válida**: Debe tener una unidad de medida (por defecto kg/min)

### Qué puede hacer

- **Crear tasa**: `DosingRate(value=50.0, unit="kg/min")`
- **Convertir a string**: Muestra valor con unidad (ej: "50.0 kg/min")

---

## DosingRange (Rango de Dosificación)

### Qué representa

El rango válido de tasas de dosificación que un dosificador puede manejar (mínimo y máximo).

### Reglas que nunca se rompen

1. **Mínimo menor que máximo**: `min_rate < max_rate` siempre
2. **Valores no negativos**: Ni el mínimo ni el máximo pueden ser negativos
3. **Unidad consistente**: Ambos valores deben usar la misma unidad

### Qué puede hacer

- **Crear rango**: `DosingRange(min_rate=10.0, max_rate=100.0, unit="kg/min")`
- **Validar tasa**: `rango.contains(tasa)` → verifica si una tasa está dentro del rango
- **Convertir a string**: Muestra rango con unidad (ej: "10.0-100.0 kg/min")

## Ejemplos de uso

```python
# Crear rango válido
rango = DosingRange(min_rate=10.0, max_rate=100.0)

# Crear tasas
tasa_valida = DosingRate(value=50.0)
tasa_invalida = DosingRate(value=150.0)

# Validar
if rango.contains(tasa_valida):
    print("Tasa dentro del rango")  # ✓ Se ejecuta

if rango.contains(tasa_invalida):
    print("Tasa dentro del rango")  # ✗ No se ejecuta
```

## Validaciones en Doser

El dosificador valida que:

- La tasa inicial esté dentro del rango al crearse
- Cualquier cambio de tasa esté dentro del rango configurado

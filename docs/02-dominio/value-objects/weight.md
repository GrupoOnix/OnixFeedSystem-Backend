# Weight (Peso)

## Qué representa

Una medida de peso precisa e inmutable que maneja conversiones entre diferentes unidades (miligramos, gramos, kilogramos, toneladas).

## Reglas que nunca se rompen

1. **No negativo**: El peso nunca puede ser negativo
2. **Precisión interna**: Internamente se almacena en miligramos para máxima precisión
3. **Inmutabilidad**: Una vez creado, no puede modificarse (las operaciones crean nuevos Weight)
4. **Operaciones seguras**: Las restas que resulten en negativo lanzan error

## Qué puede hacer

### Creación

- **Desde miligramos**: `Weight.from_miligrams(500)`
- **Desde gramos**: `Weight.from_grams(1.5)`
- **Desde kilogramos**: `Weight.from_kg(2.5)`
- **Desde toneladas**: `Weight.from_tons(1.0)`
- **Peso cero**: `Weight.zero()`

### Conversión (lectura)

- **A miligramos**: `weight.as_miligrams`
- **A gramos**: `weight.as_grams`
- **A kilogramos**: `weight.as_kg`
- **A toneladas**: `weight.as_tons`

### Operaciones matemáticas

- **Sumar**: `weight1 + weight2` → nuevo Weight
- **Restar**: `weight1 - weight2` → nuevo Weight (valida no negativo)
- **Multiplicar**: `weight * 2` o `2 * weight` → nuevo Weight
- **Comparar**: `weight1 > weight2`, `weight1 == weight2`, etc.

## Ejemplos de uso

```python
# Crear pesos
capacidad = Weight.from_kg(1000)  # 1000 kg
stock = Weight.from_kg(750)       # 750 kg

# Operaciones
disponible = capacidad - stock    # 250 kg
doble = stock * 2                 # 1500 kg

# Comparaciones
if stock < capacidad:
    print("Hay espacio disponible")

# Conversiones
print(f"Stock: {stock.as_kg} kg")      # 750.0 kg
print(f"Stock: {stock.as_tons} ton")   # 0.75 ton
```

## Representación automática

El método `__str__()` elige la unidad más apropiada:

- `0 kg` para peso cero
- `500 mg` para valores menores a 1 gramo
- `1.50 g` para valores menores a 1 kg
- `2.50 kg` para valores menores a 1 tonelada
- `1.25 ton` para valores de 1 tonelada o más

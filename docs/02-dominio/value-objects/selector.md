# Selector (Selectora)

## Qué representan

Value Objects relacionados con la configuración de la selectora.

---

## SelectorCapacity (Capacidad de la Selectora)

### Qué representa

El número de slots (ranuras) que tiene una selectora para dirigir alimento a diferentes jaulas.

### Reglas que nunca se rompen

1. **Mayor que cero**: Debe ser al menos 1
2. **Valor entero**: Debe ser un número entero

### Qué puede hacer

- **Crear capacidad**: `SelectorCapacity(value=4)`
- **Convertir a string**: Muestra valor con unidad (ej: "4 ranuras")

---

## SelectorSpeedProfile (Perfil de Velocidad)

### Qué representa

La configuración de velocidades rápida y lenta de la selectora, expresadas como porcentajes.

### Reglas que nunca se rompen

1. **Velocidad lenta < velocidad rápida**: La velocidad lenta siempre debe ser menor que la rápida
2. **Rangos válidos**: Ambas velocidades deben estar entre 0-100% (heredado de BlowerPowerPercentage)

### Qué puede hacer

- **Crear perfil**: `SelectorSpeedProfile(fast_speed=..., slow_speed=...)`
- **Convertir a string**: Muestra ambas velocidades (ej: "Fast: 80.0 %, Slow: 20.0 %")

---

## SlotNumber (Número de Slot)

### Qué representa

El número de una ranura específica en la selectora.

### Reglas que nunca se rompen

1. **Positivo**: Debe ser mayor o igual a 1
2. **Valor entero**: Debe ser un número entero

### Qué puede hacer

- **Crear slot**: `SlotNumber(value=1)`
- **Convertir a string**: Devuelve el número como texto
- **Convertir a int**: Permite usar como número entero
- **Hasheable**: Puede usarse en sets y diccionarios

---

## SlotAssignment (Asignación de Slot)

### Qué representa

La relación inmutable entre un slot de la selectora y una jaula destino.

### Reglas que nunca se rompen

1. **Slot válido**: Debe ser una instancia de SlotNumber
2. **Jaula válida**: Debe ser una instancia de CageId
3. **Inmutable**: No puede modificarse después de crearse

### Qué puede hacer

- **Crear asignación**: `SlotAssignment(slot_number=SlotNumber(1), cage_id=cage_id)`
- **Comparar**: Dos asignaciones son iguales si tienen el mismo slot y jaula
- **Hashear**: Puede usarse en sets y diccionarios
- **Convertir a string**: Muestra la relación (ej: "Ranura 1 → Jaula abc-123")

## Ejemplos de uso

```python
# Crear selectora con capacidad y velocidades
capacidad = SelectorCapacity(value=4)
perfil = SelectorSpeedProfile(
    fast_speed=BlowerPowerPercentage(80.0),
    slow_speed=BlowerPowerPercentage(20.0)
)

selector = Selector(
    name=SelectorName("Selectora Principal"),
    capacity=capacidad,
    speed_profile=perfil
)

# Crear asignación de slot
slot = SlotNumber(1)
assignment = SlotAssignment(
    slot_number=slot,
    cage_id=cage_id
)
```

## Validaciones

- Capacidad cero: `SelectorCapacity(0)` → Error
- Velocidad lenta >= rápida: `SelectorSpeedProfile(fast=20, slow=80)` → Error
- Slot negativo: `SlotNumber(-1)` → Error
- Slot cero: `SlotNumber(0)` → Error

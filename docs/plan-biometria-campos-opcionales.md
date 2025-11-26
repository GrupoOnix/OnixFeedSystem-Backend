# Plan: Hacer Campos Opcionales en Registro de Biometría

## Objetivo

Modificar el endpoint de registro de biometría para que solo actualice los campos que vienen en el JSON, evitando "ruido" en los logs con valores que no cambiaron.

## Análisis del Flujo Actual

```
Request JSON → DTO → Use Case → Dominio → Repositorio → BD
```

**Problema actual:**

- `fish_count` y `average_weight_g` son **requeridos** en el DTO
- El use case **siempre actualiza ambos** campos
- Los logs guardan OLD y NEW aunque no hayan cambiado

**Solución:**

- Hacer ambos campos **opcionales** en el DTO
- El use case solo actualiza lo que viene en el JSON
- Los logs solo guardan lo que realmente cambió

---

## Tareas por Capa

### 1. DTO (Application Layer)

**Archivo:** `src/application/dtos/biometry_dtos.py`

- [x] Cambiar `fish_count: int` a `fish_count: Optional[int] = None`
- [x] Cambiar `average_weight_g: float` a `average_weight_g: Optional[float] = None`
- [x] Mantener `sampling_date` como requerido
- [x] Mantener `note` como opcional

**Validación adicional:**

- [x] Agregar validación en el use case: al menos uno de los dos debe estar presente

---

### 2. Use Case (Application Layer)

**Archivo:** `src/application/use_cases/cage/register_biometry_use_case.py`

- [x] Agregar validación al inicio: `if not request.fish_count and not request.average_weight_g: raise ValueError(...)`
- [x] Cambiar lógica de snapshot OLD:
  - Solo guardar `old_fish_count` si `request.fish_count` está presente
  - Solo guardar `old_avg_weight` si `request.average_weight_g` está presente
- [x] Cambiar lógica de actualización de Cage:
  - Solo llamar `cage.update_fish_count()` si `request.fish_count` está presente
  - Solo llamar `cage.update_biometry()` si `request.average_weight_g` está presente
- [x] Cambiar lógica de creación de log:
  - `old_fish_count` y `new_fish_count` solo si se actualizó fish_count
  - `old_average_weight_g` y `new_average_weight_g` solo si se actualizó average_weight_g

---

### 3. Value Object de Dominio

**Archivo:** `src/domain/value_objects/biometry_log_entry.py`

**Análisis:** Ya son opcionales ✅

- `old_fish_count: Optional[int]` ✅
- `new_fish_count: Optional[int]` ✅
- `old_average_weight_g: Optional[float]` ✅
- `new_average_weight_g: Optional[float]` ✅

**Acción:** No requiere cambios

---

### 4. Modelo de Persistencia

**Archivo:** `src/infrastructure/persistence/models/biometry_log_model.py`

**Análisis:** Ya son opcionales ✅

- `old_fish_count: Optional[int] = Field(default=None)` ✅
- `new_fish_count: Optional[int] = Field(default=None)` ✅
- `old_average_weight_g: Optional[float] = Field(default=None)` ✅
- `new_average_weight_g: Optional[float] = Field(default=None)` ✅

**Acción:** No requiere cambios

---

### 5. Repositorio

**Archivo:** `src/infrastructure/persistence/repositories/biometry_log_repository.py`

**Análisis:** Solo guarda lo que recibe del VO ✅

**Acción:** No requiere cambios

---

### 6. Dominio (Cage)

**Archivo:** `src/domain/aggregates/cage.py`

**Análisis:** Métodos existentes:

- `update_fish_count(FishCount)` - Ya existe ✅
- `update_biometry(Weight)` - Ya existe ✅

**Acción:** No requiere cambios (los métodos ya son independientes)

---

### 7. API Endpoint

**Archivo:** `src/api/routers/cage_router.py`

**Análisis:** Pydantic valida automáticamente según el DTO

**Acción:** No requiere cambios (Pydantic se adapta automáticamente)

---

### 8. Documentación

**Archivo:** `docs/API_CAGES.md`

- [x] Actualizar documentación del endpoint
- [x] Aclarar que `fish_count` y `average_weight_g` son opcionales
- [x] Agregar ejemplos de uso:
  - Solo actualizar fish_count
  - Solo actualizar average_weight_g
  - Actualizar ambos

---

## Ejemplos de Uso Después del Cambio

### Caso 1: Solo actualizar conteo de peces

```json
{
  "fish_count": 4500,
  "sampling_date": "2025-11-21",
  "note": "Recuento físico"
}
```

**Resultado:**

- Actualiza `current_fish_count` en Cage
- Log guarda: `old_fish_count`, `new_fish_count`, `sampling_date`, `note`
- Log NO guarda: `old_average_weight_g`, `new_average_weight_g` (quedan en null)

### Caso 2: Solo actualizar peso promedio

```json
{
  "average_weight_g": 550.5,
  "sampling_date": "2025-11-21",
  "note": "Muestreo de peso"
}
```

**Resultado:**

- Actualiza `avg_fish_weight` en Cage
- Log guarda: `old_average_weight_g`, `new_average_weight_g`, `sampling_date`, `note`
- Log NO guarda: `old_fish_count`, `new_fish_count` (quedan en null)

### Caso 3: Actualizar ambos (como antes)

```json
{
  "fish_count": 4500,
  "average_weight_g": 550.5,
  "sampling_date": "2025-11-21",
  "note": "Muestreo completo"
}
```

**Resultado:**

- Actualiza ambos campos en Cage
- Log guarda todos los valores

### Caso 4: Error - No enviar ninguno

```json
{
  "sampling_date": "2025-11-21",
  "note": "Sin datos"
}
```

**Resultado:**

- Error 400: "Debe proporcionar al menos fish_count o average_weight_g"

---

## Validaciones Necesarias

### En el Use Case:

```python
# Al inicio del execute()
if not request.fish_count and not request.average_weight_g:
    raise ValueError(
        "Debe proporcionar al menos uno de los siguientes campos: "
        "fish_count o average_weight_g"
    )
```

---

## Ventajas de Este Cambio

✅ **Logs más limpios:** Solo se registra lo que realmente cambió
✅ **Flexibilidad:** Permite actualizaciones parciales
✅ **Menos ruido:** Fácil identificar qué se modificó en cada muestreo
✅ **Mejor UX:** El frontend puede enviar solo lo que el usuario modificó

---

## Orden de Implementación

1. ✅ Actualizar DTO (hacer campos opcionales)
2. ✅ Actualizar Use Case (lógica condicional)
3. ✅ Actualizar Documentación
4. ✅ Probar casos de uso

---

## Testing

**Archivo:** `src/test/application/use_cases/cage/test_register_biometry_use_case.py`

- [ ] Test: Actualizar solo fish_count
- [ ] Test: Actualizar solo average_weight_g
- [ ] Test: Actualizar ambos
- [ ] Test: Error si no se proporciona ninguno
- [ ] Test: Verificar que logs solo guardan lo que cambió

---

## Notas Importantes

- ⚠️ **Migración de BD:** NO es necesaria (los campos ya son opcionales en la tabla)
- ⚠️ **Compatibilidad:** El cambio es retrocompatible (enviar ambos sigue funcionando)
- ⚠️ **Frontend:** Debe adaptarse para enviar solo lo que cambió

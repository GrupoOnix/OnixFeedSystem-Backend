# Comandos de Alembic para Migraciones

## Workflow Normal de Desarrollo

### 1. Primera vez: Crear migración inicial

```bash
alembic revision --autogenerate -m "initial schema"
```

**¿Qué hace?**

- Detecta todos los modelos SQLModel importados en `alembic/env.py`
- Compara con el estado actual de la BD (vacía)
- Genera un archivo de migración en `/alembic/versions/`
- El archivo contiene funciones `upgrade()` y `downgrade()`

**¿Cuándo usarlo?**

- Primera vez que configuras la BD
- Cuando creas el proyecto desde cero

---

### 2. Aplicar migraciones a la BD

```bash
alembic upgrade head
```

**¿Qué hace?**

- Ejecuta todas las migraciones pendientes
- Crea/modifica tablas en PostgreSQL
- Actualiza la tabla `alembic_version` con la migración actual

**¿Cuándo usarlo?**

- Después de generar una migración
- Después de hacer `git pull` y hay nuevas migraciones
- En producción para actualizar el esquema

---

### 3. Modificaste un modelo: Generar nueva migración

```bash
alembic revision --autogenerate -m "add fish_count to cages"
```

**¿Qué hace?**

- Detecta cambios entre tus modelos y el esquema actual de BD
- Genera una nueva migración con los cambios
- Ejemplos de cambios detectados:
  - Agregar/eliminar columnas
  - Cambiar tipos de datos
  - Agregar/eliminar tablas
  - Modificar constraints

**¿Cuándo usarlo?**

- Cada vez que modificas un modelo SQLModel
- Después de agregar una nueva tabla
- Después de cambiar tipos de columnas

**Luego ejecutar:**

```bash
alembic upgrade head
```

---

## Comandos de Consulta

### 4. Ver migración actual

```bash
alembic current
```

**¿Qué hace?**

- Muestra qué migración está aplicada actualmente en la BD

**¿Cuándo usarlo?**

- Para verificar el estado de la BD
- Para confirmar que una migración se aplicó

---

### 5. Ver historial de migraciones

```bash
alembic history
```

**¿Qué hace?**

- Lista todas las migraciones disponibles
- Muestra el orden y descripción de cada una

**¿Cuándo usarlo?**

- Para ver todas las migraciones del proyecto
- Para identificar una migración específica

---

### 6. Ver historial con más detalle

```bash
alembic history --verbose
```

**¿Qué hace?**

- Muestra historial con información detallada
- Incluye rutas de archivos y fechas

---

## Comandos de Rollback

### 7. Deshacer última migración

```bash
alembic downgrade -1
```

**¿Qué hace?**

- Ejecuta la función `downgrade()` de la última migración
- Revierte los cambios en la BD
- Retrocede una migración

**¿Cuándo usarlo?**

- Cuando una migración causó problemas
- Para probar el rollback antes de producción
- Cuando necesitas corregir una migración

---

### 8. Volver a una migración específica

```bash
alembic downgrade <revision_id>
```

**¿Qué hace?**

- Retrocede hasta la migración especificada
- Ejecuta todos los `downgrade()` necesarios

**Ejemplo:**

```bash
alembic downgrade abc123def456
```

**¿Cuándo usarlo?**

- Para volver a un estado específico de la BD
- En casos de emergencia en producción

---

### 9. Volver al inicio (vaciar BD)

```bash
alembic downgrade base
```

**¿Qué hace?**

- Ejecuta todos los `downgrade()` hasta el inicio
- Elimina todas las tablas creadas por Alembic
- ⚠️ **PELIGROSO**: Pierdes todos los datos

**¿Cuándo usarlo?**

- Solo en desarrollo para resetear completamente
- **NUNCA en producción**

---

## Comandos Avanzados

### 10. Ver SQL sin ejecutar (dry-run)

```bash
alembic upgrade head --sql
```

**¿Qué hace?**

- Muestra el SQL que se ejecutaría
- NO modifica la BD
- Útil para revisar antes de aplicar

**¿Cuándo usarlo?**

- Antes de aplicar en producción
- Para revisar qué cambios se harán
- Para documentar cambios

---

### 11. Crear migración vacía (manual)

```bash
alembic revision -m "custom migration"
```

**¿Qué hace?**

- Crea una migración vacía sin autogenerar
- Debes escribir manualmente `upgrade()` y `downgrade()`

**¿Cuándo usarlo?**

- Para migraciones de datos (no de esquema)
- Para operaciones complejas que autogenerate no detecta
- Para poblar datos iniciales

---

## Workflow Completo: Desarrollo

```bash
# 1. Modificas un modelo (ej: agregas columna a CageModel)

# 2. Generas migración
alembic revision --autogenerate -m "add fish_count to cages"

# 3. Revisas el archivo generado en /alembic/versions/
# (Verificar que los cambios son correctos)

# 4. Aplicas la migración
alembic upgrade head

# 5. Verificas que se aplicó
alembic current
```

---

## Workflow Completo: Producción

```bash
# 1. En tu máquina local (desarrollo)
alembic revision --autogenerate -m "add new feature"
alembic upgrade head  # Probar localmente
git add alembic/versions/
git commit -m "Add migration for new feature"
git push

# 2. En servidor de producción
git pull
alembic current  # Ver estado actual
alembic history  # Ver migraciones pendientes
alembic upgrade head --sql  # Revisar SQL (opcional)
alembic upgrade head  # Aplicar migraciones

# 3. Verificar
alembic current
```

---

## Comandos de Emergencia

### Si algo sale mal en producción:

```bash
# 1. Ver estado actual
alembic current

# 2. Ver historial
alembic history

# 3. Rollback a migración anterior
alembic downgrade -1

# 4. O rollback a migración específica conocida como buena
alembic downgrade <revision_id_buena>
```

---

## Buenas Prácticas

### ✅ Hacer siempre:

1. **Revisar migraciones generadas** antes de aplicar
2. **Probar en desarrollo** antes de producción
3. **Hacer backup de BD** antes de migrar en producción
4. **Versionar migraciones** en git
5. **Escribir mensajes descriptivos** en las migraciones

### ❌ Nunca hacer:

1. **Editar migraciones ya aplicadas** en producción
2. **Eliminar archivos de migración** del historial
3. **Aplicar migraciones sin revisar** en producción
4. **Usar `downgrade base`** en producción
5. **Modificar manualmente** la tabla `alembic_version`

---

## Troubleshooting

### Error: "Can't locate revision identified by 'head'"

**Causa:** No hay migraciones creadas.  
**Solución:**

```bash
alembic revision --autogenerate -m "initial schema"
```

---

### Error: "Target database is not up to date"

**Causa:** Hay migraciones pendientes.  
**Solución:**

```bash
alembic upgrade head
```

---

### Error: "Can't proceed with autogenerate"

**Causa:** Alembic no detecta los modelos.  
**Solución:** Verificar que todos los modelos están importados en `alembic/env.py`

---

### Migración genera cambios no deseados

**Causa:** Alembic detectó diferencias inesperadas.  
**Solución:**

1. Revisar el archivo de migración generado
2. Editar manualmente si es necesario
3. O descartar y regenerar: eliminar archivo y volver a generar

---

## Resumen de Comandos Más Usados

```bash
# Desarrollo diario
alembic revision --autogenerate -m "descripción"  # Generar migración
alembic upgrade head                               # Aplicar migraciones
alembic current                                    # Ver estado
alembic history                                    # Ver historial
alembic downgrade -1                               # Rollback

# Producción
alembic upgrade head --sql                         # Ver SQL (dry-run)
alembic upgrade head                               # Aplicar
alembic current                                    # Verificar
```

---

## Próximos Pasos

Ahora que tienes Alembic configurado:

1. Genera la migración inicial:

   ```bash
   alembic revision --autogenerate -m "initial schema"
   ```

2. Revisa el archivo generado en `/alembic/versions/`

3. Aplica la migración:

   ```bash
   alembic upgrade head
   ```

4. Verifica las tablas en PostgreSQL:
   ```bash
   docker exec -it feedsystemdb psql -U postgres -d OnixFeedSystem -c "\dt"
   ```

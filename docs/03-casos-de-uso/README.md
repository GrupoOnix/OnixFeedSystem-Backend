# Casos de Uso del Sistema

Esta carpeta contiene la documentación de todos los casos de uso del sistema de alimentación de peces.

## 📋 Casos de Uso Implementados

### [UC-01: Sincronizar Trazado del Sistema](UC-01-sincronizar-trazado-sistema.md)

**Qué logra**: Sincroniza el estado completo del canvas con la base de datos en una transacción.

**Quién**: Técnico de planta

**Cuándo**: Al presionar "Guardar" después de modificar el canvas

**Importancia**: ⭐⭐⭐ Crítico - Caso de uso principal del sistema

**Estado**: ✅ Implementado

---

### [UC-02: Obtener Trazado del Sistema](UC-02-obtener-trazado-sistema.md)

**Qué logra**: Carga el estado actual del trazado desde la base de datos.

**Quién**: Técnico de planta / Sistema

**Cuándo**: Al abrir la pantalla de trazado

**Importancia**: ⭐⭐⭐ Crítico - Necesario para visualizar configuración

**Estado**: ✅ Implementado

---

## 🎯 Actores del Sistema

### Técnico de Planta

- **Rol**: Usuario operativo con permisos de configuración
- **Responsabilidades**:
  - Configurar el trazado del sistema
  - Crear y modificar silos, jaulas y líneas
  - Asignar jaulas a slots
  - Conectar silos a dosificadores

### Sistema

- **Rol**: Actor automático
- **Responsabilidades**:
  - Cargar configuración al iniciar
  - Validar reglas de negocio
  - Mantener integridad de datos
  - Registrar auditoría

---

## 🔄 Flujo Típico de Trabajo

```
1. Sistema carga configuración actual (UC-02)
   ↓
2. Técnico modifica canvas
   ↓
3. Técnico presiona "Guardar"
   ↓
4. Sistema sincroniza cambios (UC-01)
   ↓
5. Configuración actualizada en BD
```

---

## 📊 Matriz de Casos de Uso

| Caso de Uso                | Actor           | Frecuencia | Criticidad | Estado          |
| -------------------------- | --------------- | ---------- | ---------- | --------------- |
| UC-01: Sincronizar Trazado | Técnico         | Alta       | Crítica    | ✅ Implementado |
| UC-02: Obtener Trazado     | Técnico/Sistema | Alta       | Crítica    | ✅ Implementado |

---

## 🎨 Reglas de Negocio Aplicadas

Todos los casos de uso respetan las siguientes reglas:

- **FA1**: Composición mínima de línea (blower + dosers + selector)
- **FA2**: Nombres únicos por tipo de entidad
- **FA3**: Jaula solo en una línea a la vez
- **FA4**: Slots únicos y dentro de capacidad
- **FA5**: Silo asignado 1-a-1 con dosificador
- **FA6**: Referencias válidas (IDs existentes)
- **FA7**: Un sensor por tipo por línea

Ver [Documentación del Dominio](../02-dominio/README.md) para detalles completos.

---

## 📝 Convenciones de Documentación

Cada caso de uso incluye:

1. **Qué logra**: Descripción en una frase
2. **Quién lo inicia**: Actor que ejecuta el caso de uso
3. **Precondiciones**: Estado requerido antes de ejecutar
4. **Pasos principales**: Flujo normal de ejecución
5. **Qué pasa si falla**: Flujos alternativos y errores
6. **Resultado final**: Estado del sistema después de ejecutar

---

## 📚 Referencias

- [Documentación del Dominio](../02-dominio/README.md)
- [Cobertura de Tests](../test-coverage-summary.md)
- [Arquitectura del Sistema](../../README_API.md)

---

**Última actualización**: 2025-11-12  
**Total de casos de uso**: 2

# Arquitectura: Dosers de Múltiples Tipos

**Versión:** 1.0
**Fecha:** 2025-12-10
**Estado:** Validado
**Propósito:** Definir dónde debe vivir la configuración específica de cada tipo de doser

---

## 1. Contexto del Problema

El sistema de alimentación debe soportar **múltiples tipos de dosers**, cada uno con diferentes mecanismos físicos y parámetros de configuración:

### Tipos de Dosers Identificados:

1. **Doser por Pulsos (Pulse Doser)**
   - Funciona con pulsos ON/OFF
   - Parámetros: `pulse_on_time`, `pulse_off_time`, `operating_speed`, `grams_per_pulse`
   - La tasa se ajusta variando el **tiempo OFF**
   - Ejemplo: A 30% de velocidad, con ON=1s y OFF=0.5s, suelta 660g por pulso

2. **Doser Variable (VariDoser)**
   - Funciona con velocidad continua del motor
   - Parámetros: `max_motor_speed_rpm`, `flow_rate_kg_min_at_max`
   - La tasa se ajusta variando la **velocidad del motor**

3. **Doser Gravimétrico** (futuro)
   - Funciona con balanza y retroalimentación continua
   - Parámetros: `target_weight_per_second`, `PID_parameters`
   - La tasa se controla por **peso real medido**

### Pregunta Inicial:

> **¿Dónde deben vivir los parámetros específicos de cada tipo de doser?**
> ¿En la clase de dominio, en infraestructura, o mover el doser completamente a infraestructura?

---

## 2. Análisis de Requisitos

### 2.1 ¿Qué necesita saber el PROCESO DE ALIMENTACIÓN sobre el doser?

**Respuesta:** Escenario A - Agnóstico al tipo

- El proceso de alimentación **solo necesita saber la tasa máxima** según configuración
- Dice: "Alimenta a 50 kg/min"
- **NO le importa CÓMO se logra** (si es por pulsos, continuo, gravimétrico)

**Implicación:** El dominio de Alimentación no necesita conocer detalles de implementación de cada tipo.

---

### 2.2 ¿Hay reglas de negocio específicas por tipo de doser?

**Respuesta:** NO

- No hay validaciones especiales por tipo
- No hay comportamientos diferentes en el proceso de alimentación
- Todos los dosers se usan de la misma forma desde el proceso

**Implicación:** No se requiere polimorfismo en el dominio.

---

### 2.3 ¿La configuración de parámetros específicos afecta decisiones en runtime?

**Respuesta:** Mixto

**CONFIGURACIÓN ESTÁTICA** (no cambia durante alimentación):
- Velocidad del doser (ej. 30%)
- Tiempo de pulso ON (ej. 1s)
- Calibración (gramos por pulso)
- **Se modifica solo en pantalla de "Configuración de Equipos"**

**PARÁMETRO DINÁMICO** (cambia durante alimentación):
- Tasa de dosificación (kg/min)
- Para pulse doser: implica ajustar tiempo OFF
- Para vari doser: implica ajustar velocidad del motor
- **Se ajusta en tiempo real desde pantalla de "Alimentar"**

**Implicación:** Los parámetros específicos son configuración técnica que se guarda en BD. La tasa es un parámetro de la operación, no del doser.

---

## 3. Decisión Arquitectural

### 3.1 Principio de Separación

**El dominio debe saber QUÉ queremos hacer, la infraestructura sabe CÓMO hacerlo físicamente.**

- **Dominio:** "Quiero dosificar a 50 kg/min"
- **Infraestructura:** "Ok, eso significa pulsos ON=1s, OFF=0.8s a 30% de velocidad" (para pulse doser) o "Eso significa motor al 65%" (para vari doser)

---

### 3.2 Separación de Responsabilidades

#### ✅ Dominio (Doser Genérico)

**Responsabilidad:** Representar el componente y sus **capacidades lógicas**

```python
# domain/aggregates/feeding_line/doser.py
class Doser(IDoser):
    """
    Interfaz genérica de doser para el proceso de alimentación.
    NO conoce detalles de implementación física.
    UNA SOLA CLASE, sin subclases.
    """

    # Identidad
    _id: DoserId
    _name: DoserName
    _doser_type: DoserType              # PULSE | VARI | GRAVIMETRIC
    _assigned_silo_id: SiloId

    # Capacidad (valor guardado, NO calculado)
    _max_dosing_rate: DosingRate        # ej. 80 kg/min
```

**Qué NO tiene:**
- ❌ Parámetros específicos de tipo (pulsos, velocidades, calibraciones)
- ❌ Subclases (PulseDoser, VariDoser)
- ❌ Lógica de cálculo de parámetros físicos
- ❌ Current rate (la tasa es parámetro de la operación)

---

#### ✅ Infraestructura (Configuraciones Específicas)

**Responsabilidad:** Almacenar parámetros físicos de cada tipo

```python
# infrastructure/persistence/models/doser_configurations.py

class PulseDoserConfigModel(SQLModel, table=True):
    """Configuración específica de doser por pulsos."""
    __tablename__ = "pulse_doser_configurations"

    doser_id: UUID = Field(foreign_key="dosers.id", primary_key=True)
    pulse_on_time_seconds: float
    pulse_off_time_base_seconds: float  # Configuración base
    operating_speed_percentage: float
    grams_per_pulse: float              # Calibrado
    last_calibration_date: datetime


class VariDoserConfigModel(SQLModel, table=True):
    """Configuración específica de VariDoser."""
    __tablename__ = "vari_doser_configurations"

    doser_id: UUID = Field(foreign_key="dosers.id", primary_key=True)
    max_motor_speed_rpm: float
    flow_rate_kg_min_at_max: float      # Calibrado
    last_calibration_date: datetime
```

**Características:**
- ✅ Tablas separadas por tipo de doser
- ✅ Se guardan en BD
- ✅ Se administran desde pantalla de "Configuración de Equipos"
- ✅ Usadas por PLCAdapter para traducción

---

#### ✅ Infraestructura (PLCAdapter con Lógica de Traducción)

**Responsabilidad:** Traducir intenciones lógicas a comandos físicos según tipo

```python
# infrastructure/services/plc/plc_adapter.py

class ModbusPLCAdapter(IFeedingMachine):

    async def send_configuration(
        self,
        line_id: LineId,
        config: MachineConfiguration
    ) -> None:
        """
        Envía configuración al PLC.
        Traduce tasa lógica a parámetros físicos según tipo de doser.
        """
        # 1. Obtener línea y doser
        line = await self._line_repo.find_by_id(line_id)
        doser = line.doser

        # 2. Calcular tasa objetivo
        target_rate = doser.max_dosing_rate.as_kg_per_min * \
                     (config.doser_speed_percentage / 100.0)

        # 3. Traducir según tipo de doser
        if doser.doser_type == DoserType.PULSE:
            await self._configure_pulse_doser(doser.id, target_rate)

        elif doser.doser_type == DoserType.VARI:
            await self._configure_vari_doser(doser.id, target_rate)

        elif doser.doser_type == DoserType.GRAVIMETRIC:
            await self._configure_gravimetric_doser(doser.id, target_rate)

    # ─────────────────────────────────────────────────────────
    # Métodos específicos por tipo
    # ─────────────────────────────────────────────────────────

    async def _configure_pulse_doser(
        self,
        doser_id: DoserId,
        target_rate_kg_min: float
    ) -> None:
        """
        Configura doser por pulsos.
        Ajusta tiempo OFF para lograr la tasa deseada.
        """
        # Leer configuración específica de BD
        pulse_config = await self._pulse_config_repo.find_by_doser_id(doser_id)

        # Calcular tiempo OFF necesario
        pulses_per_min = (target_rate_kg_min * 1000) / pulse_config.grams_per_pulse
        cycle_time = 60.0 / pulses_per_min
        off_time = cycle_time - pulse_config.pulse_on_time_seconds

        # Validar límite físico
        if off_time < 0.1:
            raise ValueError(f"Rate too high: requires off_time={off_time}s (min 0.1s)")

        # Escribir a Modbus
        await self._modbus_client.write_registers(
            address=self._get_doser_base_address(doser_id),
            values={
                "pulse_on_time": pulse_config.pulse_on_time_seconds,
                "pulse_off_time": off_time,
                "motor_speed": pulse_config.operating_speed_percentage
            }
        )

    async def _configure_vari_doser(
        self,
        doser_id: DoserId,
        target_rate_kg_min: float
    ) -> None:
        """
        Configura VariDoser.
        Ajusta velocidad del motor para lograr la tasa deseada.
        """
        # Leer configuración específica de BD
        vari_config = await self._vari_config_repo.find_by_doser_id(doser_id)

        # Calcular velocidad del motor (porcentaje)
        motor_speed_percentage = (target_rate_kg_min /
                                 vari_config.flow_rate_kg_min_at_max) * 100.0

        # Validar rango
        if motor_speed_percentage > 100:
            raise ValueError(f"Rate too high: requires {motor_speed_percentage}% motor speed")

        # Escribir a Modbus
        await self._modbus_client.write_registers(
            address=self._get_doser_base_address(doser_id),
            values={
                "motor_speed_percentage": motor_speed_percentage
            }
        )
```

---

## 4. Flujos de Operación

### 4.1 Configuración Inicial de un Doser (Pantalla de Equipos)

```
┌─────────────────────────────────────────────┐
│  OPERADOR: Configura Doser por Pulsos      │
│  - Tipo: PULSE                              │
│  - Tiempo ON: 1.0s                          │
│  - Tiempo OFF base: 0.5s                    │
│  - Velocidad: 30%                           │
│  - Calibración: 660g/pulso                  │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
         ┌────────────────────┐
         │  Use Case          │
         │  ConfigureDoser    │
         └────────┬───────────┘
                  │
                  ▼
    ┌─────────────────────────────────┐
    │  1. Calcula max_dosing_rate:    │
    │     - Ciclo min = 1.0 + 0.1 = 1.1s │
    │     - Pulsos/min = 60/1.1 = 54.5│
    │     - Max rate = 54.5 * 660g    │
    │                = 36 kg/min      │
    └─────────────┬───────────────────┘
                  │
                  ▼
    ┌─────────────────────────────────┐
    │  2. Guarda en BD:               │
    │     dosers:                     │
    │       - max_dosing_rate: 36     │
    │                                  │
    │     pulse_doser_configurations: │
    │       - pulse_on_time: 1.0      │
    │       - pulse_off_time: 0.5     │
    │       - operating_speed: 30     │
    │       - grams_per_pulse: 660    │
    └─────────────────────────────────┘
```

---

### 4.2 Inicio de Alimentación (Pantalla de Alimentar)

```
┌─────────────────────────────────────────────┐
│  OPERADOR: Inicia alimentación              │
│  - Jaula: #12                               │
│  - Tasa: 50% de capacidad                   │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
         ┌────────────────────┐
         │  Use Case          │
         │  StartFeeding      │
         └────────┬───────────┘
                  │
                  ▼
    ┌─────────────────────────────────┐
    │  Strategy genera config:        │
    │    doser_speed_percentage: 50%  │
    └─────────────┬───────────────────┘
                  │
                  ▼
         ┌────────────────────┐
         │  FeedingSession    │
         │  start_operation() │
         └────────┬───────────┘
                  │
                  ▼
         ┌────────────────────┐
         │  IFeedingMachine   │
         │  send_configuration│
         └────────┬───────────┘
                  │
                  ▼
    ┌─────────────────────────────────┐
    │  PLCAdapter:                    │
    │  1. Lee doser.doser_type: PULSE │
    │  2. Calcula tasa:               │
    │     36 kg/min * 50% = 18 kg/min │
    │  3. Lee pulse_doser_config      │
    │  4. Calcula tiempo OFF:         │
    │     - Pulsos/min = 18000/660 = 27.3 │
    │     - Ciclo = 60/27.3 = 2.2s    │
    │     - OFF = 2.2 - 1.0 = 1.2s    │
    │  5. Escribe a Modbus:           │
    │     - ON: 1.0s                  │
    │     - OFF: 1.2s                 │
    │     - SPEED: 30%                │
    └─────────────────────────────────┘
```

---

### 4.3 Ajuste de Tasa en Caliente (Durante Alimentación)

```
┌─────────────────────────────────────────────┐
│  OPERADOR: Cambia tasa a 70%                │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
         ┌────────────────────┐
         │  Use Case          │
         │  UpdateParams      │
         └────────┬───────────┘
                  │
                  ▼
         ┌────────────────────┐
         │  FeedingSession    │
         │  update_params()   │
         └────────┬───────────┘
                  │
                  ▼
         ┌────────────────────┐
         │  PLCAdapter        │
         └────────┬───────────┘
                  │
                  ▼
    ┌─────────────────────────────────┐
    │  Para PULSE doser:              │
    │  1. Nueva tasa: 36 * 70% = 25.2 kg/min │
    │  2. Nuevo OFF: 0.46s            │
    │  3. Escribe solo OFF a Modbus   │
    │                                  │
    │  Para VARI doser:               │
    │  1. Nueva velocidad motor: 70%  │
    │  2. Escribe velocidad a Modbus  │
    └─────────────────────────────────┘
```

---

## 5. Ventajas de esta Arquitectura

### 5.1 Dominio Limpio
- ✅ Solo conceptos de negocio (capacidades, no implementación)
- ✅ Fácil de testear sin hardware
- ✅ No cambia al agregar nuevos tipos de dosers

### 5.2 Extensibilidad
- ✅ Agregar nuevo tipo = nueva tabla de config + método en PLCAdapter
- ✅ No requiere modificar el dominio de Alimentación
- ✅ No requiere modificar use cases

### 5.3 Configuración Centralizada
- ✅ Parámetros físicos administrables desde UI
- ✅ Calibración aislada en infraestructura
- ✅ Trazabilidad de cambios (last_calibration_date)

### 5.4 Separación de Responsabilidades
- ✅ Dominio: Reglas de negocio
- ✅ Infraestructura: Traducción técnica
- ✅ Cada capa con su responsabilidad clara

---

## 6. Comparación con Alternativas Descartadas

### ❌ Alternativa 1: Parámetros específicos en clase Doser genérica

```python
# INCORRECTO
class Doser:
    _pulse_on_time: float       # ¿Qué pasa con VariDoser?
    _pulse_off_time: float      # ¿Qué pasa con VariDoser?
    _grams_per_pulse: float     # ¿Qué pasa con VariDoser?
```

**Problema:** Mezcla parámetros de diferentes tipos en una sola clase.

---

### ❌ Alternativa 2: Subclases en Dominio

```python
# INCORRECTO
class Doser(ABC):
    pass

class PulseDoser(Doser):
    _pulse_on_time: float
    ...

class VariDoser(Doser):
    _max_motor_speed: float
    ...
```

**Problema:**
- El dominio de Alimentación no necesita este polimorfismo
- Agrega complejidad innecesaria
- Cada nuevo tipo requiere cambios en dominio

---

### ❌ Alternativa 3: Todo en Infraestructura

```python
# INCORRECTO: Mover Doser completamente a infraestructura
```

**Problema:**
- El Doser SÍ es un concepto de dominio (componente de la línea)
- Solo los DETALLES de implementación van en infraestructura
- La abstracción del doser (capacidad, tipo) es relevante para el negocio

---

## 7. Impacto en Otros Documentos

### 7.1 En `dominio-proceso-alimentacion.md`

**NO cambia:**
- `MachineConfiguration.doser_speed_percentage` sigue siendo correcto (0-100%)
- El flujo de operaciones sigue igual
- Las interfaces `IFeedingMachine`, `IFeedingStrategy` siguen igual

**Aclaración agregada:**
- `Doser` es genérico, sin subclases
- `max_dosing_rate` es un valor guardado, no calculado dinámicamente
- Los detalles específicos viven en infraestructura

---

### 7.2 En `proceso-de-alimentacion.md`

**Aclaración:**
- La sección de "Integración con Hardware" debe mencionar que PLCAdapter traduce según tipo de doser
- Los DTOs (`MachineConfiguration`, `MachineStatus`) son genéricos, no específicos por tipo

---

## 8. Tareas Pendientes

### 8.1 Implementación

- [ ] Actualizar clase `Doser` en dominio (eliminar parámetros específicos si existen)
- [ ] Crear modelos de configuración en infraestructura:
  - [ ] `PulseDoserConfigModel`
  - [ ] `VariDoserConfigModel`
- [ ] Crear repositorios de configuración:
  - [ ] `IPulseDoserConfigRepository`
  - [ ] `IVariDoserConfigRepository`
- [ ] Implementar lógica de traducción en `PLCAdapter`:
  - [ ] `_configure_pulse_doser()`
  - [ ] `_configure_vari_doser()`
- [ ] Migración de BD:
  - [ ] Crear tabla `pulse_doser_configurations`
  - [ ] Crear tabla `vari_doser_configurations`
  - [ ] Migrar datos existentes (si aplica)

### 8.2 Pantallas de Configuración

- [ ] UI para configurar doser por pulsos
- [ ] UI para configurar VariDoser
- [ ] UI para calibración (ambos tipos)
- [ ] Validaciones de rangos en frontend

### 8.3 Documentación

- [ ] Actualizar `dominio-proceso-alimentacion.md` con aclaración sobre Doser genérico
- [ ] Documentar proceso de calibración para cada tipo
- [ ] Manual de operador: diferencias entre tipos

---

## 9. Conclusiones

### ✅ Decisiones Validadas

1. **Doser genérico en dominio** - Una sola clase, sin subclases
2. **Configuraciones específicas en infraestructura** - Tablas separadas por tipo
3. **PLCAdapter traduce** - Según tipo, lee config y calcula parámetros físicos
4. **Sin polimorfismo en dominio** - El proceso de alimentación es agnóstico al tipo

### 🎯 Principio Arquitectural

> **"El dominio sabe QUÉ, la infraestructura sabe CÓMO"**

- Dominio: "Dosifica a 50 kg/min"
- Infraestructura: "Para pulse doser: ON=1s, OFF=1.2s, SPEED=30%"
- Infraestructura: "Para vari doser: MOTOR_SPEED=70%"

---

**Fin del Documento**

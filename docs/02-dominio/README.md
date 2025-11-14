# Documentación del Dominio

Esta carpeta contiene la documentación de todos los elementos del dominio del sistema de alimentación de peces.

## 📦 Aggregate Roots

Los Aggregate Roots son las entidades principales que garantizan la consistencia del dominio:

- **[FeedingLine](aggregates/feeding-line.md)** - Línea de alimentación completa con sus componentes
- **[Silo](aggregates/silo.md)** - Contenedor de almacenamiento de alimento
- **[Cage](aggregates/cage.md)** - Jaula de peces que recibe alimento

## 💎 Value Objects

Los Value Objects son objetos inmutables que representan conceptos del dominio:

### Identificadores

- **[Identificadores](value-objects/identificadores.md)** - IDs únicos para todas las entidades (LineId, SiloId, CageId, etc.)

### Nombres

- **[Nombres](value-objects/nombres.md)** - Nombres validados para entidades (LineName, SiloName, CageName, etc.)

### Medidas y Especificaciones

- **[Weight](value-objects/weight.md)** - Medida de peso con conversiones automáticas
- **[Dosing](value-objects/dosing.md)** - Tasas y rangos de dosificación (DosingRate, DosingRange)
- **[Blower](value-objects/blower.md)** - Configuración del soplador (BlowerPowerPercentage, BlowDurationInSeconds)
- **[Selector](value-objects/selector.md)** - Configuración de la selectora (SelectorCapacity, SelectorSpeedProfile, SlotNumber, SlotAssignment)

## 🎯 Reglas de Negocio Principales

### FA1: Composición Mínima

Una línea de alimentación debe tener obligatoriamente:

- 1 Blower (soplador)
- Al menos 1 Doser (dosificador)
- 1 Selector (selectora)

### FA2: Nombres Únicos

No puede haber dos entidades del mismo tipo con el mismo nombre:

- Silos con nombres únicos
- Jaulas con nombres únicos
- Líneas con nombres únicos

### FA3: Jaula en Una Línea

Una jaula solo puede estar asignada a una línea de alimentación a la vez.

### FA4: Slots Únicos

En una línea de alimentación:

- No puede haber dos jaulas en el mismo slot
- Una jaula no puede estar en dos slots diferentes
- Los slots deben estar dentro de la capacidad del selector

### FA5: Silo 1-a-1

Un silo solo puede estar asignado a un dosificador a la vez (relación 1-a-1).

### FA6: Referencias Válidas

Todas las referencias entre entidades deben existir:

- Un dosificador debe referenciar un silo existente
- Un slot debe referenciar una jaula existente

### FA7: Sensores Únicos por Tipo

Una línea solo puede tener un sensor de cada tipo (temperatura, presión, flujo).

## 🏗️ Arquitectura del Dominio

```
FeedingLine (Aggregate Root)
├── Blower (Entidad)
├── Doser (Entidad) [1..N]
│   └── → Silo (Referencia externa)
├── Selector (Entidad)
└── Sensor (Entidad) [0..N]
    └── SlotAssignment (VO)
        └── → Cage (Referencia externa)

Silo (Aggregate Root)
└── → Doser (Referencia externa)

Cage (Aggregate Root)
└── → FeedingLine (Referencia externa)
```

## 📚 Convenciones

### Inmutabilidad

- Los **Value Objects** son inmutables (no pueden modificarse después de crearse)
- Los **Aggregate Roots** y **Entidades** son mutables pero solo a través de métodos que validan reglas

### Validación

- Todas las validaciones ocurren en el momento de creación o modificación
- Las reglas de negocio nunca se rompen (invariantes)
- Los errores se lanzan inmediatamente si se intenta violar una regla

### Eventos de Dominio

- Los agregados lanzan eventos cuando ocurren cambios importantes
- Los eventos son inmutables y representan hechos que ya ocurrieron
- Los nombres de eventos están en pasado (ej: `SlotAssigned`, no `AssignSlot`)

## 🔍 Cómo Usar Esta Documentación

1. **Para entender un concepto**: Lee el archivo correspondiente en `aggregates/` o `value-objects/`
2. **Para implementar una regla**: Busca la regla FA en la sección correspondiente
3. **Para validar diseño**: Verifica que tu implementación respeta las reglas que nunca se rompen
4. **Para crear tests**: Usa las reglas documentadas como casos de prueba

## 📝 Notas

- Esta documentación describe el **modelo de dominio**, no la implementación técnica
- Se enfoca en **qué** hace el dominio, no en **cómo** lo hace
- Es independiente de la tecnología (base de datos, framework, etc.)
- Debe mantenerse actualizada cuando cambien las reglas de negocio

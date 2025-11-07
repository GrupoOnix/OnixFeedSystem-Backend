from __future__ import annotations
from dataclasses import dataclass
from uuid import UUID, uuid4
from typing import Any
import re

def _validate_name_format(value: str, field_name: str = "El nombre"):
    """
    Función de validación interna reutilizable para todos los VOs de Nombres.
    
    Reglas:
    1. Debe ser un string.
    2. No puede estar vacío (después de quitar espacios).
    3. No puede exceder los 100 caracteres.
    4. Solo puede contener alfanuméricos, espacios, guiones (-) y guiones bajos (_).
    """
    if not isinstance(value, str):
        raise ValueError(f"{field_name} debe ser una cadena")

    trimmed_value = value.strip()
    
    if len(trimmed_value) == 0:
        raise ValueError(f"{field_name} no puede estar vacío")
    
    if len(value) > 100:
        raise ValueError(f"{field_name} no debe exceder 100 caracteres (recibió {len(value)})")
    
    # ^[a-zA-Z0-9\s_-]+$
    # ^                 -> inicio del string
    # [a-zA-Z0-9\s_-]  -> permite letras, números, espacios, guión bajo, guión
    # +                 -> uno o más de esos caracteres
    # $                 -> fin del string
    if not re.match(r'^[a-zA-Z0-9\s_-]+$', value):
        raise ValueError(f"{field_name} solo puede contener letras, números, espacios, guiones (-) y guiones bajos (_)")

# ============================================================================
# 1. Identificador del Aggregate Root
# ============================================================================

@dataclass(frozen=True)
class LineId:
    """Identificador único para una línea de alimentación."""
    value: UUID

    @classmethod
    def generate(cls) -> 'LineId':
        """Genera un nuevo LineId único."""
        return cls(uuid4())

    @classmethod
    def from_string(cls, id_str: str) -> 'LineId':
        """Crea un LineId desde una representación de cadena."""
        return cls(UUID(id_str))

    def __str__(self) -> str:
        return str(self.value)

# ============================================================================
# 2. Identificadores de Entidades Hijas
# ============================================================================

@dataclass(frozen=True)
class BlowerId:
    """Identificador único para una entidad soplador."""
    value: UUID

    @classmethod
    def generate(cls) -> 'BlowerId':
        """Genera un nuevo BlowerId único."""
        return cls(uuid4())

    @classmethod
    def from_string(cls, id_str: str) -> 'BlowerId':
        """Crea un BlowerId desde una representación de cadena."""
        return cls(UUID(id_str))

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class DoserId:
    """Identificador único para una entidad dosificador."""
    value: UUID

    @classmethod
    def generate(cls) -> 'DoserId':
        """Genera un nuevo DoserId único."""
        return cls(uuid4())

    @classmethod
    def from_string(cls, id_str: str) -> 'DoserId':
        """Crea un DoserId desde una representación de cadena."""
        return cls(UUID(id_str))

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class SelectorId:
    """Identificador único para una entidad selector."""
    value: UUID

    @classmethod
    def generate(cls) -> 'SelectorId':
        """Genera un nuevo SelectorId único."""
        return cls(uuid4())

    @classmethod
    def from_string(cls, id_str: str) -> 'SelectorId':
        """Crea un SelectorId desde una representación de cadena."""
        return cls(UUID(id_str))

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class SensorId:
    """Identificador único para una entidad sensor"""
    value: UUID

    @classmethod
    def generate(cls) -> 'SensorId':
        """Genera un nuevo SensorId único."""
        return cls(uuid4())

    @classmethod
    def from_string(cls, id_str: str) -> 'SensorId':
        """Crea un SensorId desde una representación de cadena."""
        return cls(UUID(id_str))

    def __str__(self) -> str:
        return str(self.value)


# ============================================================================
# 3. Referencias a Agregados Externos (External Aggregate References)
# ============================================================================

@dataclass(frozen=True)
class CageId:

    value: UUID

    @classmethod
    def generate(cls) -> 'CageId':
        return cls(uuid4())

    @classmethod
    def from_string(cls, id_str: str) -> 'CageId':
        return cls(UUID(id_str))

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class SiloId:

    value: UUID

    @classmethod
    def generate(cls) -> 'SiloId':
        return cls(uuid4())

    @classmethod
    def from_string(cls, id_str: str) -> 'SiloId':
        return cls(UUID(id_str))

    def __str__(self) -> str:
        return str(self.value)

# ============================================================================
# 4. VOs de Nombres y Atributos (Names & Attributes VOs)
# ============================================================================

@dataclass(frozen=True)
class LineName:
    """Nombre de una línea de alimentación con reglas de validación."""
    value: str

    def __post_init__(self):
        """Valida el nombre de línea según las reglas de negocio."""
        _validate_name_format(self.value, "El nombre de línea")

    def __str__(self) -> str:
        return self.value

@dataclass(frozen=True)
class BlowerName:
    """Nombre de un componente soplador con validación."""
    value: str

    def __post_init__(self):
        """Valida el nombre del soplador según las reglas de negocio."""
        _validate_name_format(self.value, "El nombre del soplador")

    def __str__(self) -> str:
        return self.value

@dataclass(frozen=True)
class DoserName:
    """Nombre de un componente dosificador con validación."""
    value: str

    def __post_init__(self):
        """Valida el nombre del dosificador según las reglas de negocio."""
        _validate_name_format(self.value, "El nombre del dosificador")

    def __str__(self) -> str:
        return self.value

@dataclass(frozen=True)
class SelectorName:
    """Nombre de un componente selector con validación."""
    value: str

    def __post_init__(self):
        """Valida el nombre del selector según las reglas de negocio."""
        _validate_name_format(self.value, "El nombre del selector")

    def __str__(self) -> str:
        return self.value

@dataclass(frozen=True)
class SensorName:

    value: str

    def __post_init__(self):
        _validate_name_format(self.value, "El nombre del sensor")

    def __str__(self) -> str:
        return self.value

@dataclass(frozen=True)
class CageName:

    value: str

    def __post_init__(self):
        _validate_name_format(self.value, "El nombre de la jaula")

    def __str__(self) -> str:
        return self.value
    
@dataclass(frozen=True)
class SiloName:

    value: str

    def __post_init__(self):
        _validate_name_format(self.value, "El nombre del silo")

    def __str__(self) -> str:
        return self.value

# ============================================================================
# 5. VOs de Medidas Físicas y Especificaciones (Physical Measures & Specs)
# ============================================================================

@dataclass(frozen=True)
class BlowerPowerPercentage:
    """
    Representa la potencia del soplador como un valor porcentual (0-100).
    Este es el valor que el software maneja y que el PLC interpretará.
    """
    value: float

    def __post_init__(self):
        """Valida que el valor sea un porcentaje válido (0-100)."""
        
        if not isinstance(self.value, (int, float)):
            raise ValueError("La potencia (porcentaje) debe ser un valor numérico")
            
        # Regla de negocio: El valor debe estar entre 0% y 100%
        if not 0.0 <= self.value <= 100.0:
            raise ValueError("La potencia debe ser un porcentaje entre 0.0 y 100.0")

    def __str__(self) -> str:
        return f"{self.value} %"

@dataclass(frozen=True)
class BlowDurationInSeconds:
    """
    Representa un tiempo/duración de soplado en segundos.
    Usado para 'soplado antes' y 'soplado después'.
    """
    value: int  # segundos enteros

    def __post_init__(self):
        """Valida que la duración sea un número razonable."""
        
        if not isinstance(self.value, int):
            raise ValueError("La duración de soplado debe ser un entero (en segundos)")
            
        if self.value < 0:
            raise ValueError("La duración de soplado no puede ser negativa")
            
        if self.value > 600: 
            raise ValueError("La duración de soplado no puede exceder 600 segundos (10 minutos)")

    def __str__(self) -> str:
        return f"{self.value} s"

@dataclass(frozen=True)
class DosingRate:
    """Tasa de dosificación para componentes dosificadores con validación."""
    value: float
    unit: str = "kg/min"

    def __post_init__(self):
        """Valida la tasa de dosificación según las reglas de negocio."""
        if not isinstance(self.value, (int, float)):
            raise ValueError("La tasa de dosificación debe ser un valor numérico")
        
        # TODO: verificar si existe realmente una tasa maxima
        if self.value < 0:
            raise ValueError("La tasa de dosificación no puede ser negativa")
        
        if self.value > 1000:  # Límite superior razonable
            raise ValueError("La tasa de dosificación no puede exceder 1000 kg/min")
        
        if not isinstance(self.unit, str) or not self.unit:
            raise ValueError("La unidad de tasa de dosificación debe ser una cadena no vacía")

    def __str__(self) -> str:
        return f"{self.value} {self.unit}"

@dataclass(frozen=True)
class DosingRange:
    """Rango de tasas de dosificación válidas con validación."""
    min_rate: float
    max_rate: float
    unit: str = "kg/min"

    def __post_init__(self):
        """Valida el rango de dosificación según las reglas de negocio."""
        if not isinstance(self.min_rate, (int, float)):
            raise ValueError("La tasa mínima de dosificación debe ser un valor numérico")
        
        if not isinstance(self.max_rate, (int, float)):
            raise ValueError("La tasa máxima de dosificación debe ser un valor numérico")
        
        if self.min_rate < 0:
            raise ValueError("La tasa mínima de dosificación no puede ser negativa")
        
        if self.max_rate < 0:
            raise ValueError("La tasa máxima de dosificación no puede ser negativa")
        
        if self.min_rate >= self.max_rate:
            raise ValueError("La tasa mínima debe ser menor que la tasa máxima")
        
        if not isinstance(self.unit, str) or not self.unit:
            raise ValueError("La unidad del rango de dosificación debe ser una cadena no vacía")

    def contains(self, rate: DosingRate) -> bool:
        """Verifica si una tasa de dosificación está dentro de este rango."""
        if rate.unit != self.unit:
            raise ValueError(f"La unidad de tasa '{rate.unit}' no coincide con la unidad del rango '{self.unit}'")
        
        return self.min_rate <= rate.value <= self.max_rate

    def __str__(self) -> str:
        return f"{self.min_rate}-{self.max_rate} {self.unit}"

@dataclass(frozen=True)
class SelectorCapacity:
    """Capacidad (número de ranuras) para un componente selector."""
    value: int

    def __post_init__(self):
        """Valida la capacidad del selector."""
        if not isinstance(self.value, int):
            raise ValueError("La capacidad del selector debe ser un entero")
        
        if self.value <= 0:
            raise ValueError("La capacidad del selector debe ser mayor que 0")

    def __str__(self) -> str:
        return f"{self.value} ranuras"
     
@dataclass(frozen=True)
class SelectorSpeedProfile:
    """
    Encapsula la configuración de velocidad para una Selectora.
    
    Reutiliza el VO BlowerPowerPercentage para validar que las
    velocidades estén entre 0-100.
    """
    fast_speed: BlowerPowerPercentage
    slow_speed: BlowerPowerPercentage

    def __post_init__(self):
        """Valida reglas de negocio del perfil de velocidad."""
        if self.slow_speed.value >= self.fast_speed.value:
            raise ValueError(
                "La velocidad lenta debe ser menor que la velocidad rápida."
            )

    def __str__(self) -> str:
        return f"Fast: {self.fast_speed}, Slow: {self.slow_speed}"

# ============================================================================
# 6. VOs Estructurales y de Relación
# ============================================================================

@dataclass(frozen=True)
class SlotNumber:
    """Número de ranura (slot) con validación."""
    value: int

    def __post_init__(self):
        """Valida el número de ranura según las reglas de negocio."""
        if not isinstance(self.value, int):
            raise ValueError("El número de ranura debe ser un entero")
        
        if self.value < 1:
            raise ValueError("El número de ranura debe ser positivo (desde 1)")

    def __str__(self) -> str:
        return str(self.value)

    def __int__(self) -> int:
        return self.value
    
    def __hash__(self) -> int:
        return hash(self.value)

@dataclass(frozen=True)
class SlotAssignment:
    """
    Asignación de una jaula (CageId) a una ranura (SlotNumber) específica.
    
    Este VO representa la relación inmutable entre una ranura de la selectora
    y una jaula de destino, aplicando reglas de negocio en su creación.
    """
    # --- Ajuste Arquitectónico ---
    # Usamos el VO 'SlotNumber' en lugar de 'int' para
    # reutilizar su validación (garantiza que es >= 1).
    slot_number: SlotNumber
    cage_id: CageId

    def __post_init__(self):
        """Valida la asignación de la ranura."""
        
        if not isinstance(self.slot_number, SlotNumber):
            raise ValueError("El número de ranura debe ser una instancia de SlotNumber")
        
        if not isinstance(self.cage_id, CageId):
            raise ValueError("El ID de jaula debe ser una instancia de CageId")

    def __str__(self) -> str:
        return f"Ranura {self.slot_number} -> Jaula {self.cage_id}"
    
    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other: Any) -> bool:
        """Compara asignaciones por ranura y ID de jaula."""
        if not isinstance(other, SlotAssignment):
            return False
        return self.slot_number == other.slot_number and self.cage_id == other.cage_id

    def __hash__(self) -> int:
        """Genera hash para uso en sets y diccionarios."""
        return hash((self.slot_number, self.cage_id))


@dataclass(frozen=True, eq=False)
class Weight:

    _miligrams: int

    # --- 1. MÉTODOS DE FÁBRICA (CREACIÓN) ---
    # El usuario NUNCA llama a Weight(miligrams=...)
    # El usuario SIEMPRE llama a Weight.from_kg(...), Weight.from_grams(...), etc.

    @classmethod
    def from_miligrams(cls, mg: int | float) -> Weight:

        if not isinstance(mg, (int, float)):
            raise TypeError("La cantidad de miligramos debe ser un valor numérico.")
        if mg < 0:
            raise ValueError("El peso no puede ser negativo.")
        return cls(_miligrams=round(mg))

    @classmethod
    def from_grams(cls, grams: int | float) -> Weight:

        if not isinstance(grams, (int, float)):
            raise TypeError("La cantidad de gramos debe ser un valor numérico.")
        if grams < 0:
            raise ValueError("El peso no puede ser negativo.")
        
        miligrams_value = round(grams * 1000)
        return cls(_miligrams=miligrams_value)

    @classmethod
    def from_kg(cls, kg: int | float) -> Weight:

        if not isinstance(kg, (int, float)):
            raise TypeError("La cantidad de kg debe ser un valor numérico.")
        if kg < 0:
            raise ValueError("El peso no puede ser negativo.")
        
        miligrams_value = round(kg * 1_000_000)
        return cls(_miligrams=miligrams_value)

    @classmethod
    def from_tons(cls, tons: int | float) -> Weight:

        if not isinstance(tons, (int, float)):
            raise TypeError("La cantidad de toneladas debe ser un valor numérico.")
        if tons < 0:
            raise ValueError("El peso no puede ser negativo.")
            
        miligrams_value = round(tons * 1_000_000_000)
        return cls(_miligrams=miligrams_value)
    
    @classmethod
    def zero(cls) -> Weight:
        return cls(_miligrams=0)

    # --- 2. GETTERS DE CONVERSIÓN (LECTURA) ---

    @property
    def as_miligrams(self) -> int:
        return self._miligrams

    @property
    def as_grams(self) -> float:
        return self._miligrams / 1000.0

    @property
    def as_kg(self) -> float:
        return self._miligrams / 1_000_000.0

    @property
    def as_tons(self) -> float:
        return self._miligrams / 1_000_000_000.0

    # --- 3. OPERACIONES MATEMÁTICAS ---

    def __add__(self, other: Any) -> Weight:
        if not isinstance(other, Weight):
            return NotImplemented # Permite que Python intente otras operaciones TODO: que es esto?

        return Weight(_miligrams=self._miligrams + other._miligrams)

    def __sub__(self, other: Any) -> Weight:
        if not isinstance(other, Weight):
            return NotImplemented
        
        new_miligrams = self._miligrams - other._miligrams
        if new_miligrams < 0:
            raise ValueError("El resultado de la resta de peso no puede ser negativo (stock insuficiente).")
        return Weight(_miligrams=new_miligrams)

    def __mul__(self, multiplier: int | float) -> Weight:

        if not isinstance(multiplier, (int, float)):
            return NotImplemented
        if multiplier < 0:
            raise ValueError("No se puede multiplicar un peso por un número negativo.")
        
        new_miligrams = round(self._miligrams * multiplier)
        return Weight(_miligrams=new_miligrams)
    
    def __rmul__(self, multiplier: int | float) -> Weight:
        return self.__mul__(multiplier)

    # --- 4. COMPARACIONES SEGURAS ---

    def _validate_operand(self, other: Any) -> int:
        """Helper interno para comparaciones."""
        if not isinstance(other, Weight):
            raise TypeError(f"Solo se puede comparar Weight con otro Weight, no con {type(other)}.")
        return other._miligrams

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Weight):
            return False
        return self._miligrams == other._miligrams

    def __gt__(self, other: Any) -> bool:
        other_mg = self._validate_operand(other)
        return self._miligrams > other_mg

    def __ge__(self, other: Any) -> bool:
        other_mg = self._validate_operand(other)
        return self._miligrams >= other_mg

    def __lt__(self, other: Any) -> bool:
        other_mg = self._validate_operand(other)
        return self._miligrams < other_mg

    def __le__(self, other: Any) -> bool:
        other_mg = self._validate_operand(other)
        return self._miligrams <= other_mg

    # --- 5. REPRESENTACIÓN (LEGIBILIDAD) ---

    def __str__(self) -> str:
        if self._miligrams == 0:
            return "0 kg"
        
        if abs(self._miligrams) >= 1_000_000_000:
            return f"{self.as_tons:.2f} ton"
        
        if abs(self._miligrams) >= 1_000_000:
            return f"{self.as_kg:.2f} kg"
        
        if abs(self._miligrams) >= 1000:
            return f"{self.as_grams:.2f} g"
        
        return f"{self.as_miligrams} mg"
        
    def __repr__(self) -> str:
        return f"Weight(miligrams={self._miligrams})"
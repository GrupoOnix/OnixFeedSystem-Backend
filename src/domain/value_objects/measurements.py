"""
Value Objects para medidas físicas (peso, volumen, etc.).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Volume:
    """Volumen con precisión, almacenado internamente en milímetros cúbicos."""
    _cubic_millimeters: int

    @classmethod
    def from_cubic_millimeters(cls, mm3: int | float) -> Volume:
        if not isinstance(mm3, (int, float)):
            raise TypeError("El volumen debe ser un valor numérico")
        if mm3 < 0:
            raise ValueError("El volumen no puede ser negativo")
        return cls(_cubic_millimeters=round(mm3))

    @classmethod
    def from_liters(cls, liters: int | float) -> Volume:
        if not isinstance(liters, (int, float)):
            raise TypeError("El volumen debe ser un valor numérico")
        if liters < 0:
            raise ValueError("El volumen no puede ser negativo")
        return cls(_cubic_millimeters=round(liters * 1_000_000))

    @classmethod
    def from_cubic_meters(cls, m3: int | float) -> Volume:
        if not isinstance(m3, (int, float)):
            raise TypeError("El volumen debe ser un valor numérico")
        if m3 < 0:
            raise ValueError("El volumen no puede ser negativo")
        return cls(_cubic_millimeters=round(m3 * 1_000_000_000))

    @classmethod
    def zero(cls) -> Volume:
        return cls(_cubic_millimeters=0)

    @property
    def as_cubic_millimeters(self) -> int:
        return self._cubic_millimeters

    @property
    def as_liters(self) -> float:
        return self._cubic_millimeters / 1_000_000.0

    @property
    def as_cubic_meters(self) -> float:
        return self._cubic_millimeters / 1_000_000_000.0

    def __str__(self) -> str:
        if self._cubic_millimeters == 0:
            return "0 m³"

        if abs(self._cubic_millimeters) >= 1_000_000_000:
            return f"{self.as_cubic_meters:.2f} m³"

        if abs(self._cubic_millimeters) >= 1_000_000:
            return f"{self.as_liters:.2f} L"

        return f"{self.as_cubic_millimeters} mm³"

    def __repr__(self) -> str:
        return f"Volume(cubic_millimeters={self._cubic_millimeters})"


@dataclass(frozen=True)
class Density:
    """Densidad de biomasa en kg/m³."""
    value: float

    def __post_init__(self):
        if not isinstance(self.value, (int, float)):
            raise TypeError("La densidad debe ser un valor numérico")

        if self.value < 0:
            raise ValueError("La densidad no puede ser negativa")

        if self.value > 200:
            raise ValueError("La densidad no puede exceder 200 kg/m³")

    def __str__(self) -> str:
        return f"{self.value:.2f} kg/m³"

    def __float__(self) -> float:
        return float(self.value)


@dataclass(frozen=True, eq=False)
class Weight:
    """
    Value Object para representar peso con precisión.
    Almacena internamente en miligramos para evitar errores de redondeo.
    """
    _miligrams: int

    # --- 1. MÉTODOS DE FÁBRICA (CREACIÓN) ---

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
            return NotImplemented

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

"""
Tests unitarios para Value Objects del dominio.

Estos tests verifican:
- Creación y validación de value objects
- Inmutabilidad
- Comparaciones y operaciones
- Validación de reglas de negocio
- Conversiones y factory methods
"""

from uuid import UUID

import pytest

from domain.value_objects import (
    LineId, LineName,
    CageId, CageName,
    SiloId, SiloName,
    SessionId, OperationId,
    Weight, Volume, Density,
    FCR, FishCount
)


class TestIdentifierValueObjects:
    """Tests para value objects de identificadores (UUIDs)."""

    def test_line_id_generates_valid_uuid(self):
        """Debe generar UUID válido."""
        line_id = LineId.generate()

        assert isinstance(line_id.value, UUID)

    def test_line_id_from_string(self):
        """Debe crear desde string UUID."""
        uuid_str = "123e4567-e89b-12d3-a456-426614174000"
        line_id = LineId.from_string(uuid_str)

        assert str(line_id.value) == uuid_str

    def test_line_id_immutable(self):
        """Debe ser inmutable."""
        line_id = LineId.generate()

        with pytest.raises(Exception):  # dataclass frozen
            line_id.value = LineId.generate().value

    def test_line_id_equality(self):
        """Debe comparar correctamente por valor."""
        uuid_value = UUID("123e4567-e89b-12d3-a456-426614174000")
        line_id1 = LineId(uuid_value)
        line_id2 = LineId(uuid_value)

        assert line_id1 == line_id2

    def test_all_id_types_have_generate(self):
        """Todos los tipos de ID deben tener método generate."""
        assert LineId.generate() is not None
        assert CageId.generate() is not None
        assert SiloId.generate() is not None
        assert SessionId.generate() is not None
        assert OperationId.generate() is not None


class TestNameValueObjects:
    """Tests para value objects de nombres."""

    def test_line_name_valid(self):
        """Debe aceptar nombre válido."""
        name = LineName("Línea Principal 1")

        assert name.value == "Línea Principal 1"

    def test_line_name_rejects_empty(self):
        """Debe rechazar nombre vacío."""
        with pytest.raises(ValueError):
            LineName("")

    def test_line_name_rejects_whitespace_only(self):
        """Debe rechazar solo espacios."""
        with pytest.raises(ValueError):
            LineName("   ")

    def test_line_name_rejects_too_long(self):
        """Debe rechazar nombres muy largos (>100 caracteres)."""
        long_name = "A" * 101

        with pytest.raises(ValueError):
            LineName(long_name)

    def test_line_name_accepts_special_chars(self):
        """Debe aceptar caracteres especiales válidos."""
        name = LineName("Línea_Principal-1")

        assert name.value == "Línea_Principal-1"

    def test_line_name_accepts_tildes(self):
        """Debe aceptar tildes y ñ."""
        name = LineName("Línea Año")

        assert name.value == "Línea Año"

    def test_cage_name_validation(self):
        """CageName debe tener las mismas validaciones."""
        valid = CageName("Jaula_Principal-1")
        assert valid.value == "Jaula_Principal-1"

        with pytest.raises(ValueError):
            CageName("")

    def test_silo_name_validation(self):
        """SiloName debe tener las mismas validaciones."""
        valid = SiloName("Silo-A")
        assert valid.value == "Silo-A"

        with pytest.raises(ValueError):
            SiloName("")

    def test_name_immutable(self):
        """Los nombres deben ser inmutables."""
        name = LineName("Test")

        with pytest.raises(Exception):
            name.value = "Changed"


class TestWeightValueObject:
    """Tests para value object Weight."""

    def test_weight_from_kg(self):
        """Debe crear desde kilogramos."""
        weight = Weight.from_kg(10.5)

        assert weight.as_kg == 10.5

    def test_weight_from_grams(self):
        """Debe crear desde gramos."""
        weight = Weight.from_grams(1500.0)

        assert weight.as_grams == 1500.0
        assert weight.as_kg == 1.5

    def test_weight_from_miligrams(self):
        """Debe crear desde miligramos."""
        weight = Weight.from_miligrams(1500000)

        assert weight.as_miligrams == 1500000
        assert weight.as_kg == 1.5

    def test_weight_from_tons(self):
        """Debe crear desde toneladas."""
        weight = Weight.from_tons(0.001)

        assert weight.as_tons == 0.001
        assert weight.as_kg == 1.0

    def test_weight_zero(self):
        """Debe crear peso cero."""
        weight = Weight.zero()

        assert weight.as_kg == 0.0

    def test_weight_rejects_negative(self):
        """Debe rechazar pesos negativos."""
        with pytest.raises(ValueError):
            Weight.from_kg(-10.0)

    def test_weight_addition(self):
        """Debe sumar correctamente."""
        w1 = Weight.from_kg(10.0)
        w2 = Weight.from_kg(5.0)

        result = w1 + w2

        assert result.as_kg == 15.0

    def test_weight_subtraction(self):
        """Debe restar correctamente."""
        w1 = Weight.from_kg(10.0)
        w2 = Weight.from_kg(3.0)

        result = w1 - w2

        assert result.as_kg == 7.0

    def test_weight_multiplication(self):
        """Debe multiplicar correctamente."""
        weight = Weight.from_kg(10.0)

        result = weight * 2.0

        assert result.as_kg == 20.0

    def test_weight_comparison_equal(self):
        """Debe comparar igualdad."""
        w1 = Weight.from_kg(10.0)
        w2 = Weight.from_kg(10.0)

        assert w1 == w2

    def test_weight_comparison_less_than(self):
        """Debe comparar menor que."""
        w1 = Weight.from_kg(5.0)
        w2 = Weight.from_kg(10.0)

        assert w1 < w2

    def test_weight_comparison_greater_than(self):
        """Debe comparar mayor que."""
        w1 = Weight.from_kg(15.0)
        w2 = Weight.from_kg(10.0)

        assert w1 > w2

    def test_weight_immutable(self):
        """Debe ser inmutable."""
        weight = Weight.from_kg(10.0)

        with pytest.raises(Exception):
            weight._miligrams = 5000000


class TestVolumeValueObject:
    """Tests para value object Volume."""

    def test_volume_from_liters(self):
        """Debe crear desde litros."""
        volume = Volume.from_liters(1000.0)

        assert volume.as_liters == 1000.0

    def test_volume_from_cubic_meters(self):
        """Debe crear desde metros cúbicos."""
        volume = Volume.from_cubic_meters(1.0)

        assert volume.as_cubic_meters == 1.0
        assert volume.as_liters == 1000.0

    def test_volume_rejects_negative(self):
        """Debe rechazar volúmenes negativos."""
        with pytest.raises(ValueError):
            Volume.from_liters(-100.0)

    def test_volume_immutable(self):
        """Debe ser inmutable."""
        volume = Volume.from_liters(100.0)

        with pytest.raises(Exception):
            volume._cubic_millimeters = 5000


class TestDensityValueObject:
    """Tests para value object Density."""

    def test_density_valid_value(self):
        """Debe aceptar densidad válida."""
        density = Density(25.0)  # kg/m³

        assert density.value == 25.0

    def test_density_rejects_negative(self):
        """Debe rechazar densidad negativa."""
        with pytest.raises(ValueError):
            Density(-10.0)

    def test_density_rejects_out_of_range(self):
        """Debe rechazar densidad fuera de rango (0-200 kg/m³)."""
        with pytest.raises(ValueError):
            Density(250.0)

    def test_density_accepts_zero(self):
        """Debe aceptar densidad cero."""
        density = Density(0.0)

        assert density.value == 0.0

    def test_density_accepts_max_value(self):
        """Debe aceptar densidad máxima (200 kg/m³)."""
        density = Density(200.0)

        assert density.value == 200.0


class TestFCRValueObject:
    """Tests para value object FCR (Feed Conversion Ratio)."""

    def test_fcr_valid_value(self):
        """Debe aceptar FCR válido."""
        fcr = FCR(1.2)

        assert fcr.value == 1.2

    def test_fcr_rejects_zero(self):
        """Debe rechazar FCR cero."""
        with pytest.raises(ValueError):
            FCR(0.0)

    def test_fcr_rejects_negative(self):
        """Debe rechazar FCR negativo."""
        with pytest.raises(ValueError):
            FCR(-1.0)

    def test_fcr_rejects_out_of_range(self):
        """Debe rechazar FCR fuera de rango (0-10)."""
        with pytest.raises(ValueError):
            FCR(15.0)

    def test_fcr_accepts_typical_values(self):
        """Debe aceptar valores típicos (0.8 - 2.0)."""
        fcr1 = FCR(0.8)
        fcr2 = FCR(1.5)
        fcr3 = FCR(2.0)

        assert fcr1.value == 0.8
        assert fcr2.value == 1.5
        assert fcr3.value == 2.0


class TestFishCountValueObject:
    """Tests para value object FishCount."""

    def test_fish_count_valid(self):
        """Debe aceptar conteo válido."""
        count = FishCount(10000)

        assert count.value == 10000

    def test_fish_count_rejects_negative(self):
        """Debe rechazar conteo negativo."""
        with pytest.raises(ValueError):
            FishCount(-100)

    def test_fish_count_accepts_zero(self):
        """Debe aceptar conteo cero."""
        count = FishCount(0)

        assert count.value == 0

    def test_fish_count_immutable(self):
        """Debe ser inmutable."""
        count = FishCount(1000)

        with pytest.raises(Exception):
            count.value = 2000


class TestValueObjectsImmutability:
    """Tests generales de inmutabilidad."""

    def test_all_value_objects_are_frozen(self):
        """Todos los value objects deben ser frozen dataclasses."""
        line_id = LineId.generate()
        name = LineName("Test")
        weight = Weight.from_kg(10.0)

        # Intentar modificar debe fallar
        with pytest.raises(Exception):
            line_id.value = LineId.generate().value

        with pytest.raises(Exception):
            name.value = "Changed"

        with pytest.raises(Exception):
            weight._miligrams = 5000000

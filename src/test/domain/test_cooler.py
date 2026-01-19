"""
Tests unitarios para la entidad Cooler y sus Value Objects.

Estos tests verifican:
- Creación y validación de Cooler
- Value Objects: CoolerId, CoolerName, CoolerPowerPercentage
- Comportamiento de encendido/apagado
- Validación de potencia
- Integración con FeedingLine
"""

from datetime import datetime
from uuid import UUID

import pytest

from domain.aggregates.feeding_line.cooler import Cooler
from domain.value_objects import (
    CoolerId,
    CoolerName,
    CoolerPowerPercentage,
)

# =============================================================================
# Tests de Value Objects
# =============================================================================


class TestCoolerId:
    """Tests para el value object CoolerId."""

    def test_generate_creates_valid_uuid(self):
        """Debe generar un UUID válido."""
        cooler_id = CoolerId.generate()

        assert isinstance(cooler_id.value, UUID)

    def test_from_string_creates_valid_id(self):
        """Debe crear desde string UUID."""
        uuid_str = "123e4567-e89b-12d3-a456-426614174000"
        cooler_id = CoolerId.from_string(uuid_str)

        assert str(cooler_id.value) == uuid_str

    def test_from_string_rejects_invalid_uuid(self):
        """Debe rechazar string UUID inválido."""
        with pytest.raises(ValueError):
            CoolerId.from_string("invalid-uuid")

    def test_equality_by_value(self):
        """Debe comparar por valor."""
        uuid_value = UUID("123e4567-e89b-12d3-a456-426614174000")
        id1 = CoolerId(uuid_value)
        id2 = CoolerId(uuid_value)

        assert id1 == id2

    def test_different_ids_not_equal(self):
        """IDs diferentes no deben ser iguales."""
        id1 = CoolerId.generate()
        id2 = CoolerId.generate()

        assert id1 != id2

    def test_immutable(self):
        """Debe ser inmutable."""
        cooler_id = CoolerId.generate()

        with pytest.raises(Exception):
            cooler_id.value = CoolerId.generate().value

    def test_str_returns_uuid_string(self):
        """__str__ debe devolver string del UUID."""
        uuid_str = "123e4567-e89b-12d3-a456-426614174000"
        cooler_id = CoolerId.from_string(uuid_str)

        assert str(cooler_id) == uuid_str


class TestCoolerName:
    """Tests para el value object CoolerName."""

    def test_valid_name(self):
        """Debe aceptar nombre válido."""
        name = CoolerName("Cooler Principal")

        assert name.value == "Cooler Principal"

    def test_rejects_empty_name(self):
        """Debe rechazar nombre vacío."""
        with pytest.raises(ValueError):
            CoolerName("")

    def test_rejects_whitespace_only(self):
        """Debe rechazar solo espacios en blanco."""
        with pytest.raises(ValueError):
            CoolerName("   ")

    def test_rejects_too_long_name(self):
        """Debe rechazar nombres mayores a 100 caracteres."""
        long_name = "A" * 101

        with pytest.raises(ValueError):
            CoolerName(long_name)

    def test_accepts_max_length_name(self):
        """Debe aceptar nombre de exactamente 100 caracteres."""
        max_name = "A" * 100
        name = CoolerName(max_name)

        assert len(name.value) == 100

    def test_accepts_special_characters(self):
        """Debe aceptar caracteres especiales válidos."""
        name = CoolerName("Cooler_Principal-1")

        assert name.value == "Cooler_Principal-1"

    def test_accepts_accents_and_tildes(self):
        """Debe aceptar tildes y caracteres acentuados."""
        name = CoolerName("Enfriador Línea Ñoño")

        assert name.value == "Enfriador Línea Ñoño"

    def test_immutable(self):
        """Debe ser inmutable."""
        name = CoolerName("Test")

        with pytest.raises(Exception):
            name.value = "Changed"

    def test_str_returns_value(self):
        """__str__ debe devolver el valor del nombre."""
        name = CoolerName("Cooler Test")

        assert str(name) == "Cooler Test"


class TestCoolerPowerPercentage:
    """Tests para el value object CoolerPowerPercentage."""

    def test_valid_percentage(self):
        """Debe aceptar porcentaje válido."""
        power = CoolerPowerPercentage(75.0)

        assert power.value == 75.0

    def test_accepts_zero(self):
        """Debe aceptar 0%."""
        power = CoolerPowerPercentage(0.0)

        assert power.value == 0.0

    def test_accepts_hundred(self):
        """Debe aceptar 100%."""
        power = CoolerPowerPercentage(100.0)

        assert power.value == 100.0

    def test_accepts_decimal_values(self):
        """Debe aceptar valores decimales."""
        power = CoolerPowerPercentage(33.33)

        assert power.value == 33.33

    def test_accepts_integer_as_float(self):
        """Debe aceptar enteros que se convierten a float."""
        power = CoolerPowerPercentage(50)

        assert power.value == 50.0

    def test_rejects_negative(self):
        """Debe rechazar valores negativos."""
        with pytest.raises(ValueError) as exc_info:
            CoolerPowerPercentage(-10.0)

        assert "0.0 y 100.0" in str(exc_info.value)

    def test_rejects_above_hundred(self):
        """Debe rechazar valores mayores a 100."""
        with pytest.raises(ValueError) as exc_info:
            CoolerPowerPercentage(150.0)

        assert "0.0 y 100.0" in str(exc_info.value)

    def test_rejects_non_numeric(self):
        """Debe rechazar valores no numéricos."""
        with pytest.raises(ValueError):
            CoolerPowerPercentage("fifty")  # type: ignore

    def test_immutable(self):
        """Debe ser inmutable."""
        power = CoolerPowerPercentage(50.0)

        with pytest.raises(Exception):
            power.value = 75.0

    def test_str_format(self):
        """__str__ debe devolver formato con porcentaje."""
        power = CoolerPowerPercentage(75.5)

        assert str(power) == "75.5 %"


# =============================================================================
# Tests de la Entidad Cooler
# =============================================================================


class TestCoolerCreation:
    """Tests de creación de Cooler."""

    def test_create_with_valid_data(self):
        """Debe crear un Cooler con datos válidos."""
        cooler = Cooler(
            name=CoolerName("Cooler Principal"),
            cooling_power_percentage=CoolerPowerPercentage(75.0),
            is_on=True,
        )

        assert cooler.id is not None
        assert isinstance(cooler.id, CoolerId)
        assert str(cooler.name) == "Cooler Principal"
        assert cooler.is_on is True
        assert cooler.cooling_power_percentage.value == 75.0
        assert isinstance(cooler.created_at, datetime)

    def test_create_defaults_to_off(self):
        """Debe crear un Cooler apagado por defecto."""
        cooler = Cooler(
            name=CoolerName("Cooler Test"),
            cooling_power_percentage=CoolerPowerPercentage(50.0),
        )

        assert cooler.is_on is False

    def test_create_with_zero_power(self):
        """Debe crear un Cooler con potencia 0%."""
        cooler = Cooler(
            name=CoolerName("Cooler Apagado"),
            cooling_power_percentage=CoolerPowerPercentage(0.0),
        )

        assert cooler.cooling_power_percentage.value == 0.0

    def test_create_with_max_power(self):
        """Debe crear un Cooler con potencia 100%."""
        cooler = Cooler(
            name=CoolerName("Cooler Máximo"),
            cooling_power_percentage=CoolerPowerPercentage(100.0),
        )

        assert cooler.cooling_power_percentage.value == 100.0

    def test_each_cooler_has_unique_id(self):
        """Cada Cooler debe tener un ID único."""
        cooler1 = Cooler(
            name=CoolerName("Cooler 1"),
            cooling_power_percentage=CoolerPowerPercentage(50.0),
        )
        cooler2 = Cooler(
            name=CoolerName("Cooler 2"),
            cooling_power_percentage=CoolerPowerPercentage(50.0),
        )

        assert cooler1.id != cooler2.id

    def test_created_at_is_set_automatically(self):
        """created_at debe establecerse automáticamente."""
        before = datetime.utcnow()
        cooler = Cooler(
            name=CoolerName("Cooler Test"),
            cooling_power_percentage=CoolerPowerPercentage(50.0),
        )
        after = datetime.utcnow()

        assert before <= cooler.created_at <= after


class TestCoolerBehavior:
    """Tests de comportamiento del Cooler."""

    def test_turn_on(self):
        """Debe encender el cooler."""
        cooler = Cooler(
            name=CoolerName("Test"),
            cooling_power_percentage=CoolerPowerPercentage(50.0),
            is_on=False,
        )

        cooler.turn_on()

        assert cooler.is_on is True

    def test_turn_on_when_already_on(self):
        """turn_on cuando ya está encendido no debe causar error."""
        cooler = Cooler(
            name=CoolerName("Test"),
            cooling_power_percentage=CoolerPowerPercentage(50.0),
            is_on=True,
        )

        cooler.turn_on()

        assert cooler.is_on is True

    def test_turn_off(self):
        """Debe apagar el cooler."""
        cooler = Cooler(
            name=CoolerName("Test"),
            cooling_power_percentage=CoolerPowerPercentage(50.0),
            is_on=True,
        )

        cooler.turn_off()

        assert cooler.is_on is False

    def test_turn_off_when_already_off(self):
        """turn_off cuando ya está apagado no debe causar error."""
        cooler = Cooler(
            name=CoolerName("Test"),
            cooling_power_percentage=CoolerPowerPercentage(50.0),
            is_on=False,
        )

        cooler.turn_off()

        assert cooler.is_on is False

    def test_toggle_on_off(self):
        """Debe poder alternar entre encendido y apagado."""
        cooler = Cooler(
            name=CoolerName("Test"),
            cooling_power_percentage=CoolerPowerPercentage(50.0),
            is_on=False,
        )

        cooler.turn_on()
        assert cooler.is_on is True

        cooler.turn_off()
        assert cooler.is_on is False

        cooler.turn_on()
        assert cooler.is_on is True


class TestCoolerPowerManagement:
    """Tests de gestión de potencia del Cooler."""

    def test_change_power_percentage(self):
        """Debe poder cambiar la potencia de enfriamiento."""
        cooler = Cooler(
            name=CoolerName("Test"),
            cooling_power_percentage=CoolerPowerPercentage(50.0),
        )

        cooler.cooling_power_percentage = CoolerPowerPercentage(75.0)

        assert cooler.cooling_power_percentage.value == 75.0

    def test_change_power_to_zero(self):
        """Debe poder cambiar la potencia a 0%."""
        cooler = Cooler(
            name=CoolerName("Test"),
            cooling_power_percentage=CoolerPowerPercentage(50.0),
        )

        cooler.cooling_power_percentage = CoolerPowerPercentage(0.0)

        assert cooler.cooling_power_percentage.value == 0.0

    def test_change_power_to_max(self):
        """Debe poder cambiar la potencia a 100%."""
        cooler = Cooler(
            name=CoolerName("Test"),
            cooling_power_percentage=CoolerPowerPercentage(50.0),
        )

        cooler.cooling_power_percentage = CoolerPowerPercentage(100.0)

        assert cooler.cooling_power_percentage.value == 100.0

    def test_validate_power_is_safe_valid(self):
        """validate_power_is_safe debe retornar True para potencia válida."""
        cooler = Cooler(
            name=CoolerName("Test"),
            cooling_power_percentage=CoolerPowerPercentage(50.0),
        )

        assert cooler.validate_power_is_safe(CoolerPowerPercentage(75.0)) is True

    def test_validate_power_is_safe_invalid_type(self):
        """validate_power_is_safe debe retornar False para tipo inválido."""
        cooler = Cooler(
            name=CoolerName("Test"),
            cooling_power_percentage=CoolerPowerPercentage(50.0),
        )

        assert cooler.validate_power_is_safe(75.0) is False  # type: ignore
        assert cooler.validate_power_is_safe("75%") is False  # type: ignore
        assert cooler.validate_power_is_safe(None) is False  # type: ignore


class TestCoolerNameManagement:
    """Tests de gestión del nombre del Cooler."""

    def test_change_name(self):
        """Debe poder cambiar el nombre."""
        cooler = Cooler(
            name=CoolerName("Nombre Original"),
            cooling_power_percentage=CoolerPowerPercentage(50.0),
        )

        cooler.name = CoolerName("Nuevo Nombre")

        assert str(cooler.name) == "Nuevo Nombre"

    def test_name_persists_after_state_changes(self):
        """El nombre debe persistir después de cambios de estado."""
        cooler = Cooler(
            name=CoolerName("Cooler Persistente"),
            cooling_power_percentage=CoolerPowerPercentage(50.0),
        )

        cooler.turn_on()
        cooler.cooling_power_percentage = CoolerPowerPercentage(100.0)
        cooler.turn_off()

        assert str(cooler.name) == "Cooler Persistente"


class TestCoolerStateManagement:
    """Tests de gestión de estado usando setter directo."""

    def test_set_is_on_true(self):
        """Debe poder establecer is_on a True directamente."""
        cooler = Cooler(
            name=CoolerName("Test"),
            cooling_power_percentage=CoolerPowerPercentage(50.0),
            is_on=False,
        )

        cooler.is_on = True

        assert cooler.is_on is True

    def test_set_is_on_false(self):
        """Debe poder establecer is_on a False directamente."""
        cooler = Cooler(
            name=CoolerName("Test"),
            cooling_power_percentage=CoolerPowerPercentage(50.0),
            is_on=True,
        )

        cooler.is_on = False

        assert cooler.is_on is False


# =============================================================================
# Tests de Integración con FeedingLine
# =============================================================================


class TestCoolerFeedingLineIntegration:
    """Tests de integración de Cooler con FeedingLine."""

    @pytest.fixture
    def blower(self):
        """Fixture para crear un Blower de prueba."""
        from domain.aggregates.feeding_line.blower import Blower
        from domain.value_objects import (
            BlowDurationInSeconds,
            BlowerName,
            BlowerPowerPercentage,
        )

        return Blower(
            name=BlowerName("Blower Test"),
            non_feeding_power=BlowerPowerPercentage(50.0),
            blow_before_time=BlowDurationInSeconds(10),
            blow_after_time=BlowDurationInSeconds(5),
        )

    @pytest.fixture
    def doser(self):
        """Fixture para crear un Doser de prueba."""
        from domain.aggregates.feeding_line.doser import Doser
        from domain.enums import DoserType
        from domain.value_objects import DoserName, DosingRange, DosingRate, SiloId

        return Doser(
            name=DoserName("Doser Test"),
            assigned_silo_id=SiloId.generate(),
            dosing_range=DosingRange(min_rate=0.1, max_rate=100.0),
            doser_type=DoserType.VARI_DOSER,
            current_rate=DosingRate(50.0),
        )

    @pytest.fixture
    def selector(self):
        """Fixture para crear un Selector de prueba."""
        from domain.aggregates.feeding_line.selector import Selector
        from domain.value_objects import (
            BlowerPowerPercentage,
            SelectorCapacity,
            SelectorName,
            SelectorSpeedProfile,
        )

        return Selector(
            name=SelectorName("Selector Test"),
            capacity=SelectorCapacity(8),
            speed_profile=SelectorSpeedProfile(
                fast_speed=BlowerPowerPercentage(80.0),
                slow_speed=BlowerPowerPercentage(30.0),
            ),
        )

    def test_create_feeding_line_with_cooler(self, blower, doser, selector):
        """Debe crear una FeedingLine con Cooler."""
        from domain.aggregates.feeding_line import FeedingLine
        from domain.value_objects import LineName

        cooler = Cooler(
            name=CoolerName("Cooler Línea 1"),
            cooling_power_percentage=CoolerPowerPercentage(80.0),
        )

        line = FeedingLine.create(
            name=LineName("Línea con Cooler"),
            blower=blower,
            dosers=[doser],
            selector=selector,
            cooler=cooler,
        )

        assert line.cooler is not None
        assert str(line.cooler.name) == "Cooler Línea 1"
        assert line.cooler.cooling_power_percentage.value == 80.0

    def test_create_feeding_line_without_cooler(self, blower, doser, selector):
        """Debe crear una FeedingLine sin Cooler (opcional)."""
        from domain.aggregates.feeding_line import FeedingLine
        from domain.value_objects import LineName

        line = FeedingLine.create(
            name=LineName("Línea sin Cooler"),
            blower=blower,
            dosers=[doser],
            selector=selector,
        )

        assert line.cooler is None

    def test_update_components_with_cooler(self, blower, doser, selector):
        """Debe actualizar componentes incluyendo el Cooler."""
        from domain.aggregates.feeding_line import FeedingLine
        from domain.value_objects import LineName

        line = FeedingLine.create(
            name=LineName("Línea Test"),
            blower=blower,
            dosers=[doser],
            selector=selector,
        )

        assert line.cooler is None

        new_cooler = Cooler(
            name=CoolerName("Nuevo Cooler"),
            cooling_power_percentage=CoolerPowerPercentage(90.0),
        )

        line.update_components(
            blower=blower,
            dosers=[doser],
            selector=selector,
            cooler=new_cooler,
        )

        assert line.cooler is not None
        assert str(line.cooler.name) == "Nuevo Cooler"

    def test_update_components_remove_cooler(self, blower, doser, selector):
        """Debe poder remover el Cooler al actualizar componentes."""
        from domain.aggregates.feeding_line import FeedingLine
        from domain.value_objects import LineName

        cooler = Cooler(
            name=CoolerName("Cooler a Remover"),
            cooling_power_percentage=CoolerPowerPercentage(75.0),
        )

        line = FeedingLine.create(
            name=LineName("Línea Test"),
            blower=blower,
            dosers=[doser],
            selector=selector,
            cooler=cooler,
        )

        assert line.cooler is not None

        line.update_components(
            blower=blower,
            dosers=[doser],
            selector=selector,
            cooler=None,
        )

        assert line.cooler is None

    def test_cooler_state_independent_of_line(self, blower, doser, selector):
        """El estado del Cooler debe ser independiente de la línea."""
        from domain.aggregates.feeding_line import FeedingLine
        from domain.value_objects import LineName

        cooler = Cooler(
            name=CoolerName("Cooler Independiente"),
            cooling_power_percentage=CoolerPowerPercentage(60.0),
            is_on=False,
        )

        line = FeedingLine.create(
            name=LineName("Línea Test"),
            blower=blower,
            dosers=[doser],
            selector=selector,
            cooler=cooler,
        )

        # Modificar el cooler a través de la línea
        line.cooler.turn_on()
        line.cooler.cooling_power_percentage = CoolerPowerPercentage(85.0)

        assert line.cooler.is_on is True
        assert line.cooler.cooling_power_percentage.value == 85.0

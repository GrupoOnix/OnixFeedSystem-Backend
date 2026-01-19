"""Tests para el aggregate ScheduledAlert."""

from datetime import datetime, timedelta

import pytest

from domain.aggregates.scheduled_alert import ScheduledAlert
from domain.enums import AlertCategory, AlertType, ScheduledAlertFrequency
from domain.value_objects import ScheduledAlertId


class TestScheduledAlertCreation:
    """Tests para la creación de alertas programadas."""

    def test_create_daily_scheduled_alert(self):
        """Test crear alerta programada diaria."""
        next_date = datetime(2026, 1, 20, 8, 0, 0)
        alert = ScheduledAlert(
            title="Daily Maintenance Check",
            message="Perform daily equipment inspection",
            type=AlertType.INFO,
            category=AlertCategory.MAINTENANCE,
            frequency=ScheduledAlertFrequency.DAILY,
            next_trigger_date=next_date,
        )

        assert alert.id is not None
        assert isinstance(alert.id, ScheduledAlertId)
        assert alert.title == "Daily Maintenance Check"
        assert alert.message == "Perform daily equipment inspection"
        assert alert.type == AlertType.INFO
        assert alert.category == AlertCategory.MAINTENANCE
        assert alert.frequency == ScheduledAlertFrequency.DAILY
        assert alert.next_trigger_date == next_date
        assert alert.days_before_warning == 0
        assert alert.is_active is True
        assert alert.device_id is None
        assert alert.device_name is None
        assert alert.custom_days_interval is None
        assert alert.metadata == {}
        assert isinstance(alert.created_at, datetime)
        assert alert.last_triggered_at is None

    def test_create_weekly_scheduled_alert(self):
        """Test crear alerta programada semanal."""
        next_date = datetime(2026, 1, 27, 10, 0, 0)
        alert = ScheduledAlert(
            title="Weekly Filter Cleaning",
            message="Clean all water filters",
            type=AlertType.WARNING,
            category=AlertCategory.MAINTENANCE,
            frequency=ScheduledAlertFrequency.WEEKLY,
            next_trigger_date=next_date,
            days_before_warning=1,
        )

        assert alert.frequency == ScheduledAlertFrequency.WEEKLY
        assert alert.days_before_warning == 1

    def test_create_monthly_scheduled_alert(self):
        """Test crear alerta programada mensual."""
        next_date = datetime(2026, 2, 15, 12, 0, 0)
        alert = ScheduledAlert(
            title="Monthly Calibration",
            message="Calibrate all sensors",
            type=AlertType.CRITICAL,
            category=AlertCategory.DEVICE,
            frequency=ScheduledAlertFrequency.MONTHLY,
            next_trigger_date=next_date,
        )

        assert alert.frequency == ScheduledAlertFrequency.MONTHLY

    def test_create_custom_days_scheduled_alert(self):
        """Test crear alerta programada con días personalizados."""
        next_date = datetime(2026, 1, 20, 9, 0, 0)
        alert = ScheduledAlert(
            title="Custom Maintenance",
            message="Check equipment every 3 days",
            type=AlertType.INFO,
            category=AlertCategory.MAINTENANCE,
            frequency=ScheduledAlertFrequency.CUSTOM_DAYS,
            next_trigger_date=next_date,
            custom_days_interval=3,
        )

        assert alert.frequency == ScheduledAlertFrequency.CUSTOM_DAYS
        assert alert.custom_days_interval == 3

    def test_create_with_device_info(self):
        """Test crear alerta con información de dispositivo."""
        alert = ScheduledAlert(
            title="Device Maintenance",
            message="Check device status",
            type=AlertType.WARNING,
            category=AlertCategory.DEVICE,
            frequency=ScheduledAlertFrequency.DAILY,
            next_trigger_date=datetime.utcnow() + timedelta(days=1),
            device_id="device-001",
            device_name="Blower #1",
        )

        assert alert.device_id == "device-001"
        assert alert.device_name == "Blower #1"

    def test_create_with_metadata(self):
        """Test crear alerta con metadata."""
        metadata = {"line_id": "line-1", "component": "doser"}
        alert = ScheduledAlert(
            title="Component Check",
            message="Verify component operation",
            type=AlertType.INFO,
            category=AlertCategory.MAINTENANCE,
            frequency=ScheduledAlertFrequency.WEEKLY,
            next_trigger_date=datetime.utcnow() + timedelta(days=7),
            metadata=metadata,
        )

        assert alert.metadata == metadata
        assert alert.metadata["line_id"] == "line-1"

    def test_create_custom_days_without_interval_raises_error(self):
        """Test que crear CUSTOM_DAYS sin intervalo lanza error."""
        with pytest.raises(ValueError, match="custom_days_interval es requerido"):
            ScheduledAlert(
                title="Invalid Alert",
                message="Missing interval",
                type=AlertType.INFO,
                category=AlertCategory.MAINTENANCE,
                frequency=ScheduledAlertFrequency.CUSTOM_DAYS,
                next_trigger_date=datetime.utcnow(),
                custom_days_interval=None,
            )


class TestScheduledAlertTriggerLogic:
    """Tests para la lógica de disparo de alertas programadas."""

    def test_should_trigger_when_date_reached(self):
        """Test que debe dispararse cuando se alcanza la fecha."""
        trigger_date = datetime(2026, 1, 20, 10, 0, 0)
        alert = ScheduledAlert(
            title="Test Alert",
            message="Test",
            type=AlertType.INFO,
            category=AlertCategory.MAINTENANCE,
            frequency=ScheduledAlertFrequency.DAILY,
            next_trigger_date=trigger_date,
        )

        # Antes de la fecha: no debe dispararse
        before = datetime(2026, 1, 20, 9, 59, 0)
        assert alert.should_trigger(before) is False

        # Exactamente en la fecha: debe dispararse
        exact = datetime(2026, 1, 20, 10, 0, 0)
        assert alert.should_trigger(exact) is True

        # Después de la fecha: debe dispararse
        after = datetime(2026, 1, 20, 10, 1, 0)
        assert alert.should_trigger(after) is True

    def test_should_trigger_with_days_before_warning(self):
        """Test disparo anticipado con days_before_warning."""
        trigger_date = datetime(2026, 1, 20, 10, 0, 0)
        alert = ScheduledAlert(
            title="Early Warning",
            message="Test",
            type=AlertType.WARNING,
            category=AlertCategory.MAINTENANCE,
            frequency=ScheduledAlertFrequency.DAILY,
            next_trigger_date=trigger_date,
            days_before_warning=2,  # Disparar 2 días antes
        )

        # 3 días antes: no debe dispararse
        three_days_before = datetime(2026, 1, 17, 10, 0, 0)
        assert alert.should_trigger(three_days_before) is False

        # Exactamente 2 días antes: debe dispararse
        two_days_before = datetime(2026, 1, 18, 10, 0, 0)
        assert alert.should_trigger(two_days_before) is True

        # 1 día antes: debe dispararse
        one_day_before = datetime(2026, 1, 19, 10, 0, 0)
        assert alert.should_trigger(one_day_before) is True

        # En la fecha: debe dispararse
        exact = datetime(2026, 1, 20, 10, 0, 0)
        assert alert.should_trigger(exact) is True

    def test_should_not_trigger_if_inactive(self):
        """Test que no se dispara si está inactiva."""
        trigger_date = datetime(2026, 1, 20, 10, 0, 0)
        alert = ScheduledAlert(
            title="Inactive Alert",
            message="Test",
            type=AlertType.INFO,
            category=AlertCategory.MAINTENANCE,
            frequency=ScheduledAlertFrequency.DAILY,
            next_trigger_date=trigger_date,
        )

        alert.deactivate()

        # Aunque la fecha se alcanzó, no debe dispararse
        after_date = datetime(2026, 1, 20, 12, 0, 0)
        assert alert.should_trigger(after_date) is False

    def test_should_not_trigger_twice_for_same_date(self):
        """Test que no se dispara dos veces para la misma fecha."""
        trigger_date = datetime(2026, 1, 20, 10, 0, 0)
        alert = ScheduledAlert(
            title="Test Alert",
            message="Test",
            type=AlertType.INFO,
            category=AlertCategory.MAINTENANCE,
            frequency=ScheduledAlertFrequency.DAILY,
            next_trigger_date=trigger_date,
        )

        now = datetime(2026, 1, 20, 10, 0, 0)

        # Primera vez: debe dispararse
        assert alert.should_trigger(now) is True

        # Marcar como disparada
        alert.mark_triggered()

        # Segunda vez con la misma fecha: no debe dispararse
        assert alert.should_trigger(now) is False


class TestScheduledAlertNextDateCalculation:
    """Tests para el cálculo de próximas fechas."""

    def test_calculate_next_date_daily(self):
        """Test calcular próxima fecha para frecuencia diaria."""
        current_date = datetime(2026, 1, 20, 10, 0, 0)
        alert = ScheduledAlert(
            title="Daily Alert",
            message="Test",
            type=AlertType.INFO,
            category=AlertCategory.MAINTENANCE,
            frequency=ScheduledAlertFrequency.DAILY,
            next_trigger_date=current_date,
        )

        alert.mark_triggered()

        expected = datetime(2026, 1, 21, 10, 0, 0)
        assert alert.next_trigger_date == expected

    def test_calculate_next_date_weekly(self):
        """Test calcular próxima fecha para frecuencia semanal."""
        current_date = datetime(2026, 1, 20, 10, 0, 0)  # Martes
        alert = ScheduledAlert(
            title="Weekly Alert",
            message="Test",
            type=AlertType.INFO,
            category=AlertCategory.MAINTENANCE,
            frequency=ScheduledAlertFrequency.WEEKLY,
            next_trigger_date=current_date,
        )

        alert.mark_triggered()

        expected = datetime(2026, 1, 27, 10, 0, 0)  # Siguiente martes
        assert alert.next_trigger_date == expected

    def test_calculate_next_date_monthly_normal(self):
        """Test calcular próxima fecha para frecuencia mensual."""
        current_date = datetime(2026, 1, 15, 10, 0, 0)  # 15 de enero
        alert = ScheduledAlert(
            title="Monthly Alert",
            message="Test",
            type=AlertType.INFO,
            category=AlertCategory.MAINTENANCE,
            frequency=ScheduledAlertFrequency.MONTHLY,
            next_trigger_date=current_date,
        )

        alert.mark_triggered()

        expected = datetime(2026, 2, 15, 10, 0, 0)  # 15 de febrero
        assert alert.next_trigger_date == expected

    def test_calculate_next_date_monthly_year_rollover(self):
        """Test calcular próxima fecha mensual con cambio de año."""
        current_date = datetime(2025, 12, 20, 10, 0, 0)  # 20 de diciembre
        alert = ScheduledAlert(
            title="Monthly Alert",
            message="Test",
            type=AlertType.INFO,
            category=AlertCategory.MAINTENANCE,
            frequency=ScheduledAlertFrequency.MONTHLY,
            next_trigger_date=current_date,
        )

        alert.mark_triggered()

        expected = datetime(2026, 1, 20, 10, 0, 0)  # 20 de enero del siguiente año
        assert alert.next_trigger_date == expected

    def test_calculate_next_date_monthly_day_overflow(self):
        """Test calcular próxima fecha mensual cuando el día no existe."""
        current_date = datetime(2026, 1, 31, 10, 0, 0)  # 31 de enero
        alert = ScheduledAlert(
            title="Monthly Alert",
            message="Test",
            type=AlertType.INFO,
            category=AlertCategory.MAINTENANCE,
            frequency=ScheduledAlertFrequency.MONTHLY,
            next_trigger_date=current_date,
        )

        alert.mark_triggered()

        # Febrero no tiene día 31, debe ajustarse al 28
        expected = datetime(2026, 2, 28, 10, 0, 0)
        assert alert.next_trigger_date == expected

    def test_calculate_next_date_custom_days(self):
        """Test calcular próxima fecha con días personalizados."""
        current_date = datetime(2026, 1, 20, 10, 0, 0)
        alert = ScheduledAlert(
            title="Custom Alert",
            message="Test",
            type=AlertType.INFO,
            category=AlertCategory.MAINTENANCE,
            frequency=ScheduledAlertFrequency.CUSTOM_DAYS,
            next_trigger_date=current_date,
            custom_days_interval=5,
        )

        alert.mark_triggered()

        expected = datetime(2026, 1, 25, 10, 0, 0)  # 5 días después
        assert alert.next_trigger_date == expected

    def test_days_in_month_calculation(self):
        """Test cálculo correcto de días por mes."""
        # Método privado pero importante para la lógica
        assert ScheduledAlert._days_in_month(2026, 1) == 31  # Enero
        assert ScheduledAlert._days_in_month(2026, 2) == 28  # Febrero no bisiesto
        assert ScheduledAlert._days_in_month(2024, 2) == 29  # Febrero bisiesto
        assert ScheduledAlert._days_in_month(2026, 4) == 30  # Abril
        assert ScheduledAlert._days_in_month(2026, 12) == 31  # Diciembre


class TestScheduledAlertActivation:
    """Tests para activación/desactivación de alertas."""

    def test_toggle_active(self):
        """Test alternar estado activo."""
        alert = ScheduledAlert(
            title="Test",
            message="Test",
            type=AlertType.INFO,
            category=AlertCategory.MAINTENANCE,
            frequency=ScheduledAlertFrequency.DAILY,
            next_trigger_date=datetime.utcnow(),
        )

        assert alert.is_active is True

        # Desactivar
        new_state = alert.toggle_active()
        assert new_state is False
        assert alert.is_active is False

        # Activar de nuevo
        new_state = alert.toggle_active()
        assert new_state is True
        assert alert.is_active is True

    def test_activate_and_deactivate(self):
        """Test activar y desactivar explícitamente."""
        alert = ScheduledAlert(
            title="Test",
            message="Test",
            type=AlertType.INFO,
            category=AlertCategory.MAINTENANCE,
            frequency=ScheduledAlertFrequency.DAILY,
            next_trigger_date=datetime.utcnow(),
        )

        alert.deactivate()
        assert alert.is_active is False

        alert.activate()
        assert alert.is_active is True


class TestScheduledAlertUpdate:
    """Tests para actualización de alertas programadas."""

    def test_update_basic_fields(self):
        """Test actualizar campos básicos."""
        alert = ScheduledAlert(
            title="Original Title",
            message="Original Message",
            type=AlertType.INFO,
            category=AlertCategory.MAINTENANCE,
            frequency=ScheduledAlertFrequency.DAILY,
            next_trigger_date=datetime(2026, 1, 20, 10, 0, 0),
        )

        alert.update(
            title="Updated Title",
            message="Updated Message",
            type=AlertType.WARNING,
        )

        assert alert.title == "Updated Title"
        assert alert.message == "Updated Message"
        assert alert.type == AlertType.WARNING
        # Los demás campos no cambian
        assert alert.category == AlertCategory.MAINTENANCE
        assert alert.frequency == ScheduledAlertFrequency.DAILY

    def test_update_partial(self):
        """Test actualización parcial (solo algunos campos)."""
        alert = ScheduledAlert(
            title="Title",
            message="Message",
            type=AlertType.INFO,
            category=AlertCategory.MAINTENANCE,
            frequency=ScheduledAlertFrequency.DAILY,
            next_trigger_date=datetime(2026, 1, 20, 10, 0, 0),
        )

        alert.update(message="New Message Only")

        assert alert.title == "Title"  # No cambió
        assert alert.message == "New Message Only"  # Cambió
        assert alert.type == AlertType.INFO  # No cambió

    def test_update_frequency_and_date(self):
        """Test actualizar frecuencia y fecha."""
        alert = ScheduledAlert(
            title="Test",
            message="Test",
            type=AlertType.INFO,
            category=AlertCategory.MAINTENANCE,
            frequency=ScheduledAlertFrequency.DAILY,
            next_trigger_date=datetime(2026, 1, 20, 10, 0, 0),
        )

        new_date = datetime(2026, 2, 1, 10, 0, 0)
        alert.update(
            frequency=ScheduledAlertFrequency.WEEKLY,
            next_trigger_date=new_date,
        )

        assert alert.frequency == ScheduledAlertFrequency.WEEKLY
        assert alert.next_trigger_date == new_date

    def test_update_to_custom_days_without_interval_raises_error(self):
        """Test que cambiar a CUSTOM_DAYS sin intervalo lanza error."""
        alert = ScheduledAlert(
            title="Test",
            message="Test",
            type=AlertType.INFO,
            category=AlertCategory.MAINTENANCE,
            frequency=ScheduledAlertFrequency.DAILY,
            next_trigger_date=datetime.utcnow(),
        )

        with pytest.raises(ValueError, match="custom_days_interval es requerido"):
            alert.update(frequency=ScheduledAlertFrequency.CUSTOM_DAYS)

    def test_update_device_info(self):
        """Test actualizar información de dispositivo."""
        alert = ScheduledAlert(
            title="Test",
            message="Test",
            type=AlertType.INFO,
            category=AlertCategory.DEVICE,
            frequency=ScheduledAlertFrequency.DAILY,
            next_trigger_date=datetime.utcnow(),
        )

        alert.update(device_id="device-001", device_name="New Device")

        assert alert.device_id == "device-001"
        assert alert.device_name == "New Device"


class TestScheduledAlertReconstitution:
    """Tests para reconstitución desde base de datos."""

    def test_reconstitute_complete(self):
        """Test reconstituir alerta programada completa."""
        alert_id = ScheduledAlertId.generate()
        next_date = datetime(2026, 1, 20, 10, 0, 0)
        created = datetime(2026, 1, 10, 9, 0, 0)
        last_triggered = datetime(2026, 1, 19, 10, 0, 0)
        metadata = {"key": "value"}

        alert = ScheduledAlert.reconstitute(
            id=alert_id,
            title="Reconstituted Alert",
            message="Test message",
            type=AlertType.WARNING,
            category=AlertCategory.MAINTENANCE,
            frequency=ScheduledAlertFrequency.DAILY,
            next_trigger_date=next_date,
            days_before_warning=1,
            is_active=True,
            created_at=created,
            device_id="dev-001",
            device_name="Device 1",
            custom_days_interval=None,
            metadata=metadata,
            last_triggered_at=last_triggered,
        )

        assert alert.id == alert_id
        assert alert.title == "Reconstituted Alert"
        assert alert.message == "Test message"
        assert alert.type == AlertType.WARNING
        assert alert.category == AlertCategory.MAINTENANCE
        assert alert.frequency == ScheduledAlertFrequency.DAILY
        assert alert.next_trigger_date == next_date
        assert alert.days_before_warning == 1
        assert alert.is_active is True
        assert alert.created_at == created
        assert alert.device_id == "dev-001"
        assert alert.device_name == "Device 1"
        assert alert.custom_days_interval is None
        assert alert.metadata == metadata
        assert alert.last_triggered_at == last_triggered

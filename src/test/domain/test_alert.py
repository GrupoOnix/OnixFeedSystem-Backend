"""Tests para el aggregate Alert."""

from datetime import datetime, timedelta

import pytest

from domain.aggregates.alert import Alert
from domain.enums import AlertCategory, AlertStatus, AlertType
from domain.value_objects import AlertId


class TestAlertCreation:
    """Tests para la creación de alertas."""

    def test_create_alert_with_required_fields(self):
        """Test crear alerta con campos obligatorios."""
        alert = Alert(
            type=AlertType.WARNING,
            category=AlertCategory.DEVICE,
            title="Test Alert",
            message="This is a test alert",
        )

        assert alert.id is not None
        assert isinstance(alert.id, AlertId)
        assert alert.type == AlertType.WARNING
        assert alert.category == AlertCategory.DEVICE
        assert alert.title == "Test Alert"
        assert alert.message == "This is a test alert"
        assert alert.status == AlertStatus.UNREAD
        assert alert.source is None
        assert alert.read_at is None
        assert alert.resolved_at is None
        assert alert.resolved_by is None
        assert alert.metadata == {}
        assert isinstance(alert.timestamp, datetime)

    def test_create_alert_with_all_fields(self):
        """Test crear alerta con todos los campos."""
        metadata = {"device_id": "123", "line_name": "Line 1"}
        alert = Alert(
            type=AlertType.CRITICAL,
            category=AlertCategory.SYSTEM,
            title="Critical Error",
            message="System failure detected",
            source="System Monitor",
            metadata=metadata,
        )

        assert alert.type == AlertType.CRITICAL
        assert alert.category == AlertCategory.SYSTEM
        assert alert.source == "System Monitor"
        assert alert.metadata == metadata
        assert alert.metadata["device_id"] == "123"

    def test_create_alert_metadata_is_copied(self):
        """Test que metadata se copia y no se comparte referencia."""
        original_metadata = {"key": "value"}
        alert = Alert(
            type=AlertType.INFO,
            category=AlertCategory.FEEDING,
            title="Info",
            message="Test",
            metadata=original_metadata,
        )

        # Modificar metadata original no debe afectar la alerta
        original_metadata["key"] = "modified"
        assert alert.metadata["key"] == "value"

        # Modificar metadata de la alerta no debe afectar el original
        alert_metadata = alert.metadata
        alert_metadata["new_key"] = "new_value"
        assert "new_key" not in alert.metadata


class TestAlertStatusTransitions:
    """Tests para transiciones de estado de alertas."""

    def test_mark_as_read(self):
        """Test marcar alerta como leída."""
        alert = Alert(
            type=AlertType.WARNING,
            category=AlertCategory.DEVICE,
            title="Test",
            message="Test",
        )

        assert alert.status == AlertStatus.UNREAD
        assert alert.read_at is None

        alert.mark_as_read()

        assert alert.status == AlertStatus.READ
        assert alert.read_at is not None
        assert isinstance(alert.read_at, datetime)

    def test_mark_as_read_idempotent(self):
        """Test que marcar como leída es idempotente."""
        alert = Alert(
            type=AlertType.INFO,
            category=AlertCategory.SYSTEM,
            title="Test",
            message="Test",
        )

        alert.mark_as_read()
        first_read_at = alert.read_at

        # Esperar un poco y marcar de nuevo
        alert.mark_as_read()

        # La fecha de lectura debe permanecer igual
        assert alert.read_at == first_read_at

    def test_resolve_alert(self):
        """Test resolver alerta."""
        alert = Alert(
            type=AlertType.WARNING,
            category=AlertCategory.MAINTENANCE,
            title="Test",
            message="Test",
        )

        assert alert.status == AlertStatus.UNREAD
        assert alert.resolved_at is None
        assert alert.resolved_by is None

        alert.resolve(resolved_by="admin@example.com")

        assert alert.status == AlertStatus.RESOLVED
        assert alert.resolved_at is not None
        assert isinstance(alert.resolved_at, datetime)
        assert alert.resolved_by == "admin@example.com"

    def test_resolve_without_user(self):
        """Test resolver alerta sin especificar usuario."""
        alert = Alert(
            type=AlertType.CRITICAL,
            category=AlertCategory.CONNECTION,
            title="Test",
            message="Test",
        )

        alert.resolve()

        assert alert.status == AlertStatus.RESOLVED
        assert alert.resolved_at is not None
        assert alert.resolved_by is None

    def test_archive_alert(self):
        """Test archivar alerta."""
        alert = Alert(
            type=AlertType.SUCCESS,
            category=AlertCategory.FEEDING,
            title="Test",
            message="Test",
        )

        alert.archive()

        assert alert.status == AlertStatus.ARCHIVED

    def test_update_status_directly(self):
        """Test actualizar estado directamente."""
        alert = Alert(
            type=AlertType.INFO,
            category=AlertCategory.INVENTORY,
            title="Test",
            message="Test",
        )

        alert.update_status(AlertStatus.READ)
        assert alert.status == AlertStatus.READ

        alert.update_status(AlertStatus.RESOLVED)
        assert alert.status == AlertStatus.RESOLVED
        
    def test_cannot_modify_archived_alert(self):
        """Test que no se puede modificar una alerta archivada."""
        alert = Alert(
            type=AlertType.INFO,
            category=AlertCategory.INVENTORY,
            title="Test",
            message="Test",
        )

        alert.update_status(AlertStatus.ARCHIVED)
        assert alert.status == AlertStatus.ARCHIVED

        # Intentar cambiar estado de alerta archivada debe fallar
        with pytest.raises(ValueError, match="No se puede cambiar el estado de una alerta archivada"):
            alert.update_status(AlertStatus.RESOLVED)


class TestAlertReconstitution:
    """Tests para reconstitución de alertas desde la base de datos."""

    def test_reconstitute_alert_minimal(self):
        """Test reconstituir alerta con campos mínimos."""
        alert_id = AlertId.generate()
        timestamp = datetime.utcnow()

        alert = Alert.reconstitute(
            id=alert_id,
            type=AlertType.WARNING,
            status=AlertStatus.UNREAD,
            category=AlertCategory.DEVICE,
            title="Reconstituted Alert",
            message="Test message",
            timestamp=timestamp,
        )

        assert alert.id == alert_id
        assert alert.type == AlertType.WARNING
        assert alert.status == AlertStatus.UNREAD
        assert alert.category == AlertCategory.DEVICE
        assert alert.title == "Reconstituted Alert"
        assert alert.message == "Test message"
        assert alert.timestamp == timestamp
        assert alert.source is None
        assert alert.read_at is None
        assert alert.resolved_at is None
        assert alert.resolved_by is None
        assert alert.metadata == {}

    def test_reconstitute_alert_complete(self):
        """Test reconstituir alerta con todos los campos."""
        alert_id = AlertId.generate()
        timestamp = datetime.utcnow()
        read_at = timestamp + timedelta(minutes=5)
        resolved_at = timestamp + timedelta(minutes=10)
        metadata = {"device_id": "abc", "line_id": "xyz"}

        alert = Alert.reconstitute(
            id=alert_id,
            type=AlertType.CRITICAL,
            status=AlertStatus.RESOLVED,
            category=AlertCategory.SYSTEM,
            title="Critical Issue",
            message="System error occurred",
            timestamp=timestamp,
            source="System Monitor",
            read_at=read_at,
            resolved_at=resolved_at,
            resolved_by="operator@example.com",
            metadata=metadata,
        )

        assert alert.id == alert_id
        assert alert.type == AlertType.CRITICAL
        assert alert.status == AlertStatus.RESOLVED
        assert alert.category == AlertCategory.SYSTEM
        assert alert.title == "Critical Issue"
        assert alert.message == "System error occurred"
        assert alert.timestamp == timestamp
        assert alert.source == "System Monitor"
        assert alert.read_at == read_at
        assert alert.resolved_at == resolved_at
        assert alert.resolved_by == "operator@example.com"
        assert alert.metadata == metadata

    def test_reconstitute_preserves_immutability(self):
        """Test que la reconstitución respeta la inmutabilidad de campos."""
        alert_id = AlertId.generate()
        timestamp = datetime.utcnow()

        alert = Alert.reconstitute(
            id=alert_id,
            type=AlertType.INFO,
            status=AlertStatus.READ,
            category=AlertCategory.FEEDING,
            title="Test",
            message="Test",
            timestamp=timestamp,
        )

        # ID y timestamp no deben cambiar
        assert alert.id == alert_id
        assert alert.timestamp == timestamp


class TestAlertBusinessLogic:
    """Tests para lógica de negocio de alertas."""

    def test_alert_lifecycle_flow(self):
        """Test flujo completo del ciclo de vida de una alerta."""
        # 1. Crear alerta (UNREAD)
        alert = Alert(
            type=AlertType.WARNING,
            category=AlertCategory.DEVICE,
            title="Sensor Out of Range",
            message="Temperature sensor reading is abnormal",
            source="Sensor-01",
            metadata={"sensor_id": "temp-001", "reading": 85.5},
        )

        assert alert.status == AlertStatus.UNREAD
        assert alert.read_at is None
        assert alert.resolved_at is None

        # 2. Operador lee la alerta (READ)
        alert.mark_as_read()

        assert alert.status == AlertStatus.READ
        assert alert.read_at is not None
        assert alert.resolved_at is None

        # 3. Operador resuelve el problema (RESOLVED)
        alert.resolve(resolved_by="john.doe@example.com")

        assert alert.status == AlertStatus.RESOLVED
        assert alert.read_at is not None
        assert alert.resolved_at is not None
        assert alert.resolved_by == "john.doe@example.com"

        # 4. Después de un tiempo, se archiva (ARCHIVED)
        alert.archive()

        assert alert.status == AlertStatus.ARCHIVED

    def test_alert_types_and_categories(self):
        """Test todas las combinaciones válidas de tipos y categorías."""
        types = [AlertType.CRITICAL, AlertType.WARNING, AlertType.INFO, AlertType.SUCCESS]
        categories = [
            AlertCategory.SYSTEM,
            AlertCategory.DEVICE,
            AlertCategory.FEEDING,
            AlertCategory.INVENTORY,
            AlertCategory.MAINTENANCE,
            AlertCategory.CONNECTION,
        ]

        for alert_type in types:
            for category in categories:
                alert = Alert(
                    type=alert_type,
                    category=category,
                    title=f"{alert_type.value} - {category.value}",
                    message="Test message",
                )

                assert alert.type == alert_type
                assert alert.category == category
                assert alert.status == AlertStatus.UNREAD

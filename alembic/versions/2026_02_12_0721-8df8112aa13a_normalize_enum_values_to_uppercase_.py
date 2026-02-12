"""normalize enum values to uppercase english

Revision ID: 8df8112aa13a
Revises: b2c3d4e5f6a7
Create Date: 2026-02-12 07:21:32.166459

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '8df8112aa13a'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # CageStatus: cages.status
    op.execute("UPDATE cages SET status = 'AVAILABLE' WHERE status = 'Disponible'")
    op.execute("UPDATE cages SET status = 'IN_USE' WHERE status = 'En Uso'")
    op.execute("UPDATE cages SET status = 'MAINTENANCE' WHERE status = 'Mantenimiento'")

    # SensorType: sensors.sensor_type
    op.execute("UPDATE sensors SET sensor_type = 'TEMPERATURE' WHERE sensor_type = 'Temperatura'")
    op.execute("UPDATE sensors SET sensor_type = 'PRESSURE' WHERE sensor_type = 'Presión'")
    op.execute("UPDATE sensors SET sensor_type = 'FLOW' WHERE sensor_type = 'Caudal'")

    # SessionStatus: feeding_sessions.status
    op.execute("UPDATE feeding_sessions SET status = 'ACTIVE' WHERE status = 'Active'")
    op.execute("UPDATE feeding_sessions SET status = 'CLOSED' WHERE status = 'Closed'")

    # OperationStatus: feeding_operations.status
    op.execute("UPDATE feeding_operations SET status = 'RUNNING' WHERE status = 'Running'")
    op.execute("UPDATE feeding_operations SET status = 'PAUSED' WHERE status = 'Paused'")
    op.execute("UPDATE feeding_operations SET status = 'COMPLETED' WHERE status = 'Completed'")
    op.execute("UPDATE feeding_operations SET status = 'STOPPED' WHERE status = 'Stopped'")
    op.execute("UPDATE feeding_operations SET status = 'FAILED' WHERE status = 'Failed'")

    # FeedingEventType: feeding_events.event_type
    op.execute("UPDATE feeding_events SET event_type = 'COMMAND' WHERE event_type = 'Command'")
    op.execute("UPDATE feeding_events SET event_type = 'PARAM_CHANGE' WHERE event_type = 'ParamChange'")
    op.execute("UPDATE feeding_events SET event_type = 'SYSTEM_STATUS' WHERE event_type = 'SystemStatus'")
    op.execute("UPDATE feeding_events SET event_type = 'ALARM' WHERE event_type = 'Alarm'")

    # OperationEventType: operation_events.type
    op.execute("UPDATE operation_events SET type = 'STARTED' WHERE type = 'Started'")
    op.execute("UPDATE operation_events SET type = 'PAUSED' WHERE type = 'Paused'")
    op.execute("UPDATE operation_events SET type = 'RESUMED' WHERE type = 'Resumed'")
    op.execute("UPDATE operation_events SET type = 'PARAM_CHANGE' WHERE type = 'ParamChange'")
    op.execute("UPDATE operation_events SET type = 'COMPLETED' WHERE type = 'Completed'")
    op.execute("UPDATE operation_events SET type = 'STOPPED' WHERE type = 'Stopped'")
    op.execute("UPDATE operation_events SET type = 'FAILED' WHERE type = 'Failed'")


def downgrade() -> None:
    # CageStatus
    op.execute("UPDATE cages SET status = 'Disponible' WHERE status = 'AVAILABLE'")
    op.execute("UPDATE cages SET status = 'En Uso' WHERE status = 'IN_USE'")
    op.execute("UPDATE cages SET status = 'Mantenimiento' WHERE status = 'MAINTENANCE'")

    # SensorType
    op.execute("UPDATE sensors SET sensor_type = 'Temperatura' WHERE sensor_type = 'TEMPERATURE'")
    op.execute("UPDATE sensors SET sensor_type = 'Presión' WHERE sensor_type = 'PRESSURE'")
    op.execute("UPDATE sensors SET sensor_type = 'Caudal' WHERE sensor_type = 'FLOW'")

    # SessionStatus
    op.execute("UPDATE feeding_sessions SET status = 'Active' WHERE status = 'ACTIVE'")
    op.execute("UPDATE feeding_sessions SET status = 'Closed' WHERE status = 'CLOSED'")

    # OperationStatus
    op.execute("UPDATE feeding_operations SET status = 'Running' WHERE status = 'RUNNING'")
    op.execute("UPDATE feeding_operations SET status = 'Paused' WHERE status = 'PAUSED'")
    op.execute("UPDATE feeding_operations SET status = 'Completed' WHERE status = 'COMPLETED'")
    op.execute("UPDATE feeding_operations SET status = 'Stopped' WHERE status = 'STOPPED'")
    op.execute("UPDATE feeding_operations SET status = 'Failed' WHERE status = 'FAILED'")

    # FeedingEventType
    op.execute("UPDATE feeding_events SET event_type = 'Command' WHERE event_type = 'COMMAND'")
    op.execute("UPDATE feeding_events SET event_type = 'ParamChange' WHERE event_type = 'PARAM_CHANGE'")
    op.execute("UPDATE feeding_events SET event_type = 'SystemStatus' WHERE event_type = 'SYSTEM_STATUS'")
    op.execute("UPDATE feeding_events SET event_type = 'Alarm' WHERE event_type = 'ALARM'")

    # OperationEventType
    op.execute("UPDATE operation_events SET type = 'Started' WHERE type = 'STARTED'")
    op.execute("UPDATE operation_events SET type = 'Paused' WHERE type = 'PAUSED'")
    op.execute("UPDATE operation_events SET type = 'Resumed' WHERE type = 'RESUMED'")
    op.execute("UPDATE operation_events SET type = 'ParamChange' WHERE type = 'PARAM_CHANGE'")
    op.execute("UPDATE operation_events SET type = 'Completed' WHERE type = 'COMPLETED'")
    op.execute("UPDATE operation_events SET type = 'Stopped' WHERE type = 'STOPPED'")
    op.execute("UPDATE operation_events SET type = 'Failed' WHERE type = 'FAILED'")

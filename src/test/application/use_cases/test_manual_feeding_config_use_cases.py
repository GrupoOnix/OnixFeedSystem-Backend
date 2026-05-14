from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from application.dtos.manual_feeding_config_dtos import (
    LastValidCyclicCageConfigPayload,
    LastValidCyclicFeedingConfigPayload,
    LastValidManualFeedingConfigPayload,
)
from application.use_cases.feeding.manual_feeding_config_use_cases import (
    GetLastValidManualFeedingConfigUseCase,
    ListLastValidManualFeedingConfigsUseCase,
    UpsertLastValidCyclicFeedingConfigUseCase,
    UpsertLastValidManualFeedingConfigUseCase,
)
from infrastructure.persistence.models.last_valid_manual_feeding_config_model import (
    LastValidManualFeedingConfigModel,
)


class FakeConfigRepository:
    def __init__(self):
        self.configs = {}

    async def list(self):
        return list(self.configs.values())

    async def find_by_line_id(self, line_id):
        return self.configs.get(line_id)

    async def upsert_by_line_id(self, **kwargs):
        line_id = kwargs["line_id"]
        existing = self.configs.get(line_id)
        if existing:
            same_payload = all(getattr(existing, key) == value for key, value in kwargs.items() if key != "line_id")
            if same_payload:
                return existing

            for key, value in kwargs.items():
                setattr(existing, key, value)
            existing.updated_at = datetime.now(timezone.utc)
            return existing

        config = LastValidManualFeedingConfigModel(**kwargs)
        self.configs[line_id] = config
        return config


class FakeCyclicConfigRepository:
    def __init__(self):
        self.configs = {}

    async def find_by_line_id(self, line_id):
        return self.configs.get(line_id)

    async def upsert_by_line_id(self, **kwargs):
        now = datetime.now(timezone.utc)
        config = SimpleNamespace(
            id=uuid4(),
            updated_at=now,
            created_at=now,
            **kwargs,
        )
        self.configs[kwargs["line_id"]] = config
        return config


class FakeLineRepository:
    def __init__(self, lines):
        self.lines = lines

    async def find_by_id(self, line_id):
        return self.lines.get(line_id.value)


class FakeCageRepository:
    def __init__(self, cage_ids):
        self.cage_ids = set(cage_ids)

    async def find_by_id(self, cage_id):
        return SimpleNamespace(id=cage_id) if cage_id.value in self.cage_ids else None


class FakeSiloRepository:
    def __init__(self, silo_ids):
        self.silo_ids = set(silo_ids)

    async def find_by_id(self, silo_id):
        return SimpleNamespace(id=silo_id) if silo_id.value in self.silo_ids else None


class FakeSlotAssignmentRepository:
    def __init__(self, assignments):
        self.assignments = assignments

    async def find_by_cage(self, cage_id):
        line_id = self.assignments.get(cage_id.value)
        if not line_id:
            return None
        return SimpleNamespace(line_id=SimpleNamespace(value=line_id))


class FakeCageGroupRepository:
    def __init__(self, groups):
        self.groups = groups

    async def find_by_id(self, group_id):
        cage_ids = self.groups.get(group_id.value)
        if cage_ids is None:
            return None
        return SimpleNamespace(
            id=group_id,
            cage_ids=[SimpleNamespace(value=cage_id) for cage_id in cage_ids],
        )


def make_line(*silo_ids):
    return SimpleNamespace(
        dosers=[SimpleNamespace(assigned_silo_id=SimpleNamespace(value=silo_id)) for silo_id in silo_ids]
    )


def make_cyclic_line(doser_id, silo_id):
    selected_doser = SimpleNamespace(
        id=SimpleNamespace(value=doser_id),
        assigned_silo_id=SimpleNamespace(value=silo_id),
        max_rate_kg_per_min=30,
    )

    return SimpleNamespace(
        dosers=[selected_doser],
        get_doser_by_id=lambda value: selected_doser if value.value == doser_id else None,
    )


def make_payload(silo_id, cage_id):
    return LastValidManualFeedingConfigPayload(
        target_silo_id=str(silo_id),
        target_cage_id=str(cage_id),
        target_amount_kg=20,
        dosing_rate_kg_per_min=6.5,
        dosing_unit="KG_PER_MINUTE",
        blower_power_percentage=70,
    )


def make_use_cases(
    line_id,
    silo_id,
    cage_id,
    config_repo=None,
    assignments=None,
    existing_silo_ids=None,
):
    config_repo = config_repo or FakeConfigRepository()
    line_repo = FakeLineRepository({line_id: make_line(silo_id)})
    cage_repo = FakeCageRepository({cage_id})
    silo_repo = FakeSiloRepository(existing_silo_ids or {silo_id})
    slot_repo = FakeSlotAssignmentRepository({cage_id: line_id} if assignments is None else assignments)
    return (
        UpsertLastValidManualFeedingConfigUseCase(config_repo, line_repo, cage_repo, silo_repo, slot_repo),
        GetLastValidManualFeedingConfigUseCase(config_repo, line_repo, cage_repo, silo_repo, slot_repo),
        ListLastValidManualFeedingConfigsUseCase(config_repo, line_repo, cage_repo, silo_repo, slot_repo),
        config_repo,
    )


@pytest.mark.asyncio
async def test_creates_config_when_line_has_no_existing_record():
    line_id = uuid4()
    silo_id = uuid4()
    cage_id = uuid4()
    upsert_use_case, _, _, config_repo = make_use_cases(line_id, silo_id, cage_id)

    response = await upsert_use_case.execute(str(line_id), make_payload(silo_id, cage_id))

    assert response.line_id == str(line_id)
    assert response.target_silo_id == str(silo_id)
    assert response.is_valid_against_current_layout is True
    assert len(config_repo.configs) == 1


@pytest.mark.asyncio
async def test_updates_existing_config_for_same_line():
    line_id = uuid4()
    silo_id = uuid4()
    cage_id = uuid4()
    upsert_use_case, _, _, config_repo = make_use_cases(line_id, silo_id, cage_id)
    await upsert_use_case.execute(str(line_id), make_payload(silo_id, cage_id))

    payload = make_payload(silo_id, cage_id)
    payload.target_amount_kg = 35
    response = await upsert_use_case.execute(str(line_id), payload)

    assert response.target_amount_kg == 35
    assert len(config_repo.configs) == 1


@pytest.mark.asyncio
async def test_rejects_silo_that_does_not_belong_to_line():
    line_id = uuid4()
    silo_id = uuid4()
    other_silo_id = uuid4()
    cage_id = uuid4()
    upsert_use_case, _, _, _ = make_use_cases(
        line_id,
        silo_id,
        cage_id,
        existing_silo_ids={silo_id, other_silo_id},
    )

    with pytest.raises(ValueError, match="no pertenece a la línea"):
        await upsert_use_case.execute(str(line_id), make_payload(other_silo_id, cage_id))


@pytest.mark.asyncio
async def test_rejects_cage_that_does_not_belong_to_line():
    line_id = uuid4()
    other_line_id = uuid4()
    silo_id = uuid4()
    cage_id = uuid4()
    upsert_use_case, _, _, _ = make_use_cases(
        line_id,
        silo_id,
        cage_id,
        assignments={cage_id: other_line_id},
    )

    with pytest.raises(ValueError, match="no pertenece a la línea"):
        await upsert_use_case.execute(str(line_id), make_payload(silo_id, cage_id))


@pytest.mark.parametrize(
    "field,value",
    [
        ("target_amount_kg", 0),
        ("dosing_rate_kg_per_min", 0),
        ("blower_power_percentage", 29),
        ("blower_power_percentage", 101),
    ],
)
def test_rejects_amount_rate_or_blower_out_of_range(field, value):
    data = {
        "target_silo_id": str(uuid4()),
        "target_cage_id": str(uuid4()),
        "target_amount_kg": 20,
        "dosing_rate_kg_per_min": 6.5,
        "dosing_unit": "KG_PER_MINUTE",
        "blower_power_percentage": 70,
    }
    data[field] = value

    with pytest.raises(ValidationError):
        LastValidManualFeedingConfigPayload(**data)


def test_rejects_unsupported_dosing_unit():
    with pytest.raises(ValidationError):
        LastValidManualFeedingConfigPayload(
            target_silo_id=str(uuid4()),
            target_cage_id=str(uuid4()),
            target_amount_kg=20,
            dosing_rate_kg_per_min=6.5,
            dosing_unit="GRAMS_PER_SECOND",
            blower_power_percentage=70,
        )


@pytest.mark.asyncio
async def test_cyclic_config_ignores_stale_group_cages_when_saving():
    line_id = uuid4()
    group_id = uuid4()
    doser_id = uuid4()
    silo_id = uuid4()
    cage_id = uuid4()
    second_cage_id = uuid4()
    stale_cage_id = uuid4()
    config_repo = FakeCyclicConfigRepository()

    use_case = UpsertLastValidCyclicFeedingConfigUseCase(
        config_repo,
        FakeLineRepository({line_id: make_cyclic_line(doser_id, silo_id)}),
        FakeCageRepository({cage_id, second_cage_id}),
        FakeCageGroupRepository({group_id: {cage_id, second_cage_id, stale_cage_id}}),
        FakeSiloRepository({silo_id}),
        FakeSlotAssignmentRepository({
            cage_id: line_id,
            second_cage_id: line_id,
        }),
    )

    response = await use_case.execute(
        str(line_id),
        LastValidCyclicFeedingConfigPayload(
            group_id=str(group_id),
            doser_id=str(doser_id),
            visits=10,
            blower_power_percentage=70,
            cage_configs=[
                LastValidCyclicCageConfigPayload(
                    cage_id=str(cage_id),
                    quantity_kg=10,
                    rate_kg_per_min=10,
                    mode="NORMAL",
                ),
                LastValidCyclicCageConfigPayload(
                    cage_id=str(second_cage_id),
                    quantity_kg=10,
                    rate_kg_per_min=10,
                    mode="NORMAL",
                ),
            ],
        ),
    )

    assert response.line_id == str(line_id)
    assert response.is_valid_against_current_layout is True
    assert {config.cage_id for config in response.cage_configs} == {
        str(cage_id),
        str(second_cage_id),
    }


@pytest.mark.asyncio
async def test_list_returns_configs_indexed_by_line_id():
    line_id = uuid4()
    silo_id = uuid4()
    cage_id = uuid4()
    upsert_use_case, _, list_use_case, _ = make_use_cases(line_id, silo_id, cage_id)
    await upsert_use_case.execute(str(line_id), make_payload(silo_id, cage_id))

    response = await list_use_case.execute()

    assert set(response.keys()) == {str(line_id)}
    assert response[str(line_id)].target_cage_id == str(cage_id)


@pytest.mark.asyncio
async def test_repeated_put_with_same_payload_does_not_create_duplicates_or_touch_timestamp():
    line_id = uuid4()
    silo_id = uuid4()
    cage_id = uuid4()
    upsert_use_case, _, _, config_repo = make_use_cases(line_id, silo_id, cage_id)
    payload = make_payload(silo_id, cage_id)

    first = await upsert_use_case.execute(str(line_id), payload)
    second = await upsert_use_case.execute(str(line_id), payload)

    assert first.id == second.id
    assert first.updated_at == second.updated_at
    assert len(config_repo.configs) == 1


@pytest.mark.asyncio
async def test_invalid_saved_config_after_topology_change_is_reported_as_invalid():
    line_id = uuid4()
    silo_id = uuid4()
    cage_id = uuid4()
    config_repo = FakeConfigRepository()
    upsert_use_case, _, _, _ = make_use_cases(line_id, silo_id, cage_id, config_repo)
    await upsert_use_case.execute(str(line_id), make_payload(silo_id, cage_id))
    _, get_use_case, _, _ = make_use_cases(
        line_id,
        silo_id,
        cage_id,
        config_repo,
        assignments={},
    )

    response = await get_use_case.execute(str(line_id))

    assert response.is_valid_against_current_layout is False

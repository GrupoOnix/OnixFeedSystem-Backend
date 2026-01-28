"""
Tests de integración para GetSystemLayoutUseCase.

Estos tests verifican que el caso de uso cumple su contrato:
- Obtener el layout completo del sistema desde BD
- Devolver todos los agregados con IDs reales
- Manejar correctamente el caso de BD vacía
"""

import pytest
from application.use_cases.get_system_layout import GetSystemLayoutUseCase
from application.use_cases.sync_system_layout import SyncSystemLayoutUseCase
from api.models.system_layout import (
    SystemLayoutModel,
    SiloConfigModel,
    CageConfigModel,
    FeedingLineConfigModel,
    BlowerConfigModel,
    DoserConfigModel,
    SelectorConfigModel,
    SlotAssignmentModel,
)
from domain.factories import ComponentFactory
from infrastructure.persistence.mock_repositories import (
    MockFeedingLineRepository,
    MockSiloRepository,
    MockCageRepository,
)


@pytest.fixture
def repositories():
    """Fixture que proporciona repositorios mock limpios."""
    return {
        'line_repo': MockFeedingLineRepository(),
        'silo_repo': MockSiloRepository(),
        'cage_repo': MockCageRepository(),
    }


@pytest.fixture
def get_use_case(repositories):
    """Fixture que proporciona una instancia del caso de uso GetSystemLayout."""
    return GetSystemLayoutUseCase(
        repositories['line_repo'],
        repositories['silo_repo'],
        repositories['cage_repo']
    )


@pytest.fixture
def sync_use_case(repositories):
    """Fixture que proporciona una instancia del caso de uso SyncSystemLayout."""
    return SyncSystemLayoutUseCase(
        repositories['line_repo'],
        repositories['silo_repo'],
        repositories['cage_repo'],
        ComponentFactory()
    )


class TestGetSystemLayout_EmptyDatabase:
    """Tests para BD vacía."""

    @pytest.mark.asyncio
    async def test_get_empty_layout(self, get_use_case):
        """Debe devolver un layout vacío cuando la BD está vacía."""
        silos, cages, lines = await get_use_case.execute()

        assert len(silos) == 0
        assert len(cages) == 0
        assert len(lines) == 0


class TestGetSystemLayout_WithData:
    """Tests para BD con datos."""

    @pytest.mark.asyncio
    async def test_get_layout_with_silos_only(self, get_use_case, sync_use_case):
        """Debe devolver solo silos cuando solo hay silos en BD."""
        create_request = SystemLayoutModel(
            silos=[
                SiloConfigModel(id="temp-1", name="Silo A", capacity=1000.0),
                SiloConfigModel(id="temp-2", name="Silo B", capacity=2000.0)
            ],
            cages=[],
            feeding_lines=[]
        )
        await sync_use_case.execute(create_request)

        silos, cages, lines = await get_use_case.execute()

        assert len(silos) == 2
        assert len(cages) == 0
        assert len(lines) == 0

        for silo in silos:
            assert str(silo.id) != "temp-1" and str(silo.id) != "temp-2"
            assert len(str(silo.id)) > 10

    @pytest.mark.asyncio
    async def test_get_layout_with_cages_only(self, get_use_case, sync_use_case):
        """Debe devolver solo jaulas cuando solo hay jaulas en BD."""
        create_request = SystemLayoutModel(
            silos=[],
            cages=[
                CageConfigModel(id="temp-1", name="Jaula 1"),
                CageConfigModel(id="temp-2", name="Jaula 2")
            ],
            feeding_lines=[]
        )
        await sync_use_case.execute(create_request)

        silos, cages, lines = await get_use_case.execute()

        assert len(silos) == 0
        assert len(cages) == 2
        assert len(lines) == 0

        cage_names = {str(cage.name) for cage in cages}
        assert cage_names == {"Jaula 1", "Jaula 2"}

    @pytest.mark.asyncio
    async def test_get_complete_layout(self, get_use_case, sync_use_case):
        """Debe devolver el layout completo con todos los tipos de agregados."""
        create_request = SystemLayoutModel(
            silos=[
                SiloConfigModel(id="temp-silo-1", name="Silo A", capacity=1000.0)
            ],
            cages=[
                CageConfigModel(id="temp-cage-1", name="Jaula 1")
            ],
            feeding_lines=[
                FeedingLineConfigModel(
                    id="temp-line-1",
                    line_name="Línea 1",
                    blower_config=BlowerConfigModel(
                        id="temp-blower-1",
                        name="Soplador 1",
                        blower_type="standard",
                        non_feeding_power=50.0,
                        blow_before_time=5,
                        blow_after_time=3
                    ),
                    sensors_config=[],
                    dosers_config=[
                        DoserConfigModel(
                            id="temp-doser-1",
                            name="Dosificador 1",
                            assigned_silo_id="temp-silo-1",
                            doser_type="volumetric",
                            min_rate=10.0,
                            max_rate=100.0,
                            current_rate=50.0
                        )
                    ],
                    selector_config=SelectorConfigModel(
                        id="temp-selector-1",
                        name="Selectora 1",
                        selector_type="standard",
                        capacity=4,
                        fast_speed=80.0,
                        slow_speed=20.0
                    ),
                    slot_assignments=[
                        SlotAssignmentModel(slot_number=1, cage_id="temp-cage-1")
                    ]
                )
            ]
        )
        await sync_use_case.execute(create_request)

        silos, cages, lines = await get_use_case.execute()

        assert len(silos) == 1
        assert len(cages) == 1
        assert len(lines) == 1

        line = lines[0]
        assert str(line.name) == "Línea 1"
        assert len(line.dosers) == 1
        assert len(line.get_slot_assignments()) == 1

        doser = line.dosers[0]
        silo_id = silos[0].id
        assert doser.assigned_silo_id == silo_id

        slot = line.get_slot_assignments()[0]
        cage_id = cages[0].id
        assert slot.cage_id == cage_id


class TestGetSystemLayout_Consistency:
    """Tests para verificar consistencia entre Sync y Get."""

    @pytest.mark.asyncio
    async def test_sync_then_get_consistency(self, get_use_case, sync_use_case):
        """El resultado de Get debe ser idéntico al resultado de Sync."""
        request = SystemLayoutModel(
            silos=[
                SiloConfigModel(id="temp-1", name="Silo A", capacity=1000.0),
                SiloConfigModel(id="temp-2", name="Silo B", capacity=2000.0)
            ],
            cages=[
                CageConfigModel(id="temp-1", name="Jaula 1"),
                CageConfigModel(id="temp-2", name="Jaula 2")
            ],
            feeding_lines=[]
        )

        sync_silos, sync_cages, sync_lines = await sync_use_case.execute(request)
        get_silos, get_cages, get_lines = await get_use_case.execute()

        assert len(sync_silos) == len(get_silos)
        assert len(sync_cages) == len(get_cages)
        assert len(sync_lines) == len(get_lines)

        sync_silo_ids = {silo.id for silo in sync_silos}
        get_silo_ids = {silo.id for silo in get_silos}
        assert sync_silo_ids == get_silo_ids

        sync_cage_ids = {cage.id for cage in sync_cages}
        get_cage_ids = {cage.id for cage in get_cages}
        assert sync_cage_ids == get_cage_ids

    @pytest.mark.asyncio
    async def test_multiple_sync_then_get(self, get_use_case, sync_use_case):
        """Get debe reflejar el último estado después de múltiples Sync."""
        request1 = SystemLayoutModel(
            silos=[SiloConfigModel(id="temp-1", name="Silo Original", capacity=1000.0)],
            cages=[],
            feeding_lines=[]
        )
        result_silos, _, _ = await sync_use_case.execute(request1)
        silo_id = str(result_silos[0].id)

        request2 = SystemLayoutModel(
            silos=[SiloConfigModel(id=silo_id, name="Silo Actualizado", capacity=2000.0)],
            cages=[],
            feeding_lines=[]
        )
        await sync_use_case.execute(request2)

        get_silos, _, _ = await get_use_case.execute()

        assert len(get_silos) == 1
        assert str(get_silos[0].name) == "Silo Actualizado"
        assert get_silos[0].capacity.as_kg == 2000.0
        assert str(get_silos[0].id) == silo_id

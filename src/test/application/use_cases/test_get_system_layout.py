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
from application.dtos import (
    SystemLayoutDTO,
    SiloConfigDTO,
    CageConfigDTO,
    FeedingLineConfigDTO,
    BlowerConfigDTO,
    DoserConfigDTO,
    SelectorConfigDTO,
    SlotAssignmentDTO,
)
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
        repositories['cage_repo']
    )


class TestGetSystemLayout_EmptyDatabase:
    """Tests para BD vacía."""

    @pytest.mark.asyncio
    async def test_get_empty_layout(self, get_use_case):
        """Debe devolver un layout vacío cuando la BD está vacía."""
        result = await get_use_case.execute()
        
        assert len(result.silos) == 0
        assert len(result.cages) == 0
        assert len(result.feeding_lines) == 0
        assert hasattr(result, 'silos')
        assert hasattr(result, 'cages')
        assert hasattr(result, 'feeding_lines')


class TestGetSystemLayout_WithData:
    """Tests para BD con datos."""

    @pytest.mark.asyncio
    async def test_get_layout_with_silos_only(self, get_use_case, sync_use_case):
        """Debe devolver solo silos cuando solo hay silos en BD."""
        # Crear datos usando SyncSystemLayout
        create_request = SystemLayoutDTO(
            silos=[
                SiloConfigDTO(id="temp-1", name="Silo A", capacity=1000.0),
                SiloConfigDTO(id="temp-2", name="Silo B", capacity=2000.0)
            ],
            cages=[],
            feeding_lines=[]
        )
        await sync_use_case.execute(create_request)
        
        # Obtener layout
        result = await get_use_case.execute()
        
        assert len(result.silos) == 2
        assert len(result.cages) == 0
        assert len(result.feeding_lines) == 0
        
        # Verificar que los silos tienen IDs reales
        for silo in result.silos:
            assert silo.id != "temp-1" and silo.id != "temp-2"
            assert len(silo.id) > 10  # UUID es largo

    @pytest.mark.asyncio
    async def test_get_layout_with_cages_only(self, get_use_case, sync_use_case):
        """Debe devolver solo jaulas cuando solo hay jaulas en BD."""
        # Crear datos
        create_request = SystemLayoutDTO(
            silos=[],
            cages=[
                CageConfigDTO(id="temp-1", name="Jaula 1"),
                CageConfigDTO(id="temp-2", name="Jaula 2")
            ],
            feeding_lines=[]
        )
        await sync_use_case.execute(create_request)
        
        # Obtener layout
        result = await get_use_case.execute()
        
        assert len(result.silos) == 0
        assert len(result.cages) == 2
        assert len(result.feeding_lines) == 0
        
        # Verificar nombres
        cage_names = {cage.name for cage in result.cages}
        assert cage_names == {"Jaula 1", "Jaula 2"}

    @pytest.mark.asyncio
    async def test_get_complete_layout(self, get_use_case, sync_use_case):
        """Debe devolver el layout completo con todos los tipos de agregados."""
        # Crear layout completo
        create_request = SystemLayoutDTO(
            silos=[
                SiloConfigDTO(id="temp-silo-1", name="Silo A", capacity=1000.0)
            ],
            cages=[
                CageConfigDTO(id="temp-cage-1", name="Jaula 1")
            ],
            feeding_lines=[
                FeedingLineConfigDTO(
                    id="temp-line-1",
                    line_name="Línea 1",
                    blower_config=BlowerConfigDTO(
                        id="temp-blower-1",
                        name="Soplador 1",
                        non_feeding_power=50.0,
                        blow_before_time=5,
                        blow_after_time=3
                    ),
                    sensors_config=[],
                    dosers_config=[
                        DoserConfigDTO(
                            id="temp-doser-1",
                            name="Dosificador 1",
                            assigned_silo_id="temp-silo-1",
                            doser_type="volumetric",
                            min_rate=10.0,
                            max_rate=100.0,
                            current_rate=50.0
                        )
                    ],
                    selector_config=SelectorConfigDTO(
                        id="temp-selector-1",
                        name="Selectora 1",
                        capacity=4,
                        fast_speed=80.0,
                        slow_speed=20.0
                    ),
                    slot_assignments=[
                        SlotAssignmentDTO(slot_number=1, cage_id="temp-cage-1")
                    ]
                )
            ]
        )
        await sync_use_case.execute(create_request)
        
        # Obtener layout
        result = await get_use_case.execute()
        
        assert len(result.silos) == 1
        assert len(result.cages) == 1
        assert len(result.feeding_lines) == 1
        
        # Verificar estructura de la línea
        line = result.feeding_lines[0]
        assert line.line_name == "Línea 1"
        assert len(line.dosers_config) == 1
        assert len(line.slot_assignments) == 1
        
        # Verificar que los IDs están mapeados correctamente
        doser = line.dosers_config[0]
        silo_id = result.silos[0].id
        assert doser.assigned_silo_id == silo_id
        
        slot = line.slot_assignments[0]
        cage_id = result.cages[0].id
        assert slot.cage_id == cage_id


class TestGetSystemLayout_Consistency:
    """Tests para verificar consistencia entre Sync y Get."""

    @pytest.mark.asyncio
    async def test_sync_then_get_consistency(self, get_use_case, sync_use_case):
        """El resultado de Get debe ser idéntico al resultado de Sync."""
        request = SystemLayoutDTO(
            silos=[
                SiloConfigDTO(id="temp-1", name="Silo A", capacity=1000.0),
                SiloConfigDTO(id="temp-2", name="Silo B", capacity=2000.0)
            ],
            cages=[
                CageConfigDTO(id="temp-1", name="Jaula 1"),
                CageConfigDTO(id="temp-2", name="Jaula 2")
            ],
            feeding_lines=[]
        )
        
        # Sincronizar
        sync_result = await sync_use_case.execute(request)
        
        # Obtener
        get_result = await get_use_case.execute()
        
        # Deben ser idénticos
        assert len(sync_result.silos) == len(get_result.silos)
        assert len(sync_result.cages) == len(get_result.cages)
        assert len(sync_result.feeding_lines) == len(get_result.feeding_lines)
        
        # Verificar IDs específicos
        sync_silo_ids = {silo.id for silo in sync_result.silos}
        get_silo_ids = {silo.id for silo in get_result.silos}
        assert sync_silo_ids == get_silo_ids
        
        sync_cage_ids = {cage.id for cage in sync_result.cages}
        get_cage_ids = {cage.id for cage in get_result.cages}
        assert sync_cage_ids == get_cage_ids

    @pytest.mark.asyncio
    async def test_multiple_sync_then_get(self, get_use_case, sync_use_case):
        """Get debe reflejar el último estado después de múltiples Sync."""
        # Primera sincronización
        request1 = SystemLayoutDTO(
            silos=[SiloConfigDTO(id="temp-1", name="Silo Original", capacity=1000.0)],
            cages=[],
            feeding_lines=[]
        )
        result1 = await sync_use_case.execute(request1)
        silo_id = result1.silos[0].id
        
        # Segunda sincronización (actualizar)
        request2 = SystemLayoutDTO(
            silos=[SiloConfigDTO(id=silo_id, name="Silo Actualizado", capacity=2000.0)],
            cages=[],
            feeding_lines=[]
        )
        await sync_use_case.execute(request2)
        
        # Get debe reflejar el último estado
        get_result = await get_use_case.execute()
        
        assert len(get_result.silos) == 1
        assert get_result.silos[0].name == "Silo Actualizado"
        assert get_result.silos[0].capacity == 2000.0
        assert get_result.silos[0].id == silo_id

"""
Tests de integración para SyncSystemLayoutUseCase.

Estos tests verifican que el caso de uso cumple su contrato:
- Sincronizar el layout del sistema (crear, actualizar, eliminar)
- Mapear IDs temporales a IDs reales
- Validar reglas de negocio (FA1-FA7)
- Devolver el layout completo con IDs reales
"""

import pytest
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
def use_case(repositories):
    """Fixture que proporciona una instancia del caso de uso."""
    return SyncSystemLayoutUseCase(
        repositories['line_repo'],
        repositories['silo_repo'],
        repositories['cage_repo'],
        ComponentFactory()
    )


class TestSyncSystemLayout_Create:
    """Tests para la creación de agregados."""

    @pytest.mark.asyncio
    async def test_create_empty_layout(self, use_case):
        """Debe crear un layout vacío sin errores."""
        request = SystemLayoutModel(
            silos=[],
            cages=[],
            feeding_lines=[]
        )

        result = await use_case.execute(request)

        assert len(result.silos) == 0
        assert len(result.cages) == 0
        assert len(result.feeding_lines) == 0

    @pytest.mark.asyncio
    async def test_create_single_silo(self, use_case):
        """Debe crear un silo y devolver su ID real."""
        request = SystemLayoutModel(
            silos=[
                SiloConfigModel(
                    id="temp-silo-1",
                    name="Silo A",
                    capacity=1000.0
                )
            ],
            cages=[],
            feeding_lines=[]
        )

        result = await use_case.execute(request)

        assert len(result.silos) == 1
        assert result.silos[0].name == "Silo A"
        assert result.silos[0].capacity == 1000.0
        assert result.silos[0].id != "temp-silo-1"  # ID debe ser UUID real

    @pytest.mark.asyncio
    async def test_create_single_cage(self, use_case):
        """Debe crear una jaula y devolver su ID real."""
        request = SystemLayoutModel(
            silos=[],
            cages=[
                CageConfigModel(
                    id="temp-cage-1",
                    name="Jaula 1"
                )
            ],
            feeding_lines=[]
        )

        result = await use_case.execute(request)

        assert len(result.cages) == 1
        assert result.cages[0].name == "Jaula 1"
        assert result.cages[0].id != "temp-cage-1"

    @pytest.mark.asyncio
    async def test_create_complete_feeding_line(self, use_case):
        """Debe crear una línea completa con todos sus componentes."""
        request = SystemLayoutModel(
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

        result = await use_case.execute(request)

        assert len(result.feeding_lines) == 1
        line = result.feeding_lines[0]
        assert line.line_name == "Línea 1"
        assert line.id != "temp-line-1"
        assert len(line.dosers_config) == 1
        assert len(line.slot_assignments) == 1


class TestSyncSystemLayout_Update:
    """Tests para la actualización de agregados."""

    @pytest.mark.asyncio
    async def test_update_silo_name(self, use_case):
        """Debe actualizar el nombre de un silo existente."""
        # Crear silo inicial
        create_request = SystemLayoutModel(
            silos=[SiloConfigModel(id="temp-1", name="Silo Original", capacity=1000.0)],
            cages=[],
            feeding_lines=[]
        )
        create_result = await use_case.execute(create_request)
        silo_id = create_result.silos[0].id

        # Actualizar nombre
        update_request = SystemLayoutModel(
            silos=[SiloConfigModel(id=silo_id, name="Silo Actualizado", capacity=1000.0)],
            cages=[],
            feeding_lines=[]
        )
        update_result = await use_case.execute(update_request)

        assert len(update_result.silos) == 1
        assert update_result.silos[0].name == "Silo Actualizado"
        assert update_result.silos[0].id == silo_id

    @pytest.mark.asyncio
    async def test_update_silo_capacity(self, use_case):
        """Debe actualizar la capacidad de un silo existente."""
        # Crear silo inicial
        create_request = SystemLayoutModel(
            silos=[SiloConfigModel(id="temp-1", name="Silo A", capacity=1000.0)],
            cages=[],
            feeding_lines=[]
        )
        create_result = await use_case.execute(create_request)
        silo_id = create_result.silos[0].id

        # Actualizar capacidad
        update_request = SystemLayoutModel(
            silos=[SiloConfigModel(id=silo_id, name="Silo A", capacity=2000.0)],
            cages=[],
            feeding_lines=[]
        )
        update_result = await use_case.execute(update_request)

        assert update_result.silos[0].capacity == 2000.0


class TestSyncSystemLayout_Delete:
    """Tests para la eliminación de agregados."""

    @pytest.mark.asyncio
    async def test_delete_silo(self, use_case):
        """Debe eliminar un silo que no está en el request."""
        # Crear silo
        create_request = SystemLayoutModel(
            silos=[SiloConfigModel(id="temp-1", name="Silo A", capacity=1000.0)],
            cages=[],
            feeding_lines=[]
        )
        await use_case.execute(create_request)

        # Enviar request vacío (elimina todo)
        delete_request = SystemLayoutModel(silos=[], cages=[], feeding_lines=[])
        result = await use_case.execute(delete_request)

        assert len(result.silos) == 0

    @pytest.mark.asyncio
    async def test_delete_cage(self, use_case):
        """Debe eliminar una jaula que no está en el request."""
        # Crear jaula
        create_request = SystemLayoutModel(
            silos=[],
            cages=[CageConfigModel(id="temp-1", name="Jaula 1")],
            feeding_lines=[]
        )
        await use_case.execute(create_request)

        # Enviar request vacío
        delete_request = SystemLayoutModel(silos=[], cages=[], feeding_lines=[])
        result = await use_case.execute(delete_request)

        assert len(result.cages) == 0


class TestSyncSystemLayout_BusinessRules:
    """Tests para validación de reglas de negocio."""

    @pytest.mark.asyncio
    async def test_fa2_duplicate_silo_name_on_create(self, use_case):
        """FA2: No debe permitir crear silos con nombres duplicados."""
        # Crear primer silo
        request1 = SystemLayoutModel(
            silos=[SiloConfigModel(id="temp-1", name="Silo A", capacity=1000.0)],
            cages=[],
            feeding_lines=[]
        )
        await use_case.execute(request1)

        # Intentar crear otro silo con el mismo nombre
        request2 = SystemLayoutModel(
            silos=[
                SiloConfigModel(id="temp-1", name="Silo A", capacity=1000.0),
                SiloConfigModel(id="temp-2", name="Silo A", capacity=2000.0)
            ],
            cages=[],
            feeding_lines=[]
        )

        with pytest.raises(Exception) as exc_info:
            await use_case.execute(request2)

        assert "Ya existe un silo con el nombre" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_fa2_duplicate_cage_name_on_create(self, use_case):
        """FA2: No debe permitir crear jaulas con nombres duplicados."""
        # Crear primera jaula
        request1 = SystemLayoutModel(
            silos=[],
            cages=[CageConfigModel(id="temp-1", name="Jaula 1")],
            feeding_lines=[]
        )
        await use_case.execute(request1)

        # Intentar crear otra jaula con el mismo nombre
        request2 = SystemLayoutModel(
            silos=[],
            cages=[
                CageConfigModel(id="temp-1", name="Jaula 1"),
                CageConfigModel(id="temp-2", name="Jaula 1")
            ],
            feeding_lines=[]
        )

        with pytest.raises(Exception) as exc_info:
            await use_case.execute(request2)

        assert "Ya existe una jaula con el nombre" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_fa2_duplicate_line_name_on_create(self, use_case):
        """FA2: No debe permitir crear líneas con nombres duplicados."""
        # Crear infraestructura necesaria
        base_request = SystemLayoutModel(
            silos=[SiloConfigModel(id="temp-silo-1", name="Silo A", capacity=1000.0)],
            cages=[CageConfigModel(id="temp-cage-1", name="Jaula 1")],
            feeding_lines=[
                FeedingLineConfigModel(
                    id="temp-line-1",
                    line_name="Línea 1",
                    blower_config=BlowerConfigModel(
                        id="temp-blower-1",
                        name="Soplador 1",
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
        result1 = await use_case.execute(base_request)

        # Intentar crear otra línea con el mismo nombre
        duplicate_request = SystemLayoutModel(
            silos=[
                SiloConfigModel(id=result1.silos[0].id, name="Silo A", capacity=1000.0),
                SiloConfigModel(id="temp-silo-2", name="Silo B", capacity=1000.0)
            ],
            cages=[
                CageConfigModel(id=result1.cages[0].id, name="Jaula 1"),
                CageConfigModel(id="temp-cage-2", name="Jaula 2")
            ],
            feeding_lines=[
                FeedingLineConfigModel(
                    id=result1.feeding_lines[0].id,
                    line_name="Línea 1",
                    blower_config=BlowerConfigModel(
                        id="temp-blower-1",
                        name="Soplador 1",
                        non_feeding_power=50.0,
                        blow_before_time=5,
                        blow_after_time=3
                    ),
                    sensors_config=[],
                    dosers_config=[
                        DoserConfigModel(
                            id="temp-doser-1",
                            name="Dosificador 1",
                            assigned_silo_id=result1.silos[0].id,
                            doser_type="volumetric",
                            min_rate=10.0,
                            max_rate=100.0,
                            current_rate=50.0
                        )
                    ],
                    selector_config=SelectorConfigModel(
                        id="temp-selector-1",
                        name="Selectora 1",
                        capacity=4,
                        fast_speed=80.0,
                        slow_speed=20.0
                    ),
                    slot_assignments=[
                        SlotAssignmentModel(slot_number=1, cage_id=result1.cages[0].id)
                    ]
                ),
                FeedingLineConfigModel(
                    id="temp-line-2",
                    line_name="Línea 1",  # Nombre duplicado
                    blower_config=BlowerConfigModel(
                        id="temp-blower-2",
                        name="Soplador 2",
                        non_feeding_power=50.0,
                        blow_before_time=5,
                        blow_after_time=3
                    ),
                    sensors_config=[],
                    dosers_config=[
                        DoserConfigModel(
                            id="temp-doser-2",
                            name="Dosificador 2",
                            assigned_silo_id="temp-silo-2",
                            doser_type="volumetric",
                            min_rate=10.0,
                            max_rate=100.0,
                            current_rate=50.0
                        )
                    ],
                    selector_config=SelectorConfigModel(
                        id="temp-selector-2",
                        name="Selectora 2",
                        capacity=4,
                        fast_speed=80.0,
                        slow_speed=20.0
                    ),
                    slot_assignments=[
                        SlotAssignmentModel(slot_number=1, cage_id="temp-cage-2")
                    ]
                )
            ]
        )

        with pytest.raises(Exception) as exc_info:
            await use_case.execute(duplicate_request)

        assert "Ya existe una línea con el nombre" in str(exc_info.value)


class TestSyncSystemLayout_IDMapping:
    """Tests para el mapeo de IDs temporales a reales."""

    @pytest.mark.asyncio
    async def test_id_mapping_silo_to_doser(self, use_case):
        """Debe mapear correctamente el ID temporal del silo al doser."""
        request = SystemLayoutModel(
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
                        non_feeding_power=50.0,
                        blow_before_time=5,
                        blow_after_time=3
                    ),
                    sensors_config=[],
                    dosers_config=[
                        DoserConfigModel(
                            id="temp-doser-1",
                            name="Dosificador 1",
                            assigned_silo_id="temp-silo-1",  # ID temporal
                            doser_type="volumetric",
                            min_rate=10.0,
                            max_rate=100.0,
                            current_rate=50.0
                        )
                    ],
                    selector_config=SelectorConfigModel(
                        id="temp-selector-1",
                        name="Selectora 1",
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

        result = await use_case.execute(request)

        # El doser debe tener el ID real del silo, no el temporal
        doser = result.feeding_lines[0].dosers_config[0]
        silo_id = result.silos[0].id
        assert doser.assigned_silo_id == silo_id
        assert doser.assigned_silo_id != "temp-silo-1"

    @pytest.mark.asyncio
    async def test_id_mapping_cage_to_slot(self, use_case):
        """Debe mapear correctamente el ID temporal de la jaula al slot."""
        request = SystemLayoutModel(
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
                        capacity=4,
                        fast_speed=80.0,
                        slow_speed=20.0
                    ),
                    slot_assignments=[
                        SlotAssignmentModel(slot_number=1, cage_id="temp-cage-1")  # ID temporal
                    ]
                )
            ]
        )

        result = await use_case.execute(request)

        # El slot debe tener el ID real de la jaula, no el temporal
        slot = result.feeding_lines[0].slot_assignments[0]
        cage_id = result.cages[0].id
        assert slot.cage_id == cage_id
        assert slot.cage_id != "temp-cage-1"


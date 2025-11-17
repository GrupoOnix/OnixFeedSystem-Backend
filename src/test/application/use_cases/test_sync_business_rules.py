"""
Tests de Reglas de Negocio FA3-FA7 para SyncSystemLayoutUseCase.

Estos tests verifican las validaciones de negocio avanzadas:
- FA3: Jaula ya asignada a otra línea
- FA4: Slot duplicado en la misma línea
- FA5: Silo ya asignado a otro dosificador (1-a-1)
- FA6: Referencias rotas (IDs inexistentes)
- FA7: Sensores duplicados por tipo
- Validaciones de rangos (min_rate < max_rate, etc.)
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
    SensorConfigModel,
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
def use_case(repositories):
    """Fixture que proporciona una instancia del caso de uso."""
    from domain.factories import ComponentFactory
    return SyncSystemLayoutUseCase(
        repositories['line_repo'],
        repositories['silo_repo'],
        repositories['cage_repo'],
        ComponentFactory()
    )



class TestFA3_CageAlreadyAssigned:
    """FA3: Jaula ya asignada a otra línea."""

    @pytest.mark.asyncio
    async def test_fa3_cage_assigned_to_multiple_lines(self, use_case):
        """No debe permitir asignar la misma jaula a dos líneas diferentes."""
        # Crear infraestructura base
        base_request = SystemLayoutModel(
            silos=[
                SiloConfigModel(id="temp-silo-1", name="Silo A", capacity=1000.0),
                SiloConfigModel(id="temp-silo-2", name="Silo B", capacity=1000.0)
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
        result = await use_case.execute(base_request)
        cage_id = result.cages[0].id
        
        # Intentar crear segunda línea con la misma jaula
        duplicate_request = SystemLayoutModel(
            silos=[
                SiloConfigModel(id=result.silos[0].id, name="Silo A", capacity=1000.0),
                SiloConfigModel(id=result.silos[1].id, name="Silo B", capacity=1000.0)
            ],
            cages=[
                CageConfigModel(id=cage_id, name="Jaula 1")
            ],
            feeding_lines=[
                # Línea 1 existente
                FeedingLineConfigModel(
                    id=result.feeding_lines[0].id,
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
                            assigned_silo_id=result.silos[0].id,
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
                        SlotAssignmentModel(slot_number=1, cage_id=cage_id)
                    ]
                ),
                # Línea 2 nueva intentando usar la misma jaula
                FeedingLineConfigModel(
                    id="temp-line-2",
                    line_name="Línea 2",
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
                            assigned_silo_id=result.silos[1].id,
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
                        SlotAssignmentModel(slot_number=1, cage_id=cage_id)  # Misma jaula!
                    ]
                )
            ]
        )
        
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(duplicate_request)
        
        # Verifica que la excepción menciona que la jaula no está disponible
        error_msg = str(exc_info.value).lower()
        assert "jaula" in error_msg
        assert ("asignada" in error_msg or "disponible" in error_msg or "en uso" in error_msg)



class TestFA4_DuplicateSlot:
    """FA4: Slot duplicado en la misma línea."""

    @pytest.mark.asyncio
    async def test_fa4_duplicate_slot_in_same_line(self, use_case):
        """No debe permitir asignar el mismo slot dos veces en una línea."""
        request = SystemLayoutModel(
            silos=[
                SiloConfigModel(id="temp-silo-1", name="Silo A", capacity=1000.0)
            ],
            cages=[
                CageConfigModel(id="temp-cage-1", name="Jaula 1"),
                CageConfigModel(id="temp-cage-2", name="Jaula 2")
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
                        SlotAssignmentModel(slot_number=1, cage_id="temp-cage-1"),
                        SlotAssignmentModel(slot_number=1, cage_id="temp-cage-2")  # Slot duplicado!
                    ]
                )
            ]
        )
        
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(request)
        
        error_msg = str(exc_info.value).lower()
        assert "slot" in error_msg
        assert ("duplicado" in error_msg or "asignado" in error_msg)

    @pytest.mark.asyncio
    async def test_fa4_slot_exceeds_selector_capacity(self, use_case):
        """No debe permitir asignar un slot mayor a la capacidad de la selectora."""
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
                        capacity=4,  # Capacidad máxima: 4
                        fast_speed=80.0,
                        slow_speed=20.0
                    ),
                    slot_assignments=[
                        SlotAssignmentModel(slot_number=5, cage_id="temp-cage-1")  # Slot 5 > capacidad 4
                    ]
                )
            ]
        )
        
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(request)
        
        assert "slot" in str(exc_info.value).lower() or "capacidad" in str(exc_info.value).lower()



class TestFA5_SiloAlreadyAssigned:
    """FA5: Silo ya asignado a otro dosificador (regla 1-a-1)."""

    @pytest.mark.asyncio
    async def test_fa5_silo_assigned_to_multiple_dosers(self, use_case):
        """No debe permitir asignar el mismo silo a dos dosificadores."""
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
                            assigned_silo_id="temp-silo-1",  # Silo A
                            doser_type="volumetric",
                            min_rate=10.0,
                            max_rate=100.0,
                            current_rate=50.0
                        ),
                        DoserConfigModel(
                            id="temp-doser-2",
                            name="Dosificador 2",
                            assigned_silo_id="temp-silo-1",  # Mismo Silo A!
                            doser_type="gravimetric",
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
        
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(request)
        
        assert "silo" in str(exc_info.value).lower()
        assert "asignado" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_fa5_silo_assigned_across_lines(self, use_case):
        """No debe permitir asignar el mismo silo a dosificadores de diferentes líneas."""
        # Crear primera línea con silo asignado
        first_request = SystemLayoutModel(
            silos=[
                SiloConfigModel(id="temp-silo-1", name="Silo A", capacity=1000.0),
                SiloConfigModel(id="temp-silo-2", name="Silo B", capacity=1000.0)
            ],
            cages=[
                CageConfigModel(id="temp-cage-1", name="Jaula 1"),
                CageConfigModel(id="temp-cage-2", name="Jaula 2")
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
        result = await use_case.execute(first_request)
        
        # Intentar crear segunda línea usando el mismo silo
        second_request = SystemLayoutModel(
            silos=[
                SiloConfigModel(id=result.silos[0].id, name="Silo A", capacity=1000.0),
                SiloConfigModel(id=result.silos[1].id, name="Silo B", capacity=1000.0)
            ],
            cages=[
                CageConfigModel(id=result.cages[0].id, name="Jaula 1"),
                CageConfigModel(id=result.cages[1].id, name="Jaula 2")
            ],
            feeding_lines=[
                # Línea 1 existente
                FeedingLineConfigModel(
                    id=result.feeding_lines[0].id,
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
                            assigned_silo_id=result.silos[0].id,
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
                        SlotAssignmentModel(slot_number=1, cage_id=result.cages[0].id)
                    ]
                ),
                # Línea 2 nueva intentando usar el mismo silo
                FeedingLineConfigModel(
                    id="temp-line-2",
                    line_name="Línea 2",
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
                            assigned_silo_id=result.silos[0].id,  # Mismo silo!
                            doser_type="gravimetric",
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
                        SlotAssignmentModel(slot_number=1, cage_id=result.cages[1].id)
                    ]
                )
            ]
        )
        
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(second_request)
        
        assert "silo" in str(exc_info.value).lower()
        assert "asignado" in str(exc_info.value).lower()



class TestFA6_BrokenReferences:
    """FA6: Referencias rotas (IDs inexistentes)."""

    @pytest.mark.asyncio
    async def test_fa6_doser_references_nonexistent_silo(self, use_case):
        """No debe permitir que un dosificador referencie un silo inexistente."""
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
                            assigned_silo_id="temp-silo-999",  # Silo inexistente!
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
        
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(request)
        
        error_msg = str(exc_info.value).lower()
        assert "silo" in error_msg
        assert ("no existe" in error_msg or 
                "no encontrado" in error_msg or
                "inexistente" in error_msg or
                "no fue creado" in error_msg)

    @pytest.mark.asyncio
    async def test_fa6_slot_references_nonexistent_cage(self, use_case):
        """No debe permitir que un slot referencie una jaula inexistente."""
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
                        SlotAssignmentModel(slot_number=1, cage_id="temp-cage-999")  # Jaula inexistente!
                    ]
                )
            ]
        )
        
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(request)
        
        error_msg = str(exc_info.value).lower()
        assert "jaula" in error_msg or "cage" in error_msg
        assert ("no existe" in error_msg or 
                "no encontrado" in error_msg or
                "inexistente" in error_msg or
                "no fue creada" in error_msg)



class TestFA7_DuplicateSensorTypes:
    """FA7: Sensores duplicados por tipo."""

    @pytest.mark.asyncio
    async def test_fa7_duplicate_sensor_type_in_line(self, use_case):
        """No debe permitir dos sensores del mismo tipo en una línea."""
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
                    sensors_config=[
                        SensorConfigModel(
                            id="temp-sensor-1",
                            name="Sensor Temperatura 1",
                            sensor_type="temperature"
                        ),
                        SensorConfigModel(
                            id="temp-sensor-2",
                            name="Sensor Temperatura 2",
                            sensor_type="temperature"  # Tipo duplicado!
                        )
                    ],
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
        
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(request)
        
        assert "sensor" in str(exc_info.value).lower()
        assert ("duplicado" in str(exc_info.value).lower() or 
                "tipo" in str(exc_info.value).lower())

    @pytest.mark.asyncio
    async def test_fa7_different_sensor_types_allowed(self, use_case):
        """Debe permitir múltiples sensores de diferentes tipos."""
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
                    sensors_config=[
                        SensorConfigModel(
                            id="temp-sensor-1",
                            name="Sensor Temperatura",
                            sensor_type="TEMPERATURE"  # Mayúsculas (enum)
                        ),
                        SensorConfigModel(
                            id="temp-sensor-2",
                            name="Sensor Presión",
                            sensor_type="PRESSURE"  # Mayúsculas (enum)
                        ),
                        SensorConfigModel(
                            id="temp-sensor-3",
                            name="Sensor Flujo",
                            sensor_type="FLOW"  # Mayúsculas (enum)
                        )
                    ],
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
        
        # No debe lanzar excepción
        result = await use_case.execute(request)
        
        assert len(result.feeding_lines[0].sensors_config) == 3



class TestRangeValidations:
    """Validaciones de rangos numéricos."""

    @pytest.mark.asyncio
    async def test_doser_min_rate_greater_than_max_rate(self, use_case):
        """No debe permitir min_rate > max_rate en dosificador."""
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
                            min_rate=100.0,  # min > max!
                            max_rate=50.0,
                            current_rate=75.0
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
        
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(request)
        
        error_msg = str(exc_info.value).lower()
        assert ("rate" in error_msg or "rango" in error_msg or "tasa" in error_msg)

    @pytest.mark.asyncio
    async def test_doser_current_rate_outside_range(self, use_case):
        """No debe permitir current_rate fuera del rango [min_rate, max_rate]."""
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
                            current_rate=150.0  # Fuera de rango!
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
        
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(request)
        
        assert "current_rate" in str(exc_info.value).lower() or "rango" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_selector_slow_speed_greater_than_fast_speed(self, use_case):
        """No debe permitir slow_speed > fast_speed en selectora."""
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
                        fast_speed=20.0,  # fast < slow!
                        slow_speed=80.0
                    ),
                    slot_assignments=[
                        SlotAssignmentModel(slot_number=1, cage_id="temp-cage-1")
                    ]
                )
            ]
        )
        
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(request)
        
        assert "speed" in str(exc_info.value).lower() or "velocidad" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_negative_capacity_values(self, use_case):
        """No debe permitir valores negativos en capacidades."""
        request = SystemLayoutModel(
            silos=[
                SiloConfigModel(id="temp-silo-1", name="Silo A", capacity=-1000.0)  # Negativo!
            ],
            cages=[],
            feeding_lines=[]
        )
        
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(request)
        
        error_msg = str(exc_info.value).lower()
        assert ("capacidad" in error_msg or "capacity" in error_msg or "peso" in error_msg or "negativo" in error_msg)

    @pytest.mark.asyncio
    async def test_zero_selector_capacity(self, use_case):
        """No debe permitir capacidad cero en selectora."""
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
                        capacity=0,  # Cero!
                        fast_speed=80.0,
                        slow_speed=20.0
                    ),
                    slot_assignments=[
                        SlotAssignmentModel(slot_number=1, cage_id="temp-cage-1")
                    ]
                )
            ]
        )
        
        with pytest.raises(Exception) as exc_info:
            await use_case.execute(request)
        
        assert "capacidad" in str(exc_info.value).lower() or "capacity" in str(exc_info.value).lower()


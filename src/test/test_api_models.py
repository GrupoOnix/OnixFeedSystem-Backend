"""
Tests para los modelos Pydantic de la API.

Verifica que la validación de Pydantic funciona correctamente.
"""

import pytest
import sys
from pathlib import Path
from pydantic import ValidationError

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.models.system_layout import (
    SaveSystemLayoutRequest,
    SaveSystemLayoutResponse,
    SiloConfigModel,
    CageConfigModel,
    FeedingLineConfigModel,
    BlowerConfigModel,
    DoserConfigModel,
    SelectorConfigModel,
    SlotAssignmentModel,
)
from api.mappers import SystemLayoutMapper


def test_silo_config_model_valid():
    """Test: Validación exitosa de SiloConfigModel."""
    silo = SiloConfigModel(
        id="temp_silo_1",
        name="Silo A",
        capacity=1000.0
    )
    
    assert silo.id == "temp_silo_1"
    assert silo.name == "Silo A"
    assert silo.capacity == 1000.0


def test_silo_config_model_invalid_capacity():
    """Test: Validación falla con capacidad negativa."""
    with pytest.raises(ValidationError) as exc_info:
        SiloConfigModel(
            id="temp_silo_1",
            name="Silo A",
            capacity=-100.0  # ❌ Debe ser > 0
        )
    
    errors = exc_info.value.errors()
    assert any(error['loc'] == ('capacity',) for error in errors)


def test_cage_config_model_valid():
    """Test: Validación exitosa de CageConfigModel."""
    cage = CageConfigModel(
        id="temp_cage_1",
        name="Jaula 1"
    )
    
    assert cage.id == "temp_cage_1"
    assert cage.name == "Jaula 1"


def test_blower_config_model_valid():
    """Test: Validación exitosa de BlowerConfigModel."""
    blower = BlowerConfigModel(
        id="temp_blower_1",
        name="Soplador 1",
        non_feeding_power=50.0,
        blow_before_time=5,
        blow_after_time=3
    )
    
    assert blower.non_feeding_power == 50.0
    assert blower.blow_before_time == 5


def test_blower_config_model_invalid_power():
    """Test: Validación falla con potencia fuera de rango."""
    with pytest.raises(ValidationError) as exc_info:
        BlowerConfigModel(
            id="temp_blower_1",
            name="Soplador 1",
            non_feeding_power=150.0,  # ❌ Debe ser <= 100
            blow_before_time=5,
            blow_after_time=3
        )
    
    errors = exc_info.value.errors()
    assert any(error['loc'] == ('non_feeding_power',) for error in errors)


def test_doser_config_model_valid():
    """Test: Validación exitosa de DoserConfigModel."""
    doser = DoserConfigModel(
        id="temp_doser_1",
        name="Dosificador 1",
        assigned_silo_id="temp_silo_1",
        doser_type="volumetric",
        min_rate=10.0,
        max_rate=100.0,
        current_rate=50.0
    )
    
    assert doser.assigned_silo_id == "temp_silo_1"
    assert doser.doser_type == "volumetric"


def test_selector_config_model_valid():
    """Test: Validación exitosa de SelectorConfigModel."""
    selector = SelectorConfigModel(
        id="temp_selector_1",
        name="Selector 1",
        capacity=4,
        fast_speed=80.0,
        slow_speed=20.0
    )
    
    assert selector.capacity == 4
    assert selector.fast_speed == 80.0


def test_slot_assignment_model_valid():
    """Test: Validación exitosa de SlotAssignmentModel."""
    assignment = SlotAssignmentModel(
        slot_number=1,
        cage_id="temp_cage_1"
    )
    
    assert assignment.slot_number == 1
    assert assignment.cage_id == "temp_cage_1"


def test_slot_assignment_model_invalid_slot():
    """Test: Validación falla con slot_number <= 0."""
    with pytest.raises(ValidationError) as exc_info:
        SlotAssignmentModel(
            slot_number=0,  # ❌ Debe ser > 0
            cage_id="temp_cage_1"
        )
    
    errors = exc_info.value.errors()
    assert any(error['loc'] == ('slot_number',) for error in errors)


def test_feeding_line_config_model_valid():
    """Test: Validación exitosa de FeedingLineConfigModel completo."""
    line = FeedingLineConfigModel(
        id="temp_line_1",
        line_name="Linea Principal",
        blower_config=BlowerConfigModel(
            id="temp_blower_1",
            name="Soplador 1",
            non_feeding_power=50.0,
            blow_before_time=5,
            blow_after_time=3
        ),
        dosers_config=[
            DoserConfigModel(
                id="temp_doser_1",
                name="Dosificador 1",
                assigned_silo_id="temp_silo_1",
                doser_type="volumetric",
                min_rate=10.0,
                max_rate=100.0,
                current_rate=50.0
            )
        ],
        selector_config=SelectorConfigModel(
            id="temp_selector_1",
            name="Selector 1",
            capacity=4,
            fast_speed=80.0,
            slow_speed=20.0
        ),
        slot_assignments=[
            SlotAssignmentModel(slot_number=1, cage_id="temp_cage_1")
        ]
    )
    
    assert line.line_name == "Linea Principal"
    assert len(line.dosers_config) == 1
    assert len(line.slot_assignments) == 1


def test_save_system_layout_request_valid():
    """Test: Validación exitosa del request completo."""
    request = SaveSystemLayoutRequest(
        silos=[
            SiloConfigModel(id="temp_silo_1", name="Silo A", capacity=1000.0)
        ],
        cages=[
            CageConfigModel(id="temp_cage_1", name="Jaula 1")
        ],
        feeding_lines=[
            FeedingLineConfigModel(
                id="temp_line_1",
                line_name="Linea Principal",
                blower_config=BlowerConfigModel(
                    id="temp_blower_1",
                    name="Soplador 1",
                    non_feeding_power=50.0,
                    blow_before_time=5,
                    blow_after_time=3
                ),
                dosers_config=[
                    DoserConfigModel(
                        id="temp_doser_1",
                        name="Dosificador 1",
                        assigned_silo_id="temp_silo_1",
                        doser_type="volumetric",
                        min_rate=10.0,
                        max_rate=100.0,
                        current_rate=50.0
                    )
                ],
                selector_config=SelectorConfigModel(
                    id="temp_selector_1",
                    name="Selector 1",
                    capacity=4,
                    fast_speed=80.0,
                    slow_speed=20.0
                ),
                slot_assignments=[
                    SlotAssignmentModel(slot_number=1, cage_id="temp_cage_1")
                ]
            )
        ],
        relations_data={},
        presentation_data={}
    )
    
    assert len(request.silos) == 1
    assert len(request.cages) == 1
    assert len(request.feeding_lines) == 1


def test_mapper_api_to_app_request():
    """Test: Mapper convierte correctamente de API model a DTO."""
    api_request = SaveSystemLayoutRequest(
        silos=[
            SiloConfigModel(id="temp_silo_1", name="Silo A", capacity=1000.0)
        ],
        cages=[
            CageConfigModel(id="temp_cage_1", name="Jaula 1")
        ],
        feeding_lines=[],
        relations_data={},
        presentation_data={}
    )
    
    app_dto = SystemLayoutMapper.to_app_request(api_request)
    
    assert len(app_dto.silos) == 1
    assert app_dto.silos[0].name == "Silo A"
    assert len(app_dto.cages) == 1
    assert app_dto.cages[0].name == "Jaula 1"


def test_mapper_app_to_api_response():
    """Test: Mapper convierte correctamente de DTO a API model."""
    from application.dtos import SaveSystemLayoutResponse as AppResponse
    
    app_response = AppResponse(
        status="Sincronización completada",
        lines_processed=2,
        silos_processed=3,
        cages_processed=5
    )
    
    api_response = SystemLayoutMapper.to_api_response(app_response)
    
    assert api_response.status == "Sincronización completada"
    assert api_response.lines_processed == 2
    assert api_response.silos_processed == 3
    assert api_response.cages_processed == 5



def test_strict_mode_rejects_extra_fields():
    """Test: Modo estricto rechaza campos extra (extra='forbid')."""
    with pytest.raises(ValidationError) as exc_info:
        SaveSystemLayoutRequest(
            silos=[],
            cages=[],
            feeding_lines=[],
            relations_data={},
            presentation_data={},
            nombre="asd"  # ❌ Campo extra no permitido
        )
    
    errors = exc_info.value.errors()
    assert any(error['type'] == 'extra_forbidden' for error in errors)


def test_strict_mode_requires_all_fields():
    """Test: Modo estricto requiere todos los campos obligatorios."""
    with pytest.raises(ValidationError) as exc_info:
        SaveSystemLayoutRequest(
            silos=[]
            # ❌ Faltan: cages, feeding_lines, relations_data, presentation_data
        )
    
    errors = exc_info.value.errors()
    # Debe haber errores de campos faltantes
    assert len(errors) >= 4


def test_strict_mode_allows_empty_lists():
    """Test: Modo estricto permite listas/dicts vacíos."""
    request = SaveSystemLayoutRequest(
        silos=[],
        cages=[],
        feeding_lines=[],
        relations_data={},
        presentation_data={}
    )
    
    assert len(request.silos) == 0
    assert len(request.cages) == 0
    assert len(request.feeding_lines) == 0


def test_silo_rejects_extra_field():
    """Test: SiloConfigModel rechaza campos extra."""
    with pytest.raises(ValidationError) as exc_info:
        SiloConfigModel(
            id="temp_silo_1",
            name="Silo A",
            capacity=1000.0,
            color="red"  # ❌ Campo extra
        )
    
    errors = exc_info.value.errors()
    assert any(error['type'] == 'extra_forbidden' for error in errors)

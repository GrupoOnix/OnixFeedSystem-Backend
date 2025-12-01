"""
Script para verificar que la serialización de Enums funciona correctamente
en el flujo completo de FeedingSession.
"""
import sys
import json
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from domain.aggregates.feeding_session import FeedingSession, _serialize_for_json
from domain.enums import FeedingMode, SessionStatus
from domain.value_objects import LineId
from domain.strategies.manual import ManualFeedingStrategy
from dataclasses import asdict


def test_serialize_for_json():
    """Prueba la función helper de serialización."""
    print("=" * 60)
    print("TEST 1: Función _serialize_for_json")
    print("=" * 60)
    
    # Test con enum simple
    test_dict = {
        'mode': FeedingMode.MANUAL,
        'value': 100,
        'nested': {
            'status': SessionStatus.RUNNING,
            'count': 5
        },
        'list': [FeedingMode.CYCLIC, FeedingMode.PROGRAMMED]
    }
    
    result = _serialize_for_json(test_dict)
    print(f"Input: {test_dict}")
    print(f"Output: {result}")
    print(f"JSON serializable: {json.dumps(result)}")
    
    # Verificar que los enums se convirtieron a strings
    assert result['mode'] == 'Manual', f"Expected 'Manual', got {result['mode']}"
    assert result['nested']['status'] == 'Running', f"Expected 'Running', got {result['nested']['status']}"
    assert result['list'][0] == 'Ciclico', f"Expected 'Ciclico', got {result['list'][0]}"
    
    print("✓ Test 1 PASSED\n")


def test_manual_strategy_serialization():
    """Prueba que ManualFeedingStrategy se serializa correctamente."""
    print("=" * 60)
    print("TEST 2: Serialización de ManualFeedingStrategy")
    print("=" * 60)
    
    strategy = ManualFeedingStrategy(
        target_slot=1,
        blower_speed=75.0,
        doser_speed=50.0,
        target_amount_kg=100.0
    )
    
    config = strategy.get_plc_configuration()
    print(f"Config DTO: {config}")
    
    # Serializar con asdict (esto causaba el problema original)
    config_dict = asdict(config)
    print(f"asdict result: {config_dict}")
    print(f"Mode type: {type(config_dict['mode'])}")
    
    # Serializar con nuestra función
    config_serialized = _serialize_for_json(config_dict)
    print(f"Serialized result: {config_serialized}")
    print(f"Mode type after serialization: {type(config_serialized['mode'])}")
    
    # Verificar que es JSON serializable
    json_str = json.dumps(config_serialized)
    print(f"JSON string: {json_str}")
    
    # Verificar que el mode es string
    assert isinstance(config_serialized['mode'], str), f"Expected str, got {type(config_serialized['mode'])}"
    assert config_serialized['mode'] == 'Manual', f"Expected 'Manual', got {config_serialized['mode']}"
    
    print("✓ Test 2 PASSED\n")


def test_feeding_session_applied_config():
    """Prueba que FeedingSession guarda applied_strategy_config correctamente."""
    print("=" * 60)
    print("TEST 3: FeedingSession applied_strategy_config")
    print("=" * 60)
    
    # Crear sesión
    line_id = LineId.generate()
    session = FeedingSession(line_id)
    
    # Crear estrategia
    strategy = ManualFeedingStrategy(
        target_slot=1,
        blower_speed=75.0,
        doser_speed=50.0,
        target_amount_kg=100.0
    )
    
    # Simular lo que hace session.start() sin llamar al machine
    config_dto = strategy.get_plc_configuration()
    config_dict = asdict(config_dto)
    session._applied_strategy_config = _serialize_for_json(config_dict)
    
    print(f"Applied config: {session.applied_strategy_config}")
    
    # Verificar que es JSON serializable
    json_str = json.dumps(session.applied_strategy_config)
    print(f"JSON string: {json_str}")
    
    # Verificar que el mode es string
    assert isinstance(session.applied_strategy_config['mode'], str), \
        f"Expected str, got {type(session.applied_strategy_config['mode'])}"
    assert session.applied_strategy_config['mode'] == 'Manual', \
        f"Expected 'Manual', got {session.applied_strategy_config['mode']}"
    
    print("✓ Test 3 PASSED\n")


if __name__ == "__main__":
    try:
        test_serialize_for_json()
        test_manual_strategy_serialization()
        test_feeding_session_applied_config()
        
        print("=" * 60)
        print("✓ TODOS LOS TESTS PASARON")
        print("=" * 60)
        print("\nLa serialización de Enums está funcionando correctamente.")
        print("El error 'FeedingMode is not JSON serializable' debería estar resuelto.")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

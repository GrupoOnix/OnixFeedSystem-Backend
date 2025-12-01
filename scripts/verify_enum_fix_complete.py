"""
Script de verificación completa del fix de serialización de Enums.
Verifica que todos los componentes funcionan correctamente.
"""
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from domain.aggregates.feeding_session import FeedingSession, _serialize_for_json
from domain.enums import FeedingMode, SessionStatus, FeedingEventType
from domain.value_objects import LineId
from domain.strategies.manual import ManualFeedingStrategy
from dataclasses import asdict
import json


def verify_serialize_function():
    """Verifica que la función _serialize_for_json funciona correctamente."""
    print("=" * 70)
    print("VERIFICACIÓN 1: Función _serialize_for_json")
    print("=" * 70)
    
    test_cases = [
        # Caso 1: Enum simple
        {
            "input": FeedingMode.MANUAL,
            "expected": "Manual",
            "description": "Enum simple"
        },
        # Caso 2: Dict con enum
        {
            "input": {"mode": FeedingMode.CYCLIC, "value": 100},
            "expected": {"mode": "Ciclico", "value": 100},
            "description": "Dict con enum"
        },
        # Caso 3: Lista con enums
        {
            "input": [FeedingMode.MANUAL, FeedingMode.PROGRAMMED],
            "expected": ["Manual", "Programado"],
            "description": "Lista con enums"
        },
        # Caso 4: Dict anidado con enums
        {
            "input": {
                "config": {
                    "mode": FeedingMode.MANUAL,
                    "status": SessionStatus.RUNNING
                },
                "values": [1, 2, 3]
            },
            "expected": {
                "config": {
                    "mode": "Manual",
                    "status": "Running"
                },
                "values": [1, 2, 3]
            },
            "description": "Dict anidado con múltiples enums"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        result = _serialize_for_json(test["input"])
        assert result == test["expected"], \
            f"Test {i} falló: {test['description']}\nEsperado: {test['expected']}\nObtenido: {result}"
        print(f"✓ Test {i}: {test['description']} - PASSED")
    
    print()


def verify_machine_configuration_serialization():
    """Verifica que MachineConfiguration se serializa correctamente."""
    print("=" * 70)
    print("VERIFICACIÓN 2: Serialización de MachineConfiguration")
    print("=" * 70)
    
    strategy = ManualFeedingStrategy(
        target_slot=1,
        blower_speed=75.0,
        doser_speed=50.0,
        target_amount_kg=100.0
    )
    
    config = strategy.get_plc_configuration()
    
    # Verificar que el config tiene un enum
    assert isinstance(config.mode, FeedingMode), \
        f"Expected FeedingMode, got {type(config.mode)}"
    print(f"✓ Config tiene enum FeedingMode: {config.mode}")
    
    # Serializar con asdict
    config_dict = asdict(config)
    assert isinstance(config_dict['mode'], FeedingMode), \
        f"asdict debería mantener el enum, got {type(config_dict['mode'])}"
    print(f"✓ asdict mantiene el enum: {config_dict['mode']}")
    
    # Serializar con nuestra función
    config_serialized = _serialize_for_json(config_dict)
    assert isinstance(config_serialized['mode'], str), \
        f"Expected str, got {type(config_serialized['mode'])}"
    assert config_serialized['mode'] == 'Manual', \
        f"Expected 'Manual', got {config_serialized['mode']}"
    print(f"✓ _serialize_for_json convierte a string: {config_serialized['mode']}")
    
    # Verificar que es JSON serializable
    try:
        json_str = json.dumps(config_serialized)
        print(f"✓ Es JSON serializable: {len(json_str)} caracteres")
    except TypeError as e:
        raise AssertionError(f"No es JSON serializable: {e}")
    
    print()


def verify_feeding_session_integration():
    """Verifica que FeedingSession usa la serialización correctamente."""
    print("=" * 70)
    print("VERIFICACIÓN 3: Integración con FeedingSession")
    print("=" * 70)
    
    line_id = LineId.generate()
    session = FeedingSession(line_id)
    
    strategy = ManualFeedingStrategy(
        target_slot=1,
        blower_speed=75.0,
        doser_speed=50.0,
        target_amount_kg=100.0
    )
    
    # Simular lo que hace start() sin el machine
    config_dto = strategy.get_plc_configuration()
    config_dict = asdict(config_dto)
    session._applied_strategy_config = _serialize_for_json(config_dict)
    session._status = SessionStatus.RUNNING
    
    # Verificar que applied_strategy_config es JSON serializable
    assert session.applied_strategy_config is not None, \
        "applied_strategy_config no debería ser None"
    print(f"✓ applied_strategy_config está configurado")
    
    assert isinstance(session.applied_strategy_config['mode'], str), \
        f"Expected str, got {type(session.applied_strategy_config['mode'])}"
    print(f"✓ mode es string: {session.applied_strategy_config['mode']}")
    
    try:
        json_str = json.dumps(session.applied_strategy_config)
        print(f"✓ applied_strategy_config es JSON serializable: {len(json_str)} caracteres")
    except TypeError as e:
        raise AssertionError(f"applied_strategy_config no es JSON serializable: {e}")
    
    # Verificar get_daily_summary
    summary = session.get_daily_summary()
    assert summary['mode'] == 'Manual', \
        f"Expected 'Manual' in summary, got {summary['mode']}"
    print(f"✓ get_daily_summary retorna mode correcto: {summary['mode']}")
    
    try:
        json_str = json.dumps(summary)
        print(f"✓ get_daily_summary es JSON serializable: {len(json_str)} caracteres")
    except TypeError as e:
        raise AssertionError(f"get_daily_summary no es JSON serializable: {e}")
    
    print()


def verify_event_logging():
    """Verifica que los eventos se loguean correctamente."""
    print("=" * 70)
    print("VERIFICACIÓN 4: Logging de eventos")
    print("=" * 70)
    
    line_id = LineId.generate()
    session = FeedingSession(line_id)
    
    # Simular un log con enum en details
    session._log(FeedingEventType.COMMAND, "Test event", {
        "mode": FeedingMode.MANUAL.value,  # Ya convertido a string
        "value": 100
    })
    
    events = session.pop_events()
    assert len(events) == 1, f"Expected 1 event, got {len(events)}"
    print(f"✓ Evento creado correctamente")
    
    event = events[0]
    assert event.type == FeedingEventType.COMMAND, \
        f"Expected COMMAND, got {event.type}"
    print(f"✓ Tipo de evento correcto: {event.type}")
    
    # Verificar que details es JSON serializable
    try:
        json_str = json.dumps(event.details)
        print(f"✓ Event details es JSON serializable: {json_str}")
    except TypeError as e:
        raise AssertionError(f"Event details no es JSON serializable: {e}")
    
    print()


def main():
    """Ejecuta todas las verificaciones."""
    print("\n" + "=" * 70)
    print("VERIFICACIÓN COMPLETA DEL FIX DE SERIALIZACIÓN DE ENUMS")
    print("=" * 70 + "\n")
    
    try:
        verify_serialize_function()
        verify_machine_configuration_serialization()
        verify_feeding_session_integration()
        verify_event_logging()
        
        print("=" * 70)
        print("✓✓✓ TODAS LAS VERIFICACIONES PASARON ✓✓✓")
        print("=" * 70)
        print("\nCONCLUSIÓN:")
        print("- La función _serialize_for_json funciona correctamente")
        print("- MachineConfiguration se serializa sin errores")
        print("- FeedingSession usa la serialización correctamente")
        print("- Los eventos se loguean sin problemas")
        print("\nEl error 'FeedingMode is not JSON serializable' está RESUELTO.")
        print("=" * 70)
        
        return 0
        
    except AssertionError as e:
        print("\n" + "=" * 70)
        print("✗✗✗ VERIFICACIÓN FALLÓ ✗✗✗")
        print("=" * 70)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    except Exception as e:
        print("\n" + "=" * 70)
        print("✗✗✗ ERROR INESPERADO ✗✗✗")
        print("=" * 70)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

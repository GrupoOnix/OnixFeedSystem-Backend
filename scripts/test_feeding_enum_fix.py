"""
Script para verificar que el fix de serialización de Enums funciona
en el flujo completo con la base de datos.
"""
import asyncio
import sys
from pathlib import Path
from uuid import uuid4

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from domain.aggregates.feeding_session import FeedingSession
from domain.value_objects import LineId
from domain.strategies.manual import ManualFeedingStrategy
from infrastructure.persistence.repositories.feeding_session_repository import FeedingSessionRepository
from infrastructure.persistence.models.feeding_session_model import FeedingSessionModel


async def test_feeding_session_persistence():
    """
    Prueba que FeedingSession se puede guardar y recuperar correctamente
    con la serialización de Enums arreglada.
    """
    print("=" * 60)
    print("TEST: Persistencia de FeedingSession con Enums")
    print("=" * 60)
    
    # Crear engine de prueba (en memoria)
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )
    
    # Crear tablas
    async with engine.begin() as conn:
        await conn.run_sync(FeedingSessionModel.metadata.create_all)
    
    # Crear sesión
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Crear repositorio
        repo = FeedingSessionRepository(session)
        
        # Crear FeedingSession
        line_id = LineId(uuid4())
        feeding_session = FeedingSession(line_id)
        
        # Crear estrategia y simular start (sin machine real)
        strategy = ManualFeedingStrategy(
            target_slot=1,
            blower_speed=75.0,
            doser_speed=50.0,
            target_amount_kg=100.0
        )
        
        # Simular lo que hace start() sin el machine
        from dataclasses import asdict
        from domain.aggregates.feeding_session import _serialize_for_json
        from domain.enums import SessionStatus
        
        config_dto = strategy.get_plc_configuration()
        config_dict = asdict(config_dto)
        feeding_session._applied_strategy_config = _serialize_for_json(config_dict)
        feeding_session._status = SessionStatus.RUNNING
        
        print(f"Session ID: {feeding_session.id}")
        print(f"Applied config: {feeding_session.applied_strategy_config}")
        print(f"Mode type: {type(feeding_session.applied_strategy_config['mode'])}")
        
        # Guardar en BD
        try:
            await repo.save(feeding_session)
            await session.commit()
            print("✓ Sesión guardada exitosamente")
        except Exception as e:
            print(f"✗ Error al guardar: {e}")
            raise
        
        # Recuperar de BD
        try:
            recovered_session = await repo.find_by_id(feeding_session.id)
            print("✓ Sesión recuperada exitosamente")
            
            if recovered_session:
                print(f"Recovered config: {recovered_session.applied_strategy_config}")
                print(f"Mode value: {recovered_session.applied_strategy_config['mode']}")
                
                # Verificar que el mode es string
                assert isinstance(recovered_session.applied_strategy_config['mode'], str), \
                    f"Expected str, got {type(recovered_session.applied_strategy_config['mode'])}"
                assert recovered_session.applied_strategy_config['mode'] == 'Manual', \
                    f"Expected 'Manual', got {recovered_session.applied_strategy_config['mode']}"
                
                print("✓ Verificación de datos correcta")
            else:
                raise Exception("No se pudo recuperar la sesión")
                
        except Exception as e:
            print(f"✗ Error al recuperar: {e}")
            raise
    
    await engine.dispose()
    
    print("\n" + "=" * 60)
    print("✓ TEST COMPLETO EXITOSO")
    print("=" * 60)
    print("\nEl fix de serialización de Enums funciona correctamente")
    print("con la persistencia en base de datos.")


if __name__ == "__main__":
    try:
        asyncio.run(test_feeding_session_persistence())
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

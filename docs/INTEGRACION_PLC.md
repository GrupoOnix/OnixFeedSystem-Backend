# Guía de Integración con PLC Real

Este documento explica cómo integrar el sistema con un PLC real, reemplazando el simulador actual.

## Arquitectura Actual

El sistema está diseñado siguiendo el patrón de **Dependency Injection** y **Strategy Pattern**, lo que permite intercambiar fácilmente la implementación del PLC sin afectar el resto del código.

### Interfaz `IFeedingMachine`

Toda la comunicación con el hardware pasa por la interfaz `IFeedingMachine` definida en `src/domain/interfaces.py`:

```python
class IFeedingMachine(ABC):
    async def send_configuration(self, line_id: LineId, config: MachineConfiguration) -> None
    async def get_status(self, line_id: LineId) -> MachineStatus
    async def pause(self, line_id: LineId) -> None
    async def resume(self, line_id: LineId) -> None
    async def stop(self, line_id: LineId) -> None
```

### Implementaciones

#### PLCSimulator (Actual)
- **Ubicación**: `src/infrastructure/services/plc_simulator.py`
- **Propósito**: Desarrollo y testing sin hardware
- **Características**:
  - Simula estado de componentes (blowers, dosers, selectors)
  - Cálculo realista de dispensado basado en velocidad
  - Transiciones suaves de velocidad
  - Logging detallado
  - Simulación opcional de errores

#### PLCModbusClient (Ejemplo para integración)
- **Ubicación**: `src/infrastructure/services/plc_modbus_client.py.example`
- **Propósito**: Plantilla para integración con PLC real
- **Protocolo**: Modbus TCP
- **Estado**: Template, requiere configuración específica del PLC

## Pasos para Integrar PLC Real

### 1. Determinar Protocolo de Comunicación

El PLC puede usar diferentes protocolos:

- **Modbus TCP/RTU**: Protocolo industrial estándar
  - Biblioteca recomendada: `pymodbus`
  - Ver ejemplo en `plc_modbus_client.py.example`

- **OPC-UA**: Protocolo moderno para industria 4.0
  - Biblioteca recomendada: `asyncua`
  - Similar estructura a Modbus pero con tags en lugar de registros

- **Ethernet/IP**: Común en PLCs Allen-Bradley
  - Biblioteca recomendada: `pycomm3`

- **Propietario**: Protocolo específico del fabricante
  - Consultar documentación del PLC

### 2. Mapear Registros/Tags del PLC

Necesitas documentar qué registros/tags del PLC corresponden a cada parámetro.

#### Parámetros de Escritura (Comandos)

| Parámetro | Tipo | Descripción | Ejemplo Modbus |
|-----------|------|-------------|----------------|
| START_COMMAND | bool | Iniciar operación | Registro 1000 |
| MODE | enum | Modo de operación (0=manual, 1=auto, 2=batch) | Registro 1001 |
| BLOWER_SPEED | float | Velocidad soplador (0-100%) | Registro 1002 |
| DOSER_SPEED | float | Velocidad dosificador (0-100%) | Registro 1003 |
| TARGET_AMOUNT_KG | float | Cantidad objetivo en kg | Registros 1004-1005 |
| BATCH_AMOUNT_KG | float | Cantidad por batch en kg | Registros 1006-1007 |
| CURRENT_SLOT | int | Número de slot/jaula activo | Registro 1008 |
| PAUSE_COMMAND | bool | Pausar operación | Registro 1009 |
| STOP_COMMAND | bool | Detener operación | Registro 1010 |

#### Parámetros de Lectura (Estado)

| Parámetro | Tipo | Descripción | Ejemplo Modbus |
|-----------|------|-------------|----------------|
| IS_RUNNING | bool | Sistema en ejecución | Registro 2000 |
| IS_PAUSED | bool | Sistema en pausa | Registro 2001 |
| CURRENT_MODE | enum | Modo actual | Registro 2002 |
| TOTAL_DISPENSED_KG | float | Total dispensado en sesión | Registros 2003-2004 |
| CURRENT_FLOW_RATE | float | Tasa de flujo actual (kg/h) | Registros 2005-2006 |
| CURRENT_SLOT_NUMBER | int | Slot/jaula actual | Registro 2007 |
| CURRENT_LIST_INDEX | int | Índice en lista de slots | Registro 2008 |
| CURRENT_CYCLE_INDEX | int | Ciclo actual (para modo multi-ciclo) | Registro 2009 |
| TOTAL_CYCLES | int | Total de ciclos configurados | Registro 2010 |
| HAS_ERROR | bool | Indica si hay error activo | Registro 2011 |
| ERROR_CODE | int | Código de error (0=sin error) | Registro 2012 |

#### Parámetros de Lectura (Sensores)

**Nota**: Los sensores se leen por línea. Cada línea puede tener hasta 3 sensores (uno de cada tipo).

| Parámetro | Tipo | Descripción | Ejemplo Modbus |
|-----------|------|-------------|----------------|
| TEMPERATURE_SENSOR_VALUE | float | Temperatura del aire (°C) | Registros 3000-3001 |
| PRESSURE_SENSOR_VALUE | float | Presión del aire (bar) | Registros 3002-3003 |
| FLOW_SENSOR_VALUE | float | Flujo de aire (m³/min) | Registros 3004-3005 |

**Umbrales de alerta recomendados**:
- Temperature: Warning > 70°C, Critical > 85°C
- Pressure: Warning > 1.3 bar, Critical > 1.5 bar  
- Flow: Warning > 18 m³/min, Critical > 22 m³/min

**Valores esperados según estado**:
- **En reposo**: Temp ~15°C, Presión ~0.2 bar, Flujo ~0 m³/min
- **Durante alimentación**: Temp ~25°C, Presión ~0.8 bar, Flujo ~15 m³/min

### 3. Crear Implementación del Cliente PLC

#### Opción A: Usar plantilla Modbus

1. Copiar el archivo ejemplo:
   ```bash
   cp src/infrastructure/services/plc_modbus_client.py.example \
      src/infrastructure/services/plc_modbus_client.py
   ```

2. Actualizar constantes de registros según tu PLC:
   ```python
   REG_START_COMMAND = 1000  # Ajustar según tu PLC
   REG_MODE = 1001
   # etc...
   ```

3. Configurar direcciones IP de PLCs:
   ```python
   PLC_ADDRESSES: Dict[str, str] = {
       "line-1": "192.168.1.10",
       "line-2": "192.168.1.11",
   }
   ```

4. Instalar dependencias:
   ```bash
   pip install pymodbus
   # Actualizar requirements.txt
   ```

#### Opción B: Crear implementación custom

1. Crear nuevo archivo `src/infrastructure/services/plc_custom_client.py`

2. Implementar interfaz `IFeedingMachine`:
   ```python
   from domain.interfaces import IFeedingMachine
   
   class PLCCustomClient(IFeedingMachine):
       async def send_configuration(self, line_id: LineId, config: MachineConfiguration) -> None:
           # Tu implementación
           pass
       
       async def get_status(self, line_id: LineId) -> MachineStatus:
           # Tu implementación
           pass
       
       # etc...
   ```

### 4. Actualizar Dependency Injection

Editar `src/api/dependencies.py`:

```python
# Antes:
from infrastructure.services.plc_simulator import PLCSimulator

def get_machine_service() -> IFeedingMachine:
    global _plc_simulator_instance
    if _plc_simulator_instance is None:
        _plc_simulator_instance = PLCSimulator()
    return _plc_simulator_instance

# Después (para PLC real):
from infrastructure.services.plc_modbus_client import PLCModbusClient

_plc_client_instance: Optional[PLCModbusClient] = None

def get_machine_service() -> IFeedingMachine:
    global _plc_client_instance
    if _plc_client_instance is None:
        _plc_client_instance = PLCModbusClient(
            connection_timeout=5.0,
            retry_attempts=3
        )
    return _plc_client_instance
```

### 5. Configuración de Producción

Usa variables de entorno para configuración:

`.env`:
```bash
# PLC Configuration
PLC_ENABLED=true
PLC_PROTOCOL=modbus  # modbus, opcua, custom
PLC_LINE_1_IP=192.168.1.10
PLC_LINE_2_IP=192.168.1.11
PLC_PORT=502
PLC_TIMEOUT=5.0
PLC_RETRY_ATTEMPTS=3
```

Actualizar `dependencies.py`:
```python
import os
from infrastructure.services.plc_simulator import PLCSimulator
from infrastructure.services.plc_modbus_client import PLCModbusClient

def get_machine_service() -> IFeedingMachine:
    if os.getenv("PLC_ENABLED", "false").lower() == "true":
        # Usar PLC real
        return PLCModbusClient(
            connection_timeout=float(os.getenv("PLC_TIMEOUT", "5.0")),
            retry_attempts=int(os.getenv("PLC_RETRY_ATTEMPTS", "3"))
        )
    else:
        # Usar simulador
        return PLCSimulator()
```

### 6. Testing con Hardware Real

#### Test Manual

1. Conectar al PLC (verificar red):
   ```bash
   ping 192.168.1.10
   ```

2. Probar lectura básica con herramienta Modbus:
   ```bash
   # Usando mbpoll (instalar: apt-get install mbpoll)
   mbpoll -a 1 -r 2000 -c 10 -t 3 192.168.1.10
   ```

3. Iniciar aplicación en modo debug:
   ```bash
   PLC_ENABLED=true LOG_LEVEL=DEBUG uvicorn src.api.main:app --reload
   ```

4. Probar endpoint de inicio de alimentación:
   ```bash
   curl -X POST http://localhost:8000/api/feeding/start \
     -H "Content-Type: application/json" \
     -d '{
       "line_id": "line-1",
       "cage_id": "cage-1",
       "mode": "manual"
     }'
   ```

5. Monitorear logs:
   ```bash
   tail -f logs/app.log | grep "PLC-Modbus"
   ```

#### Test Automatizado

Crear tests de integración en `src/test/infrastructure/services/`:

```python
import pytest
from infrastructure.services.plc_modbus_client import PLCModbusClient

@pytest.mark.integration
@pytest.mark.asyncio
async def test_plc_connection():
    client = PLCModbusClient()
    line_id = LineId.from_str("line-1")
    
    # Test básico de lectura
    status = await client.get_status(line_id)
    assert status is not None
    assert isinstance(status.is_running, bool)
```

Ejecutar:
```bash
pytest -m integration -v
```

## Consideraciones de Seguridad

### 1. Red Industrial

- **Segmentar red**: PLCs en VLAN separada
- **Firewall**: Restringir acceso solo desde backend
- **VPN**: Si acceso remoto es necesario

### 2. Autenticación

Si el PLC soporta autenticación:
```python
client = AsyncModbusTcpClient(
    host=ip_address,
    port=port,
    # Agregar credenciales si el PLC lo requiere
)
```

### 3. Manejo de Errores

Implementar retry logic robusto:
```python
async def send_configuration_with_retry(self, line_id, config):
    for attempt in range(self._retry_attempts):
        try:
            await self._send_configuration_internal(line_id, config)
            return
        except ModbusException as e:
            if attempt == self._retry_attempts - 1:
                raise
            await asyncio.sleep(0.5 * (attempt + 1))
```

### 4. Watchdog

Implementar watchdog para detectar pérdida de comunicación:
```python
async def health_check_loop(self):
    while True:
        for line_id in self._clients.keys():
            try:
                await self.get_status(line_id)
            except Exception as e:
                logger.error(f"Health check failed for {line_id}: {e}")
                # Notificar al sistema de alertas
        await asyncio.sleep(30)
```

## Debugging

### Logs Útiles

Habilitar logging detallado:
```python
import logging

logging.getLogger('infrastructure.services').setLevel(logging.DEBUG)
logging.getLogger('pymodbus').setLevel(logging.DEBUG)
```

### Herramientas de Diagnóstico

1. **Wireshark**: Capturar tráfico Modbus TCP
   - Filtro: `tcp.port == 502`

2. **ModScan**: Cliente Modbus gráfico para Windows

3. **QModMaster**: Cliente Modbus multiplataforma

4. **mbpoll**: Cliente Modbus CLI

### Common Issues

#### "Connection refused"
- Verificar IP y puerto
- Verificar firewall del PLC
- Verificar que PLC acepta conexiones Modbus TCP

#### "Timeout"
- Aumentar timeout: `connection_timeout=10.0`
- Verificar latencia de red: `ping -c 10 192.168.1.10`
- Verificar carga del PLC

#### "Illegal function"
- Verificar que el PLC soporta la función Modbus usada
- Algunos PLCs solo soportan Function Codes específicos

#### "Illegal address"
- Verificar mapeo de registros
- Algunos PLCs usan base 0, otros base 1

## Rollback a Simulador

Si hay problemas con el PLC real, rollback inmediato:

1. Cambiar variable de entorno:
   ```bash
   export PLC_ENABLED=false
   ```

2. Reiniciar servicio:
   ```bash
   docker-compose restart backend
   ```

3. Verificar:
   ```bash
   curl http://localhost:8000/health
   ```

## Monitoreo en Producción

### Métricas a Monitorear

- **Tasa de éxito de comandos**: % de comandos exitosos vs fallidos
- **Latencia de lectura**: Tiempo promedio de `get_status()`
- **Latencia de escritura**: Tiempo promedio de `send_configuration()`
- **Errores de conexión**: Conteo de timeouts/desconexiones
- **Estado de líneas**: Tiempo en cada estado (running, paused, stopped)

### Alertas

Configurar alertas para:
- Pérdida de comunicación con PLC > 1 minuto
- Tasa de errores > 5%
- Latencia > 500ms sostenida
- Error crítico reportado por PLC

## Contacto y Soporte

Para soporte durante integración:
- Documentación del fabricante del PLC
- Equipo de ingeniería de control
- Logs en `logs/plc_integration.log`

## Checklist de Integración

- [ ] Protocolo de comunicación determinado
- [ ] Mapeo de registros/tags documentado
- [ ] Implementación de cliente PLC creada
- [ ] Dependency injection actualizado
- [ ] Variables de entorno configuradas
- [ ] Tests manuales con hardware pasados
- [ ] Tests automatizados creados
- [ ] Manejo de errores implementado
- [ ] Logging configurado
- [ ] Métricas de monitoreo definidas
- [ ] Alertas configuradas
- [ ] Documentación actualizada
- [ ] Plan de rollback probado

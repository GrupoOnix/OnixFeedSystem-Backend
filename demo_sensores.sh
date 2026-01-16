#!/bin/bash

# Demo completo: Sensores en Tiempo Real
# Muestra cómo los valores cambian según el estado de la máquina

LINE_ID="6e0e6354-6961-4853-a052-8e1150afe5b6"

echo "=========================================="
echo "DEMO: Sensores en Tiempo Real"
echo "=========================================="
echo ""
echo "Línea ID: $LINE_ID"
echo ""

# Función para leer sensores y formatear
read_sensors() {
    echo "$1"
    echo "----------------------------------------"
    RESPONSE=$(curl -s "http://localhost:8000/api/feeding-lines/$LINE_ID/sensors/readings")

    TEMP=$(echo "$RESPONSE" | python -c "import sys, json; r=json.load(sys.stdin); print(f\"{r['readings'][0]['value']:.2f} {r['readings'][0]['unit']}\")" 2>/dev/null || echo "Error")
    PRESSURE=$(echo "$RESPONSE" | python -c "import sys, json; r=json.load(sys.stdin); print(f\"{r['readings'][1]['value']:.3f} {r['readings'][1]['unit']}\")" 2>/dev/null || echo "Error")
    FLOW=$(echo "$RESPONSE" | python -c "import sys, json; r=json.load(sys.stdin); print(f\"{r['readings'][2]['value']:.2f} {r['readings'][2]['unit']}\")" 2>/dev/null || echo "Error")

    echo "   🌡️  Temperatura: $TEMP"
    echo "   💨 Presión:     $PRESSURE"
    echo "   🌊 Flujo:       $FLOW"
    echo ""
}

# 1. Lectura inicial (en reposo)
read_sensors "1️⃣  LECTURA INICIAL (Máquina en REPOSO)"

# 2. Obtener lista de jaulas para esta línea
echo "2️⃣  Obteniendo jaulas disponibles..."
CAGES=$(curl -s "http://localhost:8000/api/cages?line_id=$LINE_ID")
CAGE_ID=$(echo "$CAGES" | python -c "import sys, json; c=json.load(sys.stdin); print(c['cages'][0]['id'] if c['cages'] else '')" 2>/dev/null)

if [ -z "$CAGE_ID" ]; then
    echo "   ⚠️  No hay jaulas disponibles en esta línea"
    echo ""
    echo "Nota: Para ver valores durante alimentación, necesitas:"
    echo "  - Jaulas asignadas a la línea"
    echo "  - Iniciar una operación de feeding"
    echo ""
    exit 0
fi

echo "   ✓ Jaula encontrada: $CAGE_ID"
echo ""

# 3. Iniciar operación de alimentación
echo "3️⃣  Iniciando operación de ALIMENTACIÓN..."
START_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/feeding/start" \
  -H "Content-Type: application/json" \
  -d "{
    \"line_id\": \"$LINE_ID\",
    \"cage_id\": \"$CAGE_ID\",
    \"mode\": \"MANUAL\"
  }")

# Verificar si inició correctamente
if echo "$START_RESPONSE" | grep -q "error\|detail"; then
    echo "   ⚠️  No se pudo iniciar: $(echo "$START_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin).get('detail', 'Error desconocido'))" 2>/dev/null || echo "$START_RESPONSE")"
    echo ""
else
    echo "   ✓ Alimentación iniciada"
    echo ""

    # Esperar un momento para que los sensores reflejen el cambio
    echo "   ⏳ Esperando 2 segundos para que los sensores se estabilicen..."
    sleep 2
    echo ""

    # 4. Lectura durante alimentación
    read_sensors "4️⃣  LECTURA DURANTE ALIMENTACIÓN (Máquina ACTIVA)"

    # 5. Detener alimentación
    echo "5️⃣  Deteniendo alimentación..."
    STOP_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/feeding/stop" \
      -H "Content-Type: application/json" \
      -d "{\"line_id\": \"$LINE_ID\"}")
    echo "   ✓ Alimentación detenida"
    echo ""

    # Esperar un momento
    sleep 1

    # 6. Lectura final (vuelta al reposo)
    read_sensors "6️⃣  LECTURA FINAL (Máquina en REPOSO nuevamente)"
fi

echo "=========================================="
echo "✅ DEMO COMPLETADA"
echo "=========================================="
echo ""
echo "📊 Observaciones:"
echo "   • En REPOSO: Temperatura ~15°C, Presión ~0.2 bar, Flujo ~0 m³/min"
echo "   • ALIMENTANDO: Temperatura ~25°C, Presión ~0.8 bar, Flujo ~15 m³/min"
echo ""
echo "📡 Endpoint disponible:"
echo "   GET /api/feeding-lines/{line_id}/sensors/readings"
echo ""
echo "📖 Documentación completa:"
echo "   http://localhost:8000/docs"
echo ""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))


from src.domain.aggregates.feeding_line.doser import Doser
from src.domain.aggregates.feeding_line.blower import Blower
from src.domain.aggregates.feeding_line.selector import Selector
from src.domain.aggregates.feeding_line.feeding_line import FeedingLine
from src.domain.value_objects import BlowDurationInSeconds, BlowerName, BlowerPowerPercentage, CageId, DoserName, DosingRange, DosingRate, LineName, SelectorCapacity, SelectorName, SelectorSpeedProfile, SiloId


vo_blower_name = BlowerName("Blower1")
vo_power = BlowerPowerPercentage(50.0)
vo_time = BlowDurationInSeconds(10)
vo_doser_name = DoserName("Doser Silo 1")
vo_silo_id = SiloId.generate()
vo_dosing_rate = DosingRate(25.0, "kg/min")
vo_dosing_range = DosingRange(min_rate=10.0, max_rate=50.0)
vo_selector_name = SelectorName("Selector 1")
vo_capacity = SelectorCapacity(10)
vo_speed = SelectorSpeedProfile(BlowerPowerPercentage(80.0), BlowerPowerPercentage(30.0))

mi_blower = Blower(
    name=vo_blower_name,
    non_feeding_power=vo_power,
    blow_before_time=vo_time,
    blow_after_time=vo_time
)

mi_doser = Doser(
    name=vo_doser_name,
    assigned_silo_id=vo_silo_id,
    doser_type="VariDoser",
    dosing_range=vo_dosing_range,
    current_rate=vo_dosing_rate
)

mi_selector = Selector(
    name=vo_selector_name,
    capacity=vo_capacity,
    speed_profile=vo_speed
)

vo_line_name = LineName("Linea de Alimentacion 1")

nueva_linea = FeedingLine.create(
    name=vo_line_name,
    blower=mi_blower,
    dosers=[mi_doser],
    selector=mi_selector
)

print(f"¡Línea creada con éxito! ID: {nueva_linea.id}")

print(f"jaulas asignadas: {nueva_linea._slot_assignments}")

nueva_linea.assign_cage_to_slot(slot_number=1, cage_id= CageId.generate())

nueva_linea.assign_cage_to_slot(slot_number=10, cage_id= CageId.generate())

print(f"jaulas asignadas después de asignar: {nueva_linea._slot_assignments}")
print(f"slots asignados: {nueva_linea.get_slot_assignments()}")

slot_assignments = nueva_linea.get_slot_assignments()

print(f"slot 1 -> jaula {slot_assignments[0].cage_id}")  # Debería mostrar la jaula asignada al slot 1


# import sys
# import os

# # --- 1. CONFIGURACIÓN DEL PATH ---
# # Le dice a Python dónde encontrar tu carpeta 'src'.
# # Ejecuta este script desde la carpeta raíz de tu proyecto.
# try:
#     sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
#     # Asumimos que Weight está en esta ruta, ajusta si es necesario
#     from src.domain.value_objects import Weight
# except ImportError:
#     print("--- ERROR ---")
#     print("No se pudo importar el VO 'Weight'.")
#     print("Asegúrate de que este script esté en la raíz de tu proyecto")
#     print("y que tu VO Weight esté en 'src/domain/shared/value_objects.py'")
#     sys.exit(1)

# print("--- 1. Pruebas de Instanciación y Getters (Valores Extremos) ---")

# # Valor Masivo (1000 toneladas)
# w_tons = Weight.from_tons(1000)
# print(f"\nObjeto w_tons (creado desde 1000 ton):")
# print(f"  repr (miligramos): {w_tons}")
# print(f"  .as_tons: {w_tons.as_tons} ton")
# print(f"  .as_kg: {w_tons.as_kg} kg")
# print(f"  .as_grams: {w_tons.as_grams} g")

# # Valor Fraccionario (0.44 gramos)
# w_frac_g = Weight.from_grams(0.44)
# print(f"\nObjeto w_frac_g (creado desde 0.44 g):")
# print(f"  repr (miligramos): {w_frac_g}") # Esperado: 440 miligramos
# print(f"  .as_grams: {w_frac_g.as_grams} g")
# print(f"  .as_miligrams: {w_frac_g.as_miligrams} mg")

# # Valor Cero
# w_zero = Weight.zero()
# print(f"\nObjeto w_zero (creado desde .zero()):")
# print(f"  repr (miligramos): {w_zero}")
# print(f"  .as_grams: {w_zero.as_grams} g")


# print("\n--- 2. Pruebas de Operaciones Matemáticas (Unidades Mixtas) ---")

# p1 = Weight.from_kg(50)         # 50,000,000 mg
# p2 = Weight.from_grams(750.5)    # 750,500 mg

# # Suma
# total = p1 + p2
# print(f"\nSuma (50 kg + 750.5 g):")
# print(f"  Resultado: {total.as_kg} kg (Esperado: 50.7505)")
# print(f"  repr: {total}") # Esperado: 50,750,500 mg

# # Resta
# resta = p1 - p2
# print(f"\nResta (50 kg - 750.5 g):")
# print(f"  Resultado: {resta.as_kg} kg (Esperado: 49.2495)")
# print(f"  repr: {resta}") # Esperado: 49,249,500 mg

# # Multiplicación (ej. Biomasa: 1500 peces * 350.5g/pez)
# biomasa_g = Weight.from_grams(350.5)
# cantidad_peces = 1500
# biomasa_total = biomasa_g * cantidad_peces
# print(f"\nMultiplicación (350.5 g * 1500):")
# print(f"  Resultado: {biomasa_total.as_kg} kg (Esperado: 525.75)")
# print(f"  repr: {biomasa_total}") # Esperado: 525,750,000 mg


# print("\n--- 3. Pruebas de Comparación (Unidades Mixtas) ---")
# w_1_ton = Weight.from_tons(1)
# w_1000_kg = Weight.from_kg(1000)
# w_999_kg = Weight.from_kg(999)

# print(f"1 ton == 1000 kg: {w_1_ton == w_1000_kg} (Esperado: True)")
# print(f"1 ton > 999 kg:   {w_1_ton > w_999_kg} (Esperado: True)")
# print(f"1 ton < 1000 kg:  {w_1_ton < w_1000_kg} (Esperado: False)")
# print(f"999 kg >= 1 ton:  {w_999_kg >= w_1_ton} (Esperado: False)")


# print("\n--- 4. Pruebas de Representación (__str__) ---")
# print(f"  Valor en Toneladas: {w_tons}")
# print(f"  Valor en Kilos: {p1}")
# print(f"  Valor en Gramos: {p2}")
# print(f"  Valor Fraccionario: {w_frac_g}")
# print(f"  Valor en Miligramos: {Weight.from_miligrams(100)}")
# print(f"  Valor Cero: {w_zero}")


# print("\n--- 5. Pruebas de Errores (Deben fallar) ---")

# # Error al crear (negativo)
# try:
#     Weight.from_kg(-10)
# except ValueError as e:
#     print(f"OK: Error al crear con negativo: {e}")
    
# # Error al restar (resultado negativo)
# try:
#     p2 - p1 # 750g - 50kg
# except ValueError as e:
#     print(f"OK: Error al restar (resultado negativo): {e}")

# # Error al comparar (tipos incompatibles)
# try:
#     p1 > 100
# except TypeError as e:
#     print(f"OK: Error al comparar tipos incompatibles: {e}")
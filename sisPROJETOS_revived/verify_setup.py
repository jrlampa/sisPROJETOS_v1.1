import sys
import os
import numpy as np

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from modules.catenaria.logic import CatenaryLogic
    from modules.converter.logic import ConverterLogic
    print("Imports successful.")
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)

def test_catenary():
    print("✅ Catenary Module OK")
    logic = CatenaryLogic()

    # 4. Test Project Creator Logic
    print("\nTesting Project Creator...")
    from src.modules.project_creator.logic import ProjectCreatorLogic
    creator = ProjectCreatorLogic()
    if os.path.exists(creator.templates_dir):
        print(f"  Templates dir found: {creator.templates_dir}")
        required_templates = ["prancha.dwg", "cqt.xlsx", "ambiental.xlsx"]
        missing = [f for f in required_templates if not os.path.exists(os.path.join(creator.templates_dir, f))]
        if missing:
             print(f"  ❌ Missing templates: {missing}")
        else:
             print("  ✅ All templates found")
    else:
        print(f"  ❌ Templates dir NOT found: {creator.templates_dir}")
        
    # 5. Test Pole Load Logic
    print("\nTesting Pole Load Logic...")
    from src.modules.pole_load.logic import PoleLoadLogic
    pl_logic = PoleLoadLogic()
    # Simple calculation
    inputs = [{'rede': 'Convencional', 'condutor': '1/0AWG-CAA, Nu', 'vao': 40, 'angulo': 0, 'flecha': 1.0}]
    res = pl_logic.calculate_resultant("Light", "Normal", inputs)
    if res and res['resultant_force'] > 0:
        print(f"  ✅ Calculation functional. Result: {res['resultant_force']:.2f} daN")
    else:
        print("  ❌ Calculation failed or returned 0")

    # 6. Test AI Assistant Logic
    print("\nTesting AI Assistant Logic...")
    from src.modules.ai_assistant.logic import AIAssistantLogic
    ai_logic = AIAssistantLogic()
    if ai_logic.api_key:
        print(f"  ✅ API Key found: {ai_logic.api_key[:10]}...")
    else:
        print("  ❌ API Key NOT found in .env")

    print("\n✅ Setup Verification Complete!")
    # Test conductor loading
    names = logic.get_conductor_names()
    print(f"Loaded {len(names)} conductors.")
    if not names:
        print("FAIL: No conductors loaded.")
        return
    
    # Test Calculation
    # Span 100m, weight 1kg/m, Tension 1000daN
    res = logic.calculate_catenary(100, 10, 10, 1000, 1.0)
    if res:
        print(f"Calculation success: Sag = {res['sag']:.4f} m")
        # Approx sag = w * L^2 / 8T = 1 * 10000 / 8000 = 1.25m (using kgf)
        # Logic uses w_daN = 0.98. T = 1000.
        # a = 1000 / 0.98 = 1020.
        # Sag = 1020 * (cosh(50/1020) - 1).
        # Taylor: cosh(x) ~ 1 + x^2/2.
        # Sag ~ a * ( (L/2a)^2 / 2 ) = a * L^2 / (8 a^2) = L^2 / 8a = w L^2 / 8T.
        # 0.98 * 10000 / 8000 = 1.225m.
        if 1.2 < res['sag'] < 1.3:
            print("PASS: Sag within expected range.")
        else:
            print(f"WARN: Sag {res['sag']} seems off.")
    else:
        print("FAIL: Calculation returned None.")

def test_converter():
    print("\nTesting Converter Logic...")
    logic = ConverterLogic()
    # Just check if methods exist
    if hasattr(logic, 'load_file') and hasattr(logic, 'convert_to_utm'):
        print("PASS: Logic class structure correct.")
    else:
        print("FAIL: Logic class missing methods.")

if __name__ == "__main__":
    test_catenary()
    test_converter()

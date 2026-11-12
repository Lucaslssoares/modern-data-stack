import sys
from pathlib import Path

# Garante que src/, config/ e api/ estejam no path para todos os testes
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "config"))
sys.path.insert(0, str(ROOT / "api"))

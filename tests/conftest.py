import sys
from pathlib import Path

# Garante que src/ e config/ estejam no path para todos os testes
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "config"))

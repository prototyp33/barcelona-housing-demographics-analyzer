"""
Pytest configuration file.

Añade el directorio raíz del proyecto al Python path para que los tests
puedan importar módulos desde `src`.
"""

import sys
from pathlib import Path

# Añadir el directorio raíz del proyecto al Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


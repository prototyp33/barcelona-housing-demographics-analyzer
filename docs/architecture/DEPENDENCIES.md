# Reglas de Dependencias del Proyecto

**Objetivo**: Evitar acoplamiento y dependencias cíclicas entre módulos.

---

## 📐 Límites de Dependencias

### Regla General: Dependencias Unidireccionales

```
stdlib/third-party
    ↓
src/                    (código de producción, módulos reutilizables)
    ↓
scripts/                (CLI tools, scripts ejecutables)
spikes/*/scripts/       (scripts temporales de spikes)
notebooks/              (análisis exploratorio)
tests/                  (tests automatizados)
```

### Reglas Específicas por Directorio

#### `src/` (Código de Producción)
**Puede importar**:
- ✅ Librerías estándar de Python (`stdlib`)
- ✅ Paquetes de terceros (`third-party`)
- ✅ Otros módulos dentro de `src/` (evitando ciclos)

**NO puede importar**:
- ❌ `scripts/`
- ❌ `spikes/`
- ❌ `notebooks/`
- ❌ `tests/`

**Ejemplo válido**:
```python
# src/extraction/catastro/soap_client.py
from typing import Optional
import requests  # ✅ third-party
from src.extraction.base import BaseExtractor  # ✅ otro módulo de src/
```

**Ejemplo inválido**:
```python
# src/extraction/catastro/soap_client.py
from scripts.utils import setup_logging  # ❌ NO importar de scripts/
```

---

#### `scripts/` (Scripts Ejecutables)
**Puede importar**:
- ✅ Librerías estándar de Python (`stdlib`)
- ✅ Paquetes de terceros (`third-party`)
- ✅ Módulos de `src/` (para reutilizar código)

**NO puede importar**:
- ❌ Otros scripts de `scripts/` (excepto `scripts/utils/` compartido)
- ❌ `spikes/`
- ❌ `notebooks/`
- ❌ `tests/`

**Ejemplo válido**:
```python
# scripts/etl/extract_catastro.py
import sys
from pathlib import Path
import pandas as pd  # ✅ third-party
from src.extraction.catastro.soap_client import CatastroSOAPClient  # ✅ src/
from scripts.utils.setup_logging import setup_logging  # ✅ utils compartido
```

**Ejemplo inválido**:
```python
# scripts/etl/extract_catastro.py
from scripts.analysis.train_models import train_model  # ❌ NO importar otros scripts
```

---

#### `spikes/*/scripts/` (Scripts Temporales)
**Puede importar**:
- ✅ Librerías estándar de Python (`stdlib`)
- ✅ Paquetes de terceros (`third-party`)
- ✅ Módulos de `src/` (para reutilizar código de producción)

**NO puede importar**:
- ❌ Scripts de `scripts/` (solo código de producción)
- ❌ Otros spikes

**Ejemplo válido**:
```python
# spikes/data-validation/scripts/fase2/parse_catastro_xml.py
import pandas as pd  # ✅ third-party
from src.extraction.catastro.parsers import parse_xml  # ✅ src/ (si existe)
```

**Ejemplo inválido**:
```python
# spikes/data-validation/scripts/fase2/parse_catastro_xml.py
from scripts.etl.extract_catastro import extract  # ❌ NO importar scripts/
```

---

#### `notebooks/` (Análisis Exploratorio)
**Puede importar**:
- ✅ Librerías estándar de Python (`stdlib`)
- ✅ Paquetes de terceros (`third-party`)
- ✅ Módulos de `src/` (para usar funciones analíticas)

**NO puede importar**:
- ❌ `scripts/`
- ❌ `spikes/`
- ❌ `tests/`

---

#### `tests/` (Tests Automatizados)
**Puede importar**:
- ✅ Librerías estándar de Python (`stdlib`)
- ✅ Paquetes de terceros (`third-party`)
- ✅ Módulos de `src/` (código a testear)
- ✅ `tests/fixtures/` (datos de prueba compartidos)

**NO puede importar**:
- ❌ `scripts/`
- ❌ `spikes/`
- ❌ `notebooks/`

---

## 🔄 Evitar Dependencias Cíclicas

### Regla: Si A importa B, B NO puede importar A

**Ejemplo de ciclo inválido**:
```python
# src/extraction/catastro/soap_client.py
from src.etl.validators import validate_rc

# src/etl/validators.py
from src.extraction.catastro.soap_client import CatastroSOAPClient  # ❌ CICLO!
```

**Solución**: Extraer lógica compartida a un módulo común
```python
# src/extraction/catastro/utils.py (nuevo módulo común)
def normalize_rc(rc: str) -> str:
    """Normaliza referencia catastral."""
    return rc.strip()[:20]

# src/extraction/catastro/soap_client.py
from src.extraction.catastro.utils import normalize_rc  # ✅

# src/etl/validators.py
from src.extraction.catastro.utils import normalize_rc  # ✅
```

---

## 📋 Checklist de Revisión

Antes de crear un nuevo import, verificar:

- [ ] ¿El módulo fuente está en el directorio correcto según las reglas?
- [ ] ¿Estoy importando de `src/` cuando debería?
- [ ] ¿Estoy creando una dependencia cíclica?
- [ ] ¿Puedo extraer código compartido a un módulo común?

---

## 🛠️ Validación Automática (Opcional)

Para validar dependencias automáticamente, puedes usar:

### Opción 1: `import-linter`
```bash
pip install import-linter
# Crear archivo .importlinter
```

### Opción 2: Script de validación simple
```python
# scripts/maintenance/check_dependencies.py
# Valida que no haya imports prohibidos
```

---

## 📚 Ejemplos de Buenas Prácticas

### ✅ Bueno: Script usa módulo de src/
```python
# scripts/etl/extract_catastro.py
from src.extraction.catastro.soap_client import CatastroSOAPClient

def main():
    client = CatastroSOAPClient()
    # ...
```

### ✅ Bueno: Módulo de src/ usa otro módulo de src/
```python
# src/extraction/catastro/soap_client.py
from src.extraction.base import BaseExtractor

class CatastroSOAPClient(BaseExtractor):
    # ...
```

### ❌ Malo: Script importa otro script
```python
# scripts/etl/extract_catastro.py
from scripts.analysis.train_models import train_model  # ❌
```

### ❌ Malo: Módulo de src/ importa de scripts/
```python
# src/extraction/catastro/soap_client.py
from scripts.utils import setup_logging  # ❌
# Debería usar: from src.utils.logging import setup_logging
```

---

**Última actualización**: 2025-12-19


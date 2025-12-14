# Spike Setup Guide - Quick Start

**Spike:** Data Validation - Barcelona Housing Hedonic Model  
**Barrio:** Gràcia  
**Duración:** Dec 16-20, 2025

---

## Setup Rápido (5 minutos)

### 1. Activar Virtual Environment

```bash
# Desde la raíz del proyecto
source .venv-spike/bin/activate

# Verificar
which python  # Debe mostrar .venv-spike/bin/python
```

### 2. Verificar Dependencias

```bash
python -c "import pandas, statsmodels, geopandas; print('✅ OK')"
```

Si falla:
```bash
pip install -r spike-data-validation/requirements.txt
```

### 3. Configurar Jupyter Kernel

```bash
# Registrar kernel (solo primera vez)
python -m ipykernel install --user --name .venv-spike --display-name "Python (.venv-spike)"
```

### 4. Abrir Notebook

```bash
cd spike-data-validation
jupyter notebook notebooks/01-gracia-hedonic-model.ipynb
```

**Importante:** En el notebook, seleccionar kernel "Python (.venv-spike)".

---

## Verificación de Entorno

Ejecutar esta celda en el notebook:

```python
# Verificar imports
import sys
print(f"Python: {sys.version}")

import pandas as pd
import numpy as np
import geopandas as gpd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

print("✅ All imports successful")

# Verificar paths
from pathlib import Path
ROOT = Path.cwd().parent if Path.cwd().name == "spike-data-validation" else Path.cwd()
print(f"Root: {ROOT}")

# Verificar estructura
dirs = ["data/raw", "data/processed", "outputs/reports", "outputs/visualizations"]
for d in dirs:
    path = ROOT / "spike-data-validation" / d
    path.mkdir(parents=True, exist_ok=True)
    print(f"✅ {d}")
```

---

## Troubleshooting Rápido

### Kernel no aparece en Jupyter

```bash
# Re-registrar
python -m ipykernel install --user --name .venv-spike --display-name "Python (.venv-spike)"

# Reiniciar Jupyter
```

### ModuleNotFoundError

```bash
# Verificar venv activado
which python

# Reinstalar
pip install -r spike-data-validation/requirements.txt
```

### Paths incorrectos

El notebook detecta automáticamente si estás en `spike-data-validation/` o en la raíz. Si hay problemas:

```python
# En el notebook, ajustar manualmente:
ROOT = Path("/ruta/completa/al/proyecto")
```

---

## Próximos Pasos

1. ✅ Setup completo
2. 📊 Revisar notebook `01-gracia-hedonic-model.ipynb`
3. 📋 Ver issues del spike: [Master Tracker #139](https://github.com/prototyp33/barcelona-housing-demographics-analyzer/issues/139)
4. 🚀 Comenzar extracción de datos (Lunes Dec 16)

---

**Para más detalles:** Ver [SPIKE_SETUP_GUIDE.md](../../docs/SPIKE_SETUP_GUIDE.md)

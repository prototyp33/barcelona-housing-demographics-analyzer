# SPIKE Setup Guide - Barcelona Housing Hedonic Model

**Fecha:** Diciembre 2025  
**Duración del Spike:** Dec 16-20, 2025  
**Barrio Piloto:** Gràcia

---

## Objetivo

Esta guía te ayudará a configurar el entorno completo para el spike de validación del modelo hedónico de precios de vivienda en Barcelona.

---

## Prerrequisitos

### Sistema Operativo
- macOS 12+ / Linux (Ubuntu 20.04+) / Windows 10+ con WSL2
- Terminal con acceso a línea de comandos
- Git instalado y configurado

### Cuentas y Accesos Necesarios
- GitHub account con acceso al repositorio
- Acceso a APIs públicas (INE, Portal de Dades BCN)
- (Opcional) API keys si se requieren para fuentes adicionales

---

## Paso 1: Clonar y Navegar al Proyecto

```bash
# Clonar repositorio (si aún no lo tienes)
git clone https://github.com/prototyp33/barcelona-housing-demographics-analyzer.git
cd barcelona-housing-demographics-analyzer

# Navegar al directorio del spike
cd spike-data-validation
```

---

## Paso 2: Configurar Python Environment

### 2.1 Verificar Versión de Python

```bash
python3 --version
# Debe ser Python 3.11 o superior
# Si no: instalar desde python.org o usar pyenv
```

### 2.2 Crear Virtual Environment

```bash
# Desde la raíz del proyecto
python3 -m venv .venv-spike

# Activar virtual environment
# macOS/Linux:
source .venv-spike/bin/activate

# Windows:
# .venv-spike\Scripts\activate

# Verificar que está activado (debería mostrar la ruta del venv)
which python
```

### 2.3 Instalar Dependencias

```bash
# Actualizar pip
pip install --upgrade pip

# Instalar dependencias del spike
pip install -r spike-data-validation/requirements.txt

# Verificar instalación
python -c "import pandas, statsmodels, geopandas; print('✅ All packages installed')"
```

**Dependencias principales instaladas:**
- pandas, numpy, geopandas (manipulación de datos)
- statsmodels, scipy, scikit-learn (modelado estadístico)
- matplotlib, seaborn, plotly (visualización)
- requests, beautifulsoup4 (extracción de datos)
- fuzzywuzzy, python-Levenshtein (matching de strings)
- jupyter, ipykernel (notebooks)

---

## Paso 3: Configurar Jupyter Kernel

### 3.1 Registrar Kernel con Jupyter

```bash
# Con el venv activado
python -m ipykernel install --user --name .venv-spike --display-name "Python (.venv-spike)"
```

### 3.2 Verificar Kernel

```bash
jupyter kernelspec list
# Deberías ver ".venv-spike" en la lista
```

### 3.3 Abrir Jupyter Notebook

```bash
# Desde spike-data-validation/
cd spike-data-validation
jupyter notebook notebooks/01-gracia-hedonic-model.ipynb

# O usar JupyterLab
jupyter lab notebooks/01-gracia-hedonic-model.ipynb
```

**Importante:** En el notebook, selecciona el kernel "Python (.venv-spike)" desde el menú Kernel → Change Kernel.

---

## Paso 4: Configurar Variables de Entorno

### 4.1 Crear Archivo .env

```bash
# Copiar template
cp spike-data-validation/.env.example spike-data-validation/.env

# Editar con tus valores
# macOS/Linux:
nano spike-data-validation/.env
# o
code spike-data-validation/.env  # Si tienes VS Code

# Windows:
notepad spike-data-validation\.env
```

### 4.2 Variables Necesarias

```bash
# Configuración del Spike
BARRIO=Gràcia
YEAR_START=2020
YEAR_END=2025

# Umbrales de Éxito
MIN_RECORDS=100
TARGET_R2=0.55
TARGET_MATCH_RATE=0.70

# API Keys (si necesitas)
# INE_API_KEY=your_key_here
# GOOGLE_MAPS_API_KEY=your_key_here
```

---

## Paso 5: Verificar Acceso a APIs y Fuentes de Datos

### 5.1 Portal de Dades BCN (CKAN API)

```bash
# Test rápido desde Python
python3 << EOF
import requests

# Test CKAN API
url = "https://opendata-ajuntament.barcelona.cat/data/api/3/action/package_list"
response = requests.get(url, timeout=10)

if response.status_code == 200:
    print("✅ Portal de Dades API accessible")
    print(f"   Datasets disponibles: {len(response.json()['result'])}")
else:
    print(f"❌ Error: {response.status_code}")
EOF
```

### 5.2 INE (Estadística Registral)

```bash
# Verificar acceso web
# Abrir en navegador:
# https://www.ine.es/jaxiT3/Tabla.htm?t=1436
```

### 5.3 Catastro

```bash
# Verificar acceso a Sede Electrónica
# https://www.sedecatastro.gob.es/
```

---

## Paso 6: Estructura de Directorios

Verificar que la estructura esté completa:

```bash
cd spike-data-validation
tree -L 3
# O si no tienes tree:
find . -type d -maxdepth 3
```

**Estructura esperada:**

```
spike-data-validation/
├── data/
│   ├── raw/          # Datos originales sin procesar
│   ├── processed/    # Datos limpios y merged
│   └── logs/         # Logs de extracción
├── notebooks/
│   └── 01-gracia-hedonic-model.ipynb
├── outputs/
│   ├── reports/     # PDFs y markdown
│   └── visualizations/  # Gráficos PNG
├── .env              # Variables de entorno (no commitear)
├── .env.example      # Template de variables
└── requirements.txt   # Dependencias Python
```

**Crear directorios faltantes:**

```bash
mkdir -p data/{raw,processed,logs}
mkdir -p outputs/{reports,visualizations}
```

---

## Paso 7: Verificar Notebook Base

### 7.1 Abrir Notebook

```bash
jupyter notebook notebooks/01-gracia-hedonic-model.ipynb
```

### 7.2 Ejecutar Celda de Setup

En el notebook, ejecutar la primera celda (Setup) que incluye:
- Imports de librerías
- Configuración de logging
- Paths de datos
- Validación de inputs raw

**Verificar que:**
- ✅ Todos los imports funcionan sin errores
- ✅ Los paths están correctos
- ✅ El logging está configurado

---

## Paso 8: Troubleshooting Común

### Error: "ModuleNotFoundError: No module named 'X'"

**Solución:**
```bash
# Verificar que el venv está activado
which python  # Debe mostrar .venv-spike/bin/python

# Reinstalar dependencias
pip install -r spike-data-validation/requirements.txt
```

### Error: "Kernel not found" en Jupyter

**Solución:**
```bash
# Re-registrar kernel
python -m ipykernel install --user --name .venv-spike --display-name "Python (.venv-spike)"

# Reiniciar Jupyter
# Cerrar y volver a abrir el notebook
```

### Error: "Permission denied" al crear venv

**Solución:**
```bash
# Verificar permisos del directorio
ls -la | grep venv

# Si es necesario, cambiar permisos
chmod 755 .
```

### Error: "geopandas installation fails"

**Solución:**
```bash
# Instalar dependencias del sistema primero (macOS)
brew install geos proj

# O usar conda (alternativa)
conda install -c conda-forge geopandas
```

### Error: "API timeout" al acceder a Portal de Dades

**Solución:**
- Verificar conexión a internet
- Verificar que la API no esté en mantenimiento
- Aumentar timeout en requests:
  ```python
  requests.get(url, timeout=30)
  ```

---

## Paso 9: Validación Final

### Checklist Pre-Spike

Ejecutar este script de validación:

```bash
python3 << 'EOF'
import sys
import importlib

# Verificar Python version
assert sys.version_info >= (3, 11), f"Python 3.11+ required, got {sys.version}"

# Verificar paquetes críticos
packages = [
    'pandas', 'numpy', 'geopandas',
    'statsmodels', 'scipy', 'sklearn',
    'matplotlib', 'seaborn', 'plotly',
    'requests', 'jupyter'
]

missing = []
for pkg in packages:
    try:
        importlib.import_module(pkg)
        print(f"✅ {pkg}")
    except ImportError:
        print(f"❌ {pkg} missing")
        missing.append(pkg)

if missing:
    print(f"\n❌ Missing packages: {missing}")
    print("Run: pip install -r spike-data-validation/requirements.txt")
    sys.exit(1)
else:
    print("\n✅ All packages installed correctly!")

# Verificar estructura de directorios
import os
dirs = [
    'data/raw', 'data/processed', 'data/logs',
    'outputs/reports', 'outputs/visualizations'
]
missing_dirs = [d for d in dirs if not os.path.exists(d)]
if missing_dirs:
    print(f"\n⚠️  Missing directories: {missing_dirs}")
    print("Run: mkdir -p " + " ".join(missing_dirs))
else:
    print("\n✅ Directory structure complete!")
EOF
```

---

## Paso 10: Próximos Pasos

Una vez completado el setup:

1. **Revisar el notebook base:** `notebooks/01-gracia-hedonic-model.ipynb`
2. **Leer la guía del spike:** `spike-data-validation/README.md`
3. **Revisar issues del spike:** Ver milestone "Spike Completion" en GitHub
4. **Comenzar extracción de datos:** Lunes Dec 16, 9:00 AM

---

## Recursos Adicionales

- [Master Tracker Issue](https://github.com/prototyp33/barcelona-housing-demographics-analyzer/issues/139)
- [Development Environment Guide](../DEVELOPMENT_ENVIRONMENT.md)
- [Project Documentation](../../README.md)

---

## Soporte

Si encuentras problemas:
1. Revisar esta guía de troubleshooting
2. Consultar issues en GitHub con label `spike`
3. Contactar al equipo en el canal de Slack/Discord del proyecto

---

**Última actualización:** Diciembre 2025


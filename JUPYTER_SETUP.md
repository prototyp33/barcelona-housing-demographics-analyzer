# Configuración del Entorno Jupyter

## ✅ Estado Actual

**Todas las librerías están instaladas correctamente:**

- ✅ scipy: 1.15.2
- ✅ pandas: 2.3.3
- ✅ numpy: 1.26.4
- ✅ jupyter: 4.5.1
- ✅ matplotlib, seaborn, plotly

**Problema:** Jupyter no está en tu PATH actual.

---

## 🚀 SOLUCIÓN RÁPIDA (Sesión Actual)

Para usar Jupyter **ahora mismo**, ejecuta en tu terminal:

```bash
export PATH="/Users/adrianiraeguialvear/Library/Python/3.12/bin:$PATH"
jupyter lab
```

O si prefieres Jupyter Notebook clásico:

```bash
export PATH="/Users/adrianiraeguialvear/Library/Python/3.12/bin:$PATH"
jupyter notebook
```

---

## 🔧 SOLUCIÓN PERMANENTE

Para que Jupyter esté disponible **siempre**, agrega el PATH a tu `~/.zshrc`:

```bash
echo 'export PATH="/Users/adrianiraeguialvear/Library/Python/3.12/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

Luego podrás ejecutar simplemente:

```bash
jupyter lab
```

---

## 📝 COMANDOS PASO A PASO

### **Opción 1: Usar el script de setup**

```bash
cd /Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer
./setup_jupyter.sh
```

Luego ejecuta los comandos que te muestra el script.

### **Opción 2: Manual**

```bash
# 1. Agregar PATH permanentemente
echo 'export PATH="/Users/adrianiraeguialvear/Library/Python/3.12/bin:$PATH"' >> ~/.zshrc

# 2. Recargar configuración
source ~/.zshrc

# 3. Verificar que funciona
which jupyter

# 4. Iniciar Jupyter Lab
cd /Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer
jupyter lab
```

---

## 🎯 ABRIR EL NOTEBOOK DE EDA

Una vez que Jupyter Lab esté corriendo:

1. Navega a: `notebooks/01_EDA_Barcelona_Housing.ipynb`
2. Click para abrir
3. **Ejecuta todas las celdas:** Cell → Run All
4. O ejecuta celda por celda con `Shift + Enter`

---

## ✅ VERIFICAR QUE TODO FUNCIONA

En la primera celda del notebook, deberías ver:

```python
import scipy
import pandas as pd
import numpy as np
# ... etc

print(f"✅ scipy version: {scipy.__version__}")
# Output: ✅ scipy version: 1.15.2
```

---

## 🔍 TROUBLESHOOTING

### **Si jupyter sigue sin encontrarse:**

```bash
# Verificar dónde está instalado
which python3
# Output: /Library/Frameworks/Python.framework/Versions/3.12/bin/python3

# Verificar que scipy está instalado
python3 -c "import scipy; print(scipy.__version__)"
# Output: 1.15.2

# Buscar jupyter
find ~/Library/Python/3.12 -name jupyter
```

### **Si el kernel no tiene scipy:**

```bash
# Instalar ipykernel en el Python correcto
python3 -m pip install ipykernel --user

# Registrar el kernel
python3 -m ipykernel install --user --name=python3 --display-name="Python 3.12"
```

---

## 📚 ALTERNATIVA: Usar Python directamente

Si prefieres no usar Jupyter, puedes ejecutar el análisis con Python:

```bash
# Convertir notebook a script Python
jupyter nbconvert --to script notebooks/01_EDA_Barcelona_Housing.ipynb

# Ejecutar el script
python3 notebooks/01_EDA_Barcelona_Housing.py
```

---

## 🎓 RESUMEN

**Tu entorno está configurado correctamente**, solo necesitas:

1. **Agregar el PATH** (una sola vez):

   ```bash
   echo 'export PATH="/Users/adrianiraeguialvear/Library/Python/3.12/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   ```

2. **Iniciar Jupyter**:

   ```bash
   jupyter lab
   ```

3. **Abrir el notebook** y ejecutar las celdas

---

**¡Todo listo para el análisis!** 🎉

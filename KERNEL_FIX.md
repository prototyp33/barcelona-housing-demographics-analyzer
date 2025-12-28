# Solución al Problema del Kernel de Jupyter

## 🔴 PROBLEMA IDENTIFICADO

Jupyter está intentando usar un kernel de otro proyecto:

```
/Users/adrianiraeguialvear/OnSpot_Predictive_Model/.venv/bin/python
```

Este kernel no existe o no tiene scipy instalado.

---

## ✅ SOLUCIÓN

### **Paso 1: Crear un kernel específico para este proyecto**

Ejecuta en tu terminal:

```bash
python3 -m ipykernel install --user --name barcelona-housing --display-name "Python 3.12 (Barcelona Housing)"
```

Esto creará un nuevo kernel llamado "Python 3.12 (Barcelona Housing)" que usa tu Python 3.12 del sistema (donde scipy SÍ está instalado).

### **Paso 2: Iniciar Jupyter Lab**

```bash
export PATH="/Users/adrianiraeguialvear/Library/Python/3.12/bin:$PATH"
cd /Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer
jupyter lab
```

### **Paso 3: Cambiar el kernel en el notebook**

Una vez que Jupyter Lab esté abierto:

1. Abre el notebook: `notebooks/01_EDA_Barcelona_Housing.ipynb`
2. En la esquina superior derecha, verás el kernel actual (probablemente ".venv (Python 3.12.2)")
3. **Click en el nombre del kernel**
4. Selecciona: **"Python 3.12 (Barcelona Housing)"**
5. Espera a que el kernel se conecte
6. **Ejecuta la primera celda** → Debería funcionar sin errores

---

## 🎯 ALTERNATIVA: Usar el kernel por defecto

Si prefieres usar el kernel por defecto de Python 3:

```bash
# Listar kernels disponibles
jupyter kernelspec list

# Usar el kernel python3 (si existe)
# En Jupyter Lab, selecciona "Python 3" o "Python 3.12"
```

---

## 🔧 VERIFICAR KERNELS DISPONIBLES

```bash
export PATH="/Users/adrianiraeguialvear/Library/Python/3.12/bin:$PATH"
jupyter kernelspec list
```

Deberías ver algo como:

```
Available kernels:
  barcelona-housing    /Users/adrianiraeguialvear/Library/Jupyter/kernels/barcelona-housing
  python3              /Users/adrianiraeguialvear/Library/Jupyter/kernels/python3
```

---

## 📝 CAMBIAR KERNEL EN JUPYTER LAB

### **Método 1: Desde la interfaz**

1. Click en el nombre del kernel (esquina superior derecha)
2. Selecciona "Python 3.12 (Barcelona Housing)"

### **Método 2: Desde el menú**

1. Kernel → Change Kernel...
2. Selecciona "Python 3.12 (Barcelona Housing)"

### **Método 3: Al crear un nuevo notebook**

1. File → New → Notebook
2. Selecciona "Python 3.12 (Barcelona Housing)"

---

## 🚨 ELIMINAR KERNELS VIEJOS (Opcional)

Si quieres limpiar kernels que ya no existen:

```bash
# Listar kernels
jupyter kernelspec list

# Eliminar un kernel específico
jupyter kernelspec remove nombre-del-kernel

# Por ejemplo, si hay un kernel roto de OnSpot:
jupyter kernelspec remove onspot-venv
```

---

## ✅ VERIFICACIÓN FINAL

Después de cambiar el kernel, ejecuta en la primera celda del notebook:

```python
import sys
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")

import scipy
print(f"✅ scipy version: {scipy.__version__}")
```

Deberías ver:

```
Python executable: /Library/Frameworks/Python.framework/Versions/3.12/bin/python3
Python version: 3.12.x
✅ scipy version: 1.15.2
```

---

## 🎓 RESUMEN

**El problema:** Jupyter usaba un kernel de otro proyecto que no existe.

**La solución:** Crear un kernel nuevo específico para este proyecto que use el Python correcto (donde scipy está instalado).

**Comando clave:**

```bash
python3 -m ipykernel install --user --name barcelona-housing --display-name "Python 3.12 (Barcelona Housing)"
```

---

**¡Ahora el notebook debería funcionar perfectamente!** 🎉

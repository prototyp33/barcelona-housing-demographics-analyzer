# Cómo Compartir Información del Dashboard Streamlit

Esta guía te ayuda a recopilar y compartir información útil para debugging y mejoras del dashboard.

---

## 🚀 Método Rápido (Recomendado)

### Usar el script de recopilación automática

```bash
bash scripts/collect_debug_info.sh > debug_info.txt
```

Luego comparte el archivo `debug_info.txt` conmigo.

---

## 📋 Métodos Manuales

### 1. Capturas de Pantalla

**Cuándo usar:**
- Errores visuales
- Comportamiento inesperado
- Métricas que quieres mostrar

**Cómo:**
- Mac: `Cmd + Shift + 4`
- Windows: `Win + Shift + S`
- Linux: `Print Screen` o herramientas de captura

**Qué capturar:**
- Mensajes de error completos
- Secciones específicas del dashboard
- Métricas de rendimiento
- Comportamiento visual

---

### 2. Logs de la Consola

**Cuándo usar:**
- Errores al iniciar el dashboard
- Problemas de rendimiento
- Errores de conexión a BD

**Cómo capturar:**

```bash
# Opción 1: Redirigir a archivo
streamlit run src/app/main.py 2>&1 | tee streamlit_output.log

# Opción 2: Copiar directamente de la terminal
# (Selecciona y copia el texto de la terminal)
```

**Qué compartir:**
- Últimas 50-100 líneas de logs
- Mensajes de error completos (traceback)
- Advertencias relevantes

---

### 3. Archivos de Log

**Si tienes logging a archivo habilitado:**

```bash
# Ver últimas líneas
tail -50 data/logs/dashboard.log

# O compartir el archivo completo
cat data/logs/dashboard.log
```

**Ubicación:** `data/logs/dashboard.log`

---

### 4. Errores Específicos

**Formato recomendado:**

```
Error: [Descripción breve]

Traceback completo:
[Pega aquí el traceback completo]

Contexto:
- Qué estabas haciendo cuando ocurrió
- Qué esperabas que pasara
- Qué pasó en realidad
```

**Ejemplo:**

```
Error: No se pueden cargar los KPIs

Traceback completo:
File "src/app/main.py", line 203, in main
    kpis = load_kpis()
File "src/app/data_loader.py", line 742, in load_kpis
    ...
sqlite3.OperationalError: database is locked

Contexto:
- Estaba navegando entre pestañas del dashboard
- Esperaba ver los KPIs en la página Overview
- El dashboard se quedó cargando y luego mostró este error
```

---

### 5. Información del Sistema

**Comandos útiles:**

```bash
# Versiones
python3 --version
streamlit --version

# Sistema operativo
uname -a  # Linux/Mac
# o
systeminfo  # Windows

# Estado de archivos
ls -la .streamlit/
ls -la data/logs/
```

---

### 6. Descripción de Comportamiento

**Template útil:**

```
Situación:
- [Qué estabas haciendo]

Comportamiento esperado:
- [Qué esperabas que pasara]

Comportamiento actual:
- [Qué está pasando realmente]

Pasos para reproducir:
1. [Paso 1]
2. [Paso 2]
3. [Paso 3]

Información adicional:
- [Cualquier otra información relevante]
```

---

## 🎯 Casos de Uso Específicos

### Problema: Dashboard no inicia

**Comparte:**
1. Salida completa de la terminal al ejecutar `streamlit run src/app/main.py`
2. Resultado de: `bash scripts/collect_debug_info.sh`

---

### Problema: Errores al cargar datos

**Comparte:**
1. Captura de pantalla del error
2. Últimas 30 líneas de `data/logs/dashboard.log` (si existe)
3. Mensaje de error de la consola

---

### Problema: Rendimiento lento

**Comparte:**
1. Logs de rendimiento (buscar líneas con `PERF |`)
2. Tiempos específicos que observas
3. Qué acciones son lentas (cargar página, cambiar filtros, etc.)

---

### Problema: Datos incorrectos o faltantes

**Comparte:**
1. Qué datos esperabas ver
2. Qué datos estás viendo
3. Filtros/selecciones que usaste
4. Captura de pantalla si es relevante

---

## 📤 Formas de Compartir

### Opción 1: En el chat
- Pega directamente el texto/logs
- Adjunta capturas de pantalla
- Describe el problema

### Opción 2: Archivos
- Crea un archivo `.txt` o `.md` con la información
- Compártelo en el chat

### Opción 3: Script automático
```bash
# Genera archivo con toda la info
bash scripts/collect_debug_info.sh > debug_info.txt

# Luego comparte el contenido
cat debug_info.txt
```

---

## 🔍 Información Más Útil

### Para debugging de errores:
- ✅ Traceback completo
- ✅ Logs de la consola
- ✅ Archivo de log (si existe)
- ✅ Pasos para reproducir

### Para mejoras de rendimiento:
- ✅ Logs con `PERF |` (tiempos de ejecución)
- ✅ Descripción de qué es lento
- ✅ Tamaño de datos que estás cargando

### Para problemas de datos:
- ✅ Qué datos esperabas
- ✅ Qué datos ves
- ✅ Filtros/selecciones usadas
- ✅ Captura de pantalla si ayuda

---

## 💡 Tips

1. **Siempre incluye el contexto**: Qué estabas haciendo cuando ocurrió el problema
2. **Sé específico**: "Es lento" vs "load_kpis() tarda 5 segundos"
3. **Incluye pasos para reproducir**: Si puedo reproducir el problema, es más fácil solucionarlo
4. **Comparte logs completos**: A veces el error importante está unas líneas antes

---

## 🆘 Ejemplo Completo

```
Problema: El dashboard muestra "database is locked" al cambiar de pestaña

Información del sistema:
- Python 3.12.0
- Streamlit 1.28.0
- macOS 14.0

Logs de consola:
[Pega aquí los logs relevantes]

Traceback:
[Pega aquí el traceback completo]

Pasos para reproducir:
1. Iniciar dashboard: streamlit run src/app/main.py
2. Ir a pestaña "Market"
3. Cambiar a pestaña "Insights"
4. Error aparece después de 2-3 segundos

Archivo de log (últimas 20 líneas):
[Pega aquí las últimas líneas del log]
```

---

**Última actualización:** 2026-01-15

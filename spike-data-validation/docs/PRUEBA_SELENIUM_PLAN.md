# Plan: Probar Selenium + Firefox

**Fecha**: 2025-12-19  
**Issue**: #202 - Fase 2  
**Referencia**: Video tutorial que recomienda Selenium con Firefox

---

## 🎯 Objetivo

Probar si Selenium con Firefox funciona mejor que Playwright o BeautifulSoup para evitar bloqueos de Idealista.

---

## 📋 Pasos de Prueba

### **Paso 1: Verificar Instalación**

```bash
# Verificar Selenium
python3 -c "from selenium import webdriver; print('✅ Selenium OK')"

# Verificar geckodriver (Firefox)
geckodriver --version
```

**Si no está instalado**:
```bash
# Instalar Selenium
pip install selenium

# Instalar geckodriver (macOS)
brew install geckodriver

# O descargar manualmente:
# https://github.com/mozilla/geckodriver/releases
```

---

### **Paso 2: Ejecutar Script de Prueba**

```bash
# Test con 1 página (modo visible para ver qué pasa)
python3 spike-data-validation/scripts/fase2/scrape_idealista_selenium.py \
  --max-pages 1 \
  --no-headless

# Si funciona, probar con más páginas
python3 spike-data-validation/scripts/fase2/scrape_idealista_selenium.py \
  --max-pages 3
```

---

### **Paso 3: Analizar Resultados**

**Si funciona**:
- ✅ Propiedades extraídas
- ✅ CSV generado: `idealista_gracia_selenium.csv`
- ✅ Continuar con matching y re-entrenamiento

**Si falla**:
- ❌ Verificar si es Cloudflare u otro bloqueo
- ❌ Ajustar selectores CSS si es necesario
- ❌ Documentar resultado y continuar con API como única opción

---

## 🔍 Qué Observar

1. **¿Se carga la página?**
   - Si no: Error de conexión o bloqueo inmediato
   - Si sí: Continuar

2. **¿Aparece Cloudflare?**
   - Si sí: Selenium también está bloqueado
   - Si no: Puede funcionar

3. **¿Se encuentran listings?**
   - Si sí: Extraer datos
   - Si no: Selectores CSS pueden necesitar ajuste

4. **¿Se extraen datos?**
   - Si sí: ✅ Éxito
   - Si no: Revisar estructura HTML

---

## 📊 Comparación Esperada

| Método | Resultado Esperado |
|--------|-------------------|
| Playwright | ❌ Bloqueado (ya probado) |
| BeautifulSoup | ❌ HTTP 403 (ya probado) |
| Selenium | ⏳ Por determinar |

---

## 🔗 Referencias

- **Video**: https://www.youtube.com/watch?v=I6Q4B4CSPtU
- **Repositorio**: https://github.com/JuanPMC/comprar_casa
- **Script**: `spike-data-validation/scripts/fase2/scrape_idealista_selenium.py`

---

**Última actualización**: 2025-12-19


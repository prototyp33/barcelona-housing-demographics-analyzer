# Soluciones para Bloqueo de IP de Idealista

**Fecha**: 2025-12-20  
**Problema**: Idealista bloquea la IP con mensaje "Se ha detectado un uso indebido. El acceso se ha bloqueado"

---

## 🚫 ¿Qué es este Bloqueo?

No es un CAPTCHA, es un **bloqueo directo de tu IP** por parte de Idealista. El mensaje indica:

```
Se ha detectado un uso indebido
El acceso se ha bloqueado

ID: [identificador único]
IP: [tu dirección IP]
```

**Causa**: Idealista detecta comportamiento automatizado (scraping) y bloquea la IP.

---

## 💡 Soluciones

### **Opción 1: Usar VPN** ✅ **Recomendado para Pruebas**

**Ventajas:**
- ✅ Cambia tu IP inmediatamente
- ✅ Puedes probar múltiples IPs
- ✅ Funciona para desarrollo/testing

**Pasos:**
1. Conecta a una VPN (ExpressVPN, NordVPN, ProtonVPN, etc.)
2. Verifica tu nueva IP: https://whatismyipaddress.com/
3. Ejecuta el script de nuevo:
   ```bash
   python3 spike-data-validation/scripts/fase2/scrape_idealista_selenium.py \
       --max-pages 2 \
       --no-headless \
       --no-cache
   ```

**Nota**: Idealista puede bloquear también IPs de VPNs conocidas. Si una VPN no funciona, prueba otra.

---

### **Opción 2: Cambiar de Red** 📱

**Ventajas:**
- ✅ No requiere software adicional
- ✅ IP diferente automáticamente

**Pasos:**
1. **Cambiar WiFi**: Conecta a otra red WiFi
2. **Usar móvil como hotspot**: 
   - Activa hotspot en tu móvil
   - Conecta tu Mac al hotspot
   - Ejecuta el script de nuevo
3. **Usar datos móviles**: Si tienes un módem USB o tethering

---

### **Opción 3: Esperar** ⏰

**Ventajas:**
- ✅ No requiere acción
- ✅ Bloqueo puede ser temporal

**Desventajas:**
- ⚠️ No garantizado (puede ser permanente)
- ⚠️ Puede tardar horas o días

**Recomendación**: Si necesitas datos urgentemente, usa VPN o cambia de red.

---

### **Opción 4: Usar API Oficial** 🔑 **ÚNICA OPCIÓN ESTABLE**

**Ventajas:**
- ✅ No bloqueada (es la API oficial)
- ✅ Legal y permitido
- ✅ Datos estructurados
- ✅ Funciona de forma consistente

**Limitaciones:**
- ⚠️ Límite: 150 calls/mes
- ⚠️ Requiere credenciales (registro gratuito)

**Pasos:**
1. Registrarse en: https://developers.idealista.com/
2. Obtener API key y secret
3. Usar el script: `extract_idealista_api_gracia.py`

**Documentación**: Ver `spike-data-validation/docs/IDEALISTA_API_SETUP.md`

---

## 🔍 Detección Automática

El script `scrape_idealista_selenium.py` detecta automáticamente este bloqueo y muestra:

```
🚫 BLOQUEO DE IP DETECTADO
======================================================================
Idealista ha bloqueado tu IP por 'uso indebido'.

💡 SOLUCIONES:
...
```

---

## 📊 Comparación de Opciones

| Opción | Facilidad | Eficacia | Estabilidad | Costo |
|--------|-----------|----------|-------------|-------|
| **VPN** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | 💰 (pago) |
| **Cambiar Red** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ✅ Gratis |
| **Esperar** | ⭐⭐⭐ | ⭐ | ⭐ | ✅ Gratis |
| **API Oficial** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ✅ Gratis |

---

## ⚠️ Advertencias

### **VPNs Públicas**
- Algunas IPs de VPNs públicas pueden estar en listas negras
- Idealista puede detectar y bloquear IPs de VPNs conocidas
- **Solución**: Usar VPNs premium o cambiar de servidor VPN

### **Rate Limiting**
- Incluso con VPN, Idealista puede detectar comportamiento automatizado
- **Recomendación**: Usar delays largos (2-20 segundos) entre páginas
- No scrapear más de 10-20 páginas por sesión

### **Bloqueo Permanente**
- Si tu IP está bloqueada permanentemente, solo VPN o cambio de red funcionará
- La API oficial es la única opción que no se bloquea

---

## 🎯 Recomendación Final

**Para el Spike (desarrollo/testing):**
1. ✅ Usar VPN para pruebas rápidas
2. ✅ O cambiar de red (móvil como hotspot)
3. ✅ Continuar con datos mock si el bloqueo persiste

**Para Producción:**
1. ✅ **Usar API oficial** (única opción estable y legal)
2. ✅ Obtener credenciales en https://developers.idealista.com/
3. ✅ Implementar rate limiting respetuoso

---

## 🔗 Archivos Relacionados

- **Script**: `spike-data-validation/scripts/fase2/scrape_idealista_selenium.py`
- **API Setup**: `spike-data-validation/docs/IDEALISTA_API_SETUP.md`
- **Conclusión Scraping**: `spike-data-validation/docs/CONCLUSION_FINAL_SCRAPING.md`
- **Guía Uso**: `spike-data-validation/docs/GUIA_USO_SELENIUM.md`

---

**Última actualización**: 2025-12-20


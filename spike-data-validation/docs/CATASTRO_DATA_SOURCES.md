# Fuentes de Datos Catastrales para Issue #200

Este documento describe las opciones disponibles para obtener datos catastrales (superficie, año construcción, plantas) para el spike de validación de Gràcia.

**Enfoque**: Priorizar opciones 100% gratuitas, oficiales y sin dependencias externas.

---

## Opción 1: API SOAP Oficial del Catastro - **⭐ RECOMENDADA (OFICIAL Y GRATUITA)**

**Estado**: ✅ Cliente implementado  
**Script**: `spike-data-validation/scripts/catastro_soap_client.py`

### Características

- ✅ **100% Gratuita**: Sin registro, sin API key, sin coste
- ✅ **Oficial**: Servicio del Ministerio de Hacienda
- ✅ **Sostenible**: Fuente oficial que no desaparecerá
- ✅ **Independiente**: No depende de wrappers de terceros
- ✅ **Legal**: Cumple con condiciones de uso de datos públicos

### Requisitos

- **Ninguno**: Servicio público, sin autenticación
- Librería Python: `requests` (incluida en dependencias del proyecto)

### Uso

```python
from catastro_soap_client import CatastroSOAPClient

client = CatastroSOAPClient()
resultado = client.get_building_by_rc("12345678901234567890")
# Retorna: superficie_m2, ano_construccion, uso_principal, direccion_normalizada
```

### Detalles Técnicos

- **URL Endpoint**: `http://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCoordenadas.asmx`
- **Método**: SOAP / POST XML
- **Operación**: `Consulta_DNPRC` (Datos No Protegidos por Referencia Catastral)
- **Formato Respuesta**: XML con estructura `bico/bi/debi`

### Limitaciones

- ⚠️ Formato XML (requiere parsing)
- ⚠️ Rate limit no documentado (usar delays razonables entre peticiones)

---

## Opción 2: catastro-api.es (NO RECOMENDADA - Terceros)

**Estado**: ⚠️ Implementada pero NO recomendada para producción  
**Script**: `spike-data-validation/scripts/catastro_client.py`

### Características

- ⚠️ **Servicio de terceros**: No oficial, puede cambiar o desaparecer
- ⚠️ **Requiere API key**: Dependencia externa
- ⚠️ **Rate limits**: Tier gratuito limitado (100-500 calls/día)
- ✅ **Rápida**: JSON limpio, fácil de usar

### Limitaciones

- ⚠️ **No sostenible**: Dependencia de servicio de terceros
- ⚠️ **Coste potencial**: Puede requerir pago en el futuro
- ⚠️ **Riesgo**: Cambios en política o cierre del servicio

**Estado**: ✅ Implementada y lista para usar  
**Script**: `spike-data-validation/scripts/extract_catastro_gracia.py`

### Características

- ✅ **Rápida**: Consultas síncronas, resultados inmediatos
- ✅ **Simple**: API REST con JSON, fácil de integrar
- ✅ **Adecuada para spike**: Permite validación rápida del flujo

### Requisitos

- API key de `catastro-api.es` (servicio de terceros)
- Configurar variable de entorno:
  ```bash
  export CATASTRO_API_KEY='tu_api_key'
  ```

### Uso

```bash
# Verificar requisitos
python3 spike-data-validation/scripts/check_issue_200_ready.py

# Ejecutar extracción
python3 spike-data-validation/scripts/extract_catastro_gracia.py
```

### Limitaciones

- ⚠️ Servicio de terceros (no oficial)
- ⚠️ Requiere API key (posibles límites de uso)
- ⚠️ Dependencia externa

---

## Opción 3: Consulta Masiva Oficial (D.G. del Catastro) - **ALTERNATIVA ASÍNCRONA**

**Estado**: 🔧 Cliente implementado, requiere registro manual  
**Script**: `spike-data-validation/scripts/catastro_oficial_client.py`

### Características

- ✅ **Fuente oficial**: Dirección General del Catastro
- ✅ **Sin API key**: Solo requiere registro en Sede Electrónica
- ✅ **Datos completos**: Acceso directo a base de datos del Catastro

### Requisitos

1. **Registro en Sede Electrónica del Catastro**
   - URL: https://www1.sedecatastro.gob.es
   - No requiere certificado digital para datos NO protegidos

2. **Generar fichero XML de entrada**
   ```python
   from catastro_oficial_client import CatastroOficialClient
   from pathlib import Path
   
   client = CatastroOficialClient()
   referencias = ["12345678901234567890", ...]  # 20 caracteres cada una
   xml_input = client.generate_input_xml(referencias)
   print(client.generate_instructions(xml_input))
   ```

3. **Subir y procesar** (manual)
   - Subir XML a Sede Electrónica
   - Esperar procesamiento (1-2 horas)
   - Descargar XML de salida

4. **Parsear resultados**
   ```python
   resultados = client.parse_output_xml(Path("consulta_masiva_salida.xml"))
   ```

### Limitaciones

- ⚠️ **Procesamiento asíncrono**: 1-2 horas de espera
- ⚠️ **Requiere registro manual**: No automatizable completamente
- ⚠️ **Formato XML**: Más complejo de procesar que JSON

---

## Comparación para Spike

| Aspecto | catastro-api.es | Servicio Oficial |
|---------|----------------|------------------|
| **Velocidad** | ⚡ Inmediato | 🐌 1-2 horas |
| **Automatización** | ✅ Completa | ⚠️ Parcial (requiere manual) |
| **Fuente** | Terceros | Oficial |
| **API Key** | ✅ Requerida | ❌ No requerida |
| **Registro** | ❌ No | ✅ Requerido |
| **Formato** | JSON | XML |
| **Adecuado para spike** | ✅ Sí | ⚠️ Solo si hay tiempo |

---

## Recomendación para Issue #200

### Para el Spike (Validación Rápida)

**Usar**: `catastro-api.es` (Opción 1)

**Razones**:
- Permite validar el flujo completo en minutos
- Automatizable al 100%
- Suficiente para demostrar viabilidad del modelo hedonic pricing

**Pasos**:
1. Obtener API key de catastro-api.es
2. Configurar `CATASTRO_API_KEY`
3. Ejecutar `extract_catastro_gracia.py`

### Para Producción (Futuro)

**Considerar**: Servicio Oficial (Opción 2)

**Razones**:
- Fuente oficial y confiable
- Sin dependencia de terceros
- Datos directamente del Catastro

**Implementación**:
- Integrar cliente oficial en pipeline ETL principal
- Programar consultas masivas periódicas
- Procesar XML de salida automáticamente

---

## Documentación Oficial

- **Servicio Masivo Catastro**: https://www.catastro.hacienda.gob.es/ayuda/masiva/Ayuda_Masiva.htm
- **Sede Electrónica**: https://www1.sedecatastro.gob.es
- **Formato XML**: Ver documentación en Sede Electrónica

---

## Archivos Relacionados

- `spike-data-validation/scripts/extract_catastro_gracia.py` - Script principal (usa catastro-api.es)
- `spike-data-validation/scripts/catastro_client.py` - Cliente para catastro-api.es
- `spike-data-validation/scripts/catastro_oficial_client.py` - Cliente para servicio oficial
- `spike-data-validation/scripts/check_issue_200_ready.py` - Verificación de requisitos

---

**Última actualización**: 2025-12-17  
**Autor**: Equipo A - Data Infrastructure


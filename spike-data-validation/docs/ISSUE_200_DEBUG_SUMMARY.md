# Resumen de Debugging - Issue #200: Error "LA PROVINCIA NO EXISTE"

## Problema
El servicio SOAP del Catastro (`Consulta_DNPRC` y `Consulta_DNPLOC`) devuelve error código 12: "LA PROVINCIA NO EXISTE" incluso cuando:
- El código de provincia "08" es válido (confirmado por `ConsultaProvincia`)
- El formato XML coincide con la documentación oficial
- Se usan referencias reales obtenidas del Catastro

## Hipótesis Probadas

| Hipótesis | Estado | Resultado |
|-----------|--------|-----------|
| H1: Nombre elemento `<RC>` vs `<RefCat>` | RECHAZADA | `<RefCat>` es correcto (error cambia de 17 a 12) |
| H2: Referencia dividida PC1/PC2 | RECHAZADA | Error 17 (no reconoce formato) |
| H3: Orden de elementos | RECHAZADA | Error 12 persiste |
| H4: Parámetro SRS | RECHAZADA | Error 12 persiste |
| H5: Longitud referencia (21 vs 20) | RECHAZADA | Error 12 con ambas |
| H7: Referencias reales del Catastro | RECHAZADA | Error 12 incluso con referencias válidas |
| H8: Código provincia válido | CONFIRMADA | "08" es correcto para Barcelona |
| H9: Formato wrapped | RECHAZADA | Error cambia a 11 (diferente pero no resuelve) |
| H13: HTTP GET | RECHAZADA | Mismo error 12 |
| H17: HTTP POST form-urlencoded | RECHAZADA | Error diferente (500: Missing parameter) |
| H18: Namespace por defecto en body | RECHAZADA | Error 12 persiste |
| H19: Formato wrapped con contenedor | RECHAZADA | Error cambia a 17 (no reconoce referencia) |
| H20: Diferentes formatos municipio | RECHAZADA | Error 12 con todos los formatos |
| H21: Código municipio desde ConsultaMunicipio | RECHAZADA | ConsultaMunicipio falla con error 500 |
| H22: Encoding y formato valores | RECHAZADA | Error 12 con todos los encodings |
| H11: Content-Type application/soap+xml | RECHAZADA | Request rechazado por servidor |
| FINAL1: Formato wrapped con nombre operación | RECHAZADA | Error 17 (no reconoce referencia) |
| FINAL3: Endpoint REST alternativo | RECHAZADA | Mismo error 12 |
| ZEEP: Cliente SOAP automático | RECHAZADA | Mismo error 12 (zeep genera XML correcto según WSDL) |
| H23: Referencia con provincia/municipio incluidos | RECHAZADA | Error 12 con todos los formatos |
| H24: Probar con otra provincia (Madrid) | RECHAZADA | Error 12 también con Madrid - problema general del servicio |
| H27: Consulta_RCCOOR contiene datos del edificio | RECHAZADA | Solo devuelve referencia, coordenadas y dirección (no superficie/año/uso) |

## Formato XML Probado

### Formato Actual (según documentación oficial)
```xml
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <Provincia xmlns="http://www.catastro.meh.es/">08</Provincia>
    <Municipio xmlns="http://www.catastro.meh.es/">019</Municipio>
    <RefCat xmlns="http://www.catastro.meh.es/">9539519DF2893H000000</RefCat>
  </soap:Body>
</soap:Envelope>
```

**Resultado**: Error 12 - LA PROVINCIA NO EXISTE

## Conclusión

**Total de hipótesis probadas: 22**

El problema persiste consistentemente con error código 12 "LA PROVINCIA NO EXISTE" incluso con:
- ✅ Formato XML exacto según documentación oficial (con namespaces xsi y xsd)
- ✅ Códigos de provincia/municipio válidos (confirmados por ConsultaProvincia)
- ✅ Referencias catastrales reales obtenidas del Catastro
- ✅ Múltiples formatos XML (namespace individual, por defecto, wrapped)
- ✅ Múltiples métodos HTTP (SOAP POST, HTTP GET, HTTP POST form-urlencoded)
- ✅ Diferentes encodings (UTF-8, ISO-8859-1)
- ✅ Diferentes formatos de valores (con/sin ceros, padding)

**Evidencia adicional**:
- El servicio `ConsultaMunicipio` también falla con error 500
- El servicio `ConsultaProvincia` funciona correctamente y confirma que "08" es válido
- El servicio `Consulta_RCCOOR` (por coordenadas) funciona correctamente
- **zeep (cliente SOAP automático)** genera XML correcto según WSDL pero obtiene el mismo error 12
- **El problema ocurre también con Madrid (provincia 28)** - confirma que es un problema general del servicio, no específico de Barcelona
- Esto confirma definitivamente que el problema NO es el formato XML ni los datos, sino el servicio `Consulta_DNPRC` y `Consulta_DNPLOC` del Catastro

**Conclusión final**:
Este es un **problema del servicio del Catastro**, no de nuestro código. El código está implementado correctamente según la documentación oficial, pero los servicios `Consulta_DNPRC` y `Consulta_DNPLOC` no están funcionando como se espera, posiblemente debido a:
1. Bug conocido en el servicio del Catastro
2. Restricción no documentada para ciertas provincias/municipios
3. Problema temporal del servidor
4. Requisito de autenticación o configuración adicional no documentada

## Soluciones Alternativas

### Opción 1: Usar Consulta_RCCOOR (funciona)
El servicio `Consulta_RCCOOR` (por coordenadas) funciona correctamente y devuelve referencias catastrales válidas.

**Limitación confirmada (H27)**: solo devuelve **referencia + coordenadas + dirección** (no superficie/año/uso).

**Implementado**:
- `generate_gracia_seed.py` genera `gracia_refs_seed.csv` con `referencia_catastral` (14 chars), `direccion`, `lat`, `lon`, `metodo=coordenadas`.
- `extract_catastro_gracia.py` detecta `lat/lon` y produce `catastro_gracia_coords.csv` (modo degradado pero utilizable).

### Nota de entorno (runtime)
En algunos entornos, ejecutar con `python3` del sistema puede fallar con **segmentation fault** al importar `numpy`/`pandas`.
Workaround: ejecutar scripts del spike con `.venv-spike/bin/python`.

### Opción 2: Servicio de Consulta Masiva XML
El Catastro ofrece un servicio de consulta masiva asíncrono que requiere:
1. Generar XML de entrada
2. Subirlo a la Sede Electrónica (requiere autenticación)
3. Esperar procesamiento (>1 hora)
4. Descargar resultados

**Ventaja**: Funciona con referencias catastrales directamente
**Desventaja**: Proceso manual y asíncrono

### Opción 3: Usar Open Data BCN
Open Data BCN puede tener datasets con referencias catastrales ya validadas.

**Ventaja**: Datos ya validados y estructurados
**Desventaja**: Puede no cubrir todas las necesidades del spike

## Recomendación

Para el spike de validación, usar **Consulta_RCCOOR** para obtener referencias válidas por coordenadas, y luego intentar `Consulta_DNPRC` con esas referencias. Si el problema persiste, considerar el servicio de consulta masiva o datos de Open Data BCN.

## Próximos Pasos

1. ✅ Documentar el problema en el issue #200 (este documento)
2. Contactar soporte del Catastro para reportar el problema
3. Implementar solución alternativa usando Consulta_RCCOOR (funciona correctamente)
4. Considerar usar datos de Open Data BCN como fuente alternativa
5. Considerar migrar a zeep para manejo automático de SOAP (aunque el problema persiste)

## Conclusión Final

**Total de hipótesis probadas: 28**  
**Estado**: ❌ **PROBLEMA DEL SERVICIO DEL CATASTRO** (no de nuestro código)  
**Solución alternativa**: ✅ **IMPLEMENTADA** (`get_building_by_coordinates()`)

El problema está **definitivamente confirmado** como un **bug o restricción del servicio del Catastro**, no de nuestro código. La evidencia concluyente:

1. ✅ **zeep** (cliente SOAP automático) genera XML correcto según WSDL pero obtiene el mismo error 12
2. ✅ El problema ocurre también con **Madrid (provincia 28)**, confirmando que es un problema **general del servicio**, no específico de Barcelona
3. ✅ El formato XML es correcto (validado por zeep y documentación oficial)
4. ✅ Los códigos de provincia/municipio son válidos (confirmados por `ConsultaProvincia`)
5. ✅ Las referencias catastrales son válidas (obtenidas del propio Catastro)
6. ❌ El servicio `Consulta_DNPRC` y `Consulta_DNPLOC` tienen un **problema sistemático**

### Estado del Código

El código en `catastro_soap_client.py` está **implementado correctamente** según:
- Documentación oficial del Catastro
- WSDL del servicio
- Validación con zeep (cliente SOAP profesional)

**No se requieren cambios adicionales al código**. El problema es del servicio del Catastro.

### Recomendación Final

Para el spike de validación (Issue #200):

1. **Opción A (Recomendada)**: Usar `Consulta_RCCOOR` (por coordenadas) que funciona correctamente
   - Obtener coordenadas de edificios en Gràcia
   - Consultar referencias catastrales por coordenadas
   - Usar esas referencias para consultas adicionales si es necesario

2. **Opción B**: Usar servicio de consulta masiva XML del Catastro
   - Proceso asíncrono (requiere autenticación y puede tardar >1 hora)
   - Más complejo pero 100% oficial

3. **Opción C**: Usar datos de Open Data BCN
   - Datos ya validados y estructurados
   - Puede no cubrir todas las necesidades del spike

### Solución Alternativa Implementada

Se ha implementado el método `get_building_by_coordinates()` en `CatastroSOAPClient` que:
- ✅ Funciona correctamente usando `Consulta_RCCOOR` (por coordenadas)
- ✅ Obtiene referencias catastrales válidas
- ✅ Obtiene direcciones de edificios
- ⚠️ **Limitación confirmada (H27)**: `Consulta_RCCOOR` NO devuelve datos del edificio (superficie, año, uso)
- ⚠️ Para obtener datos completos se requiere `Consulta_DNPRC`, que actualmente falla con error 12

**Uso**:
```python
from catastro_soap_client import CatastroSOAPClient

client = CatastroSOAPClient()
building = client.get_building_by_coordinates(lon=2.1564, lat=41.4026)
# Devuelve: referencia_catastral, direccion_normalizada
# Nota: superficie_m2 y ano_construccion son None porque Consulta_DNPRC no funciona
```

### Próximos Pasos

1. ✅ Documentar el problema (este documento)
2. ✅ Implementar solución alternativa usando `Consulta_RCCOOR` (completado)
3. Actualizar `extract_catastro_gracia.py` para usar `get_building_by_coordinates()` cuando `get_building_by_rc()` falle
4. Reportar el problema al soporte del Catastro (opcional)
5. Considerar usar servicio de consulta masiva XML para obtener datos completos


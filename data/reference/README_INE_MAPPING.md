# Mapeo de Códigos INE para Barrios de Barcelona

**Fecha de creación**: 2025-12-14  
**Archivo**: `data/reference/barrio_ine_mapping.json`

---

## 📌 Descripción

Este archivo contiene el mapeo entre `barrio_id` (identificador interno) y códigos INE para los 73 barrios de Barcelona.

## ⚠️ Nota Importante

**El INE (Instituto Nacional de Estadística) NO tiene códigos oficiales para barrios**. Los barrios son divisiones administrativas del Ajuntament de Barcelona, no del INE.

El INE solo proporciona códigos para:
- Provincias (ej: 08 para Barcelona)
- Municipios (ej: 08019 para Barcelona ciudad)

## 🔢 Formato de Códigos

Para facilitar el matching con datos del INE y otras fuentes, hemos creado códigos compuestos siguiendo este formato:

```
08019 + codi_barri
```

Donde:
- `08019` = Código INE del municipio de Barcelona
- `codi_barri` = Código oficial del barrio según el Ajuntament (01-73)

**Ejemplos**:
- Barrio 1 (el Raval): `0801901`
- Barrio 2 (el Barri Gòtic): `0801902`
- Barrio 10 (Sant Antoni): `0801910`

## 📁 Estructura del Archivo

```json
{
  "1": "0801901",
  "2": "0801902",
  ...
  "73": "0801973"
}
```

- **Key**: `barrio_id` (string)
- **Value**: Código INE compuesto (string) o `null` si no disponible

## 🔄 Uso en el Pipeline ETL

El mapeo se carga automáticamente en el pipeline ETL a través de:

```python
from src.etl.migrations import get_ine_codes

ine_codes = get_ine_codes()  # Retorna dict[int, str]
codigo_ine = ine_codes.get(barrio_id)
```

La función `migrate_dim_barrios_if_needed()` actualiza automáticamente el campo `codigo_ine` en `dim_barrios` durante cada ejecución del pipeline.

## ✅ Validación

- ✅ 73/73 barrios tienen código INE (100%)
- ✅ Todos los códigos siguen el formato `08019XXX`
- ✅ Mapeo 1:1 con `codi_barri` del Ajuntament

## 📚 Fuentes

- **Código municipio INE**: [INE - Códigos oficiales](https://www.ine.es/daco/daco42/codmun/codmunmapa.htm)
- **Códigos barrios**: Ajuntament de Barcelona (`codi_barri` en `dim_barrios`)

## 🔄 Actualización

Si se añaden nuevos barrios o cambian los códigos:

1. Actualizar `data/reference/barrio_ine_mapping.json`
2. Ejecutar el pipeline ETL (actualizará automáticamente)
3. Verificar con: `SELECT COUNT(*) FROM dim_barrios WHERE codigo_ine IS NOT NULL`

---

**Última actualización**: 2025-12-14  
**Mantenedor**: Equipo de desarrollo


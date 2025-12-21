# ✅ Formato XML Correcto para Consulta Masiva Catastro

**Fecha**: 19 Diciembre 2025  
**Issue**: #200 (Fase 2)  
**Estado**: ✅ **RESUELTO** - Formato correcto identificado según documentación oficial (Anexo 1, versión 1.5/1.6)

---

## 📋 Solución Implementada

El formato correcto según la documentación oficial del Catastro requiere:

- **Elemento raíz**: `<LISTADATOS>` (obligatorio)
- **Etiquetas obligatorias**: `<FEC>` (fecha), `<FIN>` (finalidad)
- **Estructura**: Cada referencia catastral en un bloque `<DAT>` con `<RC>`

**Error original**:
```
The 'http://www.catastro.meh.es/:CONSULTA' element is not declared.
```

**Causa**: Estábamos usando `<CONSULTA>` como elemento raíz, cuando el esquema requiere `<LISTADATOS>`.

---

## ✅ Formato XML Correcto (Implementado)

El formato correcto según la documentación oficial (Anexo 1) es:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LISTADATOS>
    <FEC>2025-12-19</FEC>
    <FIN>CONSULTA MASIVA DATOS NO PROTEGIDOS</FIN>
    <DAT>
        <RC>8555830DF2885F</RC>
    </DAT>
    <DAT>
        <RC>8552323DF2885D</RC>
    </DAT>
    ...
</LISTADATOS>
```

### Características del Formato Correcto

- **Elemento raíz**: `<LISTADATOS>` (obligatorio, no `<CONSULTA>` ni `<consulta_municipiero>`)
- **Etiquetas obligatorias**:
  - `<FEC>`: Fecha en formato YYYY-MM-DD
  - `<FIN>`: Texto descriptivo de la finalidad
- **Bloques de datos**: Cada referencia catastral en un bloque `<DAT>` con `<RC>`
- **Referencias catastrales**: Pueden tener 14, 18 o 20 caracteres
  - Si se usa RC de 14 posiciones, el sistema devuelve todos los inmuebles de esa finca

---

## 🧪 Variantes Obsoletas (Histórico)

**NOTA**: Las siguientes variantes ya no son necesarias. Se mantienen solo como referencia histórica del proceso de debugging.

Se habían generado **4 variantes** del XML para probar cuál acepta la Sede (todas incorrectas):

### Variante 1: Básica (sin schemaLocation)
**Archivo**: `consulta_masiva_entrada_variant1_basic.xml`

```xml
<?xml version="1.0" ?>
<CONSULTA xmlns="http://www.catastro.meh.es/">
  <RC>8555830DF2885F</RC>
  ...
</CONSULTA>
```

**Características**:
- Namespace básico `xmlns="http://www.catastro.meh.es/"`
- Sin declaración de esquema
- Elemento raíz: `CONSULTA`

---

### Variante 2: Con schemaLocation
**Archivo**: `consulta_masiva_entrada_variant2_with_schema.xml`

```xml
<?xml version="1.0" ?>
<CONSULTA xmlns="http://www.catastro.meh.es/" 
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://www.catastro.meh.es/ http://www.catastro.meh.es/ConsultaMasiva.xsd">
  <RC>8555830DF2885F</RC>
  ...
</CONSULTA>
```

**Características**:
- Namespace con `xsi:schemaLocation` explícito
- Referencia a esquema XSD (puede que no exista públicamente)

---

### Variante 3: Sin namespace
**Archivo**: `consulta_masiva_entrada_variant3_no_namespace.xml`

```xml
<?xml version="1.0" ?>
<CONSULTA>
  <RC>8555830DF2885F</RC>
  ...
</CONSULTA>
```

**Características**:
- Sin namespace (namespace por defecto vacío)
- Formato más simple

---

### Variante 4: Con elemento wrapper (basado en error)
**Archivo**: `consulta_masiva_entrada_variant4_wrapper.xml`

```xml
<?xml version="1.0" ?>
<consulta_municipiero xmlns="http://www.catastro.meh.es/">
  <CONSULTA>
    <RC>8555830DF2885F</RC>
    ...
  </CONSULTA>
</consulta_municipiero>
```

**Características**:
- Elemento raíz: `consulta_municipiero` (basado en el error que mencionaba este elemento)
- `CONSULTA` como elemento hijo
- Namespace en el elemento raíz

---

## 📝 Instrucciones de Uso

### Paso 1: Generar XML con Formato Correcto
El script `download_catastro_massive.py` ya genera el XML con el formato correcto:

```bash
python3 spike-data-validation/scripts/fase2/download_catastro_massive.py
```

Esto genera `consulta_masiva_entrada.xml` con el formato `<LISTADATOS>` correcto.

### Paso 2: Subir a la Sede Electrónica
1. Accede a la Sede Electrónica: https://www1.sedecatastro.gob.es
2. Ve a "Enviar consulta masiva de datos NO protegidos"
3. Sube: `consulta_masiva_entrada.xml`
4. **El sistema debería aceptar el XML** ✅

### Paso 3: Esperar y Descargar Resultados
1. Espera el procesamiento (1-2 horas)
2. Recibirás notificación por email cuando esté listo
3. Descarga el XML de salida desde la Sede
4. Guarda el XML en: `spike-data-validation/data/raw/catastro_oficial/`

---

## 🔧 Implementación del Código

El código ya está actualizado en `catastro_oficial_client.py`:

```python
def generate_input_xml(self, referencias_catastrales, ...):
    # Elemento raíz OBLIGATORIO: LISTADATOS
    root = ET.Element("LISTADATOS")
    
    # Etiquetas obligatorias
    fec_element = ET.SubElement(root, "FEC")
    fec_element.text = fecha  # YYYY-MM-DD
    
    fin_element = ET.SubElement(root, "FIN")
    fin_element.text = finalidad  # Texto descriptivo
    
    # Cada referencia en bloque DAT con RC
    for ref in referencias_catastrales:
        dat_element = ET.SubElement(root, "DAT")
        rc_element = ET.SubElement(dat_element, "RC")
        rc_element.text = ref.strip()
    
    # ... resto del código
```

---

## 📊 Estado de Implementación

| Componente | Estado | Notas |
|-------------|--------|-------|
| Formato XML correcto | ✅ Implementado | Usa `<LISTADATOS>` según Anexo 1 |
| Generación automática | ✅ Funcional | Script `download_catastro_massive.py` |
| Validación de referencias | ✅ Implementada | Acepta 14, 18 o 20 caracteres |
| Etiquetas obligatorias | ✅ Incluidas | `<FEC>` y `<FIN>` automáticas |
| Documentación | ✅ Actualizada | Este documento refleja el formato correcto |

---

## 📚 Referencias

- **Documentación oficial**: Anexo 1, versión 1.5/1.6 del Catastro
- **Sede Electrónica**: https://www1.sedecatastro.gob.es
- **Ayuda consulta masiva**: https://www.catastro.hacienda.gob.es/ayuda/masiva/Ayuda_Masiva.htm

## ✅ Verificación

Para verificar que el XML generado es correcto:

1. **Estructura**: Debe tener `<LISTADATOS>` como elemento raíz
2. **Etiquetas obligatorias**: Debe incluir `<FEC>` y `<FIN>`
3. **Bloques de datos**: Cada referencia en `<DAT><RC>...</RC></DAT>`
4. **Encoding**: UTF-8 explícito en la declaración XML

Ejemplo de verificación:
```bash
# Verificar estructura básica
head -10 spike-data-validation/data/raw/catastro_oficial/consulta_masiva_entrada.xml
```

---

## 📁 Archivos Relacionados

- `spike-data-validation/scripts/catastro_oficial_client.py` - Cliente que genera las variantes
- `spike-data-validation/scripts/fase2/download_catastro_massive.py` - Script que ejecuta la generación
- `spike-data-validation/data/raw/catastro_oficial/` - Directorio con todos los XMLs generados

---

**Última actualización**: 2025-12-19  
**Autor**: Equipo A - Data Infrastructure


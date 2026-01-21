# Troubleshooting: Looker Studio CSV Upload Issues

## Problema: Encabezados Incorrectos Detectados

Si Looker Studio muestra encabezados incorrectos al subir un CSV:

### Solución 1: Verificar que Subiste el Archivo Correcto

Asegúrate de subir el archivo correcto:
- **Para barrios**: `01_dimensions/dim_barrios.csv`
- **Para tiempo**: `01_dimensions/dim_tiempo.csv`

### Solución 2: Re-exportar con Formato Limpio

Los archivos han sido re-exportados con formato UTF-8 estándar (sin BOM) para mejor compatibilidad:

```bash
python scripts/export_data_for_looker_studio.py
```

Luego descarga y re-sube los archivos.

### Solución 3: Verificar Encabezados Manualmente

Antes de subir, verifica los encabezados:

```bash
# Ver encabezados de dim_barrios
head -1 data/exports/looker_studio/01_dimensions/dim_barrios.csv

# Debería mostrar:
# barrio_id,barrio_nombre,barrio_nombre_normalizado,distrito_id,distrito_nombre,...
```

### Solución 4: Editar CSV Manualmente (Si es Necesario)

Si Looker Studio sigue detectando encabezados incorrectos:

1. Abre el CSV en Excel o un editor de texto
2. Verifica que la primera línea tiene los encabezados correctos
3. Guarda como CSV UTF-8 (sin BOM)
4. Re-sube a Looker Studio

### Solución 5: Usar "Skip header rows" en Looker Studio

Si Looker Studio detecta encabezados incorrectos:

1. En Looker Studio, al subir el archivo
2. Busca la opción **"Skip header rows"** o **"First row is header"**
3. Asegúrate de que está configurado correctamente
4. O manualmente especifica que la primera fila son encabezados

## Encabezados Esperados por Archivo

### dim_barrios.csv
```
barrio_id,barrio_nombre,barrio_nombre_normalizado,distrito_id,distrito_nombre,municipio,ambito,codi_districte,codi_barri,geometry_json,source_dataset,etl_created_at,etl_updated_at,codigo_ine,centroide_lat,centroide_lon,area_km2
```

### dim_tiempo.csv
```
time_id,anio,trimestre,mes,periodo,year_quarter,year_month,es_fin_de_semana,es_verano,estacion,dia_semana,fecha_inicio,fecha_fin
```

### fact_precios.csv
```
id,barrio_id,anio,periodo,trimestre,precio_m2_venta,precio_mes_alquiler,dataset_id,source,etl_loaded_at
```

## Verificar Archivos Exportados

```bash
# Ver encabezados de todos los archivos principales
head -1 data/exports/looker_studio/01_dimensions/dim_barrios.csv
head -1 data/exports/looker_studio/01_dimensions/dim_tiempo.csv
head -1 data/exports/looker_studio/02_market/fact_precios.csv
```

## Si el Problema Persiste

1. **Descarga el archivo nuevamente** desde `data/exports/looker_studio/`
2. **Abre en Excel** y verifica que los encabezados son correctos
3. **Guarda como CSV UTF-8** desde Excel
4. **Re-sube a Looker Studio**

O contacta con el error específico que muestra Looker Studio.

---

**Última actualización**: 2026-01-10

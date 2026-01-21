# Tabla Maestra para Looker Studio ✅

## Resumen

He creado una **tabla maestra consolidada** que combina todos los datos principales en un solo archivo CSV. Esto hace que sea mucho más fácil usar en Looker Studio sin necesidad de hacer blends complejos.

## Archivo Creado

**`data/exports/looker_studio/master_table_barcelona_housing.csv`**

- **Filas**: 1,014 (73 barrios × ~14 años)
- **Columnas**: 34
- **Tamaño**: 271 KB
- **Rango temporal**: 2012-2025

## Contenido

La tabla maestra incluye:

✅ **Información de barrios** (nombres, distritos, coordenadas)  
✅ **Precios** (venta y alquiler por año)  
✅ **Demografía** (población, género, edad, nacionalidad)  
✅ **Renta** (mediana, promedio)  
✅ **Turismo** (establecimientos, intensidad)  
✅ **Seguridad** (tasa de criminalidad, delitos)  
✅ **Calidad ambiental** (aire, ruido)  
✅ **Educación** (centros educativos)  
✅ **Movilidad** (metro, bus)  
✅ **Métricas calculadas** (densidad, affordability)

## Ventajas

1. ✅ **Un solo archivo** - No necesitas hacer blends
2. ✅ **Fácil de usar** - Sube y listo
3. ✅ **Datos consolidados** - Todo en un lugar
4. ✅ **Optimizado** - Solo datos relevantes

## Cómo Usar

1. **Sube el archivo** a Looker Studio:
   - `data/exports/looker_studio/master_table_barcelona_housing.csv`

2. **Crea visualizaciones directamente**:
   - Precio por distrito
   - Evolución temporal
   - Correlaciones
   - Mapas

3. **No necesitas blends** - Todo está en una tabla

## Actualizar

Cuando actualices la base de datos:

```bash
python scripts/create_master_table_for_looker.py
```

Luego re-sube el archivo actualizado.

## Documentación

- `data/exports/looker_studio/MASTER_TABLE_GUIDE.md` - Guía completa de uso
- `data/exports/looker_studio/master_table_barcelona_housing.csv` - El archivo

---

**✅ Listo para usar**: Sube `master_table_barcelona_housing.csv` a Looker Studio y empieza a crear visualizaciones inmediatamente.

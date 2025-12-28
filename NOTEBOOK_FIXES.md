# Correcciones para el Notebook de EDA

## 🔧 ERRORES ENCONTRADOS Y SOLUCIONES

### **Error 1: Nombres de columnas incorrectos**

**Problema:** El notebook usa nombres de columnas que no existen en la base de datos.

**Columnas incorrectas → Columnas correctas:**

| Tabla                 | Columna Incorrecta  | Columna Correcta   |
| --------------------- | ------------------- | ------------------ |
| `fact_renta_avanzada` | `renta_bruta_media` | `renta_bruta_llar` |

---

## ✅ SOLUCIONES RÁPIDAS

### **Opción 1: Editar manualmente en el notebook**

En la celda que da error, cambia:

```python
# ❌ INCORRECTO
display(fact_renta_avanzada[['renta_bruta_media', 'indice_gini', 'ratio_p80_p20']].describe())

# ✅ CORRECTO
display(fact_renta_avanzada[['renta_bruta_llar', 'indice_gini', 'ratio_p80_p20']].describe())
```

### **Opción 2: Ver todas las columnas disponibles**

Ejecuta esto en una celda para ver qué columnas tienes:

```python
print("Columnas de fact_renta_avanzada:")
print(fact_renta_avanzada.columns.tolist())
```

---

## 📋 COLUMNAS CORRECTAS POR TABLA

### **fact_renta_avanzada:**

- `id`
- `barrio_id`
- `anio`
- `renta_bruta_llar` ← **Usar esta**
- `indice_gini`
- `ratio_p80_p20`
- `dataset_id`
- `source`
- `etl_loaded_at`

### **fact_precios:**

- `barrio_id`
- `anio`
- `precio_m2_venta`
- `precio_mes_alquiler`

### **fact_hogares_avanzado:**

- `barrio_id`
- `anio`
- `num_hogares_con_menores`
- `promedio_personas_por_hogar`
- `pct_presencia_mujeres`
- `pct_hogares_nacionalidad_extranjera`

### **fact_catastro_avanzado:**

- `barrio_id`
- `anio`
- `num_propietarios_fisica`
- `num_propietarios_juridica`
- `pct_propietarios_extranjeros`
- `superficie_media_m2`
- `antiguedad_media_bloque`

---

## 🔍 OTROS POSIBLES ERRORES

Si encuentras más errores similares, busca y reemplaza:

1. `renta_bruta_media` → `renta_bruta_llar`
2. Verifica siempre los nombres de columnas con `.columns`

---

## 💡 CÓDIGO DE AYUDA

Ejecuta esto al inicio del notebook para verificar todas las columnas:

```python
# Verificar columnas de todas las tablas
print("="*80)
print("COLUMNAS DISPONIBLES EN CADA TABLA")
print("="*80)

print("\n📊 fact_precios:")
print(fact_precios.columns.tolist())

print("\n💰 fact_renta_avanzada:")
print(fact_renta_avanzada.columns.tolist())

print("\n🏠 fact_hogares_avanzado:")
print(fact_hogares_avanzado.columns.tolist())

print("\n🏛️ fact_catastro_avanzado:")
print(fact_catastro_avanzado.columns.tolist())
```

---

**Última actualización:** 28 de diciembre de 2024

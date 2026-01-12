#!/usr/bin/env python3
"""
Generate improved visualization code for the notebook.

This script creates code cells with:
- Dashed lines for missing data
- Tooltips with completeness info
- Option to use smoothed data
"""

improved_visualization_code = '''
# ============================================================================
# VISUALIZACIONES MEJORADAS: Líneas Temporales con Calidad de Datos
# ============================================================================

# Cargar datos suavizados si están disponibles
df_smoothed_path = PROJECT_ROOT / "data" / "exports" / "looker_studio" / "master_table_barcelona_housing_smoothed.csv"
use_smoothed = False

if df_smoothed_path.exists():
    df_smoothed = pd.read_csv(df_smoothed_path)
    df_smoothed.columns = df_smoothed.columns.str.replace(' ', '_').str.lower().str.strip()
    use_smoothed = True
    print("✅ Datos suavizados disponibles - se usarán para líneas principales")
else:
    print("⚠️ Datos suavizados no disponibles - usando datos originales")
    df_smoothed = df.copy()

# Función auxiliar para plotear con líneas discontinuas para datos faltantes
def plot_with_missing_data(ax, x, y, missing_mask, label, color, linestyle='-', 
                           marker='o', linewidth=2, markersize=6, alpha=0.7):
    """
    Plotea línea temporal con líneas discontinuas para datos faltantes.
    
    Args:
        ax: Eje matplotlib
        x: Valores de x (años)
        y: Valores de y (precios/variables)
        missing_mask: Máscara booleana indicando datos faltantes
        label: Etiqueta de la línea
        color: Color de la línea
        linestyle: Estilo de línea para datos válidos
        marker: Marcador
        linewidth: Grosor de línea
        markersize: Tamaño de marcador
        alpha: Transparencia
    """
    if len(x) == 0 or len(y) == 0:
        return
    
    # Convertir a arrays numpy
    x = np.array(x)
    y = np.array(y)
    missing_mask = np.array(missing_mask) if missing_mask is not None else np.zeros(len(x), dtype=bool)
    
    # Separar datos válidos y faltantes
    valid_mask = ~missing_mask & ~np.isnan(y)
    
    if valid_mask.sum() == 0:
        return
    
    # Plotear datos válidos con línea continua
    x_valid = x[valid_mask]
    y_valid = y[valid_mask]
    
    if len(x_valid) > 1:
        # Identificar segmentos continuos
        segments = []
        current_segment = [x_valid[0], y_valid[0]]
        
        for i in range(1, len(x_valid)):
            if x_valid[i] == x_valid[i-1] + 1:  # Años consecutivos
                current_segment.append(x_valid[i])
                current_segment.append(y_valid[i])
            else:
                # Gap detectado - guardar segmento actual y empezar nuevo
                if len(current_segment) >= 4:
                    segments.append(current_segment)
                current_segment = [x_valid[i], y_valid[i]]
        
        # Agregar último segmento
        if len(current_segment) >= 4:
            segments.append(current_segment)
        
        # Plotear cada segmento
        for seg in segments:
            x_seg = seg[::2]  # Años
            y_seg = seg[1::2]  # Valores
            ax.plot(x_seg, y_seg, linestyle=linestyle, marker=marker, 
                   color=color, linewidth=linewidth, markersize=markersize, 
                   alpha=alpha, label=label if seg == segments[0] else '')
    
    # Plotear puntos individuales para datos válidos aislados
    isolated_valid = valid_mask.copy()
    if len(x_valid) > 0:
        for i in range(len(x_valid)):
            if i == 0 or x_valid[i] != x_valid[i-1] + 1:
                if i == len(x_valid) - 1 or x_valid[i+1] != x_valid[i] + 1:
                    isolated_valid[np.where(valid_mask)[0][i]] = True
    
    x_isolated = x[isolated_valid]
    y_isolated = y[isolated_valid]
    if len(x_isolated) > 0:
        ax.scatter(x_isolated, y_isolated, color=color, s=markersize*20, 
                  alpha=alpha, zorder=5)

# Crear visualizaciones mejoradas
print("=" * 80)
print("VISUALIZACIONES MEJORADAS: Líneas Temporales con Indicadores de Calidad")
print("=" * 80)

# Seleccionar barrios para visualización (top 5 por precio promedio)
top_barrios = df.groupby('barrio_nombre')['precio_m2_venta_promedio'].mean().nlargest(5).index.tolist()

# Crear figura con subplots
fig, axes = plt.subplots(3, 2, figsize=(20, 18))

# 1. Evolución de precios con datos faltantes marcados
ax = axes[0, 0]
for barrio in top_barrios:
    barrio_data = df[df['barrio_nombre'] == barrio].sort_values('anio')
    
    # Usar datos suavizados si están disponibles
    if use_smoothed and 'precio_m2_venta_promedio_smoothed' in df_smoothed.columns:
        barrio_smoothed = df_smoothed[df_smoothed['barrio_nombre'] == barrio].sort_values('anio')
        if len(barrio_smoothed) > 0:
            # Línea suavizada (principal)
            ax.plot(barrio_smoothed['anio'], barrio_smoothed['precio_m2_venta_promedio_smoothed'],
                   linestyle='-', linewidth=3, alpha=0.5, color='gray',
                   label=f'{barrio} (suavizado)' if barrio == top_barrios[0] else '')
    
    # Línea con datos faltantes marcados
    missing_mask = barrio_data.get('precio_venta_faltante', pd.Series([0]*len(barrio_data))) == 1
    interpolated_mask = barrio_data.get('dato_interpolado', pd.Series([0]*len(barrio_data))) == 1
    
    plot_with_missing_data(ax, barrio_data['anio'], barrio_data['precio_m2_venta_promedio'],
                          missing_mask, barrio, 
                          color=plt.cm.tab10(top_barrios.index(barrio)),
                          linestyle='--' if interpolated_mask.any() else '-',
                          marker='o' if not interpolated_mask.any() else 's')

ax.set_xlabel('Año', fontsize=12)
ax.set_ylabel('Precio Venta (€/m²)', fontsize=12)
ax.set_title('Evolución de Precios (Top 5 Barrios) - Líneas Discontinuas = Datos Faltantes', 
             fontsize=14, fontweight='bold')
ax.legend(loc='best', fontsize=9)
ax.grid(True, alpha=0.3)

# 2. Completitud de datos por barrio y año (heatmap)
ax = axes[0, 1]
completitud_pivot = df.pivot_table(
    index='barrio_nombre', 
    columns='anio', 
    values='completitud_datos',
    aggfunc='mean'
)
# Seleccionar solo top barrios
completitud_pivot = completitud_pivot.loc[top_barrios]
sns.heatmap(completitud_pivot, annot=True, fmt='.0f', cmap='RdYlGn', 
           ax=ax, cbar_kws={'label': 'Completitud (%)'}, vmin=0, vmax=100)
ax.set_title('Completitud de Datos por Barrio y Año', fontsize=14, fontweight='bold')
ax.set_xlabel('Año', fontsize=12)
ax.set_ylabel('Barrio', fontsize=12)

# 3. Evolución temporal a nivel ciudad con tooltips de completitud
ax = axes[1, 0]
city_timeline = df.groupby('anio').agg({
    'precio_m2_venta_promedio': 'mean',
    'completitud_datos': 'mean',
    'precio_venta_faltante': lambda x: (x == 1).sum() / len(x) * 100
}).reset_index()

# Plotear línea principal
ax.plot(city_timeline['anio'], city_timeline['precio_m2_venta_promedio'],
       'o-', linewidth=3, markersize=10, color='steelblue', label='Precio Promedio')

# Agregar tooltips (anotaciones) con completitud
for idx, row in city_timeline.iterrows():
    ax.annotate(f"{row['completitud_datos']:.0f}%",
               xy=(row['anio'], row['precio_m2_venta_promedio']),
               xytext=(5, 5), textcoords='offset points',
               fontsize=8, alpha=0.7,
               bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.5))

ax.set_xlabel('Año', fontsize=12)
ax.set_ylabel('Precio Venta Promedio (€/m²)', fontsize=12)
ax.set_title('Evolución de Precios a Nivel Ciudad (Tooltips = Completitud %)', 
             fontsize=14, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3)

# 4. Porcentaje de datos faltantes por año
ax = axes[1, 1]
missing_by_year = df.groupby('anio').agg({
    'precio_venta_faltante': 'mean',
    'precio_alquiler_faltante': 'mean',
    'demografia_faltante': 'mean'
}).reset_index()

x = missing_by_year['anio']
width = 0.25
ax.bar(x - width, missing_by_year['precio_venta_faltante'] * 100, width, 
      label='Precio Venta', color='steelblue', alpha=0.7)
ax.bar(x, missing_by_year['precio_alquiler_faltante'] * 100, width,
      label='Precio Alquiler', color='orange', alpha=0.7)
ax.bar(x + width, missing_by_year['demografia_faltante'] * 100, width,
      label='Demografía', color='green', alpha=0.7)

ax.set_xlabel('Año', fontsize=12)
ax.set_ylabel('% de Datos Faltantes', fontsize=12)
ax.set_title('Evolución de Datos Faltantes por Tipo', fontsize=14, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3, axis='y')

# 5. Comparación datos originales vs suavizados (si disponibles)
ax = axes[2, 0]
if use_smoothed and 'precio_m2_venta_promedio_smoothed' in df_smoothed.columns:
    city_smoothed = df_smoothed.groupby('anio')['precio_m2_venta_promedio_smoothed'].mean().reset_index()
    
    ax.plot(city_timeline['anio'], city_timeline['precio_m2_venta_promedio'],
           'o-', linewidth=2, markersize=8, color='steelblue', 
           label='Datos Originales', alpha=0.7)
    ax.plot(city_smoothed['anio'], city_smoothed['precio_m2_venta_promedio_smoothed'],
           's-', linewidth=3, markersize=8, color='red', 
           label='Datos Suavizados (3 años)', alpha=0.8)
    
    ax.set_xlabel('Año', fontsize=12)
    ax.set_ylabel('Precio Venta Promedio (€/m²)', fontsize=12)
    ax.set_title('Comparación: Datos Originales vs Suavizados', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
else:
    ax.text(0.5, 0.5, 'Datos suavizados no disponibles\\nEjecuta: python scripts/add_smoothed_data_to_master.py',
           ha='center', va='center', transform=ax.transAxes, fontsize=12)
    ax.set_title('Datos Suavizados', fontsize=14, fontweight='bold')

# 6. Distribución de completitud de datos
ax = axes[2, 1]
completitud_dist = df['completitud_datos'].dropna()
ax.hist(completitud_dist, bins=30, color='steelblue', alpha=0.7, edgecolor='black')
ax.axvline(completitud_dist.mean(), color='red', linestyle='--', linewidth=2,
          label=f'Media: {completitud_dist.mean():.1f}%')
ax.set_xlabel('Completitud de Datos (%)', fontsize=12)
ax.set_ylabel('Frecuencia', fontsize=12)
ax.set_title('Distribución de Completitud de Datos', fontsize=14, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.show()

print("\\n✅ Visualizaciones mejoradas completadas")
print(f"   • Líneas discontinuas indican datos faltantes")
print(f"   • Tooltips muestran completitud de datos")
print(f"   • Datos suavizados: {'✅ Disponibles' if use_smoothed else '❌ No disponibles'}")
'''

print(improved_visualization_code)

"""
Procesa datos de regulación de alquileres y crea fact_regulacion.

Fuentes:
- Portal de Dades: Precio medio alquiler (Incasòl fianzas) - Dataset b37xv8wcjh
- Open Data BCN: Licencias VUT por barrio (habitatges-us-turistic)
- Datos estáticos: Zonas tensionadas (Decreto-ley 1/2024 Generalitat)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Lista de barrios en zonas tensionadas según Decreto-ley 1/2024 Generalitat
# Todos los barrios de Barcelona están regulados desde 2024
# Fuente: https://portaljuridic.gencat.cat/eli/es-ct/dl/2024/03/12/1
# Por simplificación, asumimos que TODOS los 73 barrios de Barcelona están regulados
BARRIOS_ZONA_TENSIONADA = None  # None = todos los barrios de Barcelona


def _load_portaldades_precio_alquiler(raw_data_path: Path) -> pd.DataFrame:
    """
    Carga datos de precio medio alquiler desde Portal de Dades.
    
    Busca archivos CSV descargados con el ID b37xv8wcjh en el directorio de regulación.
    
    Args:
        raw_data_path: Directorio base donde se encuentran los datos raw
            (por ejemplo, ``data/raw/regulacion`` o ``data/raw/portaldades``).
    
    Returns:
        DataFrame con datos de precio alquiler por barrio.
    """
    # #region agent log
    import json
    import time
    from pathlib import Path as PathLib
    debug_log_path = PathLib(__file__).parent.parent.parent / ".cursor" / "debug.log"
    debug_log_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(debug_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "B",
                "location": "prepare_regulacion.py:_load_portaldades_precio_alquiler",
                "message": "Function entry",
                "data": {"raw_data_path": str(raw_data_path), "exists": raw_data_path.exists()},
                "timestamp": int(time.time() * 1000)
            }) + "\n")
    except Exception:
        pass
    # #endregion
    
    frames: List[pd.DataFrame] = []
    
    # Buscar recursivamente en el directorio y sus subdirectorios
    search_paths = [raw_data_path]
    
    # También buscar en directorio padre si raw_data_path es "regulacion"
    if raw_data_path.name == "regulacion" and raw_data_path.parent.exists():
        search_paths.append(raw_data_path.parent)
    
    # También buscar en portaldades si existe como hermano
    portaldades_sibling = raw_data_path.parent / "portaldades"
    if portaldades_sibling.exists():
        search_paths.append(portaldades_sibling)
    
    csv_files = []
    for search_path in search_paths:
        if not search_path.exists():
            continue
        
        # Buscar recursivamente con **/
        found = sorted(search_path.glob("**/*b37xv8wcjh*.csv"))
        csv_files.extend(found)
        logger.debug("Buscando en %s: encontrados %s archivos", search_path, len(found))
    
    # Eliminar duplicados manteniendo el orden
    csv_files = list(dict.fromkeys(csv_files))
    
    # #region agent log
    try:
        with open(debug_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "B",
                "location": "prepare_regulacion.py:_load_portaldades_precio_alquiler",
                "message": "Files found",
                "data": {
                    "csv_files_count": len(csv_files),
                    "csv_files": [str(p) for p in csv_files],
                    "search_paths": [str(p) for p in search_paths],
                },
                "timestamp": int(time.time() * 1000)
            }) + "\n")
    except Exception:
        pass
    # #endregion
    
    if not csv_files:
        logger.warning(
            "No se encontraron archivos de precio alquiler (b37xv8wcjh) en %s ni en directorios relacionados",
            raw_data_path
        )
        return pd.DataFrame()
    
    for path in csv_files:
        try:
            logger.info("Cargando precio alquiler desde Portal de Dades: %s", path)
            df = pd.read_csv(path, encoding='utf-8')
            # #region agent log
            try:
                with open(debug_log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "B",
                        "location": "prepare_regulacion.py:_load_portaldades_precio_alquiler",
                        "message": "CSV loaded",
                        "data": {
                            "file": str(path),
                            "rows": len(df),
                            "columns": list(df.columns),
                        },
                        "timestamp": int(time.time() * 1000)
                    }) + "\n")
            except Exception:
                pass
            # #endregion
            frames.append(df)
        except Exception as exc:  # noqa: BLE001
            # #region agent log
            try:
                with open(debug_log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "C",
                        "location": "prepare_regulacion.py:_load_portaldades_precio_alquiler",
                        "message": "Error loading CSV",
                        "data": {
                            "file": str(path),
                            "error": str(exc),
                            "error_type": type(exc).__name__,
                        },
                        "timestamp": int(time.time() * 1000)
                    }) + "\n")
            except Exception:
                pass
            # #endregion
            logger.warning("Error leyendo CSV de precio alquiler %s: %s", path, exc)
    
    if not frames:
        logger.warning(
            "No se pudieron cargar archivos de precio alquiler (b37xv8wcjh)"
        )
        return pd.DataFrame()
    
    df = pd.concat(frames, ignore_index=True)
    logger.info("Precio alquiler Portal de Dades: %s registros cargados", len(df))
    
    # #region agent log
    try:
        with open(debug_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "B",
                "location": "prepare_regulacion.py:_load_portaldades_precio_alquiler",
                "message": "Function exit",
                "data": {"total_rows": len(df), "columns": list(df.columns)},
                "timestamp": int(time.time() * 1000)
            }) + "\n")
    except Exception:
        pass
    # #endregion
    
    return df


def _load_vut_licencias(raw_data_path: Path) -> pd.DataFrame:
    """
    Carga datos de licencias VUT desde Open Data BCN.
    
    Args:
        raw_data_path: Directorio base donde se encuentran los datos raw.
    
    Returns:
        DataFrame con licencias VUT por barrio y año.
    """
    # Buscar CSV de licencias VUT (puede estar en regulacion/ o en subdirectorios)
    vut_paths = [
        raw_data_path / "licencias_vut.csv",
        raw_data_path.parent / "regulacion" / "licencias_vut.csv",
    ]
    
    # También buscar recursivamente
    vut_files = list(raw_data_path.glob("**/licencias_vut.csv"))
    if raw_data_path.parent.exists():
        vut_files.extend(raw_data_path.parent.glob("**/licencias_vut.csv"))
    
    vut_path = None
    for path in vut_paths + vut_files:
        if path.exists():
            vut_path = path
            break
    
    if not vut_path or not vut_path.exists():
        logger.debug("Archivo de licencias VUT no encontrado (opcional)")
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(vut_path, encoding='utf-8')
        logger.info("Licencias VUT cargadas: %s registros", len(df))
        return df
    except Exception as exc:  # noqa: BLE001
        logger.warning("Error leyendo licencias VUT %s: %s", vut_path, exc)
        return pd.DataFrame()


def prepare_regulacion(
    raw_data_path: Path,
    barrios_df: pd.DataFrame,
    superficie_media_barrio: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Prepara tabla fact_regulacion desde datos brutos del Portal de Dades.
    
    Calcula métricas adicionales:
    - indice_referencia_alquiler = precio_medio_mensual / m² promedio barrio
    - zona_tensionada = TRUE si barrio está en lista regulada (todos desde 2024)
    - nivel_tension = 'alta' si precio > percentil 75, 'media' si > percentil 50, 'baja' resto
    
    Args:
        raw_data_path: Directorio donde se encuentran los archivos raw de regulación
            (por ejemplo, ``data/raw/regulacion``).
        barrios_df: DataFrame de ``dim_barrios`` con al menos las columnas
            ``barrio_id``, ``codi_barri`` y ``barrio_nombre_normalizado``.
        superficie_media_barrio: Opcional, DataFrame con superficie media por barrio.
            Si no se proporciona, se usa 70 m² como valor por defecto.
    
    Returns:
        DataFrame listo para cargar en ``fact_regulacion`` con columnas:
        - barrio_id
        - anio
        - zona_tensionada (bool)
        - nivel_tension ('alta', 'media', 'baja')
        - indice_referencia_alquiler (€/m²/mes)
        - num_licencias_vut (int)
        - derecho_tanteo (bool)
    
    Raises:
        ValueError: Si faltan columnas clave en ``barrios_df``.
    """
    if barrios_df.empty:
        raise ValueError("barrios_df no puede estar vacío en prepare_regulacion")
    
    required_dim_cols = {"barrio_id", "codi_barri", "barrio_nombre_normalizado"}
    missing_dim = required_dim_cols - set(barrios_df.columns)
    if missing_dim:
        raise ValueError(
            f"Dimensión de barrios incompleta para regulación. Faltan columnas: "
            f"{sorted(missing_dim)}"
        )
    
    # 1. Cargar datos de precio alquiler desde Portal de Dades
    precio_df = _load_portaldades_precio_alquiler(raw_data_path)
    
    # #region agent log
    try:
        with open(debug_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "B",
                "location": "prepare_regulacion.py:295",
                "message": "After loading precio_df",
                "data": {
                    "precio_df_empty": precio_df.empty,
                    "precio_df_rows": len(precio_df),
                    "precio_df_columns": list(precio_df.columns) if not precio_df.empty else [],
                },
                "timestamp": int(time.time() * 1000)
            }) + "\n")
    except Exception:
        pass
    # #endregion
    
    if precio_df.empty:
        logger.warning(
            "Datos de precio alquiler vacíos. Se devolverá DataFrame vacío."
        )
        return pd.DataFrame(
            columns=[
                "barrio_id",
                "anio",
                "zona_tensionada",
                "nivel_tension",
                "indice_referencia_alquiler",
                "num_licencias_vut",
                "derecho_tanteo",
            ]
        )
    
    df = precio_df.copy()
    
    # 2. Normalizar columnas del Portal de Dades
    # Buscar columnas comunes en datasets del Portal de Dades
    columns_lower = {c.lower(): c for c in df.columns}
    
    # #region agent log
    try:
        with open(debug_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "C",
                "location": "prepare_regulacion.py:316",
                "message": "Before column mapping",
                "data": {
                    "df_columns": list(df.columns),
                    "columns_lower_keys": list(columns_lower.keys()),
                },
                "timestamp": int(time.time() * 1000)
            }) + "\n")
    except Exception:
        pass
    # #endregion
    
    # Mapear columnas esperadas
    column_map = {}
    
    # Barrio (puede ser nombre o código)
    # Portal de Dades usa "Dim-01:TERRITORI" para territorio/barrio
    for candidate in ("barri", "barrio", "nom_barri", "barrio_nombre", "dim-01:territori", "territori"):
        if candidate in columns_lower:
            column_map["barrio_nombre"] = columns_lower[candidate]
            break
    
    # Código de barrio
    for candidate in ("codi_barri", "codi_barri_ajuntament", "barri_code", "codi"):
        if candidate in columns_lower:
            column_map["codi_barri"] = columns_lower[candidate]
            break
    
    # Año - Portal de Dades usa "Dim-00:TEMPS" para tiempo
    # Puede contener año completo (2024) o formato trimestral (2024Q1)
    for candidate in ("any", "anio", "year", "año", "dim-00:temps", "temps", "time"):
        if candidate in columns_lower:
            column_map["anio"] = columns_lower[candidate]
            break
    
    # Trimestre (opcional) - puede estar en Dim-00:TEMPS como "2024Q1"
    for candidate in ("trimestre", "quarter", "trim", "q"):
        if candidate in columns_lower:
            column_map["trimestre"] = columns_lower[candidate]
            break
    
    # Precio medio mensual - Portal de Dades usa "VALUE" para el valor
    for candidate in (
        "preu_mitja_mensual", "precio_medio_mensual", "precio_mes",
        "preu_mensual", "precio", "valor", "mitjana", "value"
    ):
        if candidate in columns_lower:
            column_map["precio_medio_mensual"] = columns_lower[candidate]
            break
    
    # Validar columnas mínimas requeridas
    required_cols = {"anio", "precio_medio_mensual"}
    missing_cols = required_cols - set(column_map.keys())
    
    # #region agent log
    try:
        with open(debug_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "C",
                "location": "prepare_regulacion.py:355",
                "message": "Column mapping result",
                "data": {
                    "column_map": column_map,
                    "required_cols": list(required_cols),
                    "missing_cols": list(missing_cols),
                },
                "timestamp": int(time.time() * 1000)
            }) + "\n")
    except Exception:
        pass
    # #endregion
    
    if missing_cols:
        logger.error(
            "Faltan columnas clave en datos del Portal de Dades. "
            f"Columnas esperadas no encontradas: {sorted(missing_cols)}. "
            f"Columnas disponibles: {sorted(df.columns)}"
        )
        raise ValueError(
            f"Faltan columnas clave: {sorted(missing_cols)}. "
            f"Columnas disponibles: {sorted(df.columns)}"
        )
    
    # Renombrar columnas
    rename_dict = {v: k for k, v in column_map.items()}
    df = df.rename(columns=rename_dict)
    
    # Extraer año y trimestre de Dim-00:TEMPS si está en formato trimestral (ej: "2024Q1")
    if "anio" in df.columns:
        # Si anio contiene valores como "2024Q1", extraer año y trimestre
        if df["anio"].dtype == "object":
            temps_str = df["anio"].astype(str)
            # Extraer año (4 dígitos)
            df["anio"] = temps_str.str.extract(r"(\d{4})", expand=False)
            # Extraer trimestre si existe (Q seguido de 1-4)
            trimestre_match = temps_str.str.extract(r"Q(\d)", expand=False)
            if trimestre_match.notna().any():
                df["trimestre"] = pd.to_numeric(trimestre_match, errors="coerce")
        df["anio"] = pd.to_numeric(df["anio"], errors="coerce").astype("Int64")
    else:
        # Si no se mapeó anio, intentar extraerlo de Dim-00:TEMPS directamente
        if "Dim-00:TEMPS" in df.columns:
            temps_str = df["Dim-00:TEMPS"].astype(str)
            df["anio"] = temps_str.str.extract(r"(\d{4})", expand=False)
            df["anio"] = pd.to_numeric(df["anio"], errors="coerce").astype("Int64")
            # Extraer trimestre si existe
            trimestre_match = temps_str.str.extract(r"Q(\d)", expand=False)
            if trimestre_match.notna().any():
                df["trimestre"] = pd.to_numeric(trimestre_match, errors="coerce")
    
    # Asegurar tipo de precio
    if "precio_medio_mensual" in df.columns:
        df["precio_medio_mensual"] = pd.to_numeric(df["precio_medio_mensual"], errors="coerce")
    elif "VALUE" in df.columns:
        df["precio_medio_mensual"] = pd.to_numeric(df["VALUE"], errors="coerce")
    
    # Si hay trimestre, agregar año completo (usar año del trimestre)
    # Agrupar por barrio y año para obtener precio promedio anual
    groupby_cols = ["anio"]
    if "barrio_nombre" in df.columns:
        groupby_cols.append("barrio_nombre")
    if "codi_barri" in df.columns:
        groupby_cols.append("codi_barri")
    
    if "trimestre" in df.columns and df["trimestre"].notna().any():
        # Agrupar por barrio y año para obtener precio promedio anual
        df_anual = df.groupby(groupby_cols, as_index=False).agg({
            "precio_medio_mensual": "mean"
        })
        df = df_anual
    
    # 3. Calcular índice de referencia (€/m²/mes)
    # Si no tenemos superficie real, usar 70 m² como proxy promedio Barcelona
    if superficie_media_barrio is None or superficie_media_barrio.empty:
        superficie_media = 70.0  # m² promedio Barcelona
        logger.info("Usando superficie media por defecto: 70 m²")
    else:
        # Merge con superficie media por barrio
        df = df.merge(
            superficie_media_barrio[["barrio_id", "superficie_media"]],
            on="barrio_id",
            how="left"
        )
        superficie_media = df["superficie_media"].fillna(70.0)
    
    df["indice_referencia_alquiler"] = (
        df["precio_medio_mensual"] / superficie_media
    )
    
    # 4. Clasificar nivel de tensión por año usando percentiles
    df["percentil_75"] = df.groupby("anio")["indice_referencia_alquiler"].transform(
        lambda x: x.quantile(0.75)
    )
    df["percentil_50"] = df.groupby("anio")["indice_referencia_alquiler"].transform(
        lambda x: x.quantile(0.50)
    )
    
    def clasificar_tension(row: pd.Series) -> str:
        """Clasifica el nivel de tensión según percentiles."""
        if pd.isna(row["indice_referencia_alquiler"]):
            return "baja"
        if row["indice_referencia_alquiler"] > row["percentil_75"]:
            return "alta"
        elif row["indice_referencia_alquiler"] > row["percentil_50"]:
            return "media"
        else:
            return "baja"
    
    df["nivel_tension"] = df.apply(clasificar_tension, axis=1)
    
    # 5. Zona tensionada (todos los barrios de Barcelona desde 2024 según Decreto-ley 1/2024)
    df["zona_tensionada"] = (df["anio"] >= 2024)
    
    # 6. Mapear a barrio_id usando codi_barri o nombre normalizado
    barrios_norm = barrios_df[["barrio_id", "codi_barri", "barrio_nombre", "barrio_nombre_normalizado"]].copy()
    barrios_norm["codi_barri"] = barrios_norm["codi_barri"].astype(str)
    
    # Crear múltiples variantes de nombres normalizados para matching flexible
    barrios_norm["barrio_nombre_lower"] = barrios_norm["barrio_nombre"].str.lower().str.strip()
    barrios_norm["barrio_nombre_normalizado_lower"] = barrios_norm["barrio_nombre_normalizado"].str.lower().str.strip()
    
    # Intentar merge por codi_barri primero
    if "codi_barri" in df.columns:
        df["codi_barri"] = df["codi_barri"].astype(str)
        merged = df.merge(
            barrios_norm[["barrio_id", "codi_barri"]],
            on="codi_barri",
            how="left"
        )
    else:
        # Fallback: merge por nombre normalizado
        if "barrio_nombre" in df.columns:
            # Filtrar registros que son distritos/municipios en lugar de barrios
            # El Portal de Dades puede incluir agregados a nivel distrito/municipio
            # NOTA: "les Corts" y "Sarrià" son barrios individuales, NO distritos agregados
            distritos_y_municipios = {
                "barcelona", "catalunya", "metropolità de barcelona", "metropolita de barcelona",
                "gràcia", "gracia", "ciutat vella", "sant martí", "sant marti", "eixample",
                "sarrià-sant gervasi", "sarria-sant gervasi", "horta-guinardó", "horta-guinardo",
                "nou barris", "sants-montjuïc", "sants-montjuic"
            }
            df["barrio_nombre_lower"] = df["barrio_nombre"].astype(str).str.lower().str.strip()
            is_distrito_municipio = df["barrio_nombre_lower"].isin(distritos_y_municipios)
            if is_distrito_municipio.any():
                logger.info(
                    "Regulación: filtrando %s registros agregados a nivel distrito/municipio",
                    is_distrito_municipio.sum()
                )
                df = df[~is_distrito_municipio].copy()
            
            if df.empty:
                logger.warning("Regulación: después de filtrar distritos/municipios, no quedan datos")
                return pd.DataFrame(
                    columns=[
                        "barrio_id", "anio", "zona_tensionada", "nivel_tension",
                        "indice_referencia_alquiler", "num_licencias_vut", "derecho_tanteo"
                    ]
                )
            
            # Usar el mismo normalizador que dim_barrios para consistencia
            from src.transform.cleaners import HousingCleaner
            cleaner = HousingCleaner()
            
            # Normalizar nombres usando el mismo método que dim_barrios
            df["barrio_nombre_normalizado"] = df["barrio_nombre"].astype(str).apply(
                cleaner.normalize_neighborhoods
            )
            
            # Añadir overrides específicos para barrios problemáticos del Portal de Dades
            barrio_name_overrides = {
                "poblesec": "elpoblesec",  # Portal de Dades puede usar "Poble-sec" sin artículo
                "poble sec": "elpoblesec",
                "marinadelpratvermell": "lamarinadelpratvermell",  # Ya está en cleaners pero por si acaso
                "marina del prat vermell": "lamarinadelpratvermell",
            }
            df["barrio_nombre_normalizado"] = df["barrio_nombre_normalizado"].replace(
                barrio_name_overrides
            )
            
            # Intentar merge por nombre normalizado
            merged = df.merge(
                barrios_norm[["barrio_id", "barrio_nombre_normalizado"]],
                left_on="barrio_nombre_normalizado",
                right_on="barrio_nombre_normalizado",
                how="left"
            )
            
            # Si aún hay registros sin mapear, intentar merge directo por nombre (case-insensitive)
            unmapped = merged["barrio_id"].isna()
            if unmapped.any():
                df_unmapped = df[unmapped].copy()
                df_unmapped["barrio_nombre_lower"] = df_unmapped["barrio_nombre"].astype(str).str.lower().str.strip()
                df_unmapped_mapped = df_unmapped.merge(
                    barrios_norm[["barrio_id", "barrio_nombre_lower"]],
                    left_on="barrio_nombre_lower",
                    right_on="barrio_nombre_lower",
                    how="left",
                    suffixes=("", "_new")
                )
                # Actualizar barrio_id para los registros mapeados
                merged.loc[unmapped, "barrio_id"] = df_unmapped_mapped["barrio_id"].values
        else:
            logger.error("No se puede mapear a barrios: faltan codi_barri y barrio_nombre")
            raise ValueError("No se puede mapear a barrios: faltan codi_barri y barrio_nombre")
    
    missing_fk = merged["barrio_id"].isna().sum()
    if missing_fk:
        logger.warning(
            "Regulación: %s registros sin mapeo a barrio_id", missing_fk
        )
        # Mostrar algunos ejemplos de nombres no mapeados para debugging
        if "barrio_nombre" in merged.columns:
            unmapped_mask = merged["barrio_id"].isna()
            if unmapped_mask.any():
                unmapped_df = merged[unmapped_mask][["barrio_nombre"]].drop_duplicates()
                unmapped_names = unmapped_df["barrio_nombre"].unique()[:20]
                logger.warning(
                    "Regulación: %s nombres únicos sin mapear: %s",
                    len(unmapped_names),
                    list(unmapped_names)
                )
                
                # Buscar nombres similares en dim_barrios para ayudar con el debugging
                import unicodedata
                for unmapped_name in unmapped_names[:10]:  # Aumentar a 10 para ver más
                    unmapped_normalized = (
                        unicodedata.normalize("NFKD", str(unmapped_name).lower())
                        .encode("ascii", errors="ignore")
                        .decode("utf-8")
                        .replace(r"[^\w\s]", "", regex=False)
                        .strip()
                    )
                    # Buscar coincidencias parciales
                    similar = barrios_df[
                        barrios_df["barrio_nombre_normalizado"].str.contains(
                            unmapped_normalized[:10], case=False, na=False, regex=False
                        )
                    ]
                    if not similar.empty:
                        logger.info(
                            "Nombres similares en dim_barrios para '%s': %s",
                            unmapped_name,
                            similar[["barrio_id", "barrio_nombre"]].to_dict("records")
                        )
                    else:
                        # Si no hay similares, mostrar todos los barrios para comparación manual
                        logger.debug(
                            "No se encontraron nombres similares para '%s'. "
                            "Barrios disponibles: %s",
                            unmapped_name,
                            barrios_df[["barrio_id", "barrio_nombre"]].head(10).to_dict("records")
                        )
    
    # 7. Licencias VUT (agrupar por barrio y año)
    vut_df = _load_vut_licencias(raw_data_path)
    if not vut_df.empty:
        # Normalizar columnas VUT y mapear a barrio_id
        vut_columns_lower = {c.lower(): c for c in vut_df.columns}
        
        # Buscar columnas de barrio y año en VUT
        vut_barrio_col = None
        vut_anio_col = None
        
        for candidate in ("codi_barri", "barri_code", "barrio_id"):
            if candidate in vut_columns_lower:
                vut_barrio_col = vut_columns_lower[candidate]
                break
        
        for candidate in ("any", "anio", "year"):
            if candidate in vut_columns_lower:
                vut_anio_col = vut_columns_lower[candidate]
                break
        
        if vut_barrio_col and vut_anio_col:
            vut_agg = vut_df.groupby([vut_barrio_col, vut_anio_col]).size().reset_index(
                name="num_licencias_vut"
            )
            vut_agg = vut_agg.rename(columns={
                vut_barrio_col: "codi_barri",
                vut_anio_col: "anio"
            })
            vut_agg["codi_barri"] = vut_agg["codi_barri"].astype(str)
            
            # Merge con datos principales
            merged = merged.merge(
                vut_agg,
                on=["codi_barri", "anio"],
                how="left"
            )
            merged["num_licencias_vut"] = merged["num_licencias_vut"].fillna(0).astype(int)
        else:
            logger.warning("No se pudieron procesar licencias VUT: columnas no encontradas")
            merged["num_licencias_vut"] = 0
    else:
        merged["num_licencias_vut"] = 0
    
    # 8. Derecho de tanteo (desde 2024 por 6 años según normativa)
    merged["derecho_tanteo"] = (merged["anio"] >= 2024) & (merged["anio"] <= 2030)
    
    # 9. Seleccionar columnas finales
    result = merged[
        [
            "barrio_id",
            "anio",
            "zona_tensionada",
            "nivel_tension",
            "indice_referencia_alquiler",
            "num_licencias_vut",
            "derecho_tanteo",
        ]
    ].copy()
    
    # Filtrar registros sin barrio_id válido
    result = result[result["barrio_id"].notna()].copy()
    
    # Eliminar duplicados: mantener solo un registro por (barrio_id, anio)
    # Si hay múltiples registros para el mismo barrio/año, usar el promedio del índice
    duplicates_before = len(result)
    result = result.groupby(["barrio_id", "anio"], as_index=False).agg({
        "zona_tensionada": "first",  # Todos deberían ser iguales para el mismo año
        "nivel_tension": "first",  # Usar el primero (recalcularemos después)
        "indice_referencia_alquiler": "mean",  # Promedio si hay múltiples valores
        "num_licencias_vut": "first",  # Debería ser el mismo
        "derecho_tanteo": "first",  # Debería ser el mismo
    })
    duplicates_removed = duplicates_before - len(result)
    if duplicates_removed > 0:
        logger.info(
            "Regulación: eliminados %s registros duplicados (agrupados por barrio_id, anio)",
            duplicates_removed
        )
        # Recalcular nivel_tension después de promediar índices
        if len(result) > 0:
            result["percentil_75"] = result.groupby("anio")["indice_referencia_alquiler"].transform(
                lambda x: x.quantile(0.75)
            )
            result["percentil_50"] = result.groupby("anio")["indice_referencia_alquiler"].transform(
                lambda x: x.quantile(0.50)
            )
            def reclasificar_tension(row: pd.Series) -> str:
                """Reclasifica el nivel de tensión después de promediar."""
                if pd.isna(row["indice_referencia_alquiler"]):
                    return "baja"
                if row["indice_referencia_alquiler"] > row["percentil_75"]:
                    return "alta"
                elif row["indice_referencia_alquiler"] > row["percentil_50"]:
                    return "media"
                else:
                    return "baja"
            result["nivel_tension"] = result.apply(reclasificar_tension, axis=1)
            result = result.drop(columns=["percentil_75", "percentil_50"])
    
    # Conversión a tipos finales
    result["zona_tensionada"] = result["zona_tensionada"].astype("bool")
    result["derecho_tanteo"] = result["derecho_tanteo"].astype("bool")
    result["anio"] = result["anio"].astype("Int64")
    result["num_licencias_vut"] = result["num_licencias_vut"].astype("Int64")
    
    # Validaciones básicas
    unique_barrios = result["barrio_id"].nunique(dropna=True)
    if unique_barrios != 73:
        logger.warning(
            "Regulación: se encontraron %s barrios únicos (esperados 73)", unique_barrios
        )
    
    # Rango esperado del índice (500-2000 €/m²/mes)
    valid_range_mask = result["indice_referencia_alquiler"].between(500, 2000)
    outliers = (~valid_range_mask) & result["indice_referencia_alquiler"].notna()
    if outliers.any():
        logger.warning(
            "Regulación: %s registros con indice_referencia_alquiler fuera del "
            "rango 500-2000 €/m²/mes",
            outliers.sum(),
        )
    
    logger.info(
        "Regulación preparada: %s filas, %s barrios únicos, años %s-%s",
        len(result),
        result["barrio_id"].nunique(dropna=True),
        result["anio"].min() if not result.empty else None,
        result["anio"].max() if not result.empty else None,
    )
    
    # #region agent log
    try:
        with open(debug_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "D",
                "location": "prepare_regulacion.py:prepare_regulacion",
                "message": "Function exit",
                "data": {
                    "result_rows": len(result),
                    "result_empty": result.empty,
                    "result_columns": list(result.columns),
                    "unique_barrios": result["barrio_id"].nunique(dropna=True) if not result.empty else 0,
                    "anio_min": int(result["anio"].min()) if not result.empty and result["anio"].notna().any() else None,
                    "anio_max": int(result["anio"].max()) if not result.empty and result["anio"].notna().any() else None,
                },
                "timestamp": int(time.time() * 1000)
            }) + "\n")
    except Exception:
        pass
    # #endregion
    
    return result


__all__ = ["prepare_regulacion"]

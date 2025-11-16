#!/usr/bin/env python3
"""
Script para extraer fuentes de datos prioritarias según QUÉ_DATOS_NECESITAMOS.md

Prioridades:
1. GeoJSON de barrios (Open Data BCN / CartoBCN)
2. Renta por barrio (Ajuntament)
3. Censo y población real (INE / Open Data BCN)
"""

import sys
import json
import logging
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

# Agregar el directorio raíz al path para imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data_extraction import BaseExtractor, OpenDataBCNExtractor, setup_logging
import pandas as pd

# Configurar logging
logger = setup_logging()


class GeoJSONExtractor(BaseExtractor):
    """Extractor para GeoJSON de barrios de Barcelona."""
    
    BASE_URL = "https://opendata-ajuntament.barcelona.cat"
    API_URL = f"{BASE_URL}/data/api/3/action"
    
    # URLs DIRECTAS DE DESCARGA (más eficiente que buscar por API)
    DIRECT_DOWNLOAD_URLS = {
        "barrios": "https://opendata-ajuntament.barcelona.cat/resources/barrios.geojson",
        "distritos": "https://opendata-ajuntament.barcelona.cat/resources/distritos.geojson",
    }
    
    # IDs CONOCIDOS Y CONFIRMADOS (de ejecución real y búsqueda manual)
    KNOWN_DATASET_IDS = [
        "20170706_Districtes_Barris",  # ✅ CONFIRMADO: "Unitats administratives de la ciutat de Barcelona"
        "20170706-districtes-barris",  # ✅ Variante con guiones (ambos funcionan)
        "limits-municipals-districtes",  # ✅ ENCONTRADO: "Municipal and district limits"
    ]
    
    # Resource IDs específicos del GeoJSON de barrios (para acceso directo)
    # ⚠️ IMPORTANTE: Desde 7/6/2023 se publican nuevos recursos con geometría incorporada
    # Los nuevos recursos BarcelonaCiutat_Barris reemplazan al antiguo Unitats_Administratives_BCN.csv
    KNOWN_GEOJSON_RESOURCE_IDS = {
        # ✅ PRIORIDAD MÁXIMA: Nuevos recursos (desde 7/6/2023) con geometría en ETRS89 y WGS84
        "barrios_json": "75197dfe-0306-4c5e-9643-34948af07fb6",  # BarcelonaCiutat_Barris.json (NUEVO - con geometría)
        "barrios_csv": "b21fa550-56ea-4f4c-9adc-b8009381896e",  # BarcelonaCiutat_Barris.csv (NUEVO - con geometría_etrs89 y geometria_wgs84)
        # ⚠️ FORMATO ANTIGUO: Mantenido por compatibilidad, pero los nuevos recursos son preferibles
        "barrios_geojson": "cd800462-f326-429f-a67a-c69b7fc4c50a",  # Unitats_Administratives_BCN.geojson (ANTIGUO - creado 2019)
    }
    
    # IDs a probar si los conocidos fallan
    FALLBACK_DATASET_IDS = [
        "barris-barcelona",
        "barris-geometria",
        "districtes-barris",
        "cartobcn-barris",
        "límits-administratius-barris",
    ]
    
    def __init__(self, rate_limit_delay: float = 1.5, output_dir: Optional[Path] = None):
        """Inicializa el extractor de GeoJSON."""
        super().__init__("GeoJSON", rate_limit_delay, output_dir)
    
    def search_geojson_datasets(self) -> list:
        """
        Busca datasets de geometrías en Open Data BCN.
        
        ESTRATEGIA OPTIMIZADA:
        1. Probar IDs conocidos primero (rápido)
        2. Solo buscar por palabras clave si es necesario
        """
        logger.info("Buscando datasets de geometrías de barrios...")
        
        bcn_extractor = OpenDataBCNExtractor()
        found_datasets = []
        
        # PASO 1: Probar IDs conocidos primero (más eficiente)
        logger.info("🔍 Probando IDs conocidos...")
        for dataset_id in self.KNOWN_DATASET_IDS:
            info = bcn_extractor.get_dataset_info(dataset_id)
            if info:
                found_datasets.append(dataset_id)
                logger.info(f"  ✓ ID conocido encontrado: {dataset_id}")
                logger.info(f"    Título: {info.get('title', 'Sin título')[:60]}")
        
        # Si ya encontramos suficientes, no buscar más
        if len(found_datasets) >= 2:
            logger.info(f"✓ Encontrados {len(found_datasets)} datasets conocidos. Saltando búsqueda por palabras clave.")
            return found_datasets
        
        # PASO 2: Probar IDs fallback
        logger.info("🔍 Probando IDs fallback...")
        for dataset_id in self.FALLBACK_DATASET_IDS:
            if dataset_id in found_datasets:
                continue
            info = bcn_extractor.get_dataset_info(dataset_id)
            if info:
                found_datasets.append(dataset_id)
                logger.info(f"  ✓ Dataset fallback encontrado: {dataset_id}")
        
        # PASO 3: Búsqueda por palabras clave (solo si necesario y limitada)
        if len(found_datasets) < 2:
            logger.info("🔍 Búsqueda limitada por palabras clave (máximo 2 keywords)...")
            # Solo buscar las palabras clave más específicas
            priority_keywords = ["limits", "districtes-barris"]  # Más específicas
            for keyword in priority_keywords[:2]:  # Limitar a 2 para no tardar tanto
                datasets = bcn_extractor.search_datasets_by_keyword(keyword)
                new_datasets = [ds for ds in datasets if ds not in found_datasets]
                found_datasets.extend(new_datasets)
                if new_datasets:
                    logger.info(f"  ✓ Encontrados {len(new_datasets)} datasets nuevos con '{keyword}'")
        
        # Eliminar duplicados
        found_datasets = list(set(found_datasets))
        logger.info(f"Total de datasets candidatos: {len(found_datasets)}")
        
        return found_datasets
    
    def _convert_tabular_to_geojson(self, data: list, geometry_field: str = 'geometria_wgs84') -> Optional[Dict[str, Any]]:
        """
        Convierte datos tabulares con geometría a GeoJSON FeatureCollection estándar.
        
        Args:
            data: Lista de diccionarios con datos tabulares que incluyen geometría
            geometry_field: Nombre del campo que contiene la geometría (geometria_wgs84 o geometria_etrs89)
            
        Returns:
            GeoJSON FeatureCollection o None si falla la conversión
        """
        if not data or not isinstance(data, list):
            logger.debug(f"    _convert_tabular_to_geojson: data vacío o no es lista")
            return None
        
        logger.info(f"    _convert_tabular_to_geojson: procesando {len(data)} items")
        features = []
        items_without_geometry = 0
        items_parse_error = 0
        
        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                continue
            
            # Buscar campo de geometría (preferir wgs84, luego etrs89)
            geometry_str = None
            if geometry_field in item:
                geometry_str = item.get(geometry_field)
            elif 'geometria_wgs84' in item:
                geometry_str = item.get('geometria_wgs84')
            elif 'geometria_etrs89' in item:
                geometry_str = item.get('geometria_etrs89')
            
            if not geometry_str:
                items_without_geometry += 1
                if idx < 3:  # Log solo los primeros 3 para no saturar
                    logger.debug(f"    Item {idx}: sin campo de geometría")
                continue
            
            # Intentar parsear la geometría
            geometry = None
            
            # Opción 1: Es un string JSON (GeoJSON geometry)
            if isinstance(geometry_str, str):
                try:
                    # Intentar parsear como JSON primero
                    parsed = json.loads(geometry_str)
                    if isinstance(parsed, dict) and 'type' in parsed:
                        geometry = parsed
                except (json.JSONDecodeError, TypeError):
                    # Si no es JSON, podría ser WKT - intentar con shapely si está disponible
                    try:
                        from shapely import wkt
                        from shapely.geometry import mapping
                        geom_obj = wkt.loads(geometry_str)
                        # Convertir shapely a GeoJSON usando mapping (compatible con todas las versiones)
                        geometry = mapping(geom_obj)
                    except (ImportError, Exception) as e:
                        # Si shapely no está disponible o falla, log el error
                        items_parse_error += 1
                        if idx < 3:  # Log solo los primeros 3 para no saturar
                            logger.warning(f"    Item {idx}: Error parseando WKT: {str(e)}")
                            logger.warning(f"    Geometría (primeros 200 chars): {geometry_str[:200] if geometry_str else 'None'}...")
                        continue
            # Opción 2: Ya es un dict (geometría parseada)
            elif isinstance(geometry_str, dict):
                geometry = geometry_str
            
            if not geometry:
                items_parse_error += 1
                continue
            
            # Crear Feature
            properties = {k: v for k, v in item.items() 
                         if k not in ['geometria_wgs84', 'geometria_etrs89', geometry_field]}
            
            feature = {
                'type': 'Feature',
                'geometry': geometry,
                'properties': properties
            }
            
            features.append(feature)
        
        logger.info(f"    _convert_tabular_to_geojson: {len(features)} features creados, {items_without_geometry} sin geometría, {items_parse_error} errores de parseo")
        
        if not features:
            logger.debug(f"    _convert_tabular_to_geojson: No se crearon features, retornando None")
            return None
        
        return {
            'type': 'FeatureCollection',
            'features': features
        }
    
    def extract_geojson(
        self,
        dataset_id: Optional[str] = None,
        prefer_direct_url: bool = True
    ) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """
        Extrae GeoJSON de barrios.
        
        ESTRATEGIA OPTIMIZADA:
        1. Intentar URLs directas primero (más rápido)
        2. Si fallan, usar API CKAN
        3. Validar formato GeoJSON
        
        Args:
            dataset_id: ID del dataset (si None, busca automáticamente)
            prefer_direct_url: Si True, intenta URLs directas primero
            
        Returns:
            Tupla con (GeoJSON dict o None, metadata)
        """
        logger.info("=== Extrayendo GeoJSON de barrios ===")
        
        metadata = {
            "extraction_date": datetime.now().isoformat(),
            "success": False,
            "dataset_id": dataset_id,
            "datasets_tried": [],
            "method_used": None,
        }
        
        # PASO 1: Intentar URLs directas (más eficiente)
        if prefer_direct_url:
            logger.info("🔍 PASO 1: Intentando URLs directas de descarga...")
            for name, url in self.DIRECT_DOWNLOAD_URLS.items():
                try:
                    logger.info(f"  Probando URL directa: {name}")
                    self._rate_limit()
                    
                    response = self.session.get(url, timeout=60)
                    if self._validate_response(response):
                        try:
                            geojson_data = response.json()
                            
                            # Validar que es un GeoJSON válido
                            if geojson_data.get('type') == 'FeatureCollection':
                                num_features = len(geojson_data.get('features', []))
                                logger.info(f"✓ GeoJSON válido encontrado: {num_features} features")
                                
                                # Guardar GeoJSON
                                filepath = self._save_raw_data(
                                    geojson_data,
                                    f"{name}_geojson",
                                    'json'
                                )
                                
                                metadata["success"] = True
                                metadata["filepath"] = str(filepath)
                                metadata["num_features"] = num_features
                                metadata["method_used"] = "direct_url"
                                metadata["url_used"] = url
                                
                                return geojson_data, metadata
                            else:
                                logger.warning(f"  URL devolvió JSON pero no es FeatureCollection válido")
                        except json.JSONDecodeError as e:
                            logger.warning(f"  Error parseando JSON desde URL directa: {e}")
                            continue
                except Exception as e:
                    logger.debug(f"  Error con URL directa {name}: {e}")
                    continue
        
        # PASO 2: Usar API CKAN si URLs directas fallaron
        logger.info("🔍 PASO 2: Intentando descarga vía API CKAN...")
        bcn_extractor = OpenDataBCNExtractor(output_dir=self.output_dir)
        
        # Si no se especifica dataset, buscar
        if dataset_id is None:
            candidates = self.search_geojson_datasets()
            if not candidates:
                logger.error("No se encontraron datasets de geometrías")
                metadata["error"] = "No se encontraron datasets"
                return None, metadata
        else:
            candidates = [dataset_id]
        
        # Probar cada dataset hasta encontrar uno con GeoJSON válido
        for dataset_id in candidates:
            logger.info(f"\n{'='*70}")
            logger.info(f"Probando dataset: {dataset_id}")
            logger.info(f"{'='*70}")
            
            metadata["dataset_id"] = dataset_id
            metadata["datasets_tried"].append(dataset_id)
            
            try:
                # Intentar descargar el dataset
                df, cov_meta = bcn_extractor.download_dataset(
                    dataset_id,
                    resource_format='json',  # GeoJSON suele venir como JSON
                    year_start=None,
                    year_end=None
                )
                
                # Si se descargó un DataFrame (CSV), no es GeoJSON
                if df is not None and not df.empty:
                    logger.warning("⚠️  Dataset descargado es CSV, no GeoJSON. Buscando recursos GeoJSON...")
                
                # Intentar con formato GeoJSON directo desde recursos
                logger.info("Intentando descargar como GeoJSON directo desde recursos...")
                dataset_info = bcn_extractor.get_dataset_info(dataset_id)
                if not dataset_info:
                    logger.warning(f"⚠️  No se pudo obtener información del dataset {dataset_id}")
                    continue  # Probar siguiente dataset
                
                # Si llegamos aquí, dataset_info existe
                resources = dataset_info.get('resources', [])
                logger.info(f"Encontrados {len(resources)} recursos en el dataset")
                
                # Priorizar recursos GeoJSON en orden de prioridad
                # ⚠️ IMPORTANTE: Desde 7/6/2023 se publican nuevos recursos BarcelonaCiutat_Barris con geometría incorporada
                # PRIORIDAD 0 (MÁXIMA): Nuevos recursos BarcelonaCiutat_Barris (desde 7/6/2023)
                priority_0 = [
                    r for r in resources 
                    if 'barcelonaciutat_barris' in r.get('name', '').lower() or
                       r.get('id', '') in [self.KNOWN_GEOJSON_RESOURCE_IDS.get('barrios_json', ''), 
                                           self.KNOWN_GEOJSON_RESOURCE_IDS.get('barrios_csv', '')]
                ]
                
                # PRIORIDAD 1: Recursos con .geojson explícito en nombre o URL
                priority_1 = [
                    r for r in resources 
                    if r not in priority_0 and
                       (r.get('name', '').lower().endswith('.geojson') or
                        r.get('url', '').lower().endswith('.geojson') or
                        ('geojson' in r.get('format', '').lower() and 'json' in r.get('format', '').lower()))
                ]
                
                # PRIORIDAD 2: Recursos con formato que contenga "geojson"
                priority_2 = [
                    r for r in resources 
                    if r not in priority_0 and r not in priority_1 and 'geojson' in r.get('format', '').lower()
                ]
                
                # PRIORIDAD 3: Recursos JSON con nombres que sugieren geometrías
                geo_keywords = ['barri', 'barrio', 'districte', 'distrito', 'geometry', 'geometria', 'limits', 'limites', 'boundary', 'boundaries']
                priority_3 = [
                    r for r in resources 
                    if r not in priority_0 and r not in priority_1 and r not in priority_2 and
                       ('json' in r.get('format', '').lower() or r.get('url', '').lower().endswith('.json')) and
                       any(kw in r.get('name', '').lower() for kw in geo_keywords)
                ]
                
                # PRIORIDAD 4: Todos los demás recursos JSON
                priority_4 = [
                    r for r in resources 
                    if r not in priority_0 and r not in priority_1 and r not in priority_2 and r not in priority_3 and
                       ('json' in r.get('format', '').lower() or r.get('url', '').lower().endswith('.json'))
                ]
                
                # Combinar en orden de prioridad (priority_0 primero)
                geojson_resources = priority_0 + priority_1 + priority_2 + priority_3 + priority_4
                
                if priority_0:
                    logger.info(f"✓ Encontrados {len(priority_0)} recursos BarcelonaCiutat_Barris (NUEVOS - prioridad máxima desde 7/6/2023)")
                if priority_1:
                    logger.info(f"✓ Encontrados {len(priority_1)} recursos con .geojson explícito")
                if priority_2:
                    logger.info(f"✓ Encontrados {len(priority_2)} recursos con formato GeoJSON")
                if priority_3:
                    logger.info(f"✓ Encontrados {len(priority_3)} recursos JSON con nombres geográficos")
                
                # Si aún no hay, intentar todos los recursos
                if not geojson_resources:
                    logger.info("No se encontraron recursos con formato GeoJSON explícito. Intentando todos los recursos...")
                    geojson_resources = resources
                
                logger.info(f"Probando {len(geojson_resources)} recursos para encontrar GeoJSON válido...")
                resources_tried = []
                
                for resource in geojson_resources:
                    url = resource.get('url', '')
                    format_type = resource.get('format', '').lower()
                    name = resource.get('name', 'sin nombre')
                    
                    logger.info(f"  Probando recurso: {name} (formato: {format_type})")
                    resource_status = {"name": name, "format": format_type, "status": "unknown"}
                    
                    # Saltar recursos CSV explícitos, EXCEPTO si tienen geometría (BarcelonaCiutat_Barris.csv)
                    if 'csv' in format_type and 'json' not in format_type:
                        # Verificar si es un CSV con geometría (BarcelonaCiutat_Barris)
                        if 'barcelonaciutat' in name.lower() and 'barris' in name.lower():
                            logger.info(f"    🔄 CSV con geometría detectado, intentando convertir a GeoJSON...")
                            # Continuar para procesar este CSV especial
                        else:
                            logger.debug(f"    Saltando recurso CSV: {name}")
                            resource_status["status"] = "skipped_csv"
                            resources_tried.append(resource_status)
                            continue
                    
                    self._rate_limit()
                    
                    try:
                        response = self.session.get(url, timeout=60)
                        if self._validate_response(response):
                            # Verificar Content-Type
                            content_type = response.headers.get('Content-Type', '').lower()
                            logger.debug(f"    Content-Type: {content_type}")
                            
                            # Si el Content-Type indica HTML o texto, probablemente es una página de error
                            if 'text/html' in content_type:
                                logger.debug(f"    ⚠️  Respuesta es HTML, no JSON. Probablemente página de error.")
                                resource_status["status"] = "html_response_not_json"
                                resources_tried.append(resource_status)
                                continue
                            
                            # Manejar CSV con geometría (BarcelonaCiutat_Barris.csv)
                            if 'csv' in format_type or 'text/csv' in content_type:
                                if 'barcelonaciutat' in name.lower() and 'barris' in name.lower():
                                    logger.info(f"    📄 Procesando CSV con geometría...")
                                    try:
                                        import io
                                        csv_text = response.text
                                        df = pd.read_csv(io.StringIO(csv_text))
                                        
                                        # Verificar que tiene columnas de geometría
                                        has_geometry = any('geometria' in col.lower() for col in df.columns)
                                        if has_geometry:
                                            logger.info(f"    ✓ CSV tiene {len(df)} registros con geometría")
                                            # Convertir DataFrame a lista de dicts
                                            data_list = df.to_dict('records')
                                            geojson_fc = self._convert_tabular_to_geojson(data_list)
                                            
                                            if geojson_fc and geojson_fc.get('features'):
                                                num_features = len(geojson_fc['features'])
                                                logger.info(f"✓ CSV convertido a GeoJSON: {num_features} features")
                                                
                                                filepath = self._save_raw_data(
                                                    geojson_fc,
                                                    "barrios_geojson",
                                                    'json'
                                                )
                                                
                                                metadata["success"] = True
                                                metadata["filepath"] = str(filepath)
                                                metadata["num_features"] = num_features
                                                metadata["method_used"] = "ckan_api_csv_converted"
                                                metadata["resource_name"] = name
                                                metadata["conversion_applied"] = True
                                                
                                                return geojson_fc, metadata
                                            else:
                                                logger.warning(f"    ⚠️  No se pudo convertir CSV a GeoJSON (geojson_fc es None o no tiene features)")
                                                if geojson_fc is None:
                                                    logger.debug(f"    _convert_tabular_to_geojson retornó None")
                                                elif not geojson_fc.get('features'):
                                                    logger.debug(f"    FeatureCollection no tiene features (features: {geojson_fc.get('features', 'missing')})")
                                                resource_status["status"] = "csv_conversion_failed"
                                                resources_tried.append(resource_status)
                                                continue
                                        else:
                                            logger.debug(f"    ⚠️  CSV no tiene columnas de geometría")
                                            resource_status["status"] = "csv_no_geometry"
                                            resources_tried.append(resource_status)
                                            continue
                                    except Exception as e:
                                        logger.warning(f"    ⚠️  Error procesando CSV: {e}")
                                        logger.debug(traceback.format_exc())
                                        resource_status["status"] = f"csv_error_{type(e).__name__}"
                                        resources_tried.append(resource_status)
                                        continue
                            
                            # Intentar parsear como JSON
                            try:
                                geojson_data = response.json()
                                
                                # Log información sobre el tipo de datos recibidos
                                if isinstance(geojson_data, dict):
                                    data_type = geojson_data.get('type', 'unknown')
                                    keys = list(geojson_data.keys())[:10]  # Primeras 10 claves
                                    logger.debug(f"    Tipo de datos: dict, 'type': {data_type}, claves: {keys}")
                                    
                                    # Si es un dict pero no tiene estructura GeoJSON, mostrar más detalles
                                    if data_type != 'FeatureCollection' and 'features' not in geojson_data:
                                        # Verificar si tiene campos que puedan indicar datos geográficos
                                        geo_indicators = ['geometry', 'coordinates', 'lat', 'lon', 'latitude', 'longitude', 'x', 'y', 'geom']
                                        has_geo_fields = any(key.lower() in str(keys).lower() for key in geo_indicators)
                                        logger.debug(f"    Dict sin estructura GeoJSON. Tiene campos geográficos: {has_geo_fields}")
                                        if has_geo_fields:
                                            logger.debug(f"    ⚠️  Dict tiene campos geográficos pero no es FeatureCollection. Estructura: {keys}")
                                    
                                    # Validar que es un GeoJSON válido
                                    if data_type == 'FeatureCollection':
                                        num_features = len(geojson_data.get('features', []))
                                        logger.info(f"✓ GeoJSON válido encontrado: {num_features} features")
                                        
                                        # Guardar GeoJSON
                                        filepath = self._save_raw_data(
                                            geojson_data,
                                            "barrios_geojson",
                                            'json'
                                        )
                                        
                                        metadata["success"] = True
                                        metadata["filepath"] = str(filepath)
                                        metadata["num_features"] = num_features
                                        metadata["method_used"] = "ckan_api"
                                        metadata["resource_name"] = name
                                        
                                        return geojson_data, metadata
                                    else:
                                        # Verificar si tiene estructura de GeoJSON pero sin el campo 'type'
                                        if 'features' in geojson_data and isinstance(geojson_data['features'], list):
                                            num_features = len(geojson_data['features'])
                                            logger.info(f"✓ GeoJSON sin 'type' encontrado: {num_features} features")
                                            # Agregar 'type' si falta
                                            if 'type' not in geojson_data:
                                                geojson_data['type'] = 'FeatureCollection'
                                            filepath = self._save_raw_data(
                                                geojson_data,
                                                "barrios_geojson",
                                                'json'
                                            )
                                            metadata["success"] = True
                                            metadata["filepath"] = str(filepath)
                                            metadata["num_features"] = num_features
                                            metadata["method_used"] = "ckan_api"
                                            metadata["resource_name"] = name
                                            return geojson_data, metadata
                                        # Verificar si tiene 'geometry' directamente (puede ser un Feature único)
                                        elif 'geometry' in geojson_data:
                                            logger.debug(f"    Recurso tiene 'geometry' pero no 'features' (puede ser un Feature único)")
                                            # Convertir Feature único a FeatureCollection
                                            geojson_fc = {
                                                'type': 'FeatureCollection',
                                                'features': [geojson_data]
                                            }
                                            logger.info(f"✓ Feature único convertido a FeatureCollection")
                                            filepath = self._save_raw_data(
                                                geojson_fc,
                                                "barrios_geojson",
                                                'json'
                                            )
                                            metadata["success"] = True
                                            metadata["filepath"] = str(filepath)
                                            metadata["num_features"] = 1
                                            metadata["method_used"] = "ckan_api"
                                            metadata["resource_name"] = name
                                            return geojson_fc, metadata
                                        logger.debug(f"    Recurso no es FeatureCollection válido (type: {data_type}, tiene 'features': {'features' in geojson_data})")
                                        resource_status["status"] = f"not_valid_geojson_type_{data_type}"
                                        resources_tried.append(resource_status)
                                elif isinstance(geojson_data, list):
                                    logger.debug(f"    Datos recibidos como lista (longitud: {len(geojson_data)})")
                                    # Verificar si es una lista de features
                                    if len(geojson_data) > 0:
                                        first_item = geojson_data[0]
                                        if isinstance(first_item, dict):
                                            has_geometry = 'geometry' in first_item
                                            has_type = first_item.get('type') == 'Feature'
                                            first_keys = list(first_item.keys())[:15]  # Primeras 15 claves
                                            logger.debug(f"    Primer elemento: dict, claves: {first_keys}")
                                            logger.debug(f"    Tiene 'geometry': {has_geometry}, type='Feature': {has_type}")
                                            
                                            # Verificar si tiene campos que puedan indicar datos geográficos o de barrios
                                            geo_indicators = ['geometry', 'coordinates', 'lat', 'lon', 'latitude', 'longitude', 'x', 'y', 'geom', 'wkt']
                                            barrio_indicators = ['barrio', 'barri', 'distrito', 'districte', 'nom', 'name', 'codi', 'code']
                                            has_geo_fields = any(ind.lower() in str(first_keys).lower() for ind in geo_indicators)
                                            has_barrio_fields = any(ind.lower() in str(first_keys).lower() for ind in barrio_indicators)
                                            
                                            logger.debug(f"    Tiene campos geográficos: {has_geo_fields}, tiene campos de barrio: {has_barrio_fields}")
                                            
                                            if has_geometry or has_type:
                                                logger.info(f"✓ GeoJSON como lista encontrado: {len(geojson_data)} features")
                                                geojson_fc = {
                                                    'type': 'FeatureCollection',
                                                    'features': geojson_data
                                                }
                                                filepath = self._save_raw_data(
                                                    geojson_fc,
                                                    "barrios_geojson",
                                                    'json'
                                                )
                                                metadata["success"] = True
                                                metadata["filepath"] = str(filepath)
                                                metadata["num_features"] = len(geojson_data)
                                                metadata["method_used"] = "ckan_api"
                                                metadata["resource_name"] = name
                                                return geojson_fc, metadata
                                            elif has_geo_fields or has_barrio_fields:
                                                # Tiene datos geográficos pero no en formato GeoJSON estándar
                                                # Intentar convertir a GeoJSON si tiene campos de geometría
                                                has_geometry_fields = any(
                                                    'geometria' in key.lower() or 'geometry' in key.lower() 
                                                    for key in first_keys
                                                )
                                                
                                                if has_geometry_fields:
                                                    logger.info(f"    🔄 Intentando convertir datos tabulares con geometría a GeoJSON...")
                                                    try:
                                                        geojson_fc = self._convert_tabular_to_geojson(geojson_data)
                                                        if geojson_fc and geojson_fc.get('features'):
                                                            num_features = len(geojson_fc['features'])
                                                            logger.info(f"✓ Datos tabulares convertidos a GeoJSON: {num_features} features")
                                                            
                                                            filepath = self._save_raw_data(
                                                                geojson_fc,
                                                                "barrios_geojson",
                                                                'json'
                                                            )
                                                            
                                                            metadata["success"] = True
                                                            metadata["filepath"] = str(filepath)
                                                            metadata["num_features"] = num_features
                                                            metadata["method_used"] = "ckan_api_converted"
                                                            metadata["resource_name"] = name
                                                            metadata["conversion_applied"] = True
                                                            
                                                            return geojson_fc, metadata
                                                        else:
                                                            logger.warning(f"    ⚠️  Conversión falló: no se pudieron crear features")
                                                            if geojson_fc is None:
                                                                logger.debug(f"    _convert_tabular_to_geojson retornó None")
                                                            elif not geojson_fc.get('features'):
                                                                logger.debug(f"    FeatureCollection no tiene features")
                                                    except Exception as e:
                                                        logger.warning(f"    ⚠️  Error en conversión: {e}")
                                                        logger.debug(traceback.format_exc())
                                                
                                                logger.debug(f"    ⚠️  Lista tiene datos geográficos/barrios pero no es formato GeoJSON estándar")
                                                logger.debug(f"    Estructura del primer elemento: {first_keys}")
                                                logger.debug(f"    Esto podría ser datos tabulares con información geográfica, no GeoJSON")
                                                resource_status["status"] = "list_has_geo_data_but_not_geojson_format"
                                                resource_status["sample_keys"] = first_keys[:5]  # Guardar muestra de claves
                                                resources_tried.append(resource_status)
                                            else:
                                                logger.debug(f"    Lista no contiene Features ni datos geográficos identificables")
                                                logger.debug(f"    Estructura del primer elemento: {first_keys}")
                                                resource_status["status"] = "list_not_features"
                                                resource_status["sample_keys"] = first_keys[:5]
                                                resources_tried.append(resource_status)
                                        else:
                                            logger.debug(f"    Lista no contiene dicts (primer elemento es {type(first_item)})")
                                            resource_status["status"] = f"list_not_dicts_{type(first_item).__name__}"
                                            resources_tried.append(resource_status)
                                    else:
                                        logger.debug(f"    Lista vacía")
                                        resource_status["status"] = "empty_list"
                                        resources_tried.append(resource_status)
                                else:
                                    logger.debug(f"    Tipo de datos inesperado: {type(geojson_data)}")
                                    resource_status["status"] = f"unexpected_type_{type(geojson_data).__name__}"
                                    resources_tried.append(resource_status)
                            except json.JSONDecodeError as e:
                                # Inspeccionar el contenido real de la respuesta
                                content_preview = response.text[:200] if hasattr(response, 'text') else str(response.content[:200])
                                logger.debug(f"    Recurso no es JSON válido: {e}")
                                logger.debug(f"    Primeros 200 caracteres de la respuesta: {content_preview}")
                                
                                # Verificar si es HTML
                                if content_preview.strip().startswith('<!DOCTYPE') or content_preview.strip().startswith('<html'):
                                    logger.debug(f"    ⚠️  Respuesta es HTML, no JSON. Probablemente página de error o redirección.")
                                    resource_status["status"] = "html_response_instead_of_json"
                                else:
                                    resource_status["status"] = f"invalid_json_{str(e)[:50]}"
                                resource_status["content_preview"] = content_preview[:100]  # Guardar preview
                                resources_tried.append(resource_status)
                                continue
                        else:
                            logger.debug(f"    Error HTTP al descargar recurso {name}: {response.status_code}")
                            resource_status["status"] = f"http_error_{response.status_code}"
                            resources_tried.append(resource_status)
                    except Exception as e:
                        logger.debug(f"    Error descargando recurso {name}: {e}")
                        resource_status["status"] = f"exception_{type(e).__name__}"
                        resources_tried.append(resource_status)
                        continue
                
                # Resumen de recursos probados
                if resources_tried:
                    logger.info(f"\n📊 Resumen de recursos probados ({len(resources_tried)}):")
                    for rs in resources_tried[:10]:  # Mostrar primeros 10
                        status_msg = rs['status']
                        if 'sample_keys' in rs:
                            status_msg += f" (claves: {rs['sample_keys']})"
                        if 'content_preview' in rs:
                            preview = rs['content_preview'].replace('\n', ' ')[:60]
                            status_msg += f" (contenido: {preview}...)"
                        logger.info(f"  - {rs['name']}: {status_msg}")
                    if len(resources_tried) > 10:
                        logger.info(f"  ... y {len(resources_tried) - 10} más")
                    
                    # Análisis del problema raíz
                    html_responses = [rs for rs in resources_tried if 'html' in rs['status'].lower()]
                    geo_data_but_not_geojson = [rs for rs in resources_tried if 'geo_data_but_not_geojson' in rs['status']]
                    
                    if html_responses:
                        logger.warning(f"\n⚠️  PROBLEMA RAÍZ: {len(html_responses)} recursos devuelven HTML en lugar de JSON")
                        logger.warning(f"   Esto indica que las URLs pueden estar rotas o requieren autenticación/redirección")
                    
                    if geo_data_but_not_geojson:
                        logger.warning(f"\n⚠️  PROBLEMA RAÍZ: {len(geo_data_but_not_geojson)} recursos tienen datos geográficos pero NO en formato GeoJSON")
                        logger.warning(f"   Estos recursos contienen información de barrios/geografía pero en formato tabular JSON")
                        logger.warning(f"   SOLUCIÓN: Necesitamos buscar recursos específicos de GeoJSON o convertir estos datos")
                        for rs in geo_data_but_not_geojson[:3]:
                            logger.warning(f"   - {rs['name']}: tiene campos {rs.get('sample_keys', [])}")
                    
                    if not html_responses and not geo_data_but_not_geojson:
                        logger.warning(f"\n⚠️  PROBLEMA RAÍZ: Los recursos JSON no contienen datos geográficos identificables")
                        logger.warning(f"   Estos recursos pueden ser metadatos o datos no geográficos")
                
                # Si llegamos aquí, no se encontró GeoJSON válido en este dataset
                logger.warning(f"\n⚠️  No se encontró GeoJSON válido en el dataset {dataset_id}")
                logger.info(f"Continuando con el siguiente dataset si está disponible...")
                continue  # Probar siguiente dataset
                
            except Exception as e:
                logger.error(f"Error procesando dataset {dataset_id}: {e}")
                logger.debug(traceback.format_exc())
                continue  # Probar siguiente dataset
        
        # Si llegamos aquí, ningún dataset tuvo éxito
        metadata["error"] = "No se pudo extraer GeoJSON de ningún dataset. Los datasets pueden contener solo CSV o los recursos GeoJSON no están disponibles."
        return None, metadata


class RentaExtractor(BaseExtractor):
    """Extractor para datos de renta familiar disponible por barrio."""
    
    BASE_URL = "https://opendata-ajuntament.barcelona.cat"
    API_URL = f"{BASE_URL}/data/api/3/action"
    
    # URLs DIRECTAS (si están disponibles)
    DIRECT_DATASET_URLS = {
        "renta_familiar_disponible": "https://opendata-ajuntament.barcelona.cat/data/es/dataset/renta-familiar-disponible",
    }
    
    # IDs CONOCIDOS Y CONFIRMADOS (de ejecución real y búsqueda manual)
    KNOWN_DATASET_IDS = [
        # ✅ PRIORIDAD MÁXIMA: Datos con Codi_Barri y Nom_Barri (se pueden agregar por barrio)
        "renda-disponible-llars-bcn",  # ✅ CONFIRMADO: "Renda disponible de les llars per càpita(€)" - Tiene Codi_Barri, Nom_Barri, Seccio_Censal, Import_Euros
        "atles-renda-bruta-per-llar",  # ✅ CONFIRMADO: "Renda tributària bruta mitjana per llar (€)" - Tiene Codi_Barri, Nom_Barri, Seccio_Censal, Import_Renda_Bruta_€
        "atles-renda-bruta-per-persona",  # ✅ CONFIRMADO: "Renda tributària bruta mitjana per persona (€)" - Tiene Codi_Barri, Nom_Barri, Seccio_Censal
        # ✅ ENCONTRADOS (pero verificar estructura):
        "atles-renda-mitjana",  # ✅ ENCONTRADO: "Average tax income per unit of consumption"
        "atles-renda-mediana",  # ✅ ENCONTRADO: "Median tax income per unit of consumption"
        # NOTA: Estos datasets tienen datos por sección censal PERO incluyen Codi_Barri y Nom_Barri
        # Se pueden agregar fácilmente por barrio usando groupby en Codi_Barri
    ]
    
    # IDs a probar si los conocidos fallan
    FALLBACK_DATASET_IDS = [
        "renta-familiar-disponible",
        "renta-familiar",
        "renta-per-barris",
        "ingressos-familiars",
        "renta-disponible",
    ]
    
    def __init__(self, rate_limit_delay: float = 1.5, output_dir: Optional[Path] = None):
        """Inicializa el extractor de renta."""
        super().__init__("Renta", rate_limit_delay, output_dir)
    
    def search_renta_datasets(self) -> list:
        """
        Busca datasets de renta en Open Data BCN.
        
        ESTRATEGIA OPTIMIZADA:
        1. Probar IDs conocidos primero
        2. Validar que tienen datos por barrio
        3. Solo buscar por palabras clave si es necesario
        """
        logger.info("Buscando datasets de renta familiar...")
        
        bcn_extractor = OpenDataBCNExtractor()
        found_datasets = []
        
        # PASO 1: Probar IDs conocidos primero
        logger.info("🔍 Probando IDs conocidos...")
        for dataset_id in self.KNOWN_DATASET_IDS:
            info = bcn_extractor.get_dataset_info(dataset_id)
            if info:
                # Validar que probablemente tiene datos por barrio
                title = info.get('title', '').lower()
                description = info.get('notes', '').lower()
                if any(kw in title + description for kw in ['barri', 'barrio', 'neighborhood', 'per capita', 'household']):
                    found_datasets.append(dataset_id)
                    logger.info(f"  ✓ ID conocido encontrado: {dataset_id}")
                    logger.info(f"    Título: {info.get('title', 'Sin título')[:60]}")
                else:
                    logger.debug(f"  ⚠️  {dataset_id} encontrado pero no parece tener datos por barrio")
        
        # Si ya encontramos suficientes, no buscar más
        if len(found_datasets) >= 2:
            logger.info(f"✓ Encontrados {len(found_datasets)} datasets conocidos. Saltando búsqueda por palabras clave.")
            return found_datasets
        
        # PASO 2: Probar IDs fallback
        logger.info("🔍 Probando IDs fallback...")
        for dataset_id in self.FALLBACK_DATASET_IDS:
            if dataset_id in found_datasets:
                continue
            info = bcn_extractor.get_dataset_info(dataset_id)
            if info:
                found_datasets.append(dataset_id)
                logger.info(f"  ✓ Dataset fallback encontrado: {dataset_id}")
        
        # PASO 3: Búsqueda limitada por palabras clave (solo si necesario)
        if len(found_datasets) < 2:
            logger.info("🔍 Búsqueda limitada por palabras clave (máximo 2 keywords)...")
            priority_keywords = ["renda disponible", "renta familiar"]  # Más específicas
            for keyword in priority_keywords[:2]:
                datasets = bcn_extractor.search_datasets_by_keyword(keyword)
                new_datasets = [ds for ds in datasets if ds not in found_datasets]
                found_datasets.extend(new_datasets)
                if new_datasets:
                    logger.info(f"  ✓ Encontrados {len(new_datasets)} datasets nuevos con '{keyword}'")
        
        # Eliminar duplicados
        found_datasets = list(set(found_datasets))
        logger.info(f"Total de datasets candidatos: {len(found_datasets)}")
        
        return found_datasets
    
    def extract_renta(
        self,
        year_start: int = 2015,
        year_end: int = 2024,
        dataset_id: Optional[str] = None,
        prefer_direct_url: bool = True
    ) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Extrae datos de renta familiar disponible por barrio.
        
        Args:
            year_start: Año inicial
            year_end: Año final
            dataset_id: ID del dataset (si None, busca automáticamente)
            
        Returns:
            Tupla con (DataFrame o None, metadata)
        """
        logger.info(f"=== Extrayendo datos de renta ({year_start}-{year_end}) ===")
        
        metadata = {
            "extraction_date": datetime.now().isoformat(),
            "requested_range": {"start": year_start, "end": year_end},
            "success": False,
            "dataset_id": dataset_id,
            "datasets_tried": [],
            "method_used": None,
        }
        
        # PASO 1: Intentar URLs directas (si están disponibles)
        if prefer_direct_url:
            logger.info("🔍 PASO 1: Intentando URLs directas de renta...")
            direct_urls = {
                "barri": "https://opendata-ajuntament.barcelona.cat/resources/rfd/rfd_barri.csv",
                "municipi": "https://opendata-ajuntament.barcelona.cat/resources/rfd/rfd_municipi.csv",
            }
            
            # Priorizar barri (más granular)
            for name, url in direct_urls.items():
                try:
                    logger.info(f"  Probando URL directa: {name}")
                    self._rate_limit()
                    response = self.session.get(url, timeout=60)
                    
                    if self._validate_response(response):
                        # Leer CSV directamente
                        import io
                        df = pd.read_csv(io.StringIO(response.text), low_memory=False)
                        
                        if not df.empty:
                            logger.info(f"✓ Datos de renta descargados desde URL directa: {len(df)} registros")
                            
                            # Guardar
                            filepath = self._save_raw_data(
                                df,
                                f"renta_{name}",
                                'csv',
                                year_start=year_start,
                                year_end=year_end
                            )
                            
                            metadata["success"] = True
                            metadata["filepath"] = str(filepath)
                            metadata["method_used"] = "direct_url"
                            metadata["url_used"] = url
                            metadata["records"] = len(df)
                            metadata["columns"] = list(df.columns)
                            
                            return df, metadata
                except Exception as e:
                    error_msg = str(e)
                    if "404" in error_msg or "Not Found" in error_msg:
                        logger.debug(f"  URL directa {name} no disponible (404). Continuando con API CKAN...")
                    else:
                        logger.debug(f"  Error con URL directa {name}: {e}")
                    continue
        
        # PASO 2: Usar API CKAN si URLs directas fallaron
        logger.info("🔍 PASO 2: Intentando descarga vía API CKAN...")
        bcn_extractor = OpenDataBCNExtractor(output_dir=self.output_dir)
        
        # Si no se especifica dataset, buscar
        if dataset_id is None:
            candidates = self.search_renta_datasets()
            if not candidates:
                logger.error("No se encontraron datasets de renta")
                metadata["error"] = "No se encontraron datasets"
                return None, metadata
            
            # Priorizar IDs conocidos
            known_ids = [ds for ds in self.KNOWN_DATASET_IDS if ds in candidates]
            if known_ids:
                dataset_id = known_ids[0]
                logger.info(f"Usando dataset conocido: {dataset_id}")
            else:
                dataset_id = candidates[0]
                logger.info(f"Usando dataset: {dataset_id}")
        
        metadata["dataset_id"] = dataset_id
        metadata["datasets_tried"].append(dataset_id)
        
        try:
            # Intentar descargar el dataset
            df, cov_meta = bcn_extractor.download_dataset(
                dataset_id,
                resource_format='csv',
                year_start=year_start,
                year_end=year_end
            )
            
            if df is None or df.empty:
                metadata["error"] = "No se obtuvieron datos"
                return None, metadata
            
            # Validar que tiene las columnas necesarias
            barrio_cols = ['barrio', 'barri', 'Codi_Barri', 'barrio_id', 'Nom_Barri', 'Barris']
            has_barrio_col = any(col in df.columns for col in barrio_cols)
            
            if not has_barrio_col:
                logger.warning("⚠️  Dataset no tiene columna de barrio identificable")
                logger.info(f"Columnas disponibles: {list(df.columns)}")
                metadata["warning"] = "Columnas de barrio no identificadas"
                metadata["error"] = "Dataset no contiene datos por barrio (puede ser a nivel distrito o municipio)"
                # No retornar error, pero marcar como warning para que el usuario lo sepa
            
            # Validar que tiene datos de renta
            # Buscar columnas que indiquen renta/ingresos (incluyendo "Import_Euros", "Import", "Euros")
            renta_keywords = ['renta', 'ingressos', 'income', 'disponible', 'renda', 'import', 'euros', '€']
            has_renta_col = any(
                any(kw in col.lower() for kw in renta_keywords)
                for col in df.columns
            )
            
            if not has_renta_col:
                logger.warning("⚠️  Dataset no tiene columna de renta identificable")
                logger.info(f"Columnas disponibles: {list(df.columns)}")
                metadata["warning"] = "Columnas de renta no identificadas"
                # Verificar si es un dataset de presupuesto (no renta familiar)
                if any(kw in str(dataset_id).lower() for kw in ['pressupost', 'presupuesto', 'budget', 'evolucio-ingressos']):
                    metadata["error"] = "Dataset parece ser de presupuesto municipal, no de renta familiar por barrio"
            else:
                # Identificar la columna de renta para logging
                renta_cols = [col for col in df.columns if any(kw in col.lower() for kw in renta_keywords)]
                if renta_cols:
                    logger.info(f"✓ Columnas de renta identificadas: {renta_cols}")
            
            metadata["success"] = True
            metadata["records"] = len(df)
            metadata["columns"] = list(df.columns)
            metadata["method_used"] = "ckan_api"
            metadata.update(cov_meta)
            
            logger.info(f"✓ Datos de renta extraídos: {len(df)} registros")
            
            return df, metadata
            
        except Exception as e:
            logger.error(f"Error extrayendo renta: {e}")
            logger.debug(traceback.format_exc())
            metadata["error"] = str(e)
            return None, metadata


class DemografiaAmpliadaExtractor(BaseExtractor):
    """
    Extractor para datos demográficos ampliados del Padrón Municipal.
    
    Busca específicamente:
    1. Población por edad quinquenal y sexo por barrios
    2. Población por nacionalidad y sexo por barrios
    3. Hogares por tipo y número de miembros por barrios
    """
    
    BASE_URL = "https://opendata-ajuntament.barcelona.cat"
    API_URL = f"{BASE_URL}/data/api/3/action"
    
    # IDs CONOCIDOS Y CONFIRMADOS (de ejecución real y búsqueda manual - probar primero)
    KNOWN_DATASET_IDS = {
        "edad_quinquenal": [
            # ✅ PRIORIDAD MÁXIMA: Datos POR BARRIO con edad quinquenal
            "pad_mdb_lloc-naix-continent_edat-q_sexe",  # ✅ CONFIRMADO: Población por continente de nacimiento, sexe y edad quinquenal POR BARRIO
            # ✅ ENCONTRADOS en ejecución real (pero agregados a nivel Barcelona, no por barrio):
            "pad_mdb_nacionalitat-contintent_edat-q_sexe",  # Población por continente, edad quinquenal y sexo (agregado Barcelona)
            "pad_mdb_nacionalitat-g_edat-q_sexe",  # Población por nacionalidad (España/UE/Resto), edad quinquenal y sexo (agregado Barcelona)
            # Nota: pad_mdbas_sexe NO tiene edad quinquenal, solo sexo
        ],
        "nacionalidad": [
            # ✅ PRIORIDAD MÁXIMA: Datos POR BARRIO con continente de nacimiento
            "pad_mdb_lloc-naix-continent_edat-q_sexe",  # ✅ CONFIRMADO: Continente de nacimiento POR BARRIO (puede usarse como proxy de nacionalidad)
            # ✅ ENCONTRADOS en ejecución real:
            "pad_mdb_nacionalitat-contintent_edat-q_sexe",  # Por continente (agregado Barcelona)
            "pad_mdb_nacionalitat-g_edat-q_sexe",  # Por grupo (España/UE/Resto) (agregado Barcelona)
            "pad_mdbas_nacionalitat-continent_sexe",  # Por continente y sexo (agregado Barcelona)
            "pad_mdb_nacionalitat-regio_sexe",  # Por región geográfica (agregado Barcelona)
            "pad_dom_mdbas_nacionalitat",  # Hogares por nacionalidad
        ],
        "hogares": [
            # ✅ ENCONTRADOS en ejecución real:
            "pad_dom_mdbas_nacionalitat",  # Hogares por nacionalidad
            # Nota: Buscar específicamente "llars" o "hogares" en búsqueda
        ],
    }
    
    # IDs genéricos a probar si los específicos fallan
    FALLBACK_DATASET_IDS = [
        "pad_mdbas_sexe",  # Ya confirmado - población por sexo (pero NO tiene edad quinquenal ni hogares)
        "poblacio-per-barris",
        "padro-municipal",
    ]
    
    # Palabras clave para búsqueda (solo si IDs conocidos fallan)
    DATASET_QUERIES = {
        "edad_quinquenal": [
            "edat quinquennal",
            "edad quinquenal",
            "poblacio per edat",
            "población por edad",
            "padro edat",
            "padrón edad",
        ],
        "nacionalidad": [
            "nacionalitat",
            "nacionalidad",
            "poblacio per nacionalitat",
            "población por nacionalidad",
        ],
        "hogares": [
            "llars per tipus",
            "hogares por tipo",
            "llars per nombre de membres",
            "hogares por número de miembros",
            "tipus de llar",
            "tipo de hogar",
        ],
    }
    
    # Patrones de nombres de columnas (para validación rápida)
    COLUMN_PATTERNS = {
        "barrio": [
            "Nom_Barri", "Codi_Barri", "Barris", "barrio", "barri", "barrio_id"
        ],
        "año": [
            "Any", "Año", "year", "anio"
        ],
        "edad_quinquenal": [
            "Edat", "Edad", "Grups d'edat", "Grupos de edad", "0-4", "5-9", "10-14"
        ],
        "nacionalidad": [
            "Nacionalitat", "Nacionalidad", "Pais", "País", "Espanya", "Estranger"
        ],
        "hogares": [
            "Llars", "Hogares", "Tipus de llar", "Tipo de hogar", "1 persona", "2 persones"
        ],
    }
    
    def __init__(self, rate_limit_delay: float = 1.5, output_dir: Optional[Path] = None):
        """Inicializa el extractor de demografía ampliada."""
        super().__init__("DemografiaAmpliada", rate_limit_delay, output_dir)
    
    def search_demografia_datasets(self, tipo: str = "all") -> Dict[str, list]:
        """
        Busca datasets de demografía ampliada en Open Data BCN.
        
        ESTRATEGIA DE BÚSQUEDA (optimizada):
        1. Probar primero IDs conocidos (más rápido)
        2. Si fallan, buscar por palabras clave
        3. Clasificar resultados automáticamente
        
        Args:
            tipo: Tipo de datos a buscar ("edad_quinquenal", "nacionalidad", "hogares", "all")
            
        Returns:
            Diccionario con listas de datasets encontrados por tipo
        """
        logger.info("Buscando datasets de demografía ampliada...")
        
        bcn_extractor = OpenDataBCNExtractor()
        
        found_datasets = {
            "edad_quinquenal": [],
            "nacionalidad": [],
            "hogares": [],
        }
        
        # Buscar por tipo específico o todos
        tipos_a_buscar = [tipo] if tipo != "all" else list(self.DATASET_QUERIES.keys())
        
        # PASO 1: Probar IDs conocidos primero (más eficiente)
        logger.info("\n🔍 PASO 1: Probando IDs conocidos (prioridad alta)...")
        for tipo_dato in tipos_a_buscar:
            known_ids = self.KNOWN_DATASET_IDS.get(tipo_dato, [])
            for dataset_id in known_ids:
                info = bcn_extractor.get_dataset_info(dataset_id)
                if info:
                    found_datasets[tipo_dato].append(dataset_id)
                    logger.info(f"  ✓ ID conocido encontrado: {dataset_id}")
                    logger.info(f"    Título: {info.get('title', 'Sin título')[:60]}")
                else:
                    logger.debug(f"  ✗ ID conocido no encontrado: {dataset_id}")
        
        # PASO 2: Probar IDs fallback
        logger.info("\n🔍 PASO 2: Probando IDs fallback...")
        for dataset_id in self.FALLBACK_DATASET_IDS:
            if dataset_id in [ds for lst in found_datasets.values() for ds in lst]:
                continue  # Ya encontrado
            
            info = bcn_extractor.get_dataset_info(dataset_id)
            if info:
                # Clasificar por título
                title = info.get('title', '').lower()
                classified = False
                
                for tipo_dato in tipos_a_buscar:
                    if tipo_dato == "edad_quinquenal" and any(kw in title for kw in ['edat', 'edad', 'quinquennal']):
                        found_datasets[tipo_dato].append(dataset_id)
                        classified = True
                    elif tipo_dato == "nacionalidad" and any(kw in title for kw in ['nacionalitat', 'nacionalidad']):
                        found_datasets[tipo_dato].append(dataset_id)
                        classified = True
                    elif tipo_dato == "hogares" and any(kw in title for kw in ['llar', 'hogar']):
                        found_datasets[tipo_dato].append(dataset_id)
                        classified = True
                
                if not classified:
                    # Agregar a todos si no se puede clasificar
                    for tipo_dato in tipos_a_buscar:
                        found_datasets[tipo_dato].append(dataset_id)
                
                logger.info(f"  ✓ Dataset fallback encontrado: {dataset_id}")
        
        # PASO 3: Búsqueda por palabras clave (solo si no se encontraron suficientes y LIMITADA)
        logger.info("\n🔍 PASO 3: Búsqueda por palabras clave (limitada, solo si necesario)...")
        for tipo_dato in tipos_a_buscar:
            if len(found_datasets[tipo_dato]) >= 2:
                logger.info(f"  ⏭️  Saltando búsqueda de '{tipo_dato}' (ya hay {len(found_datasets[tipo_dato])} datasets)")
                continue
            
            logger.info(f"\nBuscando datasets de '{tipo_dato}' (máximo 2 keywords para evitar demoras)...")
            queries = self.DATASET_QUERIES.get(tipo_dato, [])
            
            # LIMITAR a máximo 2 queries para no tardar tanto
            for query in queries[:2]:  # Solo las 2 primeras
                logger.info(f"  Buscando: '{query}'...")
                datasets = bcn_extractor.search_datasets_by_keyword(query)
                # Solo agregar si no están ya en la lista
                new_datasets = [ds for ds in datasets if ds not in found_datasets[tipo_dato]]
                found_datasets[tipo_dato].extend(new_datasets)
                
                if new_datasets:
                    logger.info(f"  ✓ Encontrados {len(new_datasets)} datasets nuevos con '{query}'")
                    for ds_id in new_datasets[:3]:  # Mostrar primeros 3
                        info = bcn_extractor.get_dataset_info(ds_id)
                        if info:
                            logger.info(f"    - {ds_id}: {info.get('title', 'Sin título')[:60]}")
                
                # Si ya encontramos suficientes, parar
                if len(found_datasets[tipo_dato]) >= 3:
                    logger.info(f"  ✓ Suficientes datasets encontrados. Parando búsqueda.")
                    break
        
        # Eliminar duplicados y mostrar resumen
        logger.info("\n" + "="*60)
        logger.info("RESUMEN DE BÚSQUEDA")
        logger.info("="*60)
        for key in found_datasets:
            found_datasets[key] = list(set(found_datasets[key]))
            logger.info(f"  {key:20s}: {len(found_datasets[key])} datasets encontrados")
            if found_datasets[key]:
                logger.info(f"    IDs: {', '.join(found_datasets[key][:5])}")
        
        return found_datasets
    
    def extract_demografia_ampliada(
        self,
        tipo: str,
        year_start: int = 2015,
        year_end: int = 2024,
        dataset_id: Optional[str] = None
    ) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Extrae datos demográficos ampliados por barrio.
        
        Args:
            tipo: Tipo de datos ("edad_quinquenal", "nacionalidad", "hogares")
            year_start: Año inicial
            year_end: Año final
            dataset_id: ID del dataset (si None, busca automáticamente)
            
        Returns:
            Tupla con (DataFrame o None, metadata)
        """
        logger.info(f"=== Extrayendo datos de '{tipo}' ({year_start}-{year_end}) ===")
        
        metadata = {
            "extraction_date": datetime.now().isoformat(),
            "tipo": tipo,
            "requested_range": {"start": year_start, "end": year_end},
            "success": False,
            "dataset_id": dataset_id,
            "datasets_tried": [],
        }
        
        bcn_extractor = OpenDataBCNExtractor(output_dir=self.output_dir)
        
        # Si no se especifica dataset, buscar
        if dataset_id is None:
            all_datasets = self.search_demografia_datasets(tipo=tipo)
            candidates = all_datasets.get(tipo, [])
            
            if not candidates:
                logger.error(f"No se encontraron datasets de '{tipo}'")
                metadata["error"] = f"No se encontraron datasets de '{tipo}'"
                metadata["datasets_found"] = all_datasets
                return None, metadata
            
            # Seleccionar el mejor candidato (priorizar IDs conocidos)
            # Ordenar: primero los que están en KNOWN_DATASET_IDS, luego los demás
            known_ids = self.KNOWN_DATASET_IDS.get(tipo, [])
            sorted_candidates = []
            
            # Primero los conocidos
            for known_id in known_ids:
                if known_id in candidates:
                    sorted_candidates.append(known_id)
            
            # Luego los demás
            for candidate in candidates:
                if candidate not in sorted_candidates:
                    sorted_candidates.append(candidate)
            
            dataset_id = sorted_candidates[0] if sorted_candidates else candidates[0]
            logger.info(f"Usando dataset: {dataset_id}")
            if len(sorted_candidates) > 1:
                logger.info(f"  (Hay {len(sorted_candidates)-1} datasets alternativos disponibles)")
                logger.info(f"  Alternativas: {', '.join(sorted_candidates[1:3])}")
        
        metadata["dataset_id"] = dataset_id
        metadata["datasets_tried"].append(dataset_id)
        
        try:
            # Intentar descargar el dataset
            df, cov_meta = bcn_extractor.download_dataset(
                dataset_id,
                resource_format='csv',
                year_start=year_start,
                year_end=year_end
            )
            
            if df is None or df.empty:
                metadata["error"] = "No se obtuvieron datos"
                return None, metadata
            
            # Validar columnas usando patrones conocidos (más eficiente)
            barrio_col = None
            for pattern in self.COLUMN_PATTERNS["barrio"]:
                if pattern in df.columns:
                    barrio_col = pattern
                    break
            
            if barrio_col is None:
                logger.warning("⚠️  Dataset no tiene columna de barrio identificable")
                logger.info(f"Columnas disponibles: {list(df.columns)}")
                metadata["warning"] = "Columnas de barrio no identificadas"
                metadata["available_columns"] = list(df.columns)
            else:
                logger.info(f"✓ Columna de barrio encontrada: '{barrio_col}'")
                metadata["barrio_column"] = barrio_col
            
            # Validar columnas específicas usando patrones conocidos
            tipo_patterns = self.COLUMN_PATTERNS.get(tipo, [])
            if tipo_patterns:
                found_cols = [col for col in df.columns if any(
                    pattern.lower() in col.lower() for pattern in tipo_patterns
                )]
                if found_cols:
                    logger.info(f"✓ Columnas de '{tipo}' encontradas: {found_cols[:5]}")
                    metadata[f"{tipo}_columns"] = found_cols
                else:
                    logger.warning(f"⚠️  No se encontraron columnas de '{tipo}' usando patrones conocidos")
                    logger.info(f"   Patrones buscados: {tipo_patterns[:3]}...")
                    logger.info(f"   Columnas disponibles: {list(df.columns)[:10]}...")
                    metadata["warning"] = f"Columnas de {tipo} no encontradas con patrones estándar"
                    
                    # Validación adicional: verificar si el dataset realmente tiene el tipo de dato esperado
                    if tipo == "edad_quinquenal":
                        # pad_mdbas_sexe NO tiene edad quinquenal, solo sexo
                        if "pad_mdbas_sexe" in str(dataset_id):
                            logger.error("❌ Dataset 'pad_mdbas_sexe' solo tiene datos de sexo, NO tiene edad quinquenal")
                            metadata["error"] = "Dataset incorrecto: pad_mdbas_sexe no contiene edad quinquenal"
                            metadata["suggestion"] = "Usar pad_mdb_nacionalitat-contintent_edat-q_sexe o pad_mdb_nacionalitat-g_edat-q_sexe"
                    
                    elif tipo == "hogares":
                        # pad_mdbas_sexe NO tiene datos de hogares
                        if "pad_mdbas_sexe" in str(dataset_id):
                            logger.error("❌ Dataset 'pad_mdbas_sexe' no tiene datos de hogares")
                            metadata["error"] = "Dataset incorrecto: pad_mdbas_sexe no contiene datos de hogares"
                            metadata["suggestion"] = "Buscar datasets con 'llars' o 'hogares' en el nombre"
            
            metadata["success"] = True
            metadata["records"] = len(df)
            metadata["columns"] = list(df.columns)
            metadata.update(cov_meta)
            
            logger.info(f"✓ Datos de '{tipo}' extraídos: {len(df)} registros")
            
            # Advertencia sobre normalización de nombres
            if barrio_col:
                sample_barrios = df[barrio_col].dropna().unique()[:5]
                logger.info(f"  Muestra de nombres de barrios: {list(sample_barrios)}")
                logger.warning(
                    "⚠️  IMPORTANTE: Los nombres de barrios pueden requerir normalización "
                    "para hacer JOIN con dim_barrios. Revisar data_processing.py::_normalize_text()"
                )
            
            return df, metadata
            
        except Exception as e:
            logger.error(f"Error extrayendo '{tipo}': {e}")
            logger.debug(traceback.format_exc())
            metadata["error"] = str(e)
            return None, metadata


class IDESCATExtractor(BaseExtractor):
    """Extractor para datos demográficos de IDESCAT API."""
    
    BASE_URL = "https://api.idescat.cat"
    API_BASE = f"{BASE_URL}/pob/v1"
    
    # Código de Barcelona: 080193
    BARCELONA_CODE = "080193"
    
    # Endpoints conocidos
    ENDPOINTS = {
        "barrios": f"{API_BASE}/barri",
        "distritos": f"{API_BASE}/districte",
        "municipio": f"{API_BASE}/mun",
    }
    
    def __init__(self, rate_limit_delay: float = 1.5, output_dir: Optional[Path] = None):
        """Inicializa el extractor de IDESCAT."""
        super().__init__("IDESCAT", rate_limit_delay, output_dir)
    
    def extract_demografia_barrios(
        self,
        year: int = 2023,
        lang: str = "es"
    ) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Extrae datos demográficos por barrios de Barcelona desde IDESCAT API.
        
        Args:
            year: Año de referencia
            lang: Idioma ('es', 'ca', 'en')
            
        Returns:
            Tupla con (DataFrame o None, metadata)
        """
        logger.info(f"=== Extrayendo demografía IDESCAT para barrios (año {year}) ===")
        
        metadata = {
            "extraction_date": datetime.now().isoformat(),
            "success": False,
            "year": year,
            "source": "idescat_api",
            "endpoint": self.ENDPOINTS["barrios"],
        }
        
        try:
            # Construir URL con parámetros
            url = self.ENDPOINTS["barrios"]
            params = {
                "date": str(year),
                "id": self.BARCELONA_CODE,
                "lang": lang,
            }
            
            logger.info(f"Consultando API IDESCAT: {url}")
            logger.info(f"Parámetros: {params}")
            
            self._rate_limit()
            response = self.session.get(url, params=params, timeout=60)
            
            if not self._validate_response(response):
                metadata["error"] = f"Error HTTP {response.status_code}"
                return None, metadata
            
            # IDESCAT API devuelve JSON
            data = response.json()
            
            # La estructura de respuesta de IDESCAT puede variar
            # Intentar parsear según estructura esperada
            if isinstance(data, dict):
                # Guardar respuesta raw para inspección
                filepath = self._save_raw_data(
                    data,
                    f"idescat_barrios_{year}",
                    'json'
                )
                metadata["raw_filepath"] = str(filepath)
                
                # Intentar convertir a DataFrame
                # La estructura exacta depende de la API
                # Por ahora, guardamos el JSON y documentamos
                logger.info("✓ Datos de IDESCAT descargados")
                logger.info("⚠️  Nota: La estructura de datos requiere inspección manual")
                logger.info(f"   Archivo guardado en: {filepath}")
                
                metadata["success"] = True
                metadata["data_structure"] = type(data).__name__
                
                # Intentar extraer DataFrame si es posible
                df = None
                if isinstance(data, dict) and "result" in data:
                    # Estructura típica de API
                    result = data["result"]
                    if isinstance(result, list):
                        df = pd.DataFrame(result)
                    elif isinstance(result, dict):
                        df = pd.DataFrame([result])
                
                return df, metadata
            else:
                metadata["error"] = "Formato de respuesta inesperado"
                return None, metadata
                
        except Exception as e:
            logger.error(f"Error extrayendo datos IDESCAT: {e}")
            logger.debug(traceback.format_exc())
            metadata["error"] = str(e)
            return None, metadata


class InsideAirbnbExtractor(BaseExtractor):
    """Extractor para datos de InsideAirbnb (descarga directa)."""
    
    BASE_URL = "http://insideairbnb.com"
    BARCELONA_DATA_URL = f"{BASE_URL}/get-the-data.html"
    
    # URLs conocidas para Barcelona (pueden cambiar con el tiempo)
    KNOWN_FILE_PATTERNS = {
        "listings": "listings.csv.gz",
        "calendar": "calendar.csv.gz",
        "reviews": "reviews.csv.gz",
    }
    
    def __init__(self, rate_limit_delay: float = 2.0, output_dir: Optional[Path] = None):
        """Inicializa el extractor de InsideAirbnb."""
        super().__init__("InsideAirbnb", rate_limit_delay, output_dir)
    
    def find_barcelona_data_urls(self) -> Dict[str, str]:
        """
        Busca las URLs de descarga para Barcelona en InsideAirbnb.
        
        Returns:
            Diccionario con tipo de archivo -> URL
        """
        logger.info("Buscando URLs de datos de Barcelona en InsideAirbnb...")
        
        urls = {}
        
        try:
            self._rate_limit()
            response = self.session.get(self.BARCELONA_DATA_URL, timeout=60)
            
            if not self._validate_response(response):
                logger.error(f"Error accediendo a {self.BARCELONA_DATA_URL}")
                return urls
            
            # Parsear HTML para encontrar enlaces a archivos de Barcelona
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscar enlaces que contengan "barcelona" y los patrones conocidos
            for link in soup.find_all('a', href=True):
                href = link.get('href', '').lower()
                text = link.get_text().lower()
                
                if 'barcelona' in href or 'barcelona' in text:
                    for file_type, pattern in self.KNOWN_FILE_PATTERNS.items():
                        if pattern.replace('.gz', '') in href or pattern in href:
                            full_url = link['href']
                            if not full_url.startswith('http'):
                                full_url = self.BASE_URL + full_url
                            urls[file_type] = full_url
                            logger.info(f"  ✓ Encontrado {file_type}: {full_url[:80]}...")
            
            if not urls:
                logger.warning("No se encontraron URLs de Barcelona. Puede que la estructura del sitio haya cambiado.")
                logger.info("Intentando construir URLs directas...")
                # Intentar construir URLs directas (estructura típica)
                base_data_url = f"{self.BASE_URL}/data"
                for file_type, pattern in self.KNOWN_FILE_PATTERNS.items():
                    # Estructura típica: /data/spain/catalonia/barcelona/YYYY-MM-DD/listings.csv.gz
                    # Necesitamos encontrar la fecha más reciente
                    urls[file_type] = f"{base_data_url}/spain/catalonia/barcelona/{pattern}"
            
        except ImportError:
            logger.error("BeautifulSoup4 no está instalado. Instalar con: pip install beautifulsoup4")
            logger.info("Intentando URLs directas sin parsing HTML...")
        except Exception as e:
            logger.error(f"Error buscando URLs de InsideAirbnb: {e}")
            logger.debug(traceback.format_exc())
        
        return urls
    
    def extract_airbnb_data(
        self,
        file_types: Optional[list] = None
    ) -> Tuple[Dict[str, Optional[pd.DataFrame]], Dict[str, Any]]:
        """
        Extrae datos de InsideAirbnb para Barcelona.
        
        Args:
            file_types: Lista de tipos a extraer (None = todos disponibles)
                       Opciones: 'listings', 'calendar', 'reviews'
        
        Returns:
            Tupla con (dict de DataFrames, metadata)
        """
        logger.info("=== Extrayendo datos de InsideAirbnb para Barcelona ===")
        
        metadata = {
            "extraction_date": datetime.now().isoformat(),
            "success": False,
            "source": "insideairbnb",
            "files_downloaded": [],
            "files_failed": [],
        }
        
        if file_types is None:
            file_types = list(self.KNOWN_FILE_PATTERNS.keys())
        
        results = {}
        
        # Buscar URLs
        urls = self.find_barcelona_data_urls()
        
        if not urls:
            metadata["error"] = "No se encontraron URLs de descarga para Barcelona"
            return results, metadata
        
        # Descargar cada tipo de archivo
        for file_type in file_types:
            if file_type not in urls:
                logger.warning(f"No se encontró URL para {file_type}")
                results[file_type] = None
                metadata["files_failed"].append(file_type)
                continue
            
            url = urls[file_type]
            logger.info(f"\n--- Descargando {file_type} ---")
            logger.info(f"URL: {url}")
            
            try:
                self._rate_limit()
                response = self.session.get(url, timeout=120, stream=True)
                
                if not self._validate_response(response):
                    logger.error(f"Error descargando {file_type}: HTTP {response.status_code}")
                    results[file_type] = None
                    metadata["files_failed"].append(file_type)
                    continue
                
                # Guardar archivo comprimido
                filename = f"insideairbnb_{file_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # Crear directorio de destino
                source_dir = self.output_dir / self.source_name.lower().replace(' ', '_')
                source_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                
                if url.endswith('.gz'):
                    # Guardar archivo comprimido
                    filepath = source_dir / f"{filename}_{timestamp}.csv.gz"
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    # Descomprimir y leer CSV
                    import gzip
                    import io
                    with gzip.open(filepath, 'rb') as f:
                        df = pd.read_csv(io.BytesIO(f.read()), low_memory=False)
                else:
                    # CSV sin comprimir - guardar directamente
                    filepath = source_dir / f"{filename}_{timestamp}.csv"
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    df = pd.read_csv(filepath, low_memory=False)
                
                logger.info(f"Datos guardados en: {filepath}")
                
                results[file_type] = df
                metadata["files_downloaded"].append(file_type)
                metadata[f"{file_type}_records"] = len(df)
                metadata[f"{file_type}_columns"] = list(df.columns)
                
                logger.info(f"✓ {file_type} descargado: {len(df)} registros, {len(df.columns)} columnas")
                
            except Exception as e:
                logger.error(f"Error descargando {file_type}: {e}")
                logger.debug(traceback.format_exc())
                results[file_type] = None
                metadata["files_failed"].append(file_type)
                metadata[f"{file_type}_error"] = str(e)
        
        metadata["success"] = len(metadata["files_downloaded"]) > 0
        
        return results, metadata


def extract_priority_sources(
    year_start: int = 2015,
    year_end: int = 2024,
    sources: Optional[list] = None,
    continue_on_error: bool = True
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Extrae fuentes de datos prioritarias.
    
    Args:
        year_start: Año inicial
        year_end: Año final
        sources: Lista de fuentes a extraer (None = todas las prioritarias)
        continue_on_error: Si True, continúa con otras fuentes si una falla
        
    Returns:
        Tupla con (resultados, metadata)
    """
    if sources is None:
        sources = ["geojson", "renta", "demografia"]
    
    # Alias y normalización
    source_aliases = {
        "censo": "demografia",
        "insideairbnb": "airbnb",
    }
    
    sources = [source_aliases.get(s, s) for s in sources]
    sources = list(set(sources))  # Eliminar duplicados
    
    # IDESCAT como fuente adicional de demografía
    if "idescat" in sources:
        sources.append("demografia_idescat")
        sources = list(set(sources))
    
    results = {}
    metadata = {
        "extraction_date": datetime.now().isoformat(),
        "requested_range": {"start": year_start, "end": year_end},
        "sources_requested": sources,
        "sources_success": [],
        "sources_failed": [],
    }
    
    # GeoJSON
    if "geojson" in sources:
        try:
            logger.info("\n" + "="*80)
            logger.info("EXTRACCIÓN DE GEOJSON DE BARRIOS")
            logger.info("="*80)
            
            geojson_extractor = GeoJSONExtractor()
            geojson_data, geojson_meta = geojson_extractor.extract_geojson()
            
            results["geojson"] = geojson_data
            metadata["geojson"] = geojson_meta
            
            if geojson_data is not None:
                metadata["sources_success"].append("geojson")
            else:
                metadata["sources_failed"].append("geojson")
                
        except Exception as e:
            logger.error(f"Error en extracción GeoJSON: {e}")
            logger.debug(traceback.format_exc())
            results["geojson"] = None
            metadata["geojson"] = {"error": str(e)}
            metadata["sources_failed"].append("geojson")
            if not continue_on_error:
                raise
    
    # Renta
    if "renta" in sources:
        try:
            logger.info("\n" + "="*80)
            logger.info("EXTRACCIÓN DE RENTA FAMILIAR")
            logger.info("="*80)
            
            renta_extractor = RentaExtractor()
            renta_df, renta_meta = renta_extractor.extract_renta(year_start, year_end)
            
            results["renta"] = renta_df
            metadata["renta"] = renta_meta
            
            if renta_df is not None and not renta_df.empty:
                metadata["sources_success"].append("renta")
            else:
                metadata["sources_failed"].append("renta")
                
        except Exception as e:
            logger.error(f"Error en extracción Renta: {e}")
            logger.debug(traceback.format_exc())
            results["renta"] = None
            metadata["renta"] = {"error": str(e)}
            metadata["sources_failed"].append("renta")
            if not continue_on_error:
                raise
    
    # Demografía Ampliada (reemplaza "censo")
    if "demografia" in sources or "censo" in sources:
        try:
            logger.info("\n" + "="*80)
            logger.info("EXTRACCIÓN DE DEMOGRAFÍA AMPLIADA")
            logger.info("="*80)
            logger.info("Buscando: edad quinquenal, nacionalidad, y composición de hogares")
            
            demo_extractor = DemografiaAmpliadaExtractor()
            
            # Extraer cada tipo de dato
            tipos = ["edad_quinquenal", "nacionalidad", "hogares"]
            for tipo in tipos:
                try:
                    logger.info(f"\n--- Extrayendo: {tipo} ---")
                    df, tipo_meta = demo_extractor.extract_demografia_ampliada(
                        tipo=tipo,
                        year_start=year_start,
                        year_end=year_end
                    )
                    
                    results[f"demografia_{tipo}"] = df
                    metadata[f"demografia_{tipo}"] = tipo_meta
                    
                    if df is not None and not df.empty:
                        metadata["sources_success"].append(f"demografia_{tipo}")
                    else:
                        metadata["sources_failed"].append(f"demografia_{tipo}")
                except Exception as e:
                    logger.error(f"Error extrayendo {tipo}: {e}")
                    results[f"demografia_{tipo}"] = None
                    metadata[f"demografia_{tipo}"] = {"error": str(e)}
                    metadata["sources_failed"].append(f"demografia_{tipo}")
                    if not continue_on_error:
                        raise
                
        except Exception as e:
            logger.error(f"Error en extracción Demografía Ampliada: {e}")
            logger.debug(traceback.format_exc())
            for tipo in ["edad_quinquenal", "nacionalidad", "hogares"]:
                if f"demografia_{tipo}" not in results:
                    results[f"demografia_{tipo}"] = None
                    metadata[f"demografia_{tipo}"] = {"error": str(e)}
                    metadata["sources_failed"].append(f"demografia_{tipo}")
            if not continue_on_error:
                raise
    
    # InsideAirbnb
    if "airbnb" in sources or "insideairbnb" in sources:
        try:
            logger.info("\n" + "="*80)
            logger.info("EXTRACCIÓN DE DATOS AIRBNB (InsideAirbnb)")
            logger.info("="*80)
            
            airbnb_extractor = InsideAirbnbExtractor()
            airbnb_results, airbnb_meta = airbnb_extractor.extract_airbnb_data()
            
            results["airbnb"] = airbnb_results
            metadata["airbnb"] = airbnb_meta
            
            if airbnb_meta.get("success", False):
                metadata["sources_success"].append("airbnb")
            else:
                metadata["sources_failed"].append("airbnb")
                
        except Exception as e:
            logger.error(f"Error en extracción InsideAirbnb: {e}")
            logger.debug(traceback.format_exc())
            results["airbnb"] = None
            metadata["airbnb"] = {"error": str(e)}
            metadata["sources_failed"].append("airbnb")
            if not continue_on_error:
                raise
    
    # Resumen
    logger.info("\n" + "="*80)
    logger.info("RESUMEN DE EXTRACCIÓN")
    logger.info("="*80)
    logger.info(f"Fuentes exitosas: {', '.join(metadata['sources_success']) if metadata['sources_success'] else 'Ninguna'}")
    logger.info(f"Fuentes fallidas: {', '.join(metadata['sources_failed']) if metadata['sources_failed'] else 'Ninguna'}")
    
    # Guardar metadata
    metadata_file = PROJECT_ROOT / "data" / "raw" / f"priority_extraction_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    metadata_file.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
    logger.info(f"Metadata guardada en: {metadata_file}")
    
    return results, metadata


if __name__ == "__main__":
    """Ejecutar extracción de fuentes prioritarias."""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Extraer fuentes de datos prioritarias")
    parser.add_argument(
        "--year-start",
        type=int,
        default=2015,
        help="Año inicial (default: 2015)"
    )
    parser.add_argument(
        "--year-end",
        type=int,
        default=2024,
        help="Año final (default: 2024)"
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=["geojson", "renta", "demografia", "censo", "airbnb", "insideairbnb"],  # "censo" es alias de "demografia", "insideairbnb" es alias de "airbnb"
        default=None,
        help="Fuentes a extraer: geojson, renta, demografia, airbnb (default: todas)"
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Detener en el primer error"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Nivel de logging: DEBUG, INFO, WARNING, ERROR (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Configurar nivel de logging
    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR
    }
    selected_level = log_level_map[args.log_level]
    
    # Configurar nivel en todos los loggers relevantes
    logging.getLogger().setLevel(selected_level)
    logger.setLevel(selected_level)
    # También configurar loggers de módulos importados
    logging.getLogger("src.data_extraction").setLevel(selected_level)
    logging.getLogger("src").setLevel(selected_level)
    
    try:
        results, metadata = extract_priority_sources(
            year_start=args.year_start,
            year_end=args.year_end,
            sources=args.sources,
            continue_on_error=not args.fail_fast
        )
        
        # Mostrar resumen
        print("\n" + "="*80)
        print("EXTRACCIÓN COMPLETADA")
        print("="*80)
        print(f"✓ Fuentes exitosas: {len(metadata['sources_success'])}")
        print(f"✗ Fuentes fallidas: {len(metadata['sources_failed'])}")
        
        if metadata['sources_failed']:
            print("\n⚠️  Fuentes con errores:")
            for source in metadata['sources_failed']:
                error = metadata.get(source, {}).get('error', 'Error desconocido')
                print(f"   - {source}: {error}")
        
        sys.exit(0 if metadata['sources_success'] else 1)
        
    except KeyboardInterrupt:
        logger.info("Extracción interrumpida por el usuario")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        logger.debug(traceback.format_exc())
        sys.exit(1)


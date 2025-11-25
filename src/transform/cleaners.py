"""
Data cleaning and transformation module for housing market data.

This module handles neighborhood normalization, geometry processing, and general
data cleaning tasks for the Barcelona Housing Market analysis.
"""

import json
import logging
import re
import unicodedata
from typing import Any, Dict, Optional, Union

import pandas as pd

# Configure logger
logger = logging.getLogger(__name__)


class HousingCleaner:
    """
    Handles data cleaning and normalization for housing market data.
    
    Attributes:
        normalization_pattern: Regex pattern for removing non-alphanumeric characters.
        leading_index_pattern: Regex pattern for removing leading indices (e.g. "1. ").
        aei_suffix_pattern: Regex pattern for removing AEI suffixes.
        footnote_pattern: Regex pattern for removing footnotes like "(1)".
    """

    def __init__(self):
        """Initialize the HousingCleaner with regex patterns."""
        self.normalization_pattern = re.compile(r"[^a-z0-9]+")
        self.leading_index_pattern = re.compile(r"^\d+[\.,]?\s*")
        self.aei_suffix_pattern = re.compile(r"\s*-\s*AEI.*$", re.IGNORECASE)
        self.footnote_pattern = re.compile(r"\s*\(\d+\)$")
        
        self.barrio_alias_overrides = {
            "antigaesquerraeixample": "lantigaesquerradeleixample",
            "novaesquerraeixample": "lanovaesquerradeleixample",
            "vilaolimpicadelpoblenou": "lavilolimpicadelpoblenou",
            "fontdenfargues": "lafontdenfargues",
            "bordeta": "labordeta",
            "marinadeport": "lamarinadeport",
            "marinadelpratvermell": "lamarinadelpratvermell",
            "trinitatnova": "latrinitatnova",
            "trinitatvella": "latrinitatvella",
            "guineueta": "laguineueta",
        }

    def _fix_mojibake(self, text: str) -> str:
        """
        Fix common encoding issues (Mojibake) where UTF-8 was interpreted as Latin-1.

        Args:
            text: The text to fix.

        Returns:
            The fixed text string.
        """
        if not isinstance(text, str):
            return text
        try:
            # Attempt to fix double encoding: encode latin-1, decode utf-8
            return text.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return text

    def normalize_neighborhoods(self, value: Optional[str]) -> str:
        """
        Standardize neighborhood names.

        Applies cleaning patterns (removing indices, suffixes) and normalization
        (lowercasing, removing accents and non-alphanumeric characters).

        Args:
            value: Raw neighborhood name.

        Returns:
            Normalized neighborhood name string.
        """
        if value is None:
            return ""
        
        # Convert to string and strip whitespace
        value = str(value).strip()
        
        # Apply cleaning patterns BEFORE lowercasing/stripping non-alphanumeric
        value = self.leading_index_pattern.sub("", value)
        value = self.aei_suffix_pattern.sub("", value)
        value = self.footnote_pattern.sub("", value)
        
        # Standard normalization
        value = value.lower()
        value = unicodedata.normalize("NFKD", value)
        value = "".join(ch for ch in value if not unicodedata.combining(ch))
        value = self.normalization_pattern.sub("", value)
        
        # Apply overrides
        return self.barrio_alias_overrides.get(value, value)

    def process_geometry(self, geometry_json: Union[str, Dict, Any], barrio_id: Any = None) -> Optional[Dict[str, Any]]:
        """
        Handle geometry_json parsing and validation.

        Parses a JSON string or validates a dictionary to ensure it represents
        a valid geometry object.

        Args:
            geometry_json: JSON string or dictionary containing geometry.
            barrio_id: Optional ID for logging context.

        Returns:
            Parsed geometry dictionary or None if invalid.
        """
        if pd.isna(geometry_json):
            return None

        try:
            # Parse string JSON to dictionary if needed
            geom = (
                json.loads(geometry_json)
                if isinstance(geometry_json, str)
                else geometry_json
            )
            
            # Validate basic structure (GeoJSON geometry should have 'type' and 'coordinates')
            if not isinstance(geom, dict) or 'type' not in geom or 'coordinates' not in geom:
                logger.warning(f"Invalid geometry structure for barrio {barrio_id}: missing type or coordinates")
                return None
                
            return geom

        except (TypeError, json.JSONDecodeError) as e:
            logger.warning(f"Error parsing geometry for barrio {barrio_id}: {e}")
            return None

    def clean_data(self, df: pd.DataFrame, geometry_col: str = 'geometry_json', name_col: str = 'barrio_nombre') -> pd.DataFrame:
        """
        Main orchestration method for the entire cleaning pipeline.

        Processes a DataFrame containing housing data, normalizing neighborhood names
        and parsing geometry fields.

        Args:
            df: Input DataFrame with housing data.
            geometry_col: Name of the column containing geometry JSON.
            name_col: Name of the column containing neighborhood names.

        Returns:
            Cleaned DataFrame with added/modified columns.
        """
        logger.info("Starting data cleaning pipeline...")
        
        cleaned_df = df.copy()

        # Normalize neighborhood names
        if name_col in cleaned_df.columns:
            logger.info(f"Normalizing neighborhood names in column '{name_col}'...")
            # First fix encoding
            cleaned_df[name_col] = cleaned_df[name_col].apply(self._fix_mojibake)
            # Then normalize
            cleaned_df[f'{name_col}_normalized'] = cleaned_df[name_col].apply(self.normalize_neighborhoods)
        else:
            logger.warning(f"Column '{name_col}' not found for normalization.")

        # Process geometry
        if geometry_col in cleaned_df.columns:
            logger.info(f"Processing geometry in column '{geometry_col}'...")
            # We don't replace the original column with dicts because pandas might have issues saving mixed types or dicts to some formats
            # But for "clean_data" processing we might want to validate it.
            # Here we validate and potentially parse. If the goal is to produce a clean DF for analysis, 
            # keeping it as valid JSON string or parsed object depends on usage. 
            # The notebook parsed it for map generation.
            
            # We'll add a validated column or just validate. 
            # Let's parse it to ensure it's valid, but keep as object/dict for internal use if needed.
            cleaned_df['geometry_obj'] = cleaned_df.apply(
                lambda row: self.process_geometry(
                    row[geometry_col], 
                    barrio_id=row.get('barrio_id', 'unknown')
                ), 
                axis=1
            )
            
            # Count valid geometries
            valid_geoms = cleaned_df['geometry_obj'].notna().sum()
            logger.info(f"Successfully processed {valid_geoms} geometries out of {len(cleaned_df)} rows.")
        else:
            logger.warning(f"Column '{geometry_col}' not found for geometry processing.")

        logger.info("Data cleaning pipeline completed.")
        return cleaned_df



import pandas as pd
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

def calculate_affordability_metrics(
    fact_precios: pd.DataFrame,
    fact_renta_hist: pd.DataFrame,
    reference_time: datetime
) -> pd.DataFrame:
    """
    Calculates housing affordability KPIs by neighborhood and year.
    
    Metrics:
    - annual_rent: Mean monthly rent * 12
    - affordability_ratio: annual_rent / renta_neta
    - is_high_stress: affordability_ratio > 0.40
    - is_moderate_stress: affordability_ratio > 0.30
    """
    if fact_precios.empty or fact_renta_hist.empty:
        logger.warning("Cannot calculate affordability: input dataframes are empty")
        return pd.DataFrame()

    # 1. Prepare Rent Data
    # We need average monthly rent per barrio/year
    rent_df = fact_precios[fact_precios["precio_mes_alquiler"].notnull()].copy()
    if rent_df.empty:
        logger.warning("No rent price data available for affordability calculation")
        return pd.DataFrame()
        
    rent_avg = rent_df.groupby(["barrio_id", "anio"])["precio_mes_alquiler"].mean().reset_index()
    rent_avg["annual_rent"] = rent_avg["precio_mes_alquiler"] * 12
    
    # 2. Join with Income Data
    # Prefer renta_neta, fallback to estimated if needed (for 2023)
    income_df = fact_renta_hist.copy()
    
    # Merge
    merged = pd.merge(
        rent_avg,
        income_df[["barrio_id", "anio", "renta_neta", "renta_bruta", "renta_media"]],
        on=["barrio_id", "anio"],
        how="inner"
    )
    
    if merged.empty:
        logger.warning("No overlapping data found between rent prices and income for affordability calculation")
        return pd.DataFrame()
        
    # 3. Calculate Ratio
    # We use renta_neta if available, else renta_media (which might be gross in 2023)
    # To handle 2023 Gross vs Net, we apply a correction factor if only Gross is present
    def get_effective_income(row):
        if pd.notnull(row["renta_neta"]):
            return row["renta_neta"]
        # If we only have gross (like 2023), estimate net using 0.60 factor
        if pd.notnull(row["renta_bruta"]):
            return row["renta_bruta"] * 0.60
        return row["renta_media"]

    merged["effective_income"] = merged.apply(get_effective_income, axis=1)
    
    merged["affordability_ratio"] = merged["annual_rent"] / merged["effective_income"]
    
    # 4. Classification
    merged["stress_level"] = "low"
    merged.loc[merged["affordability_ratio"] > 0.30, "stress_level"] = "moderate"
    merged.loc[merged["affordability_ratio"] > 0.40, "stress_level"] = "high"
    merged.loc[merged["affordability_ratio"] > 0.60, "stress_level"] = "critical"
    
    # Metadata
    merged["etl_loaded_at"] = reference_time.isoformat()
    
    logger.info(f"Affordability metrics calculated: {len(merged)} records")
    return merged

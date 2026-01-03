"""ML Model service for predictions and valuations.

Loads the XGBoost model and provides prediction capabilities.
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class ModelService:
    """Service for ML model predictions."""
    
    def __init__(self):
        """Initialize the model service."""
        self.model: Optional[xgb.XGBRegressor] = None
        self.features = [
            'renta_bruta_llar',
            'indice_penalizacion_topografica',
            'num_plantas_avg',
            'access_penalty',
            'dist_to_center',
            'dist_to_tech_hub',
            'antiguedad_media_bloque',
            'pct_propietarios_extranjeros',
            'indice_gini',
            'pct_juridica',
            'gross_yield',
            'effort_rate',
            'price_growth_1y'
        ]
        self.data_path = PROJECT_ROOT / "data" / "barcelona_ml_valuation.csv"
        self.df: Optional[pd.DataFrame] = None
        
    def load_model(self) -> bool:
        """Load and train the XGBoost model.
        
        Returns:
            bool: True if model loaded successfully
        """
        try:
            # Load data
            if not self.data_path.exists():
                logger.error(f"Data file not found: {self.data_path}")
                return False
                
            self.df = pd.read_csv(self.data_path)
            logger.info(f"Loaded data: {len(self.df)} neighborhoods")
            
            # Train model
            df_clean = self.df.dropna(subset=self.features + ['avg_venta_23']).copy()
            
            if len(df_clean) == 0:
                logger.error("No valid data for training")
                return False
            
            X = df_clean[self.features]
            y = df_clean['avg_venta_23']
            
            self.model = xgb.XGBRegressor(
                objective='reg:squarederror',
                n_estimators=100,      # Improved from 500
                learning_rate=0.04,
                max_depth=3,           # Improved from 6
                gamma=5.0,             # Regularization
                reg_alpha=1.0,         # L1
                reg_lambda=2.0,        # L2
                min_child_weight=3,    # Prevent small leaf splits
                subsample=0.7,
                colsample_bytree=0.7,
                random_state=42,
                n_jobs=-1
            )
            
            self.model.fit(X, y)
            
            # Calculate predictions and deviations for all neighborhoods
            self.df['precio_estimado'] = np.nan
            self.df['desviacion_valor'] = np.nan
            
            valid_idx = df_clean.index
            self.df.loc[valid_idx, 'precio_estimado'] = self.model.predict(X)
            self.df.loc[valid_idx, 'desviacion_valor'] = (
                (self.df.loc[valid_idx, 'avg_venta_23'] - self.df.loc[valid_idx, 'precio_estimado']) 
                / self.df.loc[valid_idx, 'precio_estimado']
            ) * 100
            
            logger.info("Model trained successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def predict(self, barrio_id: int) -> Optional[Dict]:
        """Get prediction for a specific barrio.
        
        Args:
            barrio_id: Barrio ID
            
        Returns:
            Dictionary with prediction data or None if not found
        """
        if self.model is None or self.df is None:
            logger.error("Model not loaded")
            return None
            
        barrio_data = self.df[self.df['barrio_id'] == barrio_id]
        
        if barrio_data.empty:
            logger.warning(f"Barrio {barrio_id} not found")
            return None
        
        row = barrio_data.iloc[0]
        
        return {
            'barrio_id': int(barrio_id),
            'barrio_nombre': row['barrio_nombre'],
            'current_price': float(row['avg_venta_23']) if pd.notna(row['avg_venta_23']) else None,
            'predicted_price': float(row['precio_estimado']) if pd.notna(row['precio_estimado']) else None,
            'deviation_pct': float(row['desviacion_valor']) if pd.notna(row['desviacion_valor']) else None,
        }
    
    def get_investment_recommendations(
        self, 
        budget: float, 
        strategy: str = 'yield',
        max_results: int = 5
    ) -> pd.DataFrame:
        """Get investment recommendations based on budget and strategy.
        
        Args:
            budget: Investment budget in euros
            strategy: 'yield', 'safe', or 'growth'
            max_results: Maximum number of recommendations
            
        Returns:
            DataFrame with recommendations
        """
        if self.df is None:
            logger.error("Data not loaded")
            return pd.DataFrame()
        
        # Assume average property size of 65m²
        avg_size = 65
        options = self.df[self.df['avg_venta_23'] * avg_size <= budget].copy()
        
        if options.empty:
            logger.warning(f"No options found for budget {budget}")
            return pd.DataFrame()
        
        # Sort based on strategy
        if strategy == 'yield':
            reco = options.sort_values('gross_yield', ascending=False).head(max_results)
        elif strategy == 'safe':
            reco = options.sort_values('desviacion_valor', ascending=True).head(max_results)
        else:  # growth
            reco = options.sort_values('price_growth_1y', ascending=False).head(max_results)
        
        # Add estimated total cost
        reco = reco.copy()
        reco['estimated_total_cost'] = reco['avg_venta_23'] * avg_size
        
        # Add segmento if not present
        if 'segmento' not in reco.columns:
            reco['segmento'] = 0
        
        return reco[['barrio_nombre', 'avg_venta_23', 'gross_yield', 'desviacion_valor', 
                     'segmento', 'estimated_total_cost']]
    
    def get_all_neighborhoods(self) -> pd.DataFrame:
        """Get all neighborhoods with their metrics.
        
        Returns:
            DataFrame with all neighborhood data
        """
        if self.df is None:
            return pd.DataFrame()
        
        return self.df.copy()
    
    def get_cluster_info(self) -> Dict[int, Dict]:
        """Get information about each cluster/segment.
        
        Returns:
            Dictionary mapping segment ID to characteristics
        """
        if self.df is None or 'segmento' not in self.df.columns:
            logger.warning("Segmento column missing from data")
            return {}
        
        cluster_info = {}
        
        for seg in self.df['segmento'].dropna().unique():
            seg_data = self.df[self.df['segmento'] == seg]
            
            cluster_info[int(seg)] = {
                'barrios_count': len(seg_data),
                'avg_price': float(seg_data['avg_venta_23'].mean()),
                'avg_yield': float(seg_data['gross_yield'].mean()),
                'characteristics': {
                    'avg_renta': float(seg_data['renta_bruta_llar'].mean()),
                    'avg_gini': float(seg_data['indice_gini'].mean()),
                    'avg_antiguedad': float(seg_data['antiguedad_media_bloque'].mean()),
                }
            }
        
        return cluster_info

    def get_fairness_metrics(self) -> Dict:
        """Calculate model fairness metrics (GES, IPR, PDI).
        
        Returns:
            Dictionary with fairness scores
        """
        if self.df is None or 'precio_estimado' not in self.df.columns:
            return {}
            
        df = self.df.copy()
        df['abs_error'] = np.abs(df['avg_venta_23'] - df['precio_estimado'])
        
        # 1. Geographic Equity Score (GES)
        district_maes = df.groupby('distrito_nombre')['abs_error'].mean()
        ges = 1 - (district_maes.std() / district_maes.mean()) if district_maes.mean() > 0 else 0
        
        # 2. Income Parity Ratio (IPR)
        median_income = df['renta_bruta_llar'].median()
        mae_low = df[df['renta_bruta_llar'] <= median_income]['abs_error'].mean()
        mae_high = df[df['renta_bruta_llar'] > median_income]['abs_error'].mean()
        ipr = mae_low / mae_high if mae_high > 0 else 0
        
        # 3. Prediction Dispersion Index (PDI)
        errors = df['abs_error'].dropna()
        if len(errors) > 0 and np.median(errors) > 0:
            pdi = (np.percentile(errors, 95) - np.percentile(errors, 5)) / np.median(errors)
        else:
            pdi = 0
            
        return {
            'ges': float(ges),
            'ipr': float(ipr),
            'pdi': float(pdi),
            'district_mae': district_maes.to_dict()
        }


# Global instance
_model_service: Optional[ModelService] = None


def get_model_service() -> ModelService:
    """Get or create the global model service instance.
    
    Returns:
        ModelService instance
    """
    global _model_service
    
    if _model_service is None:
        _model_service = ModelService()
        _model_service.load_model()
    
    return _model_service

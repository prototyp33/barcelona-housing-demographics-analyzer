"""Module for housing price prediction using Linear, Lasso, and Ridge regression."""

import os
import sqlite3
import logging
from typing import Dict, Any, Tuple, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LassoCV, LinearRegression, RidgeCV
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
# Get absolute path to the project root
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(ROOT_DIR, "data", "processed", "database.db")
MODELS_DIR = os.path.join(ROOT_DIR, "models")

class PricePredictor:
    """Class to handle training and prediction of housing prices."""
    
    def __init__(self, db_path: str = DB_PATH):
        """
        Initialize the predictor.
        
        Args:
            db_path: Path to the SQLite database.
        """
        self.db_path = db_path
        self.models = {}
        self.feature_cols = [
            "renta_media", "poblacion_total", "porc_jovenes", 
            "porc_mayores", "tasa_paro", "porc_extranjeros", "tam_medio_hogar", "num_airbnb"
        ]
        
    def load_data(self) -> pd.DataFrame:
        """
        Load modeling data from the database view.
        
        Returns:
            pd.DataFrame: Cleaned modeling data.
        """
        if not os.path.exists(self.db_path):
            logger.error(f"Database not found at {self.db_path}")
            raise FileNotFoundError(f"Database not found at {self.db_path}")
            
        conn = sqlite3.connect(self.db_path)
        try:
            df = pd.read_sql("SELECT * FROM vw_model_prices_demografia", conn)
            logger.info(f"Loaded {len(df)} rows from vw_model_prices_demografia")
        finally:
            conn.close()
            
        # Data cleaning: Must have target
        df = df.dropna(subset=["target_precio_m2"])
        
        # Fill missing values in features with median
        df[self.feature_cols] = df[self.feature_cols].fillna(df[self.feature_cols].median())
        
        logger.info(f"Data cleaned. {len(df)} rows remaining for modeling.")
        return df

    def train(self, cv_folds: int = 5) -> Dict[str, Any]:
        """
        Train Linear, Lasso, and Ridge models.
        
        Args:
            cv_folds: Number of cross-validation folds.
            
        Returns:
            Dict[str, Any]: Training results and metrics.
        """
        df = self.load_data()
        
        if len(df) < 20: # Arbitrary minimum
            logger.warning("Insufficient data for training. At least 20 samples required.")
            return {}
            
        X = df[self.feature_cols]
        y = df["target_precio_m2"]
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        results = {}
        
        # 1. Linear Regression (Baseline)
        lr_pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("model", LinearRegression())
        ])
        lr_pipeline.fit(X_train, y_train)
        results["linear"] = self._evaluate_model(lr_pipeline, X_train, y_train, X_test, y_test, cv_folds)
        
        # 2. Ridge Regression
        ridge_alphas = [0.1, 1.0, 10.0, 50.0, 100.0]
        ridge_pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("model", RidgeCV(alphas=ridge_alphas, cv=cv_folds))
        ])
        ridge_pipeline.fit(X_train, y_train)
        results["ridge"] = self._evaluate_model(ridge_pipeline, X_train, y_train, X_test, y_test, cv_folds)
        
        # 3. Lasso Regression
        lasso_alphas = [0.0005, 0.001, 0.01, 0.1, 1.0]
        lasso_pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("model", LassoCV(alphas=lasso_alphas, cv=cv_folds, max_iter=10000))
        ])
        lasso_pipeline.fit(X_train, y_train)
        results["lasso"] = self._evaluate_model(lasso_pipeline, X_train, y_train, X_test, y_test, cv_folds)
        
        self.models = results
        
        # Save feature statistics from the last trained scaler (they should be similar across models)
        if "ridge" in results:
            scaler = results["ridge"]["pipeline"].named_steps["scaler"]
            self.feature_stats = {
                "means": dict(zip(self.feature_cols, scaler.mean_)),
                "scales": dict(zip(self.feature_cols, scaler.scale_))
            }
            
        logger.info("Training complete.")
        return results

    def get_model_insights(self, model_name: str = "ridge") -> Dict[str, Any]:
        """Get coefficients and feature statistics for visualization."""
        if model_name not in self.models:
            self._load_model_from_disk(model_name)
            
        model_data = self.models[model_name]
        pipeline = model_data["pipeline"]
        scaler = pipeline.named_steps["scaler"]
        model = pipeline.named_steps["model"]
        
        # Normalized coefficients
        norm_coeffs = dict(zip(self.feature_cols, model.coef_))
        
        # Real-world impact (un-normalized coefficients)
        # y = beta0 + sum(beta_i * (x_i - mu_i) / sigma_i)
        # impact_i = beta_i / sigma_i (change in y per 1 unit change in x_i)
        real_impacts = {
            col: model.coef_[i] / scaler.scale_[i]
            for i, col in enumerate(self.feature_cols)
        }
        
        return {
            "normalized_coefficients": norm_coeffs,
            "real_world_impacts": real_impacts,
            "intercept": model.intercept_,
            "metrics": {k: v for k, v in model_data.items() if k != "pipeline"}
        }

    def get_marginal_effects(self, model_name: str, base_scenario: pd.DataFrame, feature: str, range_pct: float = 0.5) -> pd.DataFrame:
        """Calculate prediction changes while varying one feature."""
        if model_name not in self.models:
            self._load_model_from_disk(model_name)
            
        base_val = base_scenario[feature].iloc[0]
        # Generate 20 points around the base value
        vals = np.linspace(base_val * (1 - range_pct), base_val * (1 + range_pct), 20)
        
        results = []
        temp_scenario = base_scenario.copy()
        for v in vals:
            temp_scenario[feature] = v
            pred = self.predict(temp_scenario, model_name=model_name)[0]
            results.append({"value": v, "prediction": pred})
            
        return pd.DataFrame(results)

    def _load_model_from_disk(self, model_name: str):
        """Helper to load model from disk."""
        model_path = os.path.join(MODELS_DIR, f"{model_name}_price_model.joblib")
        if os.path.exists(model_path):
            self.models[model_name] = {"pipeline": joblib.load(model_path)}
            # Try to load metrics for coefficients if available
            metrics_path = os.path.join(MODELS_DIR, "model_metrics.joblib")
            if os.path.exists(metrics_path):
                all_metrics = joblib.load(metrics_path)
                if model_name in all_metrics:
                    self.models[model_name].update(all_metrics[model_name])
        else:
            raise ValueError(f"Model {model_name} not found on disk.")

    def _evaluate_model(self, pipeline: Pipeline, X_train: pd.DataFrame, y_train: pd.Series, 
                        X_test: pd.DataFrame, y_test: pd.Series, cv_folds: int) -> Dict[str, Any]:
        """Helper to evaluate and package model results."""
        y_pred = pipeline.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # Cross-validation
        cv_mse_scores = -cross_val_score(
            pipeline, X_train, y_train,
            cv=cv_folds, scoring="neg_mean_squared_error"
        )
        cv_mse_mean = cv_mse_scores.mean()
        
        # Get coefficients (handle pipeline)
        model = pipeline.named_steps["model"]
        coeffs = model.coef_
        
        return {
            "pipeline": pipeline,
            "mse": mse,
            "rmse": np.sqrt(mse),
            "r2": r2,
            "cv_mse": cv_mse_mean,
            "coefficients": dict(zip(X_train.columns, coeffs))
        }

    def save_models(self, path: str = MODELS_DIR):
        """
        Save models and metrics to disk.
        
        Args:
            path: Directory to save the models in.
        """
        if not self.models:
            logger.error("No models to save. Run train() first.")
            return

        if not os.path.exists(path):
            os.makedirs(path)
            
        for name, data in self.models.items():
            model_path = os.path.join(path, f"{name}_price_model.joblib")
            joblib.dump(data["pipeline"], model_path)
            logger.info(f"Saved {name} model to {model_path}")
            
        # Also save metadata/metrics (excluding the pipeline objects)
        metrics = {
            name: {k: v for k, v in data.items() if k != "pipeline"} 
            for name, data in self.models.items()
        }
        
        # Add feature stats for normalization recovery if available
        if hasattr(self, "feature_stats"):
            metrics["feature_stats"] = self.feature_stats
            
        metrics_path = os.path.join(path, "model_metrics.joblib")
        joblib.dump(metrics, metrics_path)
        logger.info(f"Saved model metrics and stats to {metrics_path}")

    def predict(self, input_data: pd.DataFrame, model_name: str = "ridge") -> np.ndarray:
        """
        Predict prices using a saved model.
        
        Args:
            input_data: DataFrame with features.
            model_name: Name of the model to use ('linear', 'ridge', 'lasso').
            
        Returns:
            np.ndarray: Predicted prices per m2.
        """
        if model_name not in self.models:
            # Try to load from disk
            model_path = os.path.join(MODELS_DIR, f"{model_name}_price_model.joblib")
            if os.path.exists(model_path):
                self.models[model_name] = {"pipeline": joblib.load(model_path)}
            else:
                logger.error(f"Model {model_name} not found.")
                raise ValueError(f"Model {model_name} not found.")
                
        return self.models[model_name]["pipeline"].predict(input_data)

if __name__ == "__main__":
    predictor = PricePredictor()
    try:
        results = predictor.train()
        if results:
            print("\nTraining Results:")
            for name, data in results.items():
                print(f"{name.capitalize():<10}: R2 = {data['r2']:.4f}, RMSE = {data['rmse']:.2f}, CV MSE = {data['cv_mse']:.2f}")
            predictor.save_models()
        else:
            print("No results returned. Check if database has enough data.")
    except Exception as e:
        print(f"Error during training: {e}")

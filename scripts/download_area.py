
from src.extraction.opendata import OpenDataBCNExtractor
import pandas as pd

extractor = OpenDataBCNExtractor()
dataset_id = "est-superficie"
df, meta = extractor.download_dataset(dataset_id)
if df is not None:
    print(f"Downloaded {dataset_id}. Columns: {list(df.columns)}")
    print(df.head())
else:
    print(f"Failed to download {dataset_id}")

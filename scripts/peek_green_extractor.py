
from src.extraction.opendata import OpenDataBCNExtractor
import pandas as pd

extractor = OpenDataBCNExtractor()
url = "https://opendata-ajuntament.barcelona.cat/data/dataset/parcs-i-jardins/resource/a933230a-9d92-4f36-932f-7634f107384a/download/opendatabcn_cultura_parcs-i-jardins.csv"
df = extractor.download_and_parse_csv(url)
if not df.empty:
    print(f"Columns: {list(df.columns)}")
    print(df.head())
    print(f"Total entries: {len(df)}")
else:
    print("Failed to load CSV")

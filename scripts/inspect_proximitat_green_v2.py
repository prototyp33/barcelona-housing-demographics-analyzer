
from src.extraction.opendata import OpenDataBCNExtractor
import pandas as pd

extractor = OpenDataBCNExtractor()
dataset_id = "proximitat-espais-verds"
info = extractor.get_dataset_info(dataset_id)
if info:
    resources = info.get('resources', [])
    for r in resources:
        print(f"Name: {r['name']}, Format: {r['format']}, URL: {r['url']}")
else:
    print(f"Dataset {dataset_id} not found")

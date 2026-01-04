
from src.extraction.opendata import OpenDataBCNExtractor
import json

extractor = OpenDataBCNExtractor()
info = extractor.get_dataset_info("transports-ciutat-barcelona")
if info:
    resources = info.get('resources', [])
    for r in resources:
        print(f"Name: {r['name']}, Format: {r['format']}, URL: {r['url']}")
else:
    print("Dataset not found")

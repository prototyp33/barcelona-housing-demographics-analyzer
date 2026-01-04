
from src.extraction.opendata import OpenDataBCNExtractor

extractor = OpenDataBCNExtractor()
dataset_id = "parcs-i-jardins"
info = extractor.get_dataset_info(dataset_id)
if info:
    resources = info.get('resources', [])
    for r in resources:
        if 'csv' in r.get('format', '').lower():
            print(f"Name: {r['name']}, Format: {r['format']}, URL: {r['url']}")
else:
    print(f"Dataset {dataset_id} not found")

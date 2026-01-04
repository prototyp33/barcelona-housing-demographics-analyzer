
from src.extraction.opendata import OpenDataBCNExtractor
import json

extractor = OpenDataBCNExtractor()
results = extractor.search_datasets_by_keyword("transports")
print(f"Datasets found for 'transports': {results}")

results_metro = extractor.search_datasets_by_keyword("metro")
print(f"Datasets found for 'metro': {results_metro}")

results_bus = extractor.search_datasets_by_keyword("bus")
print(f"Datasets found for 'bus': {results_bus}")

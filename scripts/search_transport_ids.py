
from src.extraction.opendata import OpenDataBCNExtractor

extractor = OpenDataBCNExtractor()
print("Searching for 'transports'...")
results = extractor.search_datasets_by_keyword("transports")
for r in results:
    print(f"ID: {r}")

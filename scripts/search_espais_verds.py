
from src.extraction.opendata import OpenDataBCNExtractor

extractor = OpenDataBCNExtractor()
print("Searching for 'Espais Verds'...")
results = extractor.search_datasets_by_keyword("Espais Verds")
for r in results:
    print(f"ID: {r}")

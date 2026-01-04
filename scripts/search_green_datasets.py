
from src.extraction.opendata import OpenDataBCNExtractor

extractor = OpenDataBCNExtractor()
print("Searching for 'parcs'...")
results = extractor.search_datasets_by_keyword("parcs")
for r in results:
    print(f"ID: {r}")

print("\nSearching for 'verds'...")
results_v = extractor.search_datasets_by_keyword("verds")
for r in results_v:
    print(f"ID: {r}")

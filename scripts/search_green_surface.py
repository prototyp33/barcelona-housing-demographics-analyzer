
from src.extraction.opendata import OpenDataBCNExtractor

extractor = OpenDataBCNExtractor()
print("Searching for 'superficie' and 'verd'...")
results = extractor.search_datasets_by_keyword("superficie")
for r in results:
    if "verd" in r.lower():
        print(f"ID: {r}")

print("\nSearching for 'm2' and 'verd'...")
results = extractor.search_datasets_by_keyword("m2")
for r in results:
    if "verd" in r.lower():
        print(f"ID: {r}")

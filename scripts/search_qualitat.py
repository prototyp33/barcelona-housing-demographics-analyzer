
from src.extraction.opendata import OpenDataBCNExtractor

extractor = OpenDataBCNExtractor()
results = extractor.search_datasets_by_keyword("qualitat")
for r in results:
    print(f"ID: {r}")

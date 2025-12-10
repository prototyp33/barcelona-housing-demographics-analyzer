#!/usr/bin/env python3
import urllib.request
import json

url = "https://api.idescat.cat/indicadors/v1/dades.json?id=m10409&lang=es"
print(f"Fetching {url}...")
with urllib.request.urlopen(url) as response:
    data = json.load(response)
    print(json.dumps(data, indent=2, ensure_ascii=False)[:2000]) # Print first 2000 chars

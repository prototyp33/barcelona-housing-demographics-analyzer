#!/usr/bin/env python3
import urllib.request
import json
import urllib.parse

def search_opendata(query):
    base_url = "https://opendata-ajuntament.barcelona.cat/data/api/3/action/package_search"
    params = urllib.parse.urlencode({'q': query, 'rows': 10})
    url = f"{base_url}?{params}"
    
    print(f"Searching: {url}")
    try:
        with urllib.request.urlopen(url) as response:
            data = json.load(response)
            if data['success']:
                results = data['result']['results']
                print(f"Found {len(results)} datasets:")
                for res in results:
                    print(f"- Title: {res['title']}")
                    print(f"  Name: {res['name']}")
                    print(f"  Resources:")
                    for r in res['resources']:
                        print(f"    - {r['name']} ({r['format']}): {r['url']}")
                    print()
            else:
                print("Search failed.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    search_opendata("renta barri")

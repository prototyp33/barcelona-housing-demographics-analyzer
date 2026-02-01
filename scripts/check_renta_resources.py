
import json
import requests
from pathlib import Path

def check_renta_resources():
    dataset_ids = [
        "renda-disponible-llars-bcn",
        "atles-renda-bruta-per-llar",
        "atles-renda-bruta-per-persona",
        "atles-renda-index-gini"
    ]
    
    API_URL = "https://opendata-ajuntament.barcelona.cat/data/api/3/action/package_show"
    
    results = {}
    
    for dataset_id in dataset_ids:
        print(f"Checking dataset: {dataset_id}")
        try:
            response = requests.get(API_URL, params={"id": dataset_id}, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    resources = data["result"].get("resources", [])
                    years = []
                    for r in resources:
                        import re
                        match = re.search(r'(\d{4})', r.get("name", ""))
                        if match:
                            years.append(int(match.group(1)))
                    results[dataset_id] = sorted(list(set(years)))
                    print(f"  Years found: {results[dataset_id]}")
                else:
                    print(f"  Error: {data.get('error')}")
            else:
                print(f"  HTTP Error: {response.status_code}")
        except Exception as e:
            print(f"  Exception: {e}")
            
    with open("data/raw/opendatabcn_renta_check.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    check_renta_resources()

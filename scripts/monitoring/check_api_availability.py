#!/usr/bin/env python3
"""
Script para verificar disponibilidad de APIs externas.

Verifica que las APIs externas estén respondiendo correctamente.
"""

import argparse
import sys
import time
from datetime import datetime

try:
    import requests
except ImportError:
    print("❌ Error: requests required")
    print("   Install: pip install requests")
    sys.exit(1)


def check_api_availability(url: str, name: str = "API", timeout: int = 10, retries: int = 3):
    """
    Verifica disponibilidad de una API.
    
    Args:
        url: URL de la API a verificar
        name: Nombre descriptivo de la API
        timeout: Timeout en segundos
        retries: Número de reintentos
    """
    for attempt in range(retries):
        try:
            start_time = time.time()
            response = requests.get(url, timeout=timeout)
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                print(f"✅ {name}: Available (Status: {response.status_code}, Time: {elapsed_time:.2f}s)")
                return True
            else:
                print(f"⚠️  {name}: Responding but status code {response.status_code}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                return False
        
        except requests.exceptions.Timeout:
            print(f"⏱️  {name}: Timeout after {timeout}s (attempt {attempt + 1}/{retries})")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
        
        except requests.exceptions.ConnectionError:
            print(f"❌ {name}: Connection error (attempt {attempt + 1}/{retries})")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
        
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
            return False
    
    print(f"❌ {name}: Failed after {retries} attempts")
    return False


def main():
    parser = argparse.ArgumentParser(description='Check external API availability')
    parser.add_argument('--url', required=True, help='API URL to check')
    parser.add_argument('--name', default='API', help='API name for logging')
    parser.add_argument('--timeout', type=int, default=10, help='Request timeout in seconds')
    parser.add_argument('--retries', type=int, default=3, help='Number of retry attempts')
    
    args = parser.parse_args()
    
    success = check_api_availability(args.url, args.name, args.timeout, args.retries)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()


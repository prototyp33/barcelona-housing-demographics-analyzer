#!/usr/bin/env python3
"""Quick test script for the Barcelona Housing Analytics API."""

import requests
import json
import sys
from typing import Dict, Any

API_BASE_URL = "http://localhost:8000"


def print_response(title: str, response: requests.Response) -> None:
    """Print formatted API response."""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    
    try:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error parsing response: {e}")
        print(response.text)


def test_health() -> bool:
    """Test health endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print_response("Health Check", response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_root() -> bool:
    """Test root endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}/")
        print_response("Root Endpoint", response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
        return False


def test_barrios() -> bool:
    """Test barrios list endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}/barrios")
        print_response("List Barrios", response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Barrios list failed: {e}")
        return False


def test_barrio_detail() -> bool:
    """Test barrio detail endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}/barrios/1")
        print_response("Barrio Detail (ID=1)", response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Barrio detail failed: {e}")
        return False


def test_prediction() -> bool:
    """Test prediction endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}/predictions/1")
        print_response("Price Prediction (ID=1)", response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Prediction failed: {e}")
        return False


def test_investment() -> bool:
    """Test investment recommendations endpoint."""
    try:
        payload = {
            "budget": 250000,
            "strategy": "yield",
            "max_results": 3
        }
        response = requests.post(
            f"{API_BASE_URL}/investment/recommend",
            json=payload
        )
        print_response("Investment Recommendations", response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Investment recommendations failed: {e}")
        return False


def test_clusters() -> bool:
    """Test clusters endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}/clusters/")
        print_response("Cluster Information", response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Clusters failed: {e}")
        return False


def main():
    """Run all API tests."""
    print("\n" + "="*60)
    print("🚀 Barcelona Housing Analytics API - Test Suite")
    print("="*60)
    print(f"\nTesting API at: {API_BASE_URL}")
    print("\nMake sure the API is running:")
    print("  make api")
    print("  OR")
    print("  python3 scripts/run_api.py")
    print("\n" + "="*60)
    
    tests = [
        ("Health Check", test_health),
        ("Root Endpoint", test_root),
        ("List Barrios", test_barrios),
        ("Barrio Detail", test_barrio_detail),
        ("Price Prediction", test_prediction),
        ("Investment Recommendations", test_investment),
        ("Cluster Information", test_clusters),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Print summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

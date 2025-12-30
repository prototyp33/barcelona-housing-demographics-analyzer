#!/usr/bin/env python3
"""Start the FastAPI server for Barcelona Housing Analytics API."""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main():
    """Run the FastAPI server."""
    try:
        import uvicorn
    except ImportError:
        print("❌ Error: uvicorn is not installed.")
        print("\nPlease install the required dependencies:")
        print("  pip install -r requirements.txt")
        print("\nOr install FastAPI dependencies directly:")
        print("  pip install 'fastapi>=0.115.0' 'uvicorn[standard]>=0.32.0'")
        sys.exit(1)
    
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    main()

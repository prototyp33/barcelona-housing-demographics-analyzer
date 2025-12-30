# 🚀 Quick Start Guide - Barcelona Housing Analytics API

## Prerequisites

- Python 3.11 or higher
- Virtual environment (recommended)

## Installation

### 1. Clone the Repository (if not already done)

```bash
git clone https://github.com/prototyp33/barcelona-housing-demographics-analyzer.git
cd barcelona-housing-demographics-analyzer
```

### 2. Set Up Virtual Environment

```bash
# Create virtual environment (if not exists)
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# OR
.venv\Scripts\activate     # On Windows
```

### 3. Install Dependencies

```bash
# Install all project dependencies
pip install -r requirements.txt

# OR install only API dependencies
pip install 'fastapi>=0.115.0' 'uvicorn[standard]>=0.32.0' 'pydantic>=2.10.0' 'python-multipart>=0.0.20'
```

## Running the API

### Option 1: Using Make (Recommended)

```bash
make api
```

### Option 2: Using Python Script

```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Run the API
python3 scripts/run_api.py
```

### Option 3: Using Uvicorn Directly

```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Run with uvicorn
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

## Accessing the API

Once the API is running, you can access:

- **API Base**: http://localhost:8000
- **Interactive Docs (Swagger)**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Quick Test

### 1. Test Health Endpoint

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "database_connected": true,
  "model_loaded": true,
  "timestamp": "2025-12-30T11:00:00"
}
```

### 2. Get Investment Recommendations

```bash
curl -X POST http://localhost:8000/investment/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "budget": 250000,
    "strategy": "yield",
    "max_results": 5
  }'
```

### 3. Get Neighborhood Prediction

```bash
curl http://localhost:8000/predictions/1
```

### 4. Run Full Test Suite

```bash
python3 scripts/test_api.py
```

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'uvicorn'"

**Solution**: Make sure you've activated the virtual environment and installed dependencies:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Error: "Database not found"

**Solution**: Make sure you have the database file in the correct location:

```bash
# Check if database exists
ls -lh data/master.db data/processed/database.db

# If not, run the ETL pipeline
python3 scripts/process_and_load.py
```

### Error: "Model data not found"

**Solution**: Make sure you have the valuation dataset:

```bash
# Check if file exists
ls -lh data/barcelona_ml_valuation.csv

# If not, rebuild it
python3 scripts/rebuild_valuation_dataset.py
```

### Port 8000 Already in Use

**Solution**: Kill the existing process or use a different port:

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# OR use a different port
uvicorn src.api.main:app --reload --port 8001
```

## Next Steps

1. **Explore the API**: Open http://localhost:8000/docs in your browser
2. **Read the Documentation**: See [docs/API_README.md](../API_README.md)
3. **Integrate with Frontend**: Use the API endpoints in your application
4. **Deploy to Production**: See deployment guide in API_README.md

## Common Commands

```bash
# Start API
make api

# Open API docs in browser
make api-docs

# Test API health
make api-test

# Run full test suite
python3 scripts/test_api.py

# Stop API (Ctrl+C in terminal)
```

## Getting Help

- **API Documentation**: http://localhost:8000/docs (when running)
- **Full README**: [docs/API_README.md](../API_README.md)
- **Issues**: https://github.com/prototyp33/barcelona-housing-demographics-analyzer/issues

---

**Happy coding! 🚀**

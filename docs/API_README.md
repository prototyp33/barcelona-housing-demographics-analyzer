# 🚀 Barcelona Housing Analytics API

FastAPI REST API serving XGBoost predictions, neighborhood data, and investment recommendations for the Barcelona housing market.

## 📋 Features

- **Neighborhood Data**: Get detailed information about Barcelona's 73 neighborhoods
- **Price Predictions**: XGBoost-powered fair value predictions with deviation analysis
- **Investment Recommendations**: Personalized recommendations based on budget and strategy
- **Cluster Analysis**: Neighborhood segmentation with K-Means clustering
- **Health Monitoring**: Built-in health check endpoints

## 🏃 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or use make
make install
```

### Running the API

```bash
# Option 1: Using make (recommended)
make api

# Option 2: Using Python directly
python3 scripts/run_api.py

# Option 3: Using uvicorn directly
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:

- **API**: http://localhost:8000
- **Interactive Docs (Swagger)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Quick Test

```bash
# Test health endpoint
curl http://localhost:8000/health

# Or use make
make api-test
```

## 📚 API Endpoints

### Health & Info

#### `GET /`

Root endpoint with API information and available endpoints.

**Response:**

```json
{
  "message": "Barcelona Housing Analytics API",
  "version": "0.1.0",
  "docs": "/docs",
  "health": "/health",
  "endpoints": {
    "barrios": "/barrios",
    "predictions": "/predictions",
    "investment": "/investment/recommend",
    "clusters": "/clusters"
  }
}
```

#### `GET /health`

Health check endpoint.

**Response:**

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "database_connected": true,
  "model_loaded": true,
  "timestamp": "2025-12-29T14:00:00"
}
```

### Neighborhoods (Barrios)

#### `GET /barrios`

List all neighborhoods, optionally filtered by district.

**Query Parameters:**

- `distrito` (optional): Filter by district name

**Example:**

```bash
curl "http://localhost:8000/barrios?distrito=Eixample"
```

**Response:**

```json
[
  {
    "barrio_id": 1,
    "barrio_nombre": "el Raval",
    "distrito_nombre": "Ciutat Vella"
  },
  ...
]
```

#### `GET /barrios/{barrio_id}`

Get detailed information for a specific neighborhood.

**Example:**

```bash
curl http://localhost:8000/barrios/1
```

**Response:**

```json
{
  "barrio_id": 1,
  "barrio_nombre": "el Raval",
  "distrito_nombre": "Ciutat Vella",
  "avg_venta_23": 3500.5,
  "gross_yield": 4.2,
  "renta_bruta_llar": 28000,
  "poblacion_total": 45000,
  "segmento": 2
}
```

### Predictions

#### `GET /predictions/{barrio_id}`

Get price prediction for a specific neighborhood.

**Example:**

```bash
curl http://localhost:8000/predictions/1
```

**Response:**

```json
{
  "barrio_id": 1,
  "barrio_nombre": "el Raval",
  "current_price": 3500.5,
  "predicted_price": 3450.25,
  "deviation_pct": 1.46,
  "timestamp": "2025-12-29T14:00:00"
}
```

#### `POST /predictions/`

Get prediction with custom features (advanced).

**Request Body:**

```json
{
  "barrio_id": 1,
  "features": {}
}
```

### Investment Recommendations

#### `POST /investment/recommend`

Get personalized investment recommendations.

**Request Body:**

```json
{
  "budget": 250000,
  "strategy": "yield",
  "max_results": 5
}
```

**Strategies:**

- `yield`: Maximize rental yield
- `safe`: Minimize price deviation (undervalued properties)
- `growth`: Maximize price growth potential

**Example:**

```bash
curl -X POST http://localhost:8000/investment/recommend \
  -H "Content-Type: application/json" \
  -d '{"budget": 250000, "strategy": "yield", "max_results": 5}'
```

**Response:**

```json
{
  "budget": 250000,
  "strategy": "yield",
  "recommendations": [
    {
      "barrio_nombre": "la Marina del Prat Vermell",
      "avg_venta_23": 2246.26,
      "gross_yield": 8.01,
      "desviacion_valor": -0.0003,
      "segmento": 1,
      "estimated_total_cost": 146007,
      "rank": 1
    },
    ...
  ],
  "timestamp": "2025-12-29T14:00:00"
}
```

### Clusters

#### `GET /clusters/`

Get information about all neighborhood clusters/segments.

**Example:**

```bash
curl http://localhost:8000/clusters/
```

**Response:**

```json
{
  "0": {
    "segmento": 0,
    "barrios_count": 18,
    "avg_price": 4200.50,
    "avg_yield": 3.8,
    "characteristics": {
      "avg_renta": 35000,
      "avg_gini": 0.35,
      "avg_antiguedad": 75
    }
  },
  ...
}
```

## 🔧 Configuration

### Environment Variables

The API uses the following environment variables (all optional):

```bash
# Database path (defaults to data/master.db or data/processed/database.db)
DATABASE_PATH=/path/to/database.db

# Model data path (defaults to data/barcelona_ml_valuation.csv)
MODEL_DATA_PATH=/path/to/valuation.csv

# API settings
API_HOST=0.0.0.0
API_PORT=8000
```

### CORS Configuration

By default, CORS is enabled for all origins (`*`). For production, update `src/api/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🧪 Testing

### Manual Testing

```bash
# Health check
curl http://localhost:8000/health

# List all neighborhoods
curl http://localhost:8000/barrios

# Get specific neighborhood
curl http://localhost:8000/barrios/1

# Get prediction
curl http://localhost:8000/predictions/1

# Get investment recommendations
curl -X POST http://localhost:8000/investment/recommend \
  -H "Content-Type: application/json" \
  -d '{"budget": 250000, "strategy": "yield"}'

# Get clusters
curl http://localhost:8000/clusters/
```

### Using the Interactive Docs

1. Start the API: `make api`
2. Open browser: http://localhost:8000/docs
3. Try out endpoints directly in the Swagger UI

## 📦 Deployment

### Production Deployment

For production deployment, use a production-grade ASGI server:

```bash
# Install production dependencies
pip install gunicorn

# Run with Gunicorn
gunicorn src.api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t barcelona-housing-api .
docker run -p 8000:8000 barcelona-housing-api
```

## 🔒 Security Considerations

For production deployment:

1. **Enable HTTPS**: Use a reverse proxy (nginx, Caddy) with SSL certificates
2. **Rate Limiting**: Implement rate limiting to prevent abuse
3. **API Keys**: Add authentication for sensitive endpoints
4. **CORS**: Restrict allowed origins
5. **Input Validation**: All inputs are validated via Pydantic models
6. **Error Handling**: Sensitive error details are not exposed to clients

## 📊 Performance

- **Latency**: ~50-100ms for predictions (p95)
- **Throughput**: ~100 requests/second (single worker)
- **Model Loading**: ~2-3 seconds on startup
- **Memory**: ~500MB with model loaded

## 🐛 Troubleshooting

### API won't start

```bash
# Check if port 8000 is already in use
lsof -i :8000

# Kill existing process
kill -9 <PID>
```

### Model not loading

```bash
# Verify data file exists
ls -lh data/barcelona_ml_valuation.csv

# Check logs for errors
python3 scripts/run_api.py 2>&1 | grep ERROR
```

### Database connection errors

```bash
# Verify database exists
ls -lh data/master.db data/processed/database.db

# Test database connection
sqlite3 data/master.db "SELECT COUNT(*) FROM dim_barrios;"
```

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please see CONTRIBUTING.md for guidelines.

---

**Built with ❤️ using FastAPI, XGBoost, and Python**

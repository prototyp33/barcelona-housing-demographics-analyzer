# 📊 Schema Health Monitoring - Quick Start

## 🚀 Launch Dashboard (Recommended)

```bash
./scripts/launch_schema_dashboard.sh
```

This will:

1. Start the API server (if not running)
2. Open the interactive dashboard in your browser
3. Display real-time schema health metrics

## 💻 CLI Usage

### Check Current Health

```bash
python scripts/schema_health_cli.py current
```

### Create Snapshot

```bash
python scripts/schema_health_cli.py snapshot
```

### View History

```bash
python scripts/schema_health_cli.py history --limit 10
```

### Check Specific Table

```bash
python scripts/schema_health_cli.py table fact_precios
```

## 🌐 API Endpoints

Start the API server:

```bash
python -m src.api.main
```

Access endpoints:

- **Summary**: http://localhost:8000/schema-health/summary
- **Current Health**: http://localhost:8000/schema-health/current
- **Alerts**: http://localhost:8000/schema-health/alerts
- **History**: http://localhost:8000/schema-health/history
- **API Docs**: http://localhost:8000/docs#/Schema%20Health

## 📈 Current Status

```
Health Score: 93.2/100 - EXCELLENT ✅

Issues to Address:
• 4 broken views (missing columns)
• 7 empty fact tables (no data)
• 1 table with low coverage (<95%)
```

## 📚 Full Documentation

See [SCHEMA_HEALTH_MONITORING.md](./SCHEMA_HEALTH_MONITORING.md) for complete documentation.

## 🎯 Quick Examples

### Python Integration

```python
from src.monitoring.schema_health import SchemaHealthMonitor
from src.database import DatabaseManager

db_manager = DatabaseManager()
with SchemaHealthMonitor(db_manager.db_path) as monitor:
    snapshot = monitor.collect_snapshot()
    print(f"Health Score: {monitor.get_health_score(snapshot):.1f}/100")
```

### cURL Examples

```bash
# Get summary
curl http://localhost:8000/schema-health/summary

# Get alerts
curl http://localhost:8000/schema-health/alerts

# Create snapshot
curl -X POST http://localhost:8000/schema-health/snapshot
```

---

**Need Help?** Check the full documentation or run `python scripts/schema_health_cli.py --help`

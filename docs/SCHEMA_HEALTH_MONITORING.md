# Schema Health Monitoring System

A comprehensive monitoring solution for tracking database schema health, data quality, and coverage metrics over time.

## 🎯 Overview

The Schema Health Monitoring System provides:

- **Real-time Health Metrics**: Track table counts, row counts, data coverage, and temporal ranges
- **Health Scoring**: Automated scoring (0-100) based on multiple quality dimensions
- **Historical Tracking**: Save and compare snapshots over time
- **Alert System**: Automatic detection of broken views, empty tables, and coverage issues
- **Multiple Interfaces**: CLI, API, and Web Dashboard

## 📊 Components

### 1. Core Module (`src/monitoring/schema_health.py`)

The core monitoring engine that collects and analyzes schema metrics.

**Key Classes:**

- `SchemaHealthMonitor`: Main monitoring class
- `SchemaHealthSnapshot`: Data class for health snapshots
- `TableMetrics`: Metrics for individual tables

**Features:**

- Collects metrics for all tables and views
- Calculates barrio coverage (73 Barcelona neighborhoods)
- Tracks temporal coverage (year ranges)
- Detects broken views and empty tables
- Computes overall health score

### 2. CLI Tool (`scripts/schema_health_cli.py`)

Command-line interface for quick health checks and snapshot management.

**Commands:**

```bash
# Show current health status
python scripts/schema_health_cli.py current

# Create a new snapshot
python scripts/schema_health_cli.py snapshot

# View historical snapshots
python scripts/schema_health_cli.py history --limit 10

# Check specific table metrics
python scripts/schema_health_cli.py table fact_precios

# Export health data to JSON
python scripts/schema_health_cli.py export --output health.json
```

### 3. REST API (`src/api/routers/schema_health.py`)

FastAPI endpoints for programmatic access to schema health data.

**Endpoints:**

- `GET /schema-health/current` - Current health snapshot
- `GET /schema-health/history?limit=10` - Historical snapshots
- `POST /schema-health/snapshot` - Create new snapshot
- `GET /schema-health/tables/{table_name}` - Table-specific metrics
- `GET /schema-health/summary` - Quick health summary
- `GET /schema-health/alerts` - Active health alerts

**Example:**

```bash
curl http://localhost:8000/schema-health/current
```

### 4. Web Dashboard (`dashboard/schema-health.html`)

Premium, interactive dashboard for visualizing schema health.

**Features:**

- Real-time health score with circular progress indicator
- Interactive charts (coverage distribution, temporal timeline)
- Active alerts and warnings
- Top tables by row count
- Responsive design with glassmorphic UI

**Access:**

```bash
# Start the API server
python -m src.api.main

# Open dashboard in browser
open dashboard/schema-health.html
```

## 📈 Health Score Calculation

The health score (0-100) is calculated based on:

| Factor                | Weight     | Criteria                              |
| --------------------- | ---------- | ------------------------------------- |
| **Broken Views**      | -20 points | Percentage of views with errors       |
| **Empty Tables**      | -15 points | Percentage of fact tables with 0 rows |
| **Barrio Coverage**   | -15 points | Average coverage below 100%           |
| **Temporal Coverage** | +5 points  | Bonus for ≥10 years of data           |

**Score Interpretation:**

- **90-100**: Excellent ✅ - Optimal schema health
- **75-89**: Good 👍 - Minor issues, overall solid
- **60-74**: Fair ⚠️ - Several issues need attention
- **0-59**: Poor ❌ - Critical issues detected

## 🔍 Metrics Tracked

### Table-Level Metrics

- Row count
- Year range (min/max)
- Unique barrios covered
- Barrio coverage percentage
- Geometry presence
- Health status (healthy/error)

### Database-Level Metrics

- Total tables (fact, dimension, other)
- Total views (healthy, broken)
- Total rows across all tables
- Empty tables count
- Average barrio coverage
- Temporal coverage (years)

## 📁 Snapshot Storage

Snapshots are automatically saved to:

```
data/processed/monitoring/schema_health_YYYYMMDD_HHMMSS.json
```

Each snapshot contains:

- Timestamp
- All database-level metrics
- Individual table metrics
- View errors
- Calculated health score

## 🚨 Alert Categories

The system monitors and alerts on:

1. **Broken Views** (Error)

   - Views that fail to execute
   - Missing columns or invalid SQL

2. **Empty Tables** (Warning)

   - Fact tables with 0 rows
   - Potential data pipeline issues

3. **Low Coverage** (Warning)

   - Tables with <95% barrio coverage
   - Incomplete neighborhood data

4. **Stale Data** (Info)
   - Tables with no recent data
   - Potentially outdated information

## 🔧 Integration Examples

### Python Integration

```python
from src.monitoring.schema_health import SchemaHealthMonitor
from src.database import DatabaseManager

# Get current health
db_manager = DatabaseManager()
with SchemaHealthMonitor(db_manager.db_path) as monitor:
    snapshot = monitor.collect_snapshot()
    health_score = monitor.get_health_score(snapshot)

    print(f"Health Score: {health_score:.1f}/100")
    print(f"Broken Views: {snapshot.broken_views}")
    print(f"Empty Tables: {snapshot.empty_tables}")
```

### API Integration

```python
import requests

# Get current health
response = requests.get('http://localhost:8000/schema-health/current')
data = response.json()

print(f"Health Score: {data['health_score']}")
print(f"Total Tables: {data['total_tables']}")

# Get alerts
alerts = requests.get('http://localhost:8000/schema-health/alerts').json()
for alert in alerts:
    print(f"{alert['severity'].upper()}: {alert['message']}")
```

### Automated Monitoring

Add to your ETL pipeline:

```python
# After ETL run, check schema health
with SchemaHealthMonitor(db_path) as monitor:
    snapshot = monitor.collect_snapshot()
    health_score = monitor.get_health_score(snapshot)

    # Save snapshot
    monitor.save_snapshot(snapshot)

    # Alert if health drops below threshold
    if health_score < 75:
        send_alert(f"Schema health degraded: {health_score:.1f}/100")
```

## 📊 Dashboard Features

### Visual Components

1. **Health Score Circle**

   - Animated circular progress indicator
   - Color-coded by health status
   - Real-time updates

2. **Stats Grid**

   - Key metrics at a glance
   - Trend indicators
   - Hover effects

3. **Coverage Chart**

   - Doughnut chart showing coverage distribution
   - 5 coverage tiers (100%, 95-99%, 90-94%, <90%, No Data)

4. **Alerts Panel**

   - Categorized by severity
   - Expandable details
   - Action recommendations

5. **Tables Overview**
   - Top 10 tables by row count
   - Coverage badges
   - Year ranges
   - Health status

## 🎨 Design Philosophy

The dashboard follows modern web design principles:

- **Glassmorphism**: Frosted glass effect with backdrop blur
- **Mesh Gradients**: Subtle radial gradients for depth
- **Micro-animations**: Smooth transitions and hover effects
- **Dark Mode**: Premium dark theme optimized for readability
- **Typography**: Inter for body, Outfit for headings, JetBrains Mono for code

## 🔄 Workflow

### Daily Monitoring

```bash
# Check current health
python scripts/schema_health_cli.py current

# If issues detected, investigate specific tables
python scripts/schema_health_cli.py table fact_desempleo
```

### Weekly Snapshots

```bash
# Create weekly snapshot
python scripts/schema_health_cli.py snapshot

# Review trends
python scripts/schema_health_cli.py history --limit 4
```

### Continuous Monitoring

```bash
# Start API server
python -m src.api.main

# Open dashboard
open dashboard/schema-health.html

# Dashboard auto-refreshes every 30 seconds
```

## 🐛 Troubleshooting

### Broken Views

If views are broken, check the error messages:

```bash
python scripts/schema_health_cli.py current
```

Common causes:

- Missing columns after schema changes
- Invalid SQL in view definition
- Dropped source tables

### Empty Tables

Check ETL logs for the specific table:

```bash
grep "fact_desempleo" logs/etl_*.log
```

### Low Coverage

Investigate data sources:

```bash
python scripts/schema_health_cli.py table fact_servicios_salud
```

## 📝 Best Practices

1. **Regular Snapshots**: Create daily or weekly snapshots to track trends
2. **Alert Thresholds**: Set up notifications when health score drops below 75
3. **Post-ETL Checks**: Always verify schema health after ETL runs
4. **Documentation**: Document any known issues in snapshot notes
5. **Trend Analysis**: Compare snapshots to identify degradation patterns

## 🚀 Future Enhancements

Potential improvements:

- Email/Slack notifications for critical alerts
- Automated remediation suggestions
- Schema drift detection
- Performance metrics (query times)
- Data freshness tracking
- Custom health score weights
- Multi-database support

## 📚 Related Documentation

- [Database Schema Report](../docs/DATABASE_SCHEMA_REPORT.md)
- [ETL Pipeline Documentation](../docs/ETL_PIPELINE.md)
- [API Documentation](http://localhost:8000/docs)

## 🤝 Contributing

To add new metrics:

1. Update `TableMetrics` dataclass in `schema_health.py`
2. Modify `get_table_metrics()` to collect new data
3. Update health score calculation if needed
4. Add visualization to dashboard
5. Update this documentation

---

**Built with ❤️ for Barcelona Housing Demographics Analyzer**

#!/bin/bash
# Generate summary of all custom fields for easy copy-paste into GitHub Projects UI

set -e

OUTPUT_FILE="docs/CUSTOM_FIELDS_SUMMARY.md"

echo "📋 Generando resumen de custom fields..."
echo ""

cat > "$OUTPUT_FILE" << 'EOF'
# Custom Fields Summary - Quick Reference

**Fecha:** Diciembre 2025  
**Propósito:** Resumen rápido de custom fields para todas las issues

---

## 🔷 EPICS PLACEHOLDERS

### Issue #194: Fase 2: Critical Extractors

```yaml
Status: Backlog
Priority: P0
Size: XL
Estimate: 256
Epic: ETL
Release: v2.0 Foundation
Phase: Extraction
Start date: 2026-01-20
Target date: 2026-02-14
Quarter: Q1 2026
Effort (weeks): 6.4
```

### Issue #195: Fase 3: Complementary Extractors

```yaml
Status: Backlog
Priority: P1
Size: XL
Estimate: 628
Epic: ETL
Release: v2.1 Enhanced Analytics
Phase: Extraction
Start date: 2026-02-24
Target date: 2026-03-21
Quarter: Q1 2026
Effort (weeks): 15.7
```

### Issue #196: Fase 4: Integration & Production

```yaml
Status: Backlog
Priority: P0
Size: XL
Estimate: 220
Epic: INFRA
Release: v2.0 Foundation
Phase: Infrastructure
Start date: 2026-03-28
Target date: 2026-04-11
Quarter: Q2 2026
Effort (weeks): 5.5
```

---

## 🔬 SPIKE ISSUES

### Issue #198: Spike Epic

```yaml
Status: Backlog
Priority: P0
Size: XL
Estimate: 40
Epic: DATA
Release: Spike
Phase: Planning
Start date: 2025-12-16
Target date: 2025-12-20
Quarter: Q4 2025
Effort (weeks): 1
```

### Issue #199: Portal Dades

```yaml
Status: Backlog
Priority: P0
Size: M
Estimate: 8
Epic: DATA
Release: Spike
Phase: Planning
Start date: 2025-12-16
Target date: 2025-12-20
Quarter: Q4 2025
Effort (weeks): 0.2
```

### Issue #200: INE API

```yaml
Status: Backlog
Priority: P0
Size: M
Estimate: 8
Epic: DATA
Release: Spike
Phase: Planning
Start date: 2025-12-16
Target date: 2025-12-20
Quarter: Q4 2025
Effort (weeks): 0.2
```

### Issue #201: Catastro

```yaml
Status: Backlog
Priority: P0
Size: M
Estimate: 8
Epic: DATA
Release: Spike
Phase: Planning
Start date: 2025-12-16
Target date: 2025-12-20
Quarter: Q4 2025
Effort (weeks): 0.2
```

### Issue #204: PostgreSQL Schema

```yaml
Status: Backlog
Priority: P0
Size: L
Estimate: 10
Epic: DATA
Release: Spike
Phase: Planning
Start date: 2025-12-16
Target date: 2025-12-20
Quarter: Q4 2025
Effort (weeks): 0.25
```

### Issue #205: barrio_id Linking

```yaml
Status: Backlog
Priority: P0
Size: M
Estimate: 8
Epic: DATA
Release: Spike
Phase: Planning
Start date: 2025-12-16
Target date: 2025-12-20
Quarter: Q4 2025
Effort (weeks): 0.2
```

### Issue #206: Validation Framework

```yaml
Status: Backlog
Priority: P0
Size: M
Estimate: 6
Epic: DATA
Release: Spike
Phase: Planning
Start date: 2025-12-16
Target date: 2025-12-20
Quarter: Q4 2025
Effort (weeks): 0.15
```

### Issue #207: Data Quality

```yaml
Status: Backlog
Priority: P0
Size: M
Estimate: 6
Epic: DATA
Release: Spike
Phase: Planning
Start date: 2025-12-16
Target date: 2025-12-20
Quarter: Q4 2025
Effort (weeks): 0.15
```

### Issue #208: Hedonic Model

```yaml
Status: Backlog
Priority: P0
Size: L
Estimate: 12
Epic: AN
Release: Spike
Phase: Planning
Start date: 2025-12-16
Target date: 2025-12-20
Quarter: Q4 2025
Effort (weeks): 0.3
```

### Issue #209: DiD Viability

```yaml
Status: Backlog
Priority: P0
Size: M
Estimate: 8
Epic: AN
Release: Spike
Phase: Planning
Start date: 2025-12-16
Target date: 2025-12-20
Quarter: Q4 2025
Effort (weeks): 0.2
```

---

## 📊 Quick Copy-Paste Format

Para cada issue, copiar y pegar en GitHub Projects UI:

1. Abrir issue en GitHub Projects
2. Click en custom fields
3. Copiar valores de arriba
4. Pegar y guardar

---

**Última actualización:** Diciembre 2025
EOF

echo "✅ Resumen generado en: $OUTPUT_FILE"
echo ""
echo "📋 Usar este archivo como referencia rápida para configurar custom fields en GitHub Projects UI"


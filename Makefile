# Barcelona Housing Demographics Analyzer - Makefile
# Comandos rapidos para desarrollo y gestion de issues

.PHONY: help validate-issues create-issues create-issue preview-issues sync-issues issue-stats
.PHONY: run-etl test test-coverage lint format dashboard dashboard-demo
.PHONY: install install-dev clean

help:  ## Muestra este mensaje de ayuda
	@echo "Barcelona Housing Demographics Analyzer"
	@echo "========================================"
	@echo ""
	@echo "Comandos disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

# ============================================================
# GESTION DE ISSUES
# ============================================================

validate-issues:  ## Valida todos los drafts de issues
	@echo "Validando drafts de issues..."
	@python3 scripts/validate_issues.py docs/issues/

preview-issues:  ## Preview de issues sin crearlas (--dry-run)
	@echo "Preview de issues a crear..."
	@python3 scripts/create_issues_from_drafts.py docs/issues/ --batch --dry-run

create-issue:  ## Crea una issue desde un draft (FILE=mi-issue.md)
	@if [ -z "$(FILE)" ]; then echo "Error: Especifica FILE=nombre-archivo.md"; exit 1; fi
	@echo "Creando issue desde $(FILE)..."
	@python3 scripts/create_issues_from_drafts.py docs/issues/$(FILE)

create-issues:  ## Crea todas las issues desde drafts validados
	@echo "Creando issues desde todos los drafts..."
	@python3 scripts/create_issues_from_drafts.py docs/issues/ --batch

sync-issues:  ## Sincroniza metricas de issues con documentacion
	@echo "Sincronizando metricas de issues..."
	@python3 scripts/sync_github_issues.py --update-docs --metrics

issue-stats:  ## Muestra estadisticas de issues
	@python3 scripts/sync_github_issues.py --metrics

# ============================================================
# ETL Y PIPELINE
# ============================================================

run-etl:  ## Ejecuta pipeline ETL completo
	@echo "Ejecutando pipeline ETL..."
	@python3 scripts/extract_data.py
	@python3 scripts/process_and_load.py
	@echo "Pipeline ETL completado"

extract:  ## Ejecuta solo extraccion de datos
	@echo "Extrayendo datos..."
	@python3 scripts/extract_data.py

process:  ## Ejecuta solo procesamiento y carga
	@echo "Procesando y cargando datos..."
	@python3 scripts/process_and_load.py

verify-db:  ## Verifica integridad de la base de datos
	@echo "Verificando integridad de base de datos..."
	@python3 scripts/verify_integrity.py

# ============================================================
# TESTING
# ============================================================

test:  ## Ejecuta tests
	@echo "Ejecutando tests..."
	@pytest tests/ -v

test-coverage:  ## Ejecuta tests con coverage
	@echo "Ejecutando tests con coverage..."
	@pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing
	@echo "Reporte HTML en htmlcov/index.html"

test-quick:  ## Ejecuta tests rapidos (sin markers lentos)
	@pytest tests/ -v -m "not slow"

# ============================================================
# LINTING Y FORMATO
# ============================================================

lint:  ## Ejecuta linters (black check, flake8)
	@echo "Verificando estilo de codigo..."
	@black src/ tests/ scripts/ --check --diff || true
	@flake8 src/ tests/ scripts/ --max-line-length=100 || true

format:  ## Formatea codigo con black
	@echo "Formateando codigo..."
	@black src/ tests/ scripts/
	@echo "Codigo formateado"

type-check:  ## Ejecuta verificacion de tipos con mypy
	@echo "Verificando tipos..."
	@mypy src/ --ignore-missing-imports || true

# ============================================================
# DASHBOARD
# ============================================================

dashboard:  ## Inicia dashboard Streamlit
	@echo "Iniciando dashboard Streamlit..."
	@PYTHONPATH=. streamlit run src/app/main.py

dashboard-demo:  ## Inicia dashboard en modo demo (puerto 8502)
	@echo "Iniciando dashboard en puerto 8502..."
	@PYTHONPATH=. streamlit run src/app/main.py --server.port 8502

# ============================================================
# INSTALACION Y SETUP
# ============================================================

install:  ## Instala dependencias de produccion
	@echo "Instalando dependencias..."
	@pip install -r requirements.txt
	@echo "Dependencias instaladas"

install-dev:  ## Instala dependencias de desarrollo
	@echo "Instalando dependencias de desarrollo..."
	@pip install -r requirements.txt
	@pip install -r requirements-dev.txt
	@echo "Dependencias de desarrollo instaladas"

setup-playwright:  ## Instala Playwright para scraping
	@echo "Instalando Playwright..."
	@pip install playwright
	@playwright install
	@echo "Playwright instalado"

# ============================================================
# LIMPIEZA
# ============================================================

clean:  ## Limpia archivos temporales y cache
	@echo "Limpiando archivos temporales..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "Limpieza completada"

clean-logs:  ## Limpia archivos de log
	@echo "Limpiando logs..."
	@rm -f logs/*.log 2>/dev/null || true
	@rm -f data/logs/*.txt 2>/dev/null || true
	@echo "Logs limpiados"

# ============================================================
# ATAJOS COMUNES
# ============================================================

check: validate-issues preview-issues  ## Valida y previsualiza issues

ci: lint test  ## Ejecuta lint y tests (como CI)

fix: format lint  ## Formatea y verifica codigo

# ============================================================
# ORGANIZACION DE ISSUES
# ============================================================

analyze-issues:  ## Analiza issues y muestra estadisticas
	@python3 scripts/organize_issues.py --analyze

mark-stale:  ## Etiqueta issues obsoletas (>90 dias)
	@python3 scripts/organize_issues.py --mark-stale --dry-run

mark-stale-force:  ## Etiqueta issues obsoletas (aplica cambios)
	@python3 scripts/organize_issues.py --mark-stale --force

assign-milestones:  ## Asigna milestones a issues sin asignar
	@python3 scripts/organize_issues.py --assign-milestones --dry-run

assign-milestones-force:  ## Asigna milestones (aplica cambios)
	@python3 scripts/organize_issues.py --assign-milestones --force

prioritize-sprint2:  ## Prioriza issues del Sprint 2
	@python3 scripts/prioritize_sprint2.py

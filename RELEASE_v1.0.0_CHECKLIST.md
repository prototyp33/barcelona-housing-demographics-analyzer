# Checklist Release v1.0.0

## Archivos preparados

- [x] `CHANGELOG.md` — Sección v1.0.0 con todos los cambios
- [x] `releases/RELEASE_v1.0.0.md` — Notas para GitHub Release

## Comandos para publicar (ejecutar en orden)

```bash
# 1. Añadir archivos del release
git add CHANGELOG.md releases/

# 2. Commit
git commit -m "chore(release): prepare v1.0.0 - CHANGELOG and release notes"

# 3. Crear tag anotado
git tag -a v1.0.0 -m "Release v1.0.0 - Barcelona Housing Analyzer

- Modelo Phase 5 (R²=0.81, MAE≈318€/m²)
- FastAPI backend + Streamlit dashboard
- 73 barrios, datos 2012-2025
- Fairness A/B harness, Market Intelligence"

# 4. Push commits y tag
git push origin main
git push origin v1.0.0

# 5. Crear GitHub Release (con gh CLI)
gh release create v1.0.0 \
  --title "v1.0.0 - Barcelona Housing Analyzer" \
  --notes-file releases/RELEASE_v1.0.0.md
```

## Alternativa: Release desde GitHub Web

1. Ir a https://github.com/prototyp33/barcelona-housing-demographics-analyzer/releases/new
2. Tag: `v1.0.0` (crear nuevo)
3. Title: `v1.0.0 - Barcelona Housing Analyzer`
4. Descripción: Copiar contenido de `releases/RELEASE_v1.0.0.md`
5. Publish release

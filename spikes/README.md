# Spikes - Guía de Uso

**¿Qué es un spike?**  
Un spike es una investigación técnica temporal para validar una aproximación, probar una tecnología, o explorar una solución antes de integrarla en producción.

---

## 📁 Estructura de un Spike

Cada spike debe tener esta estructura mínima:

```
spikes/
└── <nombre-spike>/
    ├── README.md          # Objetivo, resultados, decisiones
    ├── scripts/           # Scripts específicos del spike
    ├── notebooks/         # Análisis exploratorio
    ├── data/             # Datos temporales del spike
    └── docs/             # Documentación del spike
```

---

## 🔄 Ciclo de Vida de un Spike

### 1. Creación
- Crear directorio en `spikes/<nombre-spike>/`
- Documentar objetivo en `README.md`
- Crear scripts/notebooks necesarios

### 2. Desarrollo
- Usar código de `src/` cuando sea posible (no duplicar)
- Documentar decisiones y hallazgos
- Mantener scripts organizados

### 3. Conclusión
- Documentar resultados en `README.md`
- Decidir: ¿migrar a producción o descartar?

### 4. Migración (si aplica)
- **Código reutilizable** → Mover a `src/`
- **Scripts útiles** → Mover a `scripts/` (si son generales)
- **Documentación** → Mover a `docs/` (si es relevante)

### 5. Limpieza
- Eliminar spike después de migración completa
- O mantener como referencia histórica (marcar como "completado")

---

## 📋 Checklist: ¿Migrar Código del Spike?

Antes de migrar código del spike a producción:

- [ ] ¿El código es reutilizable más allá del spike?
- [ ] ¿Está bien testeado?
- [ ] ¿Sigue las convenciones del proyecto?
- [ ] ¿Está documentado?
- [ ] ¿No crea dependencias cíclicas?

**Si todas las respuestas son SÍ** → Migrar a `src/`  
**Si alguna es NO** → Mantener en spike o refactorizar primero

---

## 🎯 Spikes Actuales

### `data-validation/` (Issue #198-#204)
**Objetivo**: Validar arquitectura de modelo hedónico pricing para Gràcia  
**Estado**: En progreso (Fase 2)  
**Código candidato para migración**:
- `catastro_soap_client.py` → `src/extraction/catastro/soap_client.py`
- `catastro_oficial_client.py` → `src/extraction/catastro/oficial_client.py`

---

## 📚 Mejores Prácticas

### ✅ Hacer
- Usar módulos de `src/` cuando sea posible
- Documentar decisiones y resultados
- Mantener scripts organizados por feature
- Limpiar spikes completados

### ❌ Evitar
- Duplicar código que ya existe en `src/`
- Crear dependencias de `src/` hacia `spikes/`
- Dejar spikes sin documentar
- Acumular spikes completados sin limpiar

---

## 🔗 Referencias

- [Spike Definition (Agile)](https://www.agilealliance.org/glossary/spike/)
- Ver `docs/PROJECT_STRUCTURE_PROPOSAL.md` para estructura completa

---

**Última actualización**: 2025-12-19


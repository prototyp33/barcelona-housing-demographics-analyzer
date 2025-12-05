---
title: [FEATURE-05] Sistema de Notificaciones con Change Detection
labels: sprint-1, priority-medium, type-feature, area-etl
milestone: 1
---

## 🎯 Contexto
**Feature ID:** #05
**Sprint:** Sprint 1 (Quick Wins)
**Esfuerzo estimado:** 12-15h

## 📝 Descripción
Sistema automatizado que monitorea los datos ingresados diariamente y detecta cambios significativos (anomalías, bajadas de precio >X%, nuevos datos disponibles) enviando alertas.

## 🔧 Componentes Técnicos
- [ ] `src/monitoring/change_detector.py`: Lógica de detección de cambios
- [ ] `src/monitoring/alerting.py`: Sistema de envío (Email/Telegram)
- [ ] GitHub Actions: Workflow diario actualizado

## ✅ Criterios de Aceptación
- [ ] Detecta cambios >5% en precios medios
- [ ] Email enviado en <5min desde detección en pipeline
- [ ] Log de alertas persistido en base de datos
- [ ] Configuración de umbrales vía archivo config


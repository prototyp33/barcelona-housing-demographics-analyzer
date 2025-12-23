"""
Sistema de alertas para detectar cambios significativos en métricas clave.

Incluye:
- Detección de cambios significativos
- Sistema de notificaciones
- Priorización de alertas
"""

from .detector import detect_changes, detect_all_changes
from .notifier import Alert, AlertPriority, send_alert, create_alert

__all__ = [
    "detect_changes",
    "detect_all_changes",
    "Alert",
    "AlertPriority",
    "send_alert",
    "create_alert",
]


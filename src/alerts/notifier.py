"""
Sistema de notificaciones y priorización de alertas.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class AlertPriority(Enum):
    """Prioridad de una alerta."""
    
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Alert:
    """
    Representa una alerta del sistema.
    
    Attributes:
        alert_type: Tipo de alerta (ej: 'cambio_precio', 'nueva_zona_tensionada').
        barrio_id: ID del barrio afectado.
        priority: Prioridad de la alerta.
        title: Título de la alerta.
        message: Mensaje descriptivo.
        details: Diccionario con detalles adicionales.
        timestamp: Timestamp de creación.
        resolved: Si la alerta ha sido resuelta.
        resolved_at: Timestamp de resolución.
    """
    
    alert_type: str
    barrio_id: int
    priority: AlertPriority
    title: str
    message: str
    details: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def resolve(self) -> None:
        """Marca la alerta como resuelta."""
        self.resolved = True
        self.resolved_at = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convierte la alerta a diccionario."""
        return {
            "alert_type": self.alert_type,
            "barrio_id": self.barrio_id,
            "priority": self.priority.value,
            "title": self.title,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


def create_alert(
    alert_type: str,
    barrio_id: int,
    priority: AlertPriority,
    title: str,
    message: str,
    details: Optional[Dict] = None
) -> Alert:
    """
    Crea una nueva alerta.
    
    Args:
        alert_type: Tipo de alerta.
        barrio_id: ID del barrio.
        priority: Prioridad.
        title: Título.
        message: Mensaje.
        details: Detalles opcionales.
    
    Returns:
        Alert creada.
    """
    return Alert(
        alert_type=alert_type,
        barrio_id=barrio_id,
        priority=priority,
        title=title,
        message=message,
        details=details or {},
    )


def send_alert(
    alert: Alert,
    email_enabled: bool = False,
    email_recipients: Optional[list] = None
) -> None:
    """
    Envía una alerta (por ahora solo logging, email opcional futuro).
    
    Args:
        alert: Alert a enviar.
        email_enabled: Si True, envía email (no implementado aún).
        email_recipients: Lista de emails para notificar.
    """
    logger.info(
        "ALERTA [%s] %s - Barrio ID: %s - %s",
        alert.priority.value.upper(),
        alert.title,
        alert.barrio_id,
        alert.message
    )
    
    if email_enabled and email_recipients:
        # TODO: Implementar envío de email
        logger.warning("Envío de email no implementado aún")


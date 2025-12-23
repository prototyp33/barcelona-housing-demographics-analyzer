"""
Generador de reportes PDF usando reportlab o weasyprint.
"""

from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ReportType(Enum):
    """Tipos de reportes disponibles."""
    
    EXECUTIVE_SUMMARY = "executive_summary"
    BARRIO_DETAIL = "barrio_detail"
    QUARTERLY_REPORT = "quarterly_report"


def generate_report(
    report_type: ReportType,
    output_path: Path,
    data: Optional[Dict] = None,
    template_path: Optional[Path] = None
) -> Path:
    """
    Genera un reporte PDF.
    
    Args:
        report_type: Tipo de reporte a generar.
        output_path: Ruta donde guardar el PDF.
        data: Datos opcionales para el reporte.
        template_path: Ruta opcional a plantilla personalizada.
    
    Returns:
        Ruta al archivo PDF generado.
    
    Note:
        Implementación básica. Requiere reportlab o weasyprint instalado.
    """
    logger.info("Generando reporte %s en %s", report_type.value, output_path)
    
    # Crear directorio si no existe
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Intentar usar weasyprint (más simple para HTML a PDF)
    try:
        from weasyprint import HTML
        
        # Cargar plantilla
        if template_path is None:
            template_path = Path(__file__).parent / "templates" / f"{report_type.value}.html"
        
        if not template_path.exists():
            logger.warning("Plantilla no encontrada: %s. Creando reporte básico.", template_path)
            # Crear HTML básico
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head><title>Reporte {report_type.value}</title></head>
            <body>
                <h1>Reporte {report_type.value}</h1>
                <p>Generado automáticamente</p>
            </body>
            </html>
            """
        else:
            with open(template_path, "r", encoding="utf-8") as f:
                html_content = f.read()
        
        # Renderizar a PDF
        HTML(string=html_content).write_pdf(output_path)
        logger.info("Reporte generado exitosamente: %s", output_path)
        return output_path
    
    except ImportError:
        logger.warning("weasyprint no disponible. Instala con: pip install weasyprint")
        # Fallback: crear archivo de texto simple
        with open(output_path.with_suffix(".txt"), "w", encoding="utf-8") as f:
            f.write(f"Reporte {report_type.value}\n")
            f.write("=" * 50 + "\n")
            f.write("Generado automáticamente\n")
            if data:
                f.write(f"\nDatos: {data}\n")
        
        return output_path.with_suffix(".txt")

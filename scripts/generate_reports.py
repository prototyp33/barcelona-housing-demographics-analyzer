#!/usr/bin/env python3
"""
Script para generar reportes automáticos.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from src.reports.generator import generate_report, ReportType


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera reportes en PDF")
    parser.add_argument(
        "--type",
        dest="report_type",
        default="executive_summary",
        choices=[rt.value for rt in ReportType],
        help="Tipo de reporte a generar",
    )
    parser.add_argument(
        "--output",
        dest="output",
        default="reports/output/report.pdf",
        help="Ruta de salida del reporte",
    )
    args = parser.parse_args()

    report_type = ReportType(args.report_type)
    output_path = Path(args.output)

    generate_report(report_type, output_path)


if __name__ == "__main__":
    main()


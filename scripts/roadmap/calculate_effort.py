#!/usr/bin/env python3
"""
Helper script para calcular effort (semanas) entre dos fechas.

Útil para popular el campo "Effort (weeks)" en GitHub Projects.
"""

import argparse
import sys
from datetime import datetime


def calculate_effort_weeks(start_date: str, target_date: str) -> float:
    """
    Calcula effort en semanas entre dos fechas.
    
    Args:
        start_date: Fecha inicio en formato YYYY-MM-DD
        target_date: Fecha fin en formato YYYY-MM-DD
    
    Returns:
        Número de semanas (float, 1 decimal)
    """
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(target_date, '%Y-%m-%d')
        
        if end < start:
            raise ValueError("Target date must be after start date")
        
        days = (end - start).days
        weeks = days / 7.0
        
        return round(weeks, 1)
    
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("   Dates must be in YYYY-MM-DD format")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Calculate effort in weeks between two dates'
    )
    parser.add_argument('start_date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('target_date', help='Target date (YYYY-MM-DD)')
    parser.add_argument('--format', choices=['number', 'json'], default='number',
                       help='Output format')
    
    args = parser.parse_args()
    
    effort = calculate_effort_weeks(args.start_date, args.target_date)
    
    if args.format == 'json':
        import json
        output = {
            'start_date': args.start_date,
            'target_date': args.target_date,
            'effort_weeks': effort
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"{effort}")


if __name__ == "__main__":
    main()


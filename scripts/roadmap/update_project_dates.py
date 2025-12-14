#!/usr/bin/env python3
"""
Script para sincronizar fechas de issues con GitHub Projects Roadmap View.

Lee Start Date y Target Date del body de issues y actualiza los campos
correspondientes en GitHub Projects v2.
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    from github import Github
except ImportError:
    print("❌ Error: PyGithub required")
    print("   Install: pip install PyGithub")
    sys.exit(1)


def extract_dates_from_issue_body(body: str) -> tuple:
    """
    Extrae Start Date y Target Date del body de un issue.
    
    Busca patrones como:
    - **Start Date:** 2026-01-06
    - **Target Date:** 2026-01-17
    - Start: 2026-01-06
    - Target: 2026-01-17
    
    Returns:
        tuple: (start_date, target_date) o (None, None) si no se encuentran
    """
    start_date = None
    target_date = None
    
    # Patrones para Start Date
    start_patterns = [
        r'\*\*Start Date:\*\*\s*(\d{4}-\d{2}-\d{2})',
        r'Start:\s*(\d{4}-\d{2}-\d{2})',
        r'Start Date:\s*(\d{4}-\d{2}-\d{2})'
    ]
    
    # Patrones para Target Date
    target_patterns = [
        r'\*\*Target Date:\*\*\s*(\d{4}-\d{2}-\d{2})',
        r'Target:\s*(\d{4}-\d{2}-\d{2})',
        r'Target Date:\s*(\d{4}-\d{2}-\d{2})'
    ]
    
    for pattern in start_patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            start_date = match.group(1)
            break
    
    for pattern in target_patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            target_date = match.group(1)
            break
    
    return start_date, target_date


def update_project_dates(github_token: str, project_number: int, owner: str, repo: str):
    """
    Actualiza fechas en GitHub Projects desde issues.
    
    Args:
        github_token: GitHub personal access token
        project_number: Número del proyecto GitHub
        owner: Owner del repositorio
        repo: Nombre del repositorio
    """
    g = Github(github_token)
    repository = g.get_repo(f"{owner}/{repo}")
    
    # Obtener issues con labels epic o user-story
    issues = repository.get_issues(state='open', labels=['epic', 'user-story'])
    
    updated_count = 0
    skipped_count = 0
    
    print(f"📊 Processing {issues.totalCount} issues...")
    print("")
    
    for issue in issues:
        start_date, target_date = extract_dates_from_issue_body(issue.body)
        
        if not start_date and not target_date:
            skipped_count += 1
            continue
        
        print(f"Issue #{issue.number}: {issue.title}")
        if start_date:
            print(f"  Start Date: {start_date}")
        if target_date:
            print(f"  Target Date: {target_date}")
        
        # Nota: GitHub Projects v2 API requiere GraphQL
        # Este script prepara los datos, pero la actualización real
        # debe hacerse vía GitHub Projects UI o GraphQL API
        
        updated_count += 1
    
    print("")
    print("="*50)
    print(f"✅ Processed: {updated_count} issues with dates")
    print(f"⏭️  Skipped: {skipped_count} issues without dates")
    print("")
    print("⚠️  Note: Actual field updates require GitHub Projects GraphQL API")
    print("   This script extracts dates for manual update or GraphQL automation")


def main():
    parser = argparse.ArgumentParser(description='Sync issue dates to GitHub Projects')
    parser.add_argument('--project-number', type=int, required=True, help='GitHub Project number')
    parser.add_argument('--owner', required=True, help='Repository owner')
    parser.add_argument('--repo', required=True, help='Repository name')
    parser.add_argument('--token', help='GitHub token (or use GITHUB_TOKEN env var)')
    
    args = parser.parse_args()
    
    token = args.token or sys.environ.get('GITHUB_TOKEN')
    if not token:
        print("❌ Error: GitHub token required")
        print("   Set GITHUB_TOKEN env var or use --token")
        sys.exit(1)
    
    update_project_dates(token, args.project_number, args.owner, args.repo)


if __name__ == "__main__":
    main()


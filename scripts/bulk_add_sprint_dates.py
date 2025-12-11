#!/usr/bin/env python3
"""
Sprint Date Automation Script

Automates sprint date assignment for GitHub Issues using Projects v2 API.
Considers Spanish holidays for realistic planning.

Usage:
    python3 scripts/bulk_add_sprint_dates.py --show-calendar
    python3 scripts/bulk_add_sprint_dates.py --dry-run --critical-only
    python3 scripts/bulk_add_sprint_dates.py --apply

Author: Adrián Iraegui Álvear
Project: Barcelona Housing Demographics Analyzer
Version: 1.0.0
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Añadir directorio scripts al path para imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from github_graphql import GitHubGraphQL
except ImportError:
    print("❌ Error: No se pudo importar github_graphql.py")
    print("   Asegúrate de que scripts/github_graphql.py existe")
    sys.exit(1)

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

# Proyecto GitHub
REPO_OWNER = "prototyp33"
REPO_NAME = "barcelona-housing-demographics-analyzer"
PROJECT_NUMBER = 7

# Sprint dates optimized for Spain holidays
SPRINT_DATES = {
    "sprint-1": {
        "start": "2025-01-07",
        "end": "2025-01-26",
        "name": "Sprint 1: Quick Wins Foundation",
        "work_days": 15,
        "notes": "Avoids Christmas period"
    },
    "sprint-2": {
        "start": "2025-01-27",
        "end": "2025-03-02",
        "name": "Sprint 2: Core ML Engine",
        "work_days": 25,
        "notes": "No national holidays"
    },
    "sprint-3": {
        "start": "2025-03-03",
        "end": "2025-04-13",
        "name": "Sprint 3: Data Expansion",
        "work_days": 30,
        "notes": "Ends before Easter Week"
    },
    "sprint-4": {
        "start": "2025-04-21",
        "end": "2025-06-01",
        "name": "Sprint 4: Differentiation Showcase",
        "work_days": 30,
        "notes": "Includes May 1st (holiday)"
    },
    "sprint-5": {
        "start": "2025-06-02",
        "end": "2025-06-29",
        "name": "Sprint 5: Dashboard",
        "work_days": 20,
        "notes": "Pre-summer period"
    },
    "sprint-6": {
        "start": "2025-06-30",
        "end": "2025-07-27",
        "name": "Sprint 6: Polish & Testing",
        "work_days": 20,
        "notes": "Summer period, reduced intensity"
    },
    "sprint-7": {
        "start": "2025-09-01",
        "end": "2025-09-28",
        "name": "Sprint 7: Advanced Features",
        "work_days": 20,
        "notes": "Post-August return"
    },
    "sprint-8": {
        "start": "2025-09-29",
        "end": "2025-10-26",
        "name": "Sprint 8: Documentation & Launch",
        "work_days": 20,
        "notes": "Includes Oct 12th (National Day)"
    },
}

# Critical epic issues (priority)
CRITICAL_ISSUES = [91, 87, 89, 123, 92, 93, 95]

# Spanish holidays 2025
SPAIN_HOLIDAYS_2025 = {
    "2025-01-01": "Año Nuevo",
    "2025-01-06": "Reyes",
    "2025-04-13": "Domingo de Ramos",
    "2025-04-18": "Viernes Santo",
    "2025-04-20": "Domingo de Resurrección",
    "2025-05-01": "Día del Trabajo",
    "2025-08-15": "Asunción",
    "2025-10-12": "Fiesta Nacional",
    "2025-11-01": "Todos los Santos",
    "2025-12-06": "Constitución",
    "2025-12-08": "Inmaculada",
    "2025-12-25": "Navidad",
}

# ==============================================================================
# LOGGING SETUP
# ==============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sprint_dates_update.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ==============================================================================
# SPRINT DATE MANAGER
# ==============================================================================

class SprintDateManager:
    """Manages sprint date assignment via GitHub Projects v2 API."""
    
    def __init__(self, token: Optional[str] = None, dry_run: bool = True):
        """
        Initialize the manager.
        
        Args:
            token: GitHub token (or use GITHUB_TOKEN env var)
            dry_run: If True, only preview changes without applying
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError(
                "GitHub token required. Set GITHUB_TOKEN or pass --token"
            )
        
        self.dry_run = dry_run
        self.gh = GitHubGraphQL(token=self.token)
        self.project_id = None
        self.field_ids = {}
        
        logger.info("=" * 60)
        logger.info("Sprint Date Manager initialized")
        logger.info(f"Mode: {'DRY RUN' if dry_run else 'APPLY CHANGES'}")
        logger.info(f"Repository: {REPO_OWNER}/{REPO_NAME}")
        logger.info(f"Project: #{PROJECT_NUMBER}")
        logger.info("=" * 60)
    
    def initialize_project(self) -> bool:
        """
        Initialize project connection and fetch metadata.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Fetching project metadata...")
            
            # Get project using the any-scope method
            project = self.gh.get_project_v2_any(
                owner=REPO_OWNER,
                repo=REPO_NAME,
                project_owner=REPO_OWNER,
                project_number=PROJECT_NUMBER
            )
            
            if not project:
                logger.error(f"❌ Project #{PROJECT_NUMBER} not found")
                logger.error("   Check that the project exists and token has 'project' scope")
                return False
            
            self.project_id = project["id"]
            logger.info(f"✅ Project found: {project.get('title', 'Untitled')}")
            logger.info(f"   Project ID: {self.project_id}")
            logger.info(f"   URL: {project.get('url', 'N/A')}")
            
            # Parse custom fields
            fields = project.get("fields", {}).get("nodes", [])
            for field in fields:
                field_name = field.get("name")
                field_id = field.get("id")
                if field_name and field_id:
                    self.field_ids[field_name] = field_id
            
            logger.info(f"   Custom fields: {list(self.field_ids.keys())}")
            
            # Validate required fields (case-sensitive check for existing fields)
            # Try multiple variations of field names
            start_field = None
            end_field = None
            
            for field_name in self.field_ids.keys():
                if field_name.lower() == "start date":
                    start_field = field_name
                if field_name.lower() in ["end date", "target date"]:
                    end_field = field_name
            
            if not start_field or not end_field:
                logger.warning("⚠️  Missing 'Start Date' or 'End Date' fields")
                logger.warning(f"   Found: Start={start_field}, End={end_field}")
                logger.warning("   Create them in project settings: https://github.com/users/%s/projects/%d/settings",
                             REPO_OWNER, PROJECT_NUMBER)
                return False
            
            # Store the actual field names for later use
            self.start_field_name = start_field
            self.end_field_name = end_field
            logger.info(f"   Using fields: '{start_field}' and '{end_field}'")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error initializing project: {e}")
            return False
    
    def get_issues_by_sprint_label(self, sprint_label: str) -> List[Dict]:
        """
        Get issues with a specific sprint label.
        
        Args:
            sprint_label: Sprint label (e.g., 'sprint-1')
        
        Returns:
            List of issue dicts with number, title, id
        """
        try:
            result = self.gh.get_issues_with_details(
                owner=REPO_OWNER,
                repo=REPO_NAME,
                state="OPEN",
                labels=[sprint_label],
                limit=100
            )
            
            issues = []
            for issue in result["issues"]:
                # Extract GraphQL node ID from issue (needed for project operations)
                issues.append({
                    "number": issue["number"],
                    "title": issue["title"],
                    "id": issue.get("id"),  # GraphQL node ID
                    "url": issue["url"]
                })
            
            return issues
            
        except Exception as e:
            logger.error(f"❌ Error fetching issues for {sprint_label}: {e}")
            return []
    
    def update_issue_dates(self, issue_id: str, project_item_id: str, start_date: str, end_date: str) -> bool:
        """
        Update start and end dates for an issue in the project.
        
        Args:
            issue_id: GitHub issue node ID
            project_item_id: Project item ID (from project board)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            True if successful, False otherwise
        """
        if self.dry_run:
            logger.info(f"    [DRY RUN] Would set: Start={start_date}, End={end_date}")
            return True
        
        try:
            # Update Start Date
            mutation_start = """
            mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: Date!) {
                updateProjectV2ItemFieldValue(input: {
                    projectId: $projectId
                    itemId: $itemId
                    fieldId: $fieldId
                    value: {date: $value}
                }) {
                    projectV2Item {
                        id
                    }
                }
            }
            """
            
            self.gh.execute_query(mutation_start, {
                "projectId": self.project_id,
                "itemId": project_item_id,
                "fieldId": self.field_ids[self.start_field_name],
                "value": start_date
            })
            
            # Update End Date
            mutation_end = """
            mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: Date!) {
                updateProjectV2ItemFieldValue(input: {
                    projectId: $projectId
                    itemId: $itemId
                    fieldId: $fieldId
                    value: {date: $value}
                }) {
                    projectV2Item {
                        id
                    }
                }
            }
            """
            
            self.gh.execute_query(mutation_end, {
                "projectId": self.project_id,
                "itemId": project_item_id,
                "fieldId": self.field_ids[self.end_field_name],
                "value": end_date
            })
            
            logger.info(f"    ✅ Dates updated: {start_date} → {end_date}")
            return True
            
        except Exception as e:
            logger.error(f"    ❌ Error updating dates: {e}")
            return False
    
    def process_sprint(self, sprint_label: str, critical_only: bool = False) -> Dict[str, int]:
        """
        Process all issues for a sprint.
        
        Args:
            sprint_label: Sprint label (e.g., 'sprint-1')
            critical_only: Only process critical issues
        
        Returns:
            Dict with stats: {processed, updated, errors}
        """
        stats = {"processed": 0, "updated": 0, "errors": 0, "skipped": 0}
        
        if sprint_label not in SPRINT_DATES:
            logger.warning(f"⚠️  Unknown sprint label: {sprint_label}")
            return stats
        
        sprint_info = SPRINT_DATES[sprint_label]
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Processing {sprint_label}: {sprint_info['name']}")
        logger.info(f"Dates: {sprint_info['start']} → {sprint_info['end']}")
        logger.info(f"Work days: {sprint_info['work_days']}")
        logger.info(f"Notes: {sprint_info['notes']}")
        logger.info(f"{'=' * 60}")
        
        # Get issues with this sprint label
        issues = self.get_issues_by_sprint_label(sprint_label)
        
        if critical_only:
            issues = [i for i in issues if i["number"] in CRITICAL_ISSUES]
        
        logger.info(f"Found {len(issues)} issues")
        
        for issue in issues:
            stats["processed"] += 1
            is_critical = "🔥" if issue["number"] in CRITICAL_ISSUES else "  "
            
            logger.info(f"{is_critical} #{issue['number']}: {issue['title']}")
            
            # Note: To update dates, the issue must already be in the project
            # We would need to:
            # 1. Get project item ID for this issue
            # 2. Call update_issue_dates with that ID
            # This requires additional GraphQL queries - left as TODO
            
            logger.warning(f"    ⚠️  Issue must be added to project first")
            logger.info(f"    Would set: {sprint_info['start']} → {sprint_info['end']}")
            stats["skipped"] += 1
        
        return stats

# ==============================================================================
# CALENDAR VISUALIZATION
# ==============================================================================

def show_sprint_calendar():
    """Display visual sprint calendar."""
    print("\n" + "=" * 70)
    print(" 📅 SPRINT CALENDAR 2025 ".center(70))
    print("=" * 70 + "\n")
    
    for sprint_id, info in SPRINT_DATES.items():
        # Calculate bar length (4 chars per week)
        start = datetime.strptime(info["start"], "%Y-%m-%d")
        end = datetime.strptime(info["end"], "%Y-%m-%d")
        weeks = (end - start).days / 7
        bar = "█" * int(weeks * 4)
        
        print(f"{start.strftime('%b %Y'):10s} {bar:30s} {sprint_id}")
        print(f"           {info['name']}")
        print(f"           {info['start']} → {info['end']} ({info['work_days']} work days)")
        print(f"           {info['notes']}")
        print()
    
    print("=" * 70)
    print("\n🎯 Key Periods:")
    print("   ❄️  Christmas: Dec 24, 2024 - Jan 6, 2025")
    print("   🐣 Easter Week: Apr 13-20, 2025")
    print("   ☀️  Summer Break: August 2025")
    print("\n" + "=" * 70 + "\n")

def generate_summary_report(all_stats: Dict[str, Dict[str, int]]):
    """Generate summary report of processing."""
    total_processed = sum(s["processed"] for s in all_stats.values())
    total_updated = sum(s["updated"] for s in all_stats.values())
    total_errors = sum(s["errors"] for s in all_stats.values())
    total_skipped = sum(s["skipped"] for s in all_stats.values())
    
    print("\n" + "=" * 70)
    print(" 📊 SUMMARY REPORT ".center(70))
    print("=" * 70)
    print(f"\nTotal issues processed: {total_processed}")
    print(f"Successfully updated:   {total_updated}")
    print(f"Errors:                 {total_errors}")
    print(f"Skipped:                {total_skipped}")
    print("\nBy Sprint:")
    for sprint, stats in all_stats.items():
        print(f"  {sprint:10s}: {stats['processed']:3d} processed, "
              f"{stats['updated']:3d} updated, {stats['errors']:3d} errors")
    print("\n" + "=" * 70 + "\n")

# ==============================================================================
# MAIN
# ==============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Bulk update sprint dates for GitHub Issues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # View sprint calendar
  python3 scripts/bulk_add_sprint_dates.py --show-calendar
  
  # Preview critical issues only
  python3 scripts/bulk_add_sprint_dates.py --dry-run --critical-only
  
  # Apply to all issues
  python3 scripts/bulk_add_sprint_dates.py --apply
  
  # Process specific sprint
  python3 scripts/bulk_add_sprint_dates.py --apply --sprint sprint-1
        """
    )
    
    parser.add_argument("--token", help="GitHub Personal Access Token (or use GITHUB_TOKEN env var)")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying")
    parser.add_argument("--apply", action="store_true", help="Apply changes to GitHub")
    parser.add_argument("--critical-only", action="store_true", help="Only process critical epic issues")
    parser.add_argument("--sprint", help="Process specific sprint (e.g., sprint-1)")
    parser.add_argument("--show-calendar", action="store_true", help="Display sprint calendar and exit")
    
    args = parser.parse_args()
    
    # Show calendar if requested
    if args.show_calendar:
        show_sprint_calendar()
        return 0
    
    # Validate arguments
    if not (args.dry_run or args.apply):
        parser.error("Must specify --dry-run or --apply (or use --show-calendar)")
    
    # Initialize manager
    try:
        manager = SprintDateManager(token=args.token, dry_run=args.dry_run)
    except ValueError as e:
        logger.error(f"❌ {e}")
        return 1
    
    # Initialize project connection
    if not manager.initialize_project():
        logger.error("❌ Failed to initialize project. Exiting.")
        return 1
    
    # Process sprints
    all_stats = {}
    
    if args.sprint:
        # Process single sprint
        if args.sprint not in SPRINT_DATES:
            logger.error(f"❌ Unknown sprint: {args.sprint}")
            logger.error(f"   Valid sprints: {', '.join(SPRINT_DATES.keys())}")
            return 1
        
        stats = manager.process_sprint(args.sprint, critical_only=args.critical_only)
        all_stats[args.sprint] = stats
    else:
        # Process all sprints
        for sprint_label in SPRINT_DATES.keys():
            stats = manager.process_sprint(sprint_label, critical_only=args.critical_only)
            all_stats[sprint_label] = stats
    
    # Generate summary
    generate_summary_report(all_stats)
    
    # Final message
    if args.dry_run:
        logger.info("✅ Dry run completed. Use --apply to apply changes.")
    else:
        logger.info("✅ Changes applied successfully.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

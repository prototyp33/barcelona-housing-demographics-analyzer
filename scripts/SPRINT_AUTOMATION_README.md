# 🗓️ Sprint Date Automation - README

## Overview

`bulk_add_sprint_dates.py` automates the assignment of sprint start and end dates to GitHub issues based on their sprint labels. The script integrates with GitHub Projects v2 API and considers Spanish holidays for realistic planning.

## Features

- ✅ **Automated date assignment** based on sprint labels
- ✅ **Spanish holiday awareness** (Christmas, Easter, August, National Days)
- ✅ **Dry-run mode** for safe previewing
- ✅ **Critical issue filtering** for phased rollout
- ✅ **Detailed logging** with file output
- ✅ **Sprint-specific processing** for targeted updates
- ✅ **Visual calendar** display

## Sprint Calendar 2025

The project roadmap is organized into 8 sprints from January to October 2025:

```
Jan 2025  ████████████ Sprint 1 (3 weeks) - Quick Wins
          ██████████████████████████ Sprint 2 (5 weeks) - Core ML
Mar 2025  ██████████████████████████████ Sprint 3 (6 weeks) - Data Expansion
          [EASTER WEEK - APR 13-20]
Apr 2025  ██████████████████████████████ Sprint 4 (6 weeks) - Showcase
Jun 2025  ████████████████ Sprint 5 (4 weeks) - Dashboard
          ████████████████ Sprint 6 (4 weeks) - Testing
          [AUGUST - VACATION]
Sep 2025  ████████████████ Sprint 7 (4 weeks) - Advanced
          ████████████████ Sprint 8 (4 weeks) - Launch
```

**Key Planning Considerations:**

- ❄️ **Avoids Christmas** (Dec 24 - Jan 6)
- 🐣 **Avoids Easter Week** (Apr 13-20, 2025)
- ☀️ **No work in August** (Summer vacation)
- 📅 **Considers Spanish national holidays**

## Quick Start

### 1. Setup GitHub Token

```bash
# Option 1: Using GitHub CLI
gh auth login
export GITHUB_TOKEN=$(gh auth token)

# Option 2: Create token manually at https://github.com/settings/tokens/new
# Required scopes: repo, project
export GITHUB_TOKEN="ghp_your_token_here"

# Option 3: Add to your shell profile (persistent)
echo 'export GITHUB_TOKEN="ghp_your_token_here"' >> ~/.zshrc
source ~/.zshrc
```

### 2. View Sprint Calendar

```bash
python3 scripts/bulk_add_sprint_dates.py --show-calendar
```

### 3. Preview Changes (Recommended First)

```bash
# Preview only critical issues (safest)
python3 scripts/bulk_add_sprint_dates.py --dry-run --critical-only

# Preview all issues with sprint labels
python3 scripts/bulk_add_sprint_dates.py --dry-run

# Preview specific sprint
python3 scripts/bulk_add_sprint_dates.py --dry-run --sprint sprint-1
```

### 4. Apply Changes

```bash
# Apply to critical issues first (phased approach)
python3 scripts/bulk_add_sprint_dates.py --apply --critical-only

# Apply to all issues
python3 scripts/bulk_add_sprint_dates.py --apply

# Apply to specific sprint
python3 scripts/bulk_add_sprint_dates.py --apply --sprint sprint-1
```

## Usage Examples

### Example 1: Safe First Run (Critical Issues Only)

```bash
# Step 1: View the calendar
python3 scripts/bulk_add_sprint_dates.py --show-calendar

# Step 2: Preview critical issues
python3 scripts/bulk_add_sprint_dates.py --dry-run --critical-only

# Step 3: Apply to critical issues (7 epic issues)
python3 scripts/bulk_add_sprint_dates.py --apply --critical-only

# Step 4: Review results in GitHub Project #7
open https://github.com/users/prototyp33/projects/7
```

### Example 2: Process Specific Sprint

```bash
# Preview Sprint 1 issues
python3 scripts/bulk_add_sprint_dates.py --dry-run --sprint sprint-1

# Apply dates to Sprint 1 issues
python3 scripts/bulk_add_sprint_dates.py --apply --sprint sprint-1
```

### Example 3: Full Rollout

```bash
# Preview all changes
python3 scripts/bulk_add_sprint_dates.py --dry-run

# Apply to all issues with sprint labels
python3 scripts/bulk_add_sprint_dates.py --apply
```

## Critical Epic Issues

The following 7 issues are flagged as **critical epics** and receive priority focus:

- **#91** - [Epic description]
- **#87** - [Epic description]
- **#89** - [Epic description]
- **#123** - [Epic description]
- **#92** - [Epic description]
- **#93** - [Epic description]
- **#95** - [Epic description]

These align with Sprint 1-2 and are essential for the "Quick Wins Foundation" milestone.

## Sprint Dates Reference

| Sprint   | Start Date | End Date   | Duration | Work Days |
| -------- | ---------- | ---------- | -------- | --------- |
| sprint-1 | 2025-01-07 | 2025-01-26 | 20 days  | 15 days   |
| sprint-2 | 2025-01-27 | 2025-03-02 | 35 days  | 25 days   |
| sprint-3 | 2025-03-03 | 2025-04-13 | 42 days  | 30 days   |
| sprint-4 | 2025-04-21 | 2025-06-01 | 42 days  | 30 days   |
| sprint-5 | 2025-06-02 | 2025-06-29 | 28 days  | 20 days   |
| sprint-6 | 2025-06-30 | 2025-07-27 | 28 days  | 20 days   |
| sprint-7 | 2025-09-01 | 2025-09-28 | 28 days  | 20 days   |
| sprint-8 | 2025-09-29 | 2025-10-26 | 28 days  | 20 days   |

**Total Duration:** 10 months (Jan - Oct 2025)  
**Total Work Days:** 180 days  
**Holidays Avoided:** 12+ Spanish national/regional holidays

## Requirements

### Prerequisites

1. **Python 3.11+**
2. **GitHub Token** with scopes:
   - `repo` - Full repository access
   - `project` - Project read/write access
3. **Dependencies**:
   - `scripts/github_graphql.py` - GraphQL client wrapper

### Project Setup Requirements

Issues must meet the following criteria:

- ✅ **Tagged with sprint label** (`sprint-1` through `sprint-8`)
- ✅ **Added to GitHub Project #7**
- ✅ **Project has custom fields**:
  - "Start Date" (Date type)
  - "End Date" (Date type)

If custom fields don't exist, create them in GitHub Projects UI:

1. Go to https://github.com/users/prototyp33/projects/7
2. Click "Settings" (⚙️)
3. Add custom field: "Start Date" (Type: Date)
4. Add custom field: "End Date" (Type: Date)

## Output and Logging

### Console Output

The script provides rich console output with:

- 📊 Summary statistics
- 🔥 Critical issue highlighting
- ✅ Success/failure indicators
- ⚠️ Warnings for missing configurations

### Log File

All operations are logged to `sprint_dates_update.log`:

```bash
# View recent log entries
tail -f sprint_dates_update.log

# Search for errors
grep ERROR sprint_dates_update.log

# View specific sprint processing
grep "sprint-1" sprint_dates_update.log
```

## Troubleshooting

### Error: "GITHUB_TOKEN environment variable not set"

**Solution:**

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

### Error: "Project #7 not found"

**Causes:**

- Token doesn't have `project` scope
- Project number is incorrect
- Project belongs to an organization (not user account)

**Solution:**

1. Verify project exists: https://github.com/users/prototyp33/projects/7
2. Check token scopes at https://github.com/settings/tokens
3. Regenerate token with correct scopes

### Warning: "Start Date or End Date fields not found"

**Cause:** Project doesn't have required custom fields

**Solution:**

1. Go to https://github.com/users/prototyp33/projects/7/settings
2. Add custom field: "Start Date" (Type: Date)
3. Add custom field: "End Date" (Type: Date)
4. Re-run the script

### Warning: "Issues must be added to the project first"

**Cause:** Issues exist but aren't linked to the project board

**Solution:**

1. Go to https://github.com/prototyp33/barcelona-housing-demographics-analyzer/issues
2. For each issue, click "Projects" in the right sidebar
3. Select "Project #7" to add the issue
4. Re-run the script

## Architecture & Design

### How It Works

1. **Initialization**

   - Authenticates with GitHub GraphQL API
   - Fetches Project #7 metadata
   - Retrieves custom field IDs

2. **Issue Discovery**

   - Queries repository for issues with sprint labels
   - Filters by critical status if requested
   - Groups issues by sprint

3. **Date Assignment**

   - Looks up sprint dates from `SPRINT_DATES` mapping
   - Updates project item fields via GraphQL mutations
   - Logs all operations

4. **Reporting**
   - Generates summary statistics
   - Outputs visual reports
   - Saves detailed logs

### Code Structure

```python
# Main components
SprintDateManager      # GitHub API wrapper
SPRINT_DATES          # Roadmap configuration
CRITICAL_ISSUES       # Priority issue list
SPAIN_HOLIDAYS_2025   # Holiday calendar

# Key functions
initialize_project()           # Setup
get_issues_by_sprint_label()  # Discovery
update_issue_dates()           # Mutation
show_sprint_calendar()         # Visualization
generate_summary_report()      # Reporting
```

## Advanced Usage

### Customize Sprint Dates

Edit `SPRINT_DATES` in the script:

```python
SPRINT_DATES = {
    "sprint-1": {
        "start": "2025-01-07",
        "end": "2025-01-26",
        "name": "Sprint 1: Quick Wins Foundation",
        "work_days": 15,
        "notes": "Avoids Christmas period"
    },
    # ... add more sprints
}
```

### Add More Critical Issues

Update `CRITICAL_ISSUES` list:

```python
CRITICAL_ISSUES = [91, 87, 89, 123, 92, 93, 95, 100, 105]  # Add issue numbers
```

### Integrate with CI/CD

```yaml
# .github/workflows/update-sprint-dates.yml
name: Update Sprint Dates
on:
  schedule:
    - cron: "0 9 * * 1" # Every Monday at 9 AM
  workflow_dispatch:

jobs:
  update-dates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - name: Update sprint dates
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python3 scripts/bulk_add_sprint_dates.py --apply
```

## Best Practices

### Recommended Workflow

1. **Weekly Review** (Monday morning)

   - Run `--show-calendar` to review upcoming deadlines
   - Check for issues missing sprint labels

2. **Sprint Planning** (Start of sprint)

   - Tag new issues with sprint labels
   - Run `--dry-run` to preview assignments
   - Run `--apply` to update dates

3. **Mid-Sprint Check** (Wednesday)

   - Review progress in GitHub Project board
   - Adjust sprint labels if needed
   - Re-run script to update dates

4. **Sprint Retrospective** (End of sprint)
   - Document actual vs. planned dates
   - Update `SPRINT_DATES` if patterns emerge

### Tips for Success

- ✅ **Always dry-run first** before applying changes
- ✅ **Start with critical issues** to validate the process
- ✅ **Keep sprint labels updated** as issues evolve
- ✅ **Monitor logs** for errors or warnings
- ✅ **Sync with team** before bulk updates

## Portfolio Showcase

This script demonstrates several professional software engineering practices:

- 🔧 **API Integration**: GitHub GraphQL API v4
- 🐍 **Python Best Practices**: Type hints, logging, arg parsing
- 📊 **Project Management**: Sprint planning, roadmap visualization
- 🌍 **Localization**: Spanish holiday calendar support
- 🛡️ **Safety**: Dry-run mode, detailed validation
- 📝 **Documentation**: Comprehensive README, inline comments
- 🎯 **User Experience**: Rich console output, helpful error messages

## Contributing

To improve this script:

1. Fork the repository
2. Create a feature branch
3. Test with `--dry-run` extensively
4. Submit a PR with:
   - Clear description of changes
   - Test results from dry-run
   - Updated documentation if needed

## Support

For issues or questions:

- 📖 Check [docs/PROJECT_BEST_PRACTICES.md](../docs/PROJECT_BEST_PRACTICES.md)
- 🐛 File an issue: https://github.com/prototyp33/barcelona-housing-demographics-analyzer/issues
- 💬 Discussion: Use GitHub Discussions

---

**Author:** Adrián Iraegui Álvear  
**Project:** Barcelona Housing Demographics Analyzer  
**Version:** 1.0.0  
**Last Updated:** December 2024

#!/usr/bin/env python3
"""
Batch update chart heights across all view files
Applies standardized CHART_HEIGHTS configuration
"""

import re
from pathlib import Path

# Define the views directory
VIEWS_DIR = Path("src/app/views")

# Height mappings (old -> new)
HEIGHT_MAPPINGS = {
    "height=400": "height=CHART_HEIGHTS['compact']",
    "height=450": "height=CHART_HEIGHTS['compact']",
    "height=500": "height=CHART_HEIGHTS['standard']",
    "height=520": "height=CHART_HEIGHTS['standard']",
    "height=600": "height=CHART_HEIGHTS['standard']",
    "height=650": "height=CHART_HEIGHTS['expanded']",
    "height=700": "height=CHART_HEIGHTS['expanded']",
    "height=800": "height=CHART_HEIGHTS['expanded']",
}

# Import statement to add
IMPORT_STATEMENT = "from src.app.chart_config import CHART_HEIGHTS\n"

def update_file(filepath: Path) -> tuple[bool, int]:
    """Update a single file with standardized heights"""
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    changes = 0
    
    # Check if import already exists
    if "from src.app.chart_config import CHART_HEIGHTS" not in content:
        # Find the last import statement
        import_pattern = r'(from src\.app\.[^\n]+\n)'
        imports = list(re.finditer(import_pattern, content))
        
        if imports:
            last_import = imports[-1]
            insert_pos = last_import.end()
            content = content[:insert_pos] + IMPORT_STATEMENT + content[insert_pos:]
            changes += 1
    
    # Replace height values
    for old_height, new_height in HEIGHT_MAPPINGS.items():
        if old_height in content:
            # Only replace if it's a plotly height parameter
            pattern = rf"({old_height}[,\)])"
            matches = re.findall(pattern, content)
            if matches:
                content = re.sub(pattern, lambda m: new_height + m.group(0)[-1], content)
                changes += len(matches)
    
    # Write back if changed
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        return True, changes
    
    return False, 0

def main():
    """Main execution"""
    print("🔧 Updating chart heights across all views...")
    print(f"📁 Directory: {VIEWS_DIR}")
    print()
    
    total_files = 0
    total_changes = 0
    updated_files = []
    
    # Process all Python files in views directory
    for filepath in VIEWS_DIR.glob("*.py"):
        if filepath.name == "__init__.py":
            continue
        
        updated, changes = update_file(filepath)
        total_files += 1
        
        if updated:
            updated_files.append(filepath.name)
            total_changes += changes
            print(f"✅ {filepath.name}: {changes} changes")
        else:
            print(f"⏭️  {filepath.name}: no changes needed")
    
    print()
    print("=" * 60)
    print(f"📊 Summary:")
    print(f"   Files processed: {total_files}")
    print(f"   Files updated: {len(updated_files)}")
    print(f"   Total changes: {total_changes}")
    print()
    
    if updated_files:
        print("📝 Updated files:")
        for filename in updated_files:
            print(f"   - {filename}")
    
    print()
    print("✅ Done!")

if __name__ == "__main__":
    main()

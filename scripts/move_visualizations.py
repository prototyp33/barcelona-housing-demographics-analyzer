import os
import shutil
from pathlib import Path

def move_existing_visualizations(source_paths, target_dir):
    os.makedirs(target_dir, exist_ok=True)
    
    for source in source_paths:
        source_path = Path(source)
        if not source_path.exists():
            print(f"Source not found: {source}")
            continue
            
        if source_path.is_file():
            # It's a single file
            target_path = Path(target_dir) / source_path.name
            shutil.copy2(source_path, target_path)
            print(f"Copied {source_path} to {target_path}")
        elif source_path.is_dir():
            # It's a directory, find all images inside
            for img_path in source_path.glob("**/*.*"):
                if img_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.svg', '.pdf']:
                    # Avoid moving from internal envs if caught by mistake
                    if '.venv' in str(img_path) or 'node_modules' in str(img_path) or '.git' in str(img_path):
                        continue
                    
                    # Also avoid the visualizations folder itself
                    if 'visualizations' in str(img_path.parent) and img_path.parent.name == 'visualizations':
                         if img_path.parent == Path(target_dir).resolve():
                             continue

                    target_path = Path(target_dir) / img_path.name
                    shutil.copy2(img_path, target_path)
                    print(f"Copied {img_path} to {target_path}")

if __name__ == "__main__":
    project_root = "/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer"
    target_dir = os.path.join(project_root, "visualizations")
    
    sources = [
        os.path.join(project_root, "reports"),
        os.path.join(project_root, "spike-data-validation/outputs/visualizations"),
        os.path.join(project_root, "spike-data-validation/data/processed"),
        os.path.join(project_root, "src/app/assets/hero_barcelona.png")
    ]
    
    move_existing_visualizations(sources, target_dir)

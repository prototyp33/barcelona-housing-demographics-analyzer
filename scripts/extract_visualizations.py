import json
import os
import base64
from pathlib import Path
import re

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text.strip('_')

def extract_images_from_notebooks(notebooks_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    notebook_paths = list(Path(notebooks_dir).glob("*.ipynb"))
    
    extracted_count = 0
    for nb_path in notebook_paths:
        print(f"Processing {nb_path.name}...")
        with open(nb_path, 'r', encoding='utf-8') as f:
            try:
                nb_data = json.load(f)
            except Exception as e:
                print(f"Error loading {nb_path}: {e}")
                continue
        
        last_markdown = "untitled"
        for i, cell in enumerate(nb_data.get('cells', [])):
            if cell.get('cell_type') == 'markdown':
                # Try to get a name from the header
                content = "".join(cell.get('source', []))
                headers = re.findall(r'^#+\s+(.*)', content, re.MULTILINE)
                if headers:
                    last_markdown = slugify(headers[-1])
            
            if cell.get('cell_type') == 'code':
                outputs = cell.get('outputs', [])
                for j, output in enumerate(outputs):
                    if 'data' in output and 'image/png' in output['data']:
                        img_data = output['data']['image/png']
                        # Handle list of strings or single string
                        if isinstance(img_data, list):
                            img_data = "".join(img_data)
                        
                        img_bytes = base64.b64decode(img_data)
                        
                        nb_name = slugify(nb_path.stem)
                        filename = f"{nb_name}_{last_markdown}_{i}_{j}.png"
                        filepath = os.path.join(output_dir, filename)
                        
                        with open(filepath, 'wb') as img_f:
                            img_f.write(img_bytes)
                        extracted_count += 1
                        print(f"  Saved {filename}")
    
    print(f"Total extracted: {extracted_count}")

if __name__ == "__main__":
    project_root = "/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer"
    notebooks_dir = os.path.join(project_root, "notebooks")
    output_dir = os.path.join(project_root, "visualizations")
    extract_images_from_notebooks(notebooks_dir, output_dir)

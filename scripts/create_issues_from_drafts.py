#!/usr/bin/env python3
"""
Crea GitHub issues automáticamente desde drafts validados.

Uso:
    # Crear una issue específica
    python scripts/create_issues_from_drafts.py docs/issues/mi-issue.md
    
    # Crear todas las issues de un directorio
    python scripts/create_issues_from_drafts.py docs/issues/ --batch
    
    # Preview sin crear
    python scripts/create_issues_from_drafts.py docs/issues/mi-issue.md --dry-run

Requiere:
    - gh CLI instalado y autenticado
    - Issues draft válidas en docs/issues/
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional, List, Tuple


# Labels válidos del proyecto
VALID_LABELS = {
    "bug", "enhancement", "task", "documentation",
    "etl", "testing", "data-quality", "quality-assurance",
    "code-quality", "cleanup", "ci-cd", "workflow",
    "data-extraction", "analysis", "dashboard", "streamlit",
    "database", "data-processing", "data-loading",
    "sprint-1", "sprint-2", "sprint-3", "sprint-4",
}


def validate_issue_content(content: str) -> Tuple[List[str], List[str]]:
    """
    Valida que una issue cumpla con las mejores prácticas.
    
    Returns:
        Tupla de (errores, advertencias)
    """
    errors = []
    warnings = []
    
    # Validar secciones requeridas
    if not re.search(r"##.*Objetivo|##.*Descripción", content, re.IGNORECASE):
        errors.append("Falta sección 'Objetivo' o 'Descripción'")
    
    if not re.search(r"##.*Criterios de Aceptación|##.*Definition of Done", content, re.IGNORECASE):
        errors.append("Falta sección 'Criterios de Aceptación'")
    
    if not re.search(r"- \[ \]", content):
        errors.append("No hay criterios de aceptación con checkboxes")
    
    if not re.search(r"\d+\s*(horas?|días?|minutos?)", content, re.IGNORECASE):
        errors.append("Falta estimación de tiempo numérica")
    
    return errors, warnings


def parse_issue_metadata(content: str) -> dict:
    """Extrae metadatos de la issue (labels, milestone, título)."""
    metadata = {
        "labels": [],
        "milestone": None,
        "title": None,
    }
    
    # Extraer título del frontmatter o del contenido
    # Buscar en frontmatter: title: "[FEATURE] Mi título"
    title_match = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', content, re.MULTILINE)
    if title_match:
        metadata["title"] = title_match.group(1).strip()
    else:
        # Buscar primer heading H1 o H2
        heading_match = re.search(r'^##?\s+(.+)$', content, re.MULTILINE)
        if heading_match:
            metadata["title"] = heading_match.group(1).strip()
    
    # Buscar labels en frontmatter: labels: bug, etl
    labels_match = re.search(r'^labels:\s*(.+)$', content, re.MULTILINE)
    if labels_match:
        labels_str = labels_match.group(1).strip()
        labels = [l.strip() for l in labels_str.split(',')]
        metadata["labels"] = [l for l in labels if l in VALID_LABELS]
    
    # Si no hay labels en frontmatter, buscar en contenido
    if not metadata["labels"]:
        # Buscar labels entre backticks o en formato **Labels**: `bug`, `etl`
        label_pattern = r'`([a-z0-9-]+)`'
        found_labels = re.findall(label_pattern, content)
        metadata["labels"] = list(set(l for l in found_labels if l in VALID_LABELS))
    
    # Buscar milestone
    milestone_match = re.search(
        r'\*\*(?:Milestone|Sprint)\*\*:\s*(.+?)(?:\n|$)',
        content
    )
    if milestone_match:
        metadata["milestone"] = milestone_match.group(1).strip()
    
    return metadata


def create_github_issue(
    filepath: Path,
    dry_run: bool = False
) -> Optional[str]:
    """
    Crea una issue en GitHub desde un draft.
    
    Args:
        filepath: Ruta al archivo .md del draft
        dry_run: Si es True, solo muestra qué haría sin crear
    
    Returns:
        URL de la issue creada, o None si hubo error
    """
    content = filepath.read_text(encoding="utf-8")
    
    # Validar contenido
    errors, warnings = validate_issue_content(content)
    if errors:
        print(f"❌ {filepath.name} tiene errores:")
        for error in errors:
            print(f"   - {error}")
        return None
    
    # Extraer metadatos
    metadata = parse_issue_metadata(content)
    
    if not metadata["title"]:
        print(f"❌ {filepath.name}: No se encontró título")
        return None
    
    # Limpiar contenido (remover frontmatter si existe)
    body = content
    if content.startswith('---'):
        # Remover frontmatter YAML
        parts = content.split('---', 2)
        if len(parts) >= 3:
            body = parts[2].strip()
    
    # Construir comando gh
    cmd = [
        "gh", "issue", "create",
        "--title", metadata["title"],
        "--body", body
    ]
    
    # Añadir labels
    for label in metadata["labels"]:
        cmd.extend(["--label", label])
    
    # Añadir milestone (si existe y es válido)
    if metadata["milestone"]:
        cmd.extend(["--milestone", metadata["milestone"]])
    
    if dry_run:
        print(f"\n🔍 [DRY RUN] {filepath.name}")
        print(f"   Título: {metadata['title']}")
        print(f"   Labels: {', '.join(metadata['labels']) or '(ninguno)'}")
        print(f"   Milestone: {metadata['milestone'] or '(ninguno)'}")
        print(f"   Comando: {' '.join(cmd[:6])}...")
        return "DRY_RUN"
    
    # Ejecutar comando
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Extraer URL de la issue creada
        url_match = re.search(r"https://github\.com/[^\s]+", result.stdout)
        if url_match:
            issue_url = url_match.group(0)
            print(f"✅ Issue creada: {issue_url}")
            
            # Mover draft a carpeta 'created'
            created_dir = filepath.parent / "created"
            created_dir.mkdir(exist_ok=True)
            new_path = created_dir / filepath.name
            filepath.rename(new_path)
            print(f"   Draft movido a: {new_path}")
            
            return issue_url
        else:
            print(f"⚠️  Issue creada pero no se pudo extraer URL")
            print(f"   Output: {result.stdout}")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creando issue desde {filepath.name}:")
        print(f"   {e.stderr}")
        return None


def check_gh_cli() -> bool:
    """Verifica que gh CLI está instalado y autenticado."""
    # Verificar instalación
    try:
        subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Error: gh CLI no está instalado o no está en el PATH")
        print("   Instalar desde: https://cli.github.com/")
        return False
    
    # Verificar autenticación
    try:
        subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            check=True
        )
    except subprocess.CalledProcessError:
        print("❌ Error: gh CLI no está autenticado")
        print("   Ejecutar: gh auth login")
        return False
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Crea GitHub issues desde drafts validados",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Crear una issue específica
  python scripts/create_issues_from_drafts.py docs/issues/mi-issue.md
  
  # Crear todas las issues de un directorio
  python scripts/create_issues_from_drafts.py docs/issues/ --batch
  
  # Preview sin crear
  python scripts/create_issues_from_drafts.py docs/issues/ --batch --dry-run
        """
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Archivo .md o directorio con drafts"
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Crear todas las issues del directorio"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview sin crear issues (muestra qué haría)"
    )
    
    args = parser.parse_args()
    
    # Verificar gh CLI (excepto en dry-run)
    if not args.dry_run and not check_gh_cli():
        sys.exit(1)
    
    # Verificar que la ruta existe
    if not args.path.exists():
        print(f"❌ Error: {args.path} no existe")
        sys.exit(1)
    
    # Procesar drafts
    if args.path.is_file():
        # Crear issue individual
        result = create_github_issue(args.path, dry_run=args.dry_run)
        sys.exit(0 if result else 1)
    
    elif args.path.is_dir():
        if not args.batch:
            print("❌ Error: Para procesar directorio, usa --batch")
            print("   Ejemplo: python scripts/create_issues_from_drafts.py docs/issues/ --batch")
            sys.exit(1)
        
        # Buscar todos los drafts (excluir README.md y carpeta created)
        drafts = [
            f for f in args.path.glob("*.md")
            if not f.name.upper().startswith("README")
            and not f.name.startswith("_")
            and f.parent.name != "created"
        ]
        
        if not drafts:
            print(f"⚠️  No se encontraron drafts de issues en {args.path}")
            print(f"   Crea un draft: cp docs/issues/ejemplo-issue-draft.md docs/issues/mi-issue.md")
            sys.exit(0)
        
        print(f"📋 Encontrados {len(drafts)} drafts")
        
        created = []
        failed = []
        
        for draft in sorted(drafts):
            print(f"\n{'─' * 50}")
            print(f"▶️  Procesando: {draft.name}")
            result = create_github_issue(draft, dry_run=args.dry_run)
            
            if result:
                created.append(draft.name)
            else:
                failed.append(draft.name)
        
        # Resumen
        print("\n" + "=" * 60)
        print("📊 RESUMEN")
        print("=" * 60)
        
        if args.dry_run:
            print(f"🔍 [DRY RUN] - No se crearon issues reales")
            print(f"   Issues que se crearían: {len(created)}")
        else:
            print(f"✅ Issues creadas: {len(created)}")
        
        print(f"❌ Fallidas: {len(failed)}")
        
        if failed:
            print("\n⚠️  Drafts que fallaron:")
            for name in failed:
                print(f"   - {name}")
        
        sys.exit(0 if not failed else 1)
    
    else:
        print(f"❌ Error: {args.path} no es un archivo ni directorio válido")
        sys.exit(1)


if __name__ == "__main__":
    main()


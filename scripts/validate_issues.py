#!/usr/bin/env python3
"""
Valida que las issues cumplan con las mejores prácticas del proyecto.

Uso:
    python scripts/validate_issues.py docs/NEW_ISSUE_DRAFT.md
    
    # Validar todas las issues en un directorio
    python scripts/validate_issues.py docs/issues/
"""

import re
import sys
from pathlib import Path
from typing import List


REQUIRED_SECTIONS = [
    (r"##.*Objetivo|##.*Descripción", "Objetivo o Descripción"),
    (r"##.*Criterios de Aceptación|##.*Definition of Done", "Criterios de Aceptación"),
    (r"⏱️.*Tiempo|Estimación|estimated", "Estimación de Tiempo"),
]

RECOMMENDED_SECTIONS = [
    (r"##.*Archivos Afectados|Archivos afectados", "Archivos Afectados"),
    (r"##.*Pasos para|##.*Pasos de", "Pasos de Implementación"),
    (r"##.*Riesgos|##.*Bloqueos", "Riesgos/Bloqueos"),
    (r"##.*Impacto|##.*KPI", "Impacto/KPI"),
]


def validate_issue(content: str, filepath: Path) -> List[str]:
    """
    Valida que una issue cumpla con las mejores prácticas.
    
    Args:
        content: Contenido de la issue en markdown
        filepath: Ruta del archivo para contexto en errores
    
    Returns:
        Lista de errores encontrados (vacía si todo está bien)
    """
    errors = []
    warnings = []
    
    # Validar secciones requeridas
    for pattern, section_name in REQUIRED_SECTIONS:
        if not re.search(pattern, content, re.IGNORECASE):
            errors.append(f"❌ Falta sección requerida: {section_name}")
    
    # Validar secciones recomendadas
    for pattern, section_name in RECOMMENDED_SECTIONS:
        if not re.search(pattern, content, re.IGNORECASE):
            warnings.append(f"⚠️  Sección recomendada faltante: {section_name}")
    
    # Validar que tenga al menos un criterio de aceptación con checkbox
    if not re.search(r"- \[ \]", content):
        errors.append("❌ No hay criterios de aceptación con checkboxes (- [ ])")
    
    # Validar que tenga estimación numérica
    if not re.search(r"\d+\s*(horas?|días?|minutos?)", content, re.IGNORECASE):
        errors.append("❌ Falta estimación de tiempo numérica (ej: '2 horas', '30 minutos')")
    
    # Validar que tenga título con formato [TIPO] (solo para archivos que parecen issues)
    # Ignorar README.md y otros archivos de documentación
    if filepath.name.endswith('.md') and not filepath.name.upper().startswith('README'):
        first_line = content.split('\n')[0] if content else ""
        # Solo validar si parece una issue (tiene secciones típicas de issues)
        if re.search(r"##.*Objetivo|##.*Descripción|##.*Criterios", content, re.IGNORECASE):
            if not re.search(r"\[(BUG|FEATURE|QUALITY|DATA|TEST|DOCS|REFACTOR|SUB-ISSUE)\]", first_line, re.IGNORECASE):
                warnings.append("⚠️  Título no sigue formato [TIPO] (recomendado pero no requerido)")
    
    # Validar que tenga enlaces a issues relacionadas si menciona números
    if re.search(r"#\d+", content) and not re.search(r"##.*Issues Relacionadas|##.*Relacionadas", content, re.IGNORECASE):
        warnings.append("⚠️  Menciona números de issues pero no tiene sección 'Issues Relacionadas'")
    
    return errors, warnings


def validate_file(filepath: Path) -> tuple[bool, List[str], List[str]]:
    """Valida un archivo de issue."""
    try:
        content = filepath.read_text(encoding='utf-8')
        errors, warnings = validate_issue(content, filepath)
        return len(errors) == 0, errors, warnings
    except Exception as e:
        return False, [f"❌ Error leyendo archivo: {e}"], []


def main():
    """Función principal."""
    if len(sys.argv) < 2:
        print("Uso: python validate_issues.py <archivo.md> o <directorio/>")
        print("\nEjemplos:")
        print("  python scripts/validate_issues.py docs/NEW_ISSUE_DRAFT.md")
        print("  python scripts/validate_issues.py docs/issues/")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    
    if not input_path.exists():
        print(f"❌ Error: {input_path} no existe")
        print(f"\n💡 Sugerencias:")
        print(f"   - Verifica que la ruta sea correcta")
        print(f"   - Si es un directorio, créalo primero: mkdir -p {input_path}")
        print(f"   - O valida un archivo específico: python scripts/validate_issues.py <archivo.md>")
        sys.exit(1)
    
    # Obtener lista de archivos a validar
    if input_path.is_file():
        files_to_validate = [input_path]
    elif input_path.is_dir():
        # Excluir README.md y otros archivos de documentación
        all_md_files = list(input_path.glob("*.md"))
        files_to_validate = [
            f for f in all_md_files 
            if not f.name.upper().startswith('README') 
            and not f.name.startswith('_')
        ]
        if not files_to_validate:
            print(f"⚠️  No se encontraron archivos .md de issues en {input_path}")
            print(f"\n💡 El directorio existe pero está vacío o solo contiene README.md")
            print(f"   Crea un borrador de issue: cp .github/ISSUE_TEMPLATE.md {input_path}/nueva-issue.md")
            sys.exit(0)
    else:
        print(f"❌ Error: {input_path} no es un archivo ni directorio")
        sys.exit(1)
    
    
    # Validar cada archivo
    all_valid = True
    total_errors = 0
    total_warnings = 0
    
    for filepath in files_to_validate:
        is_valid, errors, warnings = validate_file(filepath)
        
        if not is_valid or warnings:
            all_valid = False
            total_errors += len(errors)
            total_warnings += len(warnings)
            
            print(f"\n📄 {filepath.name}")
            print("=" * 60)
            
            if errors:
                print("\n❌ Errores (deben corregirse):")
                for error in errors:
                    print(f"  {error}")
            
            if warnings:
                print("\n⚠️  Advertencias (recomendadas):")
                for warning in warnings:
                    print(f"  {warning}")
        else:
            print(f"✅ {filepath.name} - Cumple mejores prácticas")
    
    # Resumen
    print("\n" + "=" * 60)
    print(f"📊 Resumen:")
    print(f"  Archivos validados: {len(files_to_validate)}")
    print(f"  Errores encontrados: {total_errors}")
    print(f"  Advertencias: {total_warnings}")
    
    # Solo fallar si hay errores reales, no advertencias
    if total_errors == 0:
        if total_warnings == 0:
            print("\n✅ Todas las issues cumplen las mejores prácticas!")
        else:
            print("\n✅ Issues válidas (cumplen requisitos mínimos)")
            print("⚠️  Hay advertencias que sería bueno corregir")
        sys.exit(0)
    else:
        print("\n❌ Algunas issues tienen errores que deben corregirse")
        print("\n💡 Ver: docs/BEST_PRACTICES_GITHUB_ISSUES.md")
        sys.exit(1)


if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
Script de investigación para localizar y explorar el dataset de Incasòl
en Dades Obertes Catalunya (Socrata).

Uso:
    python scripts/research_incasol.py
"""

import json
import sys
from pathlib import Path

import requests


# Lista de IDs candidatos conocida por documentación previa / exploración manual.
# Se puede extender si en el futuro se detectan otros datasets relevantes.
CANDIDATE_IDS = [
    # Mercat de lloguer d'habitatge per barris (esperado)
    "qew5-756p",
]


def _inspect_dataset(dataset_id: str) -> None:
    """Descarga una pequeña muestra de un dataset Socrata y muestra sus columnas."""
    print(f"\n🔬 Inspeccionando dataset: {dataset_id}\n")
    data_url = f"https://analisi.transparenciacatalunya.cat/resource/{dataset_id}.json"

    query_params = {
        "$limit": 5,
    }

    data_resp = requests.get(data_url, params=query_params, timeout=30)
    data_resp.raise_for_status()
    data = data_resp.json()

    if not data:
        print("⚠️ El dataset respondió pero no devolvió filas con la consulta básica.")
        return

    print("✅ Datos de muestra obtenidos (primer registro):\n")
    print(json.dumps(data[0], indent=2, ensure_ascii=False))

    keys = list(data[0].keys())
    print("\n📋 Columnas disponibles:")
    print(keys)

    print(
        "\n💡 Revisa si existen campos como:\n"
        "   - any / year (año)\n"
        "   - trimestre / quarter\n"
        "   - codi_barri / nom_barri\n"
        "   - lloguer_mitja_mensual / lloguer_mitja_per_superficie\n"
        "   - nombre_contractes\n",
    )


def research_incasol() -> None:
    """Busca datasets candidatos y muestra estructura básica del mejor candidato."""
    print("🔍 Iniciando búsqueda en API Socrata (Generalitat)...\n")

    discovery_url = "https://api.us.socrata.com/api/catalog/v1"
    params = {
        "domains": "analisi.transparenciacatalunya.cat",
        "search_context": "analisi.transparenciacatalunya.cat",
        "q": "lloguer habitatge barris barcelona",
        "limit": 5,
    }

    try:
        resp = requests.get(discovery_url, params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        results = payload.get("results", [])

        if not results:
            print("❌ No se encontraron datasets via catálogo. Probando IDs conocidos...\n")
            for ds_id in CANDIDATE_IDS:
                try:
                    _inspect_dataset(ds_id)
                    print(f"\n👉 Dataset ID candidato a usar en el extractor: {ds_id}")
                    return
                except Exception as inner_exc:  # pragma: no cover - defensivo
                    print(f"⚠️ Error inspeccionando {ds_id}: {inner_exc}")
            return

        print(f"✅ Encontrados {len(results)} candidatos:\n")
        target_id = None

        for item in results:
            res = item.get("resource", {})
            rid = res.get("id")
            name = res.get("name")
            updated = res.get("updatedAt")
            permalink = res.get("permalink")

            print(f"🆔 ID: {rid}")
            print(f"📛 Nombre: {name}")
            print(f"📅 Actualizado: {updated}")
            print(f"🔗 Link: {permalink}")
            print("-" * 40)

            # Seleccionar el primer candidato como target por defecto
            if target_id is None:
                target_id = rid

        if not target_id:
            print("\n⚠️ No se pudo determinar un dataset objetivo desde el catálogo.")
            return

        _inspect_dataset(target_id)
        print(f"\n👉 Dataset ID candidato a usar en el extractor: {target_id}")

    except requests.RequestException as exc:
        print(f"❌ Error de conexión con Socrata: {exc}")
        print("\n👉 Intentando inspeccionar IDs conocidos directamente...\n")
        for ds_id in CANDIDATE_IDS:
            try:
                _inspect_dataset(ds_id)
                print(f"\n👉 Dataset ID candidato a usar en el extractor: {ds_id}")
                return
            except Exception as inner_exc:  # pragma: no cover - defensivo
                print(f"⚠️ Error inspeccionando {ds_id}: {inner_exc}")
    except Exception as exc:  # pragma: no cover - defensivo
        print(f"❌ Error inesperado: {exc}")


if __name__ == "__main__":
    # Asegurar que el script se ejecuta desde la raíz del proyecto si es necesario
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    research_incasol()



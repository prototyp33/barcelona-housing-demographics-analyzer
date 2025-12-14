#!/usr/bin/env python3
"""
Script de búsqueda refinada para localizar datasets de alquiler por BARRIOS
en Dades Obertes Catalunya (Socrata).

Uso:
    python3 scripts/find_neighborhood_data.py
"""

import json

import requests


def find_neighborhood_dataset() -> None:
    """Busca datasets relacionados con alquiler y barrios/distritos."""
    print("🕵️‍♂️ Buscando dataset de ALQUILER por BARRIOS en Dades Obertes Catalunya...\n")

    catalog_url = "https://api.us.socrata.com/api/catalog/v1"

    params = {
        "domains": "analisi.transparenciacatalunya.cat",
        "q": "lloguer habitatge",
        "limit": 50,
    }

    try:
        response = requests.get(catalog_url, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results", [])

        print(f"🔄 Analizando {len(results)} datasets encontrados...\n")

        candidates = []

        for item in results:
            res = item.get("resource", {})
            name = (res.get("name") or "").lower()
            desc = (res.get("description") or "").lower()

            # FILTRO CLAVE: debe mencionar "barri" o "districte" en título o descripción
            if "barri" in name or "districte" in name or "barri" in desc or "districte" in desc:
                candidates.append(
                    {
                        "id": res.get("id"),
                        "name": res.get("name"),
                        "updated": res.get("updatedAt"),
                        "link": res.get("permalink"),
                    }
                )

        if candidates:
            print(f"✅ ¡ÉXITO! Encontrados {len(candidates)} datasets de BARRIOS/DISTRICTES:\n")
            for c in candidates:
                print(f"🆔 ID: {c['id']}")
                print(f"📛 Nombre: {c['name']}")
                print(f"📅 Actualizado: {c['updated']}")
                print(f"🔗 Link: {c['link']}")
                print("-" * 40)

            print(
                "\n💡 COPIA el ID que diga explícitamente 'Barcelona' o 'Barris' y úsalo en tu extractor.\n"
            )
        else:
            print("\n⚠️ No se encontró nada con 'barri' o 'districte' en el catálogo de la Generalitat.")
            print("💡 PISTA: Es muy probable que el dato granular por barrios lo publique Open Data BCN.")
            print(
                "   Revisa manualmente, por ejemplo:\n"
                "   - https://opendata-ajuntament.barcelona.cat/data/es/dataset/"
                "est-mercat-immobiliari-lloguer-mitja-mensual\n"
            )

    except requests.RequestException as exc:
        print(f"❌ Error al consultar el catálogo de Socrata: {exc}")
        print(
            "\n👉 Si el catálogo falla de forma persistente, ve directamente al portal web:\n"
            "   https://analisi.transparenciacatalunya.cat/\n"
            "y busca manualmente 'lloguer', 'barris', 'Barcelona' para identificar el ID.\n"
        )
    except Exception as exc:  # pragma: no cover - defensivo
        print(f"❌ Error inesperado: {exc}")


if __name__ == "__main__":
    find_neighborhood_dataset()



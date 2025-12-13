"""
Script de diagnóstico para validar URLs de renta BCN.

Intenta descargar sólo el inicio del CSV (1 KB) para un año concreto usando
BcnIncomeExtractor. Si recibe 404, imprime la URL probada.
"""

import argparse
import sys

import requests

from src.extraction.bcn_income import BcnIncomeExtractor


def check_year(year: int) -> None:
    extractor = BcnIncomeExtractor(rate_limit_delay=0)
    urls = extractor._build_candidate_urls(year)  # noqa: SLF001 uso diagnóstico

    for url in urls:
        try:
            resp = extractor.session.get(url, timeout=15, stream=True)
            status = resp.status_code
            if status == 404:
                print(f"❌ 404 para {url}")
                continue

            resp.raise_for_status()

            # Leer solo los primeros bytes para no descargar todo
            chunk = next(resp.iter_content(chunk_size=1024), b"")
            print(f"✅ {url} (status {status}) - preview: {chunk[:120]!r}")
            return
        except requests.HTTPError as exc:
            print(f"❌ HTTP error {url}: {exc}")
        except Exception as exc:  # noqa: BLE001
            print(f"❌ Error general {url}: {exc}")

    print("No se encontró una URL válida.")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Verifica URLs de renta BCN por año")
    parser.add_argument("--year", type=int, default=2021, help="Año a probar (default 2021)")
    args = parser.parse_args(argv)

    check_year(args.year)
    return 0


if __name__ == "__main__":
    sys.exit(main())


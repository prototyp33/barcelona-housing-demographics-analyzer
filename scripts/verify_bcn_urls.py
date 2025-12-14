"""
Verifica las URLs reales de renta BCN para años recientes.

Para cada año indicado, usa BcnIncomeExtractor para obtener la URL candidata
(YEAR_URLS) y realiza una petición HEAD (o GET parcial) para validar status.
"""

import sys

import requests

from src.extraction.bcn_income import BcnIncomeExtractor


def check_year(year: int) -> None:
    extractor = BcnIncomeExtractor(rate_limit_delay=0)
    urls = extractor._build_candidate_urls(year)  # noqa: SLF001 uso interno para diagnóstico

    for url in urls:
        try:
            resp = extractor.session.head(url, timeout=15)
            status = resp.status_code
            print(f"Año {year}: URL {url} -> Status {status}")
            return
        except requests.RequestException as exc:
            print(f"Año {year}: URL {url} -> Error {exc}")
            continue

    print(f"Año {year}: sin URL válida")


def main() -> int:
    for year in range(2015, 2026):
        check_year(year)
    return 0


if __name__ == "__main__":
    sys.exit(main())


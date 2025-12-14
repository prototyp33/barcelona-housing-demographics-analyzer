import json

from pyjstat import pyjstat

from src.extraction.idescat_income import IdescatIncomeExtractor


def main() -> None:
    extractor = IdescatIncomeExtractor()

    params = {
        "id": extractor.INDICATOR_ID,
        "lang": "es",
        "time": "2022:2022",
    }
    response = extractor.session.get(extractor.API_URL, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    print("\n=== Claves de respuesta cruda ===")
    print(list(payload.keys()))
    print("\n=== Vista parcial de payload['indicadors'] ===")
    print(json.dumps(payload.get("indicadors", {}), ensure_ascii=False)[:800])

    df_crudo = None
    try:
        dataset = pyjstat.Dataset.read(json.dumps(payload))
        df_crudo = dataset.write("dataframe")
        print("\n=== Columnas DataFrame crudo (pyjstat) ===")
        print(df_crudo.columns.tolist())
    except Exception as exc:  # noqa: BLE001 - diagnóstico
        print("\n❌ pyjstat no pudo parsear la respuesta")
        print(f"Detalle: {exc}")
        print("Payload indicadors (parcial):")
        print(json.dumps(payload.get("indicadors", {}), ensure_ascii=False, indent=2)[:1200])

    df_final = None
    try:
        df_final = extractor.extract_income_by_barrio(start_year=2022, end_year=2022)
    except Exception as exc:  # noqa: BLE001 - diagnóstico
        print("\n❌ Error en extracción final:")
        print(exc)

    if df_crudo is not None:
        print("\n=== Columnas DataFrame crudo (pyjstat) ===")
        print(df_crudo.columns.tolist())

    if df_final is not None:
        print("\n=== Primeras 5 filas DataFrame final mapeado ===")
        print(df_final.head())


if __name__ == "__main__":
    main()

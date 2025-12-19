#!/usr/bin/env python3
"""
Test sistemático de variantes SOAP para Consulta_DNPRC.

Prueba hipótesis H2-H5:
- H2: Referencia dividida en PC1 (14) + PC2 (6)
- H3: Orden de elementos
- H4: Parámetro SRS
- H5: Referencia de 21 chars vs 20 chars
"""

import sys
from pathlib import Path
import requests
import xml.etree.ElementTree as ET
import json
import time

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Referencia de prueba del seed (21 caracteres)
REF_TEST = "8021115DF7789A14854CD"  # 21 chars
REF_20 = REF_TEST[:20]  # 20 chars
REF_PC1 = REF_20[:14]  # 14 chars (PC1)
REF_PC2 = REF_20[14:]  # 6 chars (PC2)

ENDPOINT = "http://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx"
SOAP_ACTION = "http://tempuri.org/OVCServWeb/OVCCallejero/Consulta_DNPRC"
LOG_PATH = Path("/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log")


def log_debug(hypothesis_id: str, location: str, message: str, data: dict):
    """Escribe log de debug."""
    log_entry = {
        "sessionId": "debug-session",
        "runId": "run1",
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000)
    }
    with open(LOG_PATH, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')


def test_soap_request(soap_body: str, test_name: str, hypothesis_id: str) -> tuple[bool, str]:
    """
    Prueba una variante de SOAP request.
    
    Returns:
        (success, error_message)
    """
    log_debug(hypothesis_id, "test_soap_variants.py:test_soap_request", f"Iniciando test: {test_name}", {
        "test_name": test_name,
        "soap_body_preview": soap_body[:300]
    })
    
    try:
        response = requests.post(
            ENDPOINT,
            headers={
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': SOAP_ACTION
            },
            data=soap_body.encode('utf-8'),
            timeout=30
        )
        
        log_debug(hypothesis_id, "test_soap_variants.py:test_soap_request", "Respuesta recibida", {
            "status_code": response.status_code,
            "response_preview": response.text[:500]
        })
        
        if 'bico' in response.text:
            log_debug(hypothesis_id, "test_soap_variants.py:test_soap_request", "✓ ÉXITO - Datos encontrados", {})
            return True, "ÉXITO - Datos encontrados"
        
        # Parsear error
        root = ET.fromstring(response.text)
        cod_elem = root.find('.//{http://www.catastro.meh.es/}cod')
        des_elem = root.find('.//{http://www.catastro.meh.es/}des')
        cod = cod_elem.text if cod_elem is not None else '?'
        des = des_elem.text if des_elem is not None else '?'
        
        error_msg = f"Error {cod}: {des}"
        log_debug(hypothesis_id, "test_soap_variants.py:test_soap_request", "Error del servidor", {
            "cod": cod,
            "des": des
        })
        
        return False, error_msg
        
    except Exception as e:
        log_debug(hypothesis_id, "test_soap_variants.py:test_soap_request", "Excepción", {
            "error": str(e)
        })
        return False, f"Excepción: {e}"


def test_h2_pc1_pc2():
    """H2: Probar con referencia dividida en PC1 (14) + PC2 (6)."""
    print("\n" + "="*70)
    print("H2: REFERENCIA DIVIDIDA EN PC1 (14) + PC2 (6)")
    print("="*70)
    
    # Variante A: RC con subelementos PC1 y PC2
    soap_body_a = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body xmlns="http://www.catastro.meh.es/">
    <Provincia>08</Provincia>
    <Municipio>019</Municipio>
    <RC>
      <PC1>{REF_PC1}</PC1>
      <PC2>{REF_PC2}</PC2>
    </RC>
  </soap:Body>
</soap:Envelope>"""
    
    success_a, msg_a = test_soap_request(soap_body_a, "H2-A: RC con PC1/PC2", "H2")
    print(f"{'✓' if success_a else '✗'} H2-A: RC con PC1/PC2 | {msg_a}")
    
    # Variante B: Elementos PC1 y PC2 separados
    soap_body_b = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body xmlns="http://www.catastro.meh.es/">
    <Provincia>08</Provincia>
    <Municipio>019</Municipio>
    <PC1>{REF_PC1}</PC1>
    <PC2>{REF_PC2}</PC2>
  </soap:Body>
</soap:Envelope>"""
    
    success_b, msg_b = test_soap_request(soap_body_b, "H2-B: PC1 y PC2 separados", "H2")
    print(f"{'✓' if success_b else '✗'} H2-B: PC1 y PC2 separados | {msg_b}")
    
    return success_a or success_b


def test_h3_element_order():
    """H3: Probar diferentes órdenes de elementos."""
    print("\n" + "="*70)
    print("H3: ORDEN DE ELEMENTOS")
    print("="*70)
    
    # Orden actual: Provincia, Municipio, RefCat
    soap_body_current = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body xmlns="http://www.catastro.meh.es/">
    <Provincia>08</Provincia>
    <Municipio>019</Municipio>
    <RefCat>{REF_20}</RefCat>
  </soap:Body>
</soap:Envelope>"""
    
    success_current, msg_current = test_soap_request(soap_body_current, "H3-A: Orden actual (Prov, Mun, RefCat)", "H3")
    print(f"{'✓' if success_current else '✗'} H3-A: Orden actual | {msg_current}")
    
    # Orden alternativo: RefCat, Provincia, Municipio
    soap_body_alt = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body xmlns="http://www.catastro.meh.es/">
    <RefCat>{REF_20}</RefCat>
    <Provincia>08</Provincia>
    <Municipio>019</Municipio>
  </soap:Body>
</soap:Envelope>"""
    
    success_alt, msg_alt = test_soap_request(soap_body_alt, "H3-B: Orden alternativo (RefCat, Prov, Mun)", "H3")
    print(f"{'✓' if success_alt else '✗'} H3-B: Orden alternativo | {msg_alt}")
    
    return success_current or success_alt


def test_h4_srs():
    """H4: Probar añadiendo parámetro SRS."""
    print("\n" + "="*70)
    print("H4: PARÁMETRO SRS")
    print("="*70)
    
    # Con SRS EPSG:4326
    soap_body_4326 = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body xmlns="http://www.catastro.meh.es/">
    <Provincia>08</Provincia>
    <Municipio>019</Municipio>
    <RefCat>{REF_20}</RefCat>
    <SRS>EPSG:4326</SRS>
  </soap:Body>
</soap:Envelope>"""
    
    success_4326, msg_4326 = test_soap_request(soap_body_4326, "H4-A: Con SRS EPSG:4326", "H4")
    print(f"{'✓' if success_4326 else '✗'} H4-A: Con SRS EPSG:4326 | {msg_4326}")
    
    # Con SRS EPSG:25831 (ETRS89 UTM 31N - Cataluña)
    soap_body_25831 = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body xmlns="http://www.catastro.meh.es/">
    <Provincia>08</Provincia>
    <Municipio>019</Municipio>
    <RefCat>{REF_20}</RefCat>
    <SRS>EPSG:25831</SRS>
  </soap:Body>
</soap:Envelope>"""
    
    success_25831, msg_25831 = test_soap_request(soap_body_25831, "H4-B: Con SRS EPSG:25831", "H4")
    print(f"{'✓' if success_25831 else '✗'} H4-B: Con SRS EPSG:25831 | {msg_25831}")
    
    return success_4326 or success_25831


def test_h5_ref_length():
    """H5: Probar con referencia de 21 chars vs 20 chars."""
    print("\n" + "="*70)
    print("H5: LONGITUD DE REFERENCIA (21 vs 20 chars)")
    print("="*70)
    
    log_debug("H5", "test_soap_variants.py:test_h5_ref_length", "Iniciando test H5", {
        "ref_21": REF_TEST,
        "ref_20": REF_20,
        "len_21": len(REF_TEST),
        "len_20": len(REF_20)
    })
    
    # Con referencia de 21 caracteres (original)
    soap_body_21 = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body xmlns="http://www.catastro.meh.es/">
    <Provincia>08</Provincia>
    <Municipio>019</Municipio>
    <RefCat>{REF_TEST}</RefCat>
  </soap:Body>
</soap:Envelope>"""
    
    success_21, msg_21 = test_soap_request(soap_body_21, "H5-A: Referencia de 21 chars", "H5")
    print(f"{'✓' if success_21 else '✗'} H5-A: Referencia de 21 chars ({REF_TEST}) | {msg_21}")
    
    # Con referencia de 20 caracteres (truncada)
    soap_body_20 = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body xmlns="http://www.catastro.meh.es/">
    <Provincia>08</Provincia>
    <Municipio>019</Municipio>
    <RefCat>{REF_20}</RefCat>
  </soap:Body>
</soap:Envelope>"""
    
    success_20, msg_20 = test_soap_request(soap_body_20, "H5-B: Referencia de 20 chars", "H5")
    print(f"{'✓' if success_20 else '✗'} H5-B: Referencia de 20 chars ({REF_20}) | {msg_20}")
    
    return success_21 or success_20


def main():
    """Ejecuta todos los tests sistemáticos."""
    print("="*70)
    print("TEST SISTEMÁTICO DE VARIANTES SOAP - CONSULTA_DNPRC")
    print("="*70)
    print(f"\nReferencia de prueba:")
    print(f"  Original (21 chars): {REF_TEST}")
    print(f"  Truncada (20 chars): {REF_20}")
    print(f"  PC1 (14 chars): {REF_PC1}")
    print(f"  PC2 (6 chars): {REF_PC2}")
    
    # Limpiar log anterior
    if LOG_PATH.exists():
        LOG_PATH.unlink()
    
    results = {
        "H2": test_h2_pc1_pc2(),
        "H3": test_h3_element_order(),
        "H4": test_h4_srs(),
        "H5": test_h5_ref_length(),
    }
    
    print("\n" + "="*70)
    print("RESUMEN DE RESULTADOS")
    print("="*70)
    for hyp, success in results.items():
        status = "✓ CONFIRMADA" if success else "✗ RECHAZADA"
        print(f"{hyp}: {status}")
    
    if any(results.values()):
        print("\n✅ AL MENOS UNA HIPÓTESIS FUNCIONÓ")
        print("Revisar logs en:", LOG_PATH)
    else:
        print("\n❌ TODAS LAS HIPÓTESIS RECHAZADAS")
        print("Revisar logs en:", LOG_PATH)
        print("Considerar: Las referencias del seed pueden ser inválidas")
        print("Solución: Usar búsqueda inversa por dirección (ENFOQUE 1)")


if __name__ == '__main__':
    main()


"""
Cliente para la API SOAP oficial del Catastro (Sede Electrónica).

Este cliente usa el servicio oficial gratuito del Ministerio de Hacienda para
obtener datos no protegidos de inmuebles (superficie, año construcción, uso).

URL Endpoint: http://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCoordenadas.asmx
Operación: Consulta_DNPRC (Datos No Protegidos por Referencia Catastral)

Issue: #200
Author: Equipo A - Data Infrastructure
Enfoque: 100% gratuito, oficial, sin dependencias externas
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class CatastroSOAPConfig:
    """
    Configuración para el cliente SOAP oficial del Catastro.

    Attributes:
        base_url: URL base del servicio SOAP.
        timeout: Timeout en segundos para peticiones HTTP.
    """

    base_url: str = "http://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx"
    timeout: int = 30


class CatastroSOAPError(Exception):
    """Error de alto nivel para problemas con la API SOAP del Catastro."""


class CatastroSOAPClient:
    """
    Cliente para la API SOAP oficial del Catastro.

    Este cliente consulta el servicio oficial gratuito del Ministerio de Hacienda
    para obtener datos no protegidos de inmuebles sin necesidad de API key ni registro.
    """

    def __init__(self, config: Optional[CatastroSOAPConfig] = None) -> None:
        """
        Inicializa el cliente SOAP del Catastro.

        Args:
            config: Configuración; si es None, usa valores por defecto.
        """
        self.config = config or CatastroSOAPConfig()
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": "http://tempuri.org/OVCServWeb/OVCCallejero/Consulta_DNPRC",
        })

    def _build_soap_request(self, referencia_catastral: str) -> str:
        """
        Construye el cuerpo SOAP para consultar datos no protegidos.

        Args:
            referencia_catastral: Referencia catastral completa (20 caracteres).

        Returns:
            XML SOAP como string.
        """
        # Para Barcelona: Provincia 08, Municipio 019 (códigos INE)
        # Formato correcto según WSDL: elementos directos en el body con namespace catastro
        provincia = "08"  # Barcelona
        municipio = "019"  # Barcelona ciudad
        
        # #region agent log
        import json
        import time
        with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H2,H3,H4,H5","location":"catastro_soap_client.py:_build_soap_request","message":"Construyendo SOAP request","data":{"provincia":provincia,"municipio":municipio,"ref":referencia_catastral,"ref_len":len(referencia_catastral)},"timestamp":int(time.time()*1000)}) + '\n')
        # #endregion
        
        # Normalizar referencia: truncar a 20 caracteres si tiene 21
        ref_normalized = referencia_catastral[:20] if len(referencia_catastral) > 20 else referencia_catastral
        
        # #region agent log
        with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H5","location":"catastro_soap_client.py:_build_soap_request","message":"Referencia normalizada","data":{"ref_original":referencia_catastral,"ref_normalized":ref_normalized,"original_len":len(referencia_catastral),"normalized_len":len(ref_normalized)},"timestamp":int(time.time()*1000)}) + '\n')
        # #endregion
        
        # Formato según documentación oficial del Catastro
        # NOTA: zeep usa RC como parámetro Python, pero el elemento XML correcto es RefCat
        # Usar RefCat en el XML (error 12 = reconoce elemento) vs RC (error 17 = no reconoce)
        # Incluir namespaces xsi y xsd en soap:Envelope como en los ejemplos oficiales
        soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <Provincia xmlns="http://www.catastro.meh.es/">{provincia}</Provincia>
    <Municipio xmlns="http://www.catastro.meh.es/">{municipio}</Municipio>
    <RefCat xmlns="http://www.catastro.meh.es/">{ref_normalized}</RefCat>
  </soap:Body>
</soap:Envelope>"""
        
        # #region agent log
        with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H3","location":"catastro_soap_client.py:_build_soap_request","message":"SOAP body generado (orden: Provincia, Municipio, RefCat)","data":{"soap_body_preview":soap_body[:200]},"timestamp":int(time.time()*1000)}) + '\n')
        # #endregion
        
        return soap_body

    def _parse_soap_response(self, xml_content: str) -> Dict[str, Any]:
        """
        Parsea la respuesta SOAP XML del Catastro.

        Estructura esperada:
        <bico>
          <bi>
            <debi>
              <luso>V</luso> <!-- Uso: V=Vivienda -->
              <sfc>120</sfc> <!-- Superficie construida -->
              <ant>1975</ant> <!-- Año construcción -->
            </debi>
          </bi>
        </bico>

        Args:
            xml_content: Contenido XML de la respuesta SOAP.

        Returns:
            Diccionario con datos del inmueble.

        Raises:
            CatastroSOAPError: Si el XML no se puede parsear o falta información.
        """
        try:
            # Parsear XML
            root = ET.fromstring(xml_content)

            # Buscar namespace SOAP
            namespaces = {
                "soap": "http://schemas.xmlsoap.org/soap/envelope/",
                "temp": "http://tempuri.org/",
            }

            # Extraer cuerpo SOAP
            body = root.find(".//soap:Body", namespaces)
            if body is None:
                raise CatastroSOAPError("No se encontró el cuerpo SOAP en la respuesta")

            # Buscar Consulta_DNP (formato real de la respuesta)
            namespaces_catastro = {
                "soap": "http://schemas.xmlsoap.org/soap/envelope/",
                "cat": "http://www.catastro.meh.es/",
            }
            result = body.find(".//cat:Consulta_DNP", namespaces_catastro)
            if result is None:
                # Intentar sin namespace
                result = body.find(".//Consulta_DNP")
                if result is None:
                    # Intentar Consulta_DNPRCResult (formato alternativo)
                    result = body.find(".//Consulta_DNPRCResult")
                    if result is None:
                        raise CatastroSOAPError("No se encontró Consulta_DNP ni Consulta_DNPRCResult en la respuesta")

            # Verificar si hay errores en la respuesta
            # El formato real es: <Consulta_DNP xmlns="http://www.catastro.meh.es/"><consulta_dnp><control>...
            # Todos los elementos dentro tienen el namespace http://www.catastro.meh.es/
            consulta_dnp = result.find(".//{http://www.catastro.meh.es/}consulta_dnp")
            if consulta_dnp is not None:
                control = consulta_dnp.find(".//{http://www.catastro.meh.es/}control")
                if control is not None:
                    cuerr = control.find(".//{http://www.catastro.meh.es/}cuerr")
                    if cuerr is not None and cuerr.text and cuerr.text.strip() != "0":
                        # Hay errores, buscar mensaje de error
                        lerr = consulta_dnp.find(".//{http://www.catastro.meh.es/}lerr")
                        if lerr is not None:
                            err = lerr.find(".//{http://www.catastro.meh.es/}err")
                            if err is not None:
                                cod = err.find(".//{http://www.catastro.meh.es/}cod")
                                des = err.find(".//{http://www.catastro.meh.es/}des")
                                cod_text = cod.text if cod is not None and cod.text else "?"
                                des_text = des.text if des is not None and des.text else "Error desconocido"
                                raise CatastroSOAPError(f"Error del servidor Catastro (código {cod_text}): {des_text}")
            
            # También buscar control directamente en result (formato alternativo)
            control = result.find(".//{http://www.catastro.meh.es/}control")
            if control is not None:
                cuerr = control.find(".//{http://www.catastro.meh.es/}cuerr")
                if cuerr is not None and cuerr.text and cuerr.text.strip() != "0":
                    # Hay errores, buscar mensaje de error
                    lerr = result.find(".//{http://www.catastro.meh.es/}lerr")
                    if lerr is not None:
                        err = lerr.find(".//{http://www.catastro.meh.es/}err")
                        if err is not None:
                            cod = err.find(".//{http://www.catastro.meh.es/}cod")
                            des = err.find(".//{http://www.catastro.meh.es/}des")
                            cod_text = cod.text if cod is not None and cod.text else "?"
                            des_text = des.text if des is not None and des.text else "Error desconocido"
                            raise CatastroSOAPError(f"Error del servidor Catastro (código {cod_text}): {des_text}")
            
            # Parsear bico (Bien Inmueble Catastral)
            bico = result.find(".//bico")
            if bico is None:
                raise CatastroSOAPError("No se encontró información del inmueble (bico) en la respuesta")

            bi = bico.find(".//bi")
            if bi is None:
                raise CatastroSOAPError("No se encontró información del bien (bi)")

            debi = bi.find(".//debi")
            if debi is None:
                raise CatastroSOAPError("No se encontró información descriptiva (debi)")

            # Extraer campos
            luso_elem = debi.find(".//luso")
            sfc_elem = debi.find(".//sfc")
            ant_elem = debi.find(".//ant")

            # Extraer dirección (opcional)
            locat = bi.find(".//locat")
            direccion_parts = []
            if locat is not None:
                via_elem = locat.find(".//via")
                num_elem = locat.find(".//num")
                if via_elem is not None and via_elem.text:
                    direccion_parts.append(via_elem.text.strip())
                if num_elem is not None and num_elem.text:
                    direccion_parts.append(num_elem.text.strip())

            direccion_normalizada = " ".join(direccion_parts) if direccion_parts else None

            # Construir resultado
            resultado: Dict[str, Any] = {
                "referencia_catastral": None,  # Se añadirá desde el input
                "superficie_m2": float(sfc_elem.text) if sfc_elem is not None and sfc_elem.text else None,
                "ano_construccion": int(ant_elem.text) if ant_elem is not None and ant_elem.text else None,
                "uso_principal": luso_elem.text.strip() if luso_elem is not None and luso_elem.text else None,
                "direccion_normalizada": direccion_normalizada,
            }

            return resultado

        except ET.ParseError as exc:
            raise CatastroSOAPError(f"Error al parsear XML de respuesta: {exc}") from exc
        except (ValueError, AttributeError) as exc:
            raise CatastroSOAPError(f"Error al extraer datos del XML: {exc}") from exc

    def _normalize_referencia_catastral(self, ref_catastral: str) -> str:
        """
        Normaliza una referencia catastral al formato esperado por la API SOAP.

        La API SOAP espera exactamente 20 caracteres. Algunas fuentes (como Open Data BCN)
        pueden proporcionar referencias con 21 caracteres (formato extendido).

        Args:
            ref_catastral: Referencia catastral en cualquier formato.

        Returns:
            Referencia normalizada a 20 caracteres.
        """
        # #region agent log
        import json
        with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H1,H3,H4","location":"catastro_soap_client.py:_normalize_referencia_catastral","message":"Normalizando referencia","data":{"original":ref_catastral,"len_original":len(ref_catastral)},"timestamp":int(__import__('time').time()*1000)}) + '\n')
        # #endregion
        
        ref_clean = ref_catastral.strip().upper()
        
        # Si tiene 21 caracteres, intentar normalizar a 20
        if len(ref_clean) == 21:
            # Hipótesis: El último carácter puede ser un checksum o separador
            # Intentar truncar a 20 caracteres
            ref_normalized = ref_clean[:20]
            # #region agent log
            with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H3","location":"catastro_soap_client.py:_normalize_referencia_catastral","message":"Truncado de 21 a 20","data":{"original":ref_clean,"normalized":ref_normalized,"removed_char":ref_clean[20]},"timestamp":int(__import__('time').time()*1000)}) + '\n')
            # #endregion
            return ref_normalized
        elif len(ref_clean) == 20:
            return ref_clean
        else:
            # #region agent log
            with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H5","location":"catastro_soap_client.py:_normalize_referencia_catastral","message":"Formato inesperado","data":{"original":ref_clean,"len":len(ref_clean)},"timestamp":int(__import__('time').time()*1000)}) + '\n')
            # #endregion
            return ref_clean

    def get_building_by_rc(self, ref_catastral: str) -> Dict[str, Any]:
        """
        Obtiene información de un inmueble a partir de su referencia catastral.

        Args:
            ref_catastral: Referencia catastral (se normaliza automáticamente si tiene 21 caracteres).

        Returns:
            Diccionario con atributos relevantes del inmueble:
            - referencia_catastral: Referencia catastral
            - superficie_m2: Superficie construida en m²
            - ano_construccion: Año de construcción
            - uso_principal: Uso principal (V=Vivienda, etc.)
            - direccion_normalizada: Dirección del inmueble

        Raises:
            CatastroSOAPError: Si la API devuelve un error o el payload es inválido.
        """
        # #region agent log
        import json
        with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H1","location":"catastro_soap_client.py:get_building_by_rc","message":"Entrada función","data":{"ref_original":ref_catastral,"len_original":len(ref_catastral) if ref_catastral else 0},"timestamp":int(__import__('time').time()*1000)}) + '\n')
        # #endregion
        
        if not ref_catastral:
            raise CatastroSOAPError("La referencia catastral está vacía")

        # Normalizar referencia (21 -> 20 caracteres si es necesario)
        ref_normalized = self._normalize_referencia_catastral(ref_catastral)
        
        # #region agent log
        with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H1","location":"catastro_soap_client.py:get_building_by_rc","message":"Después normalización","data":{"ref_normalized":ref_normalized,"len_normalized":len(ref_normalized)},"timestamp":int(__import__('time').time()*1000)}) + '\n')
        # #endregion

        if len(ref_normalized) != 20:
            raise CatastroSOAPError(
                f"Referencia catastral inválida después de normalización: '{ref_normalized}' "
                f"(debe tener 20 caracteres, tiene {len(ref_normalized)})",
            )

        # Construir petición SOAP con referencia normalizada
        soap_body = self._build_soap_request(ref_normalized)
        
        # #region agent log
        import json
        with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H2","location":"catastro_soap_client.py:get_building_by_rc","message":"Antes petición SOAP","data":{"ref_usada":ref_normalized},"timestamp":int(__import__('time').time()*1000)}) + '\n')
        # #endregion

        try:
            # Realizar petición SOAP
            # #region agent log
            import json
            with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H6,H7","location":"catastro_soap_client.py:get_building_by_rc","message":"Enviando petición SOAP","data":{"url":self.config.base_url,"ref":ref_normalized,"soap_body_len":len(soap_body),"soap_body":soap_body},"timestamp":int(__import__('time').time()*1000)}) + '\n')
            # #endregion
            
            response = self.session.post(
                self.config.base_url,
                data=soap_body.encode("utf-8"),
                timeout=self.config.timeout,
            )
            
            # #region agent log
            import json
            with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H6,H7","location":"catastro_soap_client.py:get_building_by_rc","message":"Respuesta HTTP recibida","data":{"ref":ref_normalized,"status_code":response.status_code,"response_preview":response.text[:1000] if response.text else "empty","headers":dict(response.headers)},"timestamp":int(__import__('time').time()*1000)}) + '\n')
            # #endregion
            
            response.raise_for_status()
        except requests.RequestException as exc:
            # #region agent log
            import json
            response_text = None
            status_code = None
            if hasattr(exc, 'response') and exc.response is not None:
                response_text = exc.response.text[:1000] if exc.response.text else None
                status_code = exc.response.status_code
            with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H2,H6,H7","location":"catastro_soap_client.py:get_building_by_rc","message":"Error de red/HTTP","data":{"ref":ref_normalized,"error":str(exc),"status_code":status_code,"response_text":response_text},"timestamp":int(__import__('time').time()*1000)}) + '\n')
            # #endregion
            raise CatastroSOAPError(f"Error de red al consultar Catastro SOAP: {exc}") from exc

        # #region agent log
        import json
        with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H2","location":"catastro_soap_client.py:get_building_by_rc","message":"Respuesta HTTP recibida","data":{"ref":ref_normalized,"status_code":response.status_code,"response_len":len(response.text)},"timestamp":int(__import__('time').time()*1000)}) + '\n')
        # #endregion

        # Parsear respuesta
        try:
            resultado = self._parse_soap_response(response.text)
            resultado["referencia_catastral"] = ref_normalized
            # #region agent log
            import json
            with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H2","location":"catastro_soap_client.py:get_building_by_rc","message":"Respuesta exitosa","data":{"ref_original":ref_catastral,"ref_normalized":ref_normalized,"superficie":resultado.get("superficie_m2")},"timestamp":int(__import__('time').time()*1000)}) + '\n')
            # #endregion
            logger.debug("Respuesta Catastro SOAP para %s: %s", ref_normalized, resultado)
            return resultado
        except CatastroSOAPError as parse_exc:
            # #region agent log
            import json
            with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H2","location":"catastro_soap_client.py:get_building_by_rc","message":"Error parsing respuesta","data":{"ref":ref_normalized,"error":str(parse_exc),"response_preview":response.text[:500]},"timestamp":int(__import__('time').time()*1000)}) + '\n')
            # #endregion
            raise
        except Exception as exc:
            # #region agent log
            import json
            with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H2","location":"catastro_soap_client.py:get_building_by_rc","message":"Error inesperado parsing","data":{"ref":ref_normalized,"error":str(exc)},"timestamp":int(__import__('time').time()*1000)}) + '\n')
            # #endregion
            raise CatastroSOAPError(f"Error inesperado al procesar respuesta: {exc}") from exc

    def get_buildings_batch(
        self,
        referencias: list[str],
        continue_on_error: bool = True,
        delay_seconds: float = 1.0,
    ) -> list[dict[str, Any]]:
        """
        Obtiene información de múltiples inmuebles en lote.

        Args:
            referencias: Lista de referencias catastrales.
            continue_on_error: Si True, continúa aunque haya errores individuales.
            delay_seconds: Delay entre peticiones para evitar rate limiting.

        Returns:
            Lista de diccionarios con datos de inmuebles (solo los exitosos).
        """
        import time

        resultados: list[dict[str, Any]] = []
        total = len(referencias)

        logger.info(f"Iniciando extracción batch de {total} referencias...")

        for idx, ref in enumerate(referencias, start=1):
            # #region agent log
            import json
            with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H1","location":"catastro_soap_client.py:get_buildings_batch","message":"Procesando referencia en batch","data":{"idx":idx,"total":total,"ref":ref,"len":len(ref)},"timestamp":int(__import__('time').time()*1000)}) + '\n')
            # #endregion
            try:
                resultado = self.get_building_by_rc(ref)
                resultados.append(resultado)
                # #region agent log
                import json
                with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H2","location":"catastro_soap_client.py:get_buildings_batch","message":"Referencia exitosa","data":{"idx":idx,"ref":ref,"superficie":resultado.get("superficie_m2")},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                # #endregion
                logger.info(f"({idx}/{total}) ✓ {ref}: {resultado.get('superficie_m2')} m²")
            except CatastroSOAPError as exc:
                # #region agent log
                import json
                with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H2","location":"catastro_soap_client.py:get_buildings_batch","message":"Error en referencia","data":{"idx":idx,"ref":ref,"error":str(exc)},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                # #endregion
                if continue_on_error:
                    logger.warning(f"({idx}/{total}) ✗ {ref}: {exc}")
                    continue
                else:
                    raise
            except Exception as exc:
                # #region agent log
                import json
                with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H2","location":"catastro_soap_client.py:get_buildings_batch","message":"Error inesperado","data":{"idx":idx,"ref":ref,"error":str(exc),"error_type":type(exc).__name__},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                # #endregion
                if continue_on_error:
                    logger.warning(f"({idx}/{total}) ✗ {ref}: Error inesperado: {exc}")
                    continue
                else:
                    raise

            # Delay entre peticiones para evitar rate limiting
            if idx < total and delay_seconds > 0:
                time.sleep(delay_seconds)

        logger.info(f"Extracción batch completada: {len(resultados)}/{total} exitosos")
        return resultados

    def get_rc_by_address(
        self,
        provincia: str,
        municipio: str,
        tipo_via: str,
        nombre_via: str,
        numero: str,
        bloque: Optional[str] = None,
        escalera: Optional[str] = None,
        planta: Optional[str] = None,
        puerta: Optional[str] = None,
    ) -> Optional[str]:
        """
        Obtiene referencia catastral por dirección usando Consulta_DNPLOC.

        Args:
            provincia: Código provincia (ej: "08" para Barcelona)
            municipio: Código municipio (ej: "019" para Barcelona)
            tipo_via: Tipo de vía (CL=calle, AV=avenida, PZ=plaza, etc.)
            nombre_via: Nombre de la vía
            numero: Número de portal
            bloque: Bloque (opcional)
            escalera: Escalera (opcional)
            planta: Planta (opcional)
            puerta: Puerta (opcional)

        Returns:
            Referencia catastral si se encuentra, None en caso contrario

        Raises:
            CatastroSOAPError: Si hay error en la petición SOAP
        """
        # #region agent log
        import json
        with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H35","location":"catastro_soap_client.py:get_rc_by_address","message":"Buscando RC por dirección","data":{"provincia":provincia,"municipio":municipio,"tipo_via":tipo_via,"nombre_via":nombre_via,"numero":numero},"timestamp":int(__import__('time').time()*1000)}) + '\n')
        # #endregion

        # Construir SOAP request para Consulta_DNPLOC según documentación oficial
        # Formato según ejemplos oficiales del Catastro
        soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <Provincia xmlns="http://www.catastro.meh.es/">{provincia}</Provincia>
    <Municipio xmlns="http://www.catastro.meh.es/">{municipio}</Municipio>
    <Sigla xmlns="http://www.catastro.meh.es/">{tipo_via}</Sigla>
    <Calle xmlns="http://www.catastro.meh.es/">{nombre_via}</Calle>
    <Numero xmlns="http://www.catastro.meh.es/">{numero}</Numero>"""
        
        if bloque:
            soap_body += f"\n    <Bloque xmlns=\"http://www.catastro.meh.es/\">{bloque}</Bloque>"
        if escalera:
            soap_body += f"\n    <Escalera xmlns=\"http://www.catastro.meh.es/\">{escalera}</Escalera>"
        if planta:
            soap_body += f"\n    <Planta xmlns=\"http://www.catastro.meh.es/\">{planta}</Planta>"
        if puerta:
            soap_body += f"\n    <Puerta xmlns=\"http://www.catastro.meh.es/\">{puerta}</Puerta>"
            
        soap_body += """
  </soap:Body>
</soap:Envelope>"""

        # #region agent log
        with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H35","location":"catastro_soap_client.py:get_rc_by_address","message":"SOAP request construido","data":{"soap_body":soap_body},"timestamp":int(__import__('time').time()*1000)}) + '\n')
        # #endregion

        try:
            # Usar SOAPAction específico para Consulta_DNPLOC
            headers = {
                "Content-Type": "text/xml; charset=utf-8",
                "SOAPAction": "http://tempuri.org/OVCServWeb/OVCCallejero/Consulta_DNPLOC",
            }

            response = self.session.post(
                self.config.base_url,
                data=soap_body.encode("utf-8"),
                headers=headers,
                timeout=self.config.timeout,
            )

            # #region agent log
            with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H35","location":"catastro_soap_client.py:get_rc_by_address","message":"Respuesta recibida","data":{"status_code":response.status_code,"response_preview":response.text[:500]},"timestamp":int(__import__('time').time()*1000)}) + '\n')
            # #endregion

            response.raise_for_status()

            # Parsear respuesta para extraer referencia catastral
            root = ET.fromstring(response.text)

            # Verificar errores
            consulta_dnp = root.find(".//{http://www.catastro.meh.es/}Consulta_DNP")
            if consulta_dnp is not None:
                consulta_dnp_inner = consulta_dnp.find(".//{http://www.catastro.meh.es/}consulta_dnp")
                if consulta_dnp_inner is not None:
                    control = consulta_dnp_inner.find(".//{http://www.catastro.meh.es/}control")
                    if control is not None:
                        cuerr = control.find(".//{http://www.catastro.meh.es/}cuerr")
                        if cuerr is not None and cuerr.text and cuerr.text.strip() != "0":
                            # Hay errores
                            lerr = consulta_dnp_inner.find(".//{http://www.catastro.meh.es/}lerr")
                            if lerr is not None:
                                err = lerr.find(".//{http://www.catastro.meh.es/}err")
                                if err is not None:
                                    cod = err.find(".//{http://www.catastro.meh.es/}cod")
                                    des = err.find(".//{http://www.catastro.meh.es/}des")
                                    cod_text = cod.text if cod is not None and cod.text else "?"
                                    des_text = des.text if des is not None and des.text else "Error desconocido"
                                    logger.warning(f"Error del servidor (código {cod_text}): {des_text}")
                                    return None

            # Buscar referencia catastral en la respuesta
            # Formato: <pc1>08019</pc1><pc2>2VH5797S0001W</pc2>
            pc1_elem = root.find(".//{http://www.catastro.meh.es/}pc1")
            pc2_elem = root.find(".//{http://www.catastro.meh.es/}pc2")

            if pc1_elem is not None and pc2_elem is not None:
                pc1 = pc1_elem.text.strip() if pc1_elem.text else ""
                pc2 = pc2_elem.text.strip() if pc2_elem.text else ""
                referencia_completa = f"{pc1}{pc2}"

                # #region agent log
                with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H35","location":"catastro_soap_client.py:get_rc_by_address","message":"Referencia encontrada","data":{"pc1":pc1,"pc2":pc2,"referencia_completa":referencia_completa},"timestamp":int(__import__('time').time()*1000)}) + '\n')
                # #endregion

                logger.debug(f"Referencia encontrada: {referencia_completa}")
                return referencia_completa

            # Si no se encuentra pc1/pc2, buscar en otros formatos
            # Algunas respuestas pueden tener la referencia en otro formato
            for elem in root.iter():
                if elem.tag.endswith("pc1") or elem.tag.endswith("pc2"):
                    if elem.text:
                        logger.debug(f"Referencia parcial encontrada: {elem.text}")
                        # Intentar construir referencia completa
                        if len(elem.text) >= 5:
                            return elem.text

            logger.warning(f"No se encontró referencia catastral para {tipo_via} {nombre_via} {numero}")
            return None

        except requests.RequestException as exc:
            # #region agent log
            with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H35","location":"catastro_soap_client.py:get_rc_by_address","message":"Error de red","data":{"error":str(exc)},"timestamp":int(__import__('time').time()*1000)}) + '\n')
            # #endregion
            raise CatastroSOAPError(f"Error de red al consultar por dirección: {exc}") from exc
        except ET.ParseError as exc:
            # #region agent log
            with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H35","location":"catastro_soap_client.py:get_rc_by_address","message":"Error parsing XML","data":{"error":str(exc)},"timestamp":int(__import__('time').time()*1000)}) + '\n')
            # #endregion
            raise CatastroSOAPError(f"Error al parsear respuesta XML: {exc}") from exc

    def get_building_by_coordinates(
        self, lon: float, lat: float, srs: str = "EPSG:4326"
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de un inmueble por coordenadas usando Consulta_RCCOOR.
        
        Este método funciona correctamente y puede usarse como alternativa
        cuando Consulta_DNPRC falla con error "LA PROVINCIA NO EXISTE".
        
        Args:
            lon: Longitud (coordenada X)
            lat: Latitud (coordenada Y)
            srs: Sistema de referencia espacial (default: EPSG:4326)
            
        Returns:
            Diccionario con datos del inmueble o None si no se encuentra
            
        Raises:
            CatastroSOAPError: Si hay error en la petición
        """
        # #region agent log
        import json
        import time
        with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"ALTERNATIVE","location":"catastro_soap_client.py:get_building_by_coordinates","message":"Consultando por coordenadas","data":{"lon":lon,"lat":lat,"srs":srs},"timestamp":int(time.time()*1000)}) + '\n')
        # #endregion
        
        url = "http://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCoordenadas.asmx/Consulta_RCCOOR"
        params = {
            "SRS": srs,
            "Coordenada_X": str(lon),
            "Coordenada_Y": str(lat),
        }
        
        try:
            response = requests.get(url, params=params, timeout=self.config.timeout)
            response.raise_for_status()
            
            # #region agent log
            with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"ALTERNATIVE","location":"catastro_soap_client.py:get_building_by_coordinates","message":"Respuesta recibida","data":{"status_code":response.status_code,"response_preview":response.text[:500]},"timestamp":int(time.time()*1000)}) + '\n')
            # #endregion
            
            # Parsear respuesta
            root = ET.fromstring(response.text)
            
            # Extraer referencia catastral
            pc1_elem = root.find(".//{http://www.catastro.meh.es/}pc1")
            pc2_elem = root.find(".//{http://www.catastro.meh.es/}pc2")
            
            if pc1_elem is None or pc2_elem is None:
                logger.warning(f"No se encontró referencia catastral para coordenadas ({lon}, {lat})")
                return None
            
            ref_catastral = f"{pc1_elem.text}{pc2_elem.text}"
            
            # #region agent log
            with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"ALTERNATIVE","location":"catastro_soap_client.py:get_building_by_coordinates","message":"Referencia obtenida","data":{"ref":ref_catastral},"timestamp":int(time.time()*1000)}) + '\n')
            # #endregion
            
            # Consulta_RCCOOR devuelve referencias de 14 caracteres (PC1 + PC2)
            # Consulta_DNPRC requiere 20 caracteres, pero actualmente falla con error "LA PROVINCIA NO EXISTE"
            # Por ahora, devolver los datos disponibles desde Consulta_RCCOOR
            
            # Extraer dirección de la respuesta de coordenadas
            ldt_elem = root.find(".//{http://www.catastro.meh.es/}ldt")
            direccion = ldt_elem.text if ldt_elem is not None else None
            
            # Intentar obtener datos usando Consulta_DNPRC solo si la referencia tiene 20 caracteres
            # NOTA: Actualmente Consulta_DNPRC falla con error "LA PROVINCIA NO EXISTE" (Issue #200)
            # Este es un workaround hasta que el servicio se solucione
            building_data = {
                "referencia_catastral": ref_catastral,
                "direccion_normalizada": direccion,
                "superficie_m2": None,
                "ano_construccion": None,
                "uso_principal": None,
                "metodo": "coordenadas",  # Indicar que se obtuvo por coordenadas
                "nota": "Consulta_DNPRC actualmente no funciona (error 'LA PROVINCIA NO EXISTE'). Datos obtenidos por coordenadas.",
            }
            
            # Si la referencia tiene 20 caracteres, intentar Consulta_DNPRC (aunque probablemente falle)
            if len(ref_catastral) == 20:
                try:
                    rc_data = self.get_building_by_rc(ref_catastral)
                    # Si funciona, combinar datos
                    building_data.update(rc_data)
                    building_data["metodo"] = "coordenadas+RC"
                    # #region agent log
                    with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"ALTERNATIVE","location":"catastro_soap_client.py:get_building_by_coordinates","message":"Datos obtenidos por RC","data":{"ref":ref_catastral,"superficie":rc_data.get("superficie_m2")},"timestamp":int(time.time()*1000)}) + '\n')
                    # #endregion
                except CatastroSOAPError as rc_error:
                    # Si Consulta_DNPRC falla (esperado actualmente), mantener datos de coordenadas
                    logger.warning(
                        f"Consulta_DNPRC falló para {ref_catastral} (esperado): {rc_error}"
                    )
                    # #region agent log
                    with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"ALTERNATIVE","location":"catastro_soap_client.py:get_building_by_coordinates","message":"Consulta_DNPRC falló (esperado)","data":{"ref":ref_catastral,"error":str(rc_error)},"timestamp":int(time.time()*1000)}) + '\n')
                    # #endregion
            
            # #region agent log
            with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"ALTERNATIVE","location":"catastro_soap_client.py:get_building_by_coordinates","message":"Datos devueltos","data":{"ref":ref_catastral,"direccion":direccion,"metodo":building_data.get("metodo")},"timestamp":int(time.time()*1000)}) + '\n')
            # #endregion
            
            return building_data
                
        except requests.RequestException as exc:
            # #region agent log
            with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"ALTERNATIVE","location":"catastro_soap_client.py:get_building_by_coordinates","message":"Error de red","data":{"error":str(exc)},"timestamp":int(time.time()*1000)}) + '\n')
            # #endregion
            raise CatastroSOAPError(f"Error de red al consultar por coordenadas: {exc}") from exc
        except ET.ParseError as exc:
            # #region agent log
            with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"ALTERNATIVE","location":"catastro_soap_client.py:get_building_by_coordinates","message":"Error parsing XML","data":{"error":str(exc)},"timestamp":int(time.time()*1000)}) + '\n')
            # #endregion
            raise CatastroSOAPError(f"Error al parsear respuesta XML: {exc}") from exc


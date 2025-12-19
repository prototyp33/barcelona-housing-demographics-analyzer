"""
Cliente para el servicio oficial de consulta masiva de datos NO protegidos del Catastro.

Este servicio permite obtener datos catastrales (sin titularidad ni valor) mediante
un fichero XML de entrada con referencias catastrales.

Documentación oficial:
- https://www.catastro.hacienda.gob.es/ayuda/masiva/Ayuda_Masiva.htm
- Requiere registro en la Sede Electrónica del Catastro

Issue: #200
Author: Equipo A - Data Infrastructure
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
from xml.dom import minidom

logger = logging.getLogger(__name__)


@dataclass
class CatastroOficialConfig:
    """
    Configuración para el servicio oficial de consulta masiva del Catastro.

    Attributes:
        sede_url: URL base de la Sede Electrónica del Catastro.
        output_dir: Directorio donde guardar ficheros XML de entrada y salida.
    """

    sede_url: str = "https://www1.sedecatastro.gob.es"
    output_dir: Path = Path("spike-data-validation/data/raw/catastro_oficial")


class CatastroOficialClient:
    """
    Cliente para generar ficheros XML de consulta masiva al Catastro oficial.

    Este cliente genera el fichero XML de entrada según el formato requerido
    por la D.G. del Catastro. El procesamiento es asíncrono y requiere:
    1. Generar fichero XML de entrada
    2. Subirlo a la Sede Electrónica (requiere autenticación)
    3. Esperar procesamiento (puede tardar >1 hora)
    4. Descargar fichero XML de salida
    5. Parsear resultados

    Para el spike, este método es más complejo que catastro-api.es, pero
    es la fuente oficial y no requiere API key de terceros.
    """

    def __init__(self, config: Optional[CatastroOficialConfig] = None) -> None:
        """
        Inicializa el cliente del servicio oficial.

        Args:
            config: Configuración; si es None, usa valores por defecto.
        """
        self.config = config or CatastroOficialConfig()
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_input_xml(
        self,
        referencias_catastrales: List[str],
        output_file: Optional[Path] = None,
    ) -> Path:
        """
        Genera el fichero XML de entrada para consulta masiva.

        Formato según documentación oficial:
        - Root: <CONSULTA>
        - Elementos: <RC> con referencia catastral (20 caracteres)

        Args:
            referencias_catastrales: Lista de referencias catastrales (20 caracteres).
            output_file: Ruta del fichero XML a generar. Si es None, usa nombre por defecto.

        Returns:
            Ruta del fichero XML generado.

        Nota:
            La documentación suele referirse a RC de 20 caracteres, pero en el spike
            también manejamos referencias tipo PC1+PC2 (14 caracteres) obtenidas vía
            `Consulta_RCCOOR`. Para no bloquear la Fase 2, aceptamos 14 o 20 caracteres
            y dejamos que la Sede valide el fichero.\n\n+            Si la Sede rechaza RC de 14, el paso previo será obtener RC de 20 (cuando
            el servicio vuelva a funcionar o mediante otra fuente oficial).

        Raises:
            ValueError: Si alguna referencia no tiene 14 ni 20 caracteres.
        """
        if output_file is None:
            output_file = self.config.output_dir / "consulta_masiva_entrada.xml"

        # Validar formato de referencias (14 o 20) sin asumir que ya tenemos RC completa
        for ref in referencias_catastrales:
            ref_clean = ref.strip()
            if len(ref_clean) not in (14, 20):
                raise ValueError(
                    f"Referencia catastral inválida: '{ref_clean}' (debe tener 14 o 20 caracteres, tiene "
                    f"{len(ref_clean)})",
                )

        # Crear estructura XML
        root = ET.Element("CONSULTA")
        root.set("xmlns", "http://www.catastro.meh.es/")

        for ref in referencias_catastrales:
            rc_element = ET.SubElement(root, "RC")
            rc_element.text = ref.strip()

        # Formatear XML con indentación
        xml_str = ET.tostring(root, encoding="unicode")
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ")

        # Guardar fichero
        output_file.write_text(pretty_xml, encoding="utf-8")
        logger.info(
            "Fichero XML de entrada generado: %s (%s referencias)",
            output_file,
            len(referencias_catastrales),
        )

        return output_file

    def parse_output_xml(self, xml_file: Path) -> List[Dict[str, Optional[object]]]:
        """
        Parsea el fichero XML de salida del Catastro.

        El formato de salida contiene información de cada inmueble consultado.
        Estructura típica:
        - <CONSULTA>
          - <INMUEBLE>
            - <RC> (referencia catastral)
            - <SUP> (superficie)
            - <ANYO> (año construcción)
            - <PLANTAS> (número de plantas)
            - <DIRECCION> (dirección)

        Args:
            xml_file: Ruta del fichero XML de salida.

        Returns:
            Lista de diccionarios con datos de inmuebles.

        Raises:
            FileNotFoundError: Si el fichero no existe.
            ET.ParseError: Si el XML es inválido.
        """
        if not xml_file.exists():
            raise FileNotFoundError(f"Fichero XML no encontrado: {xml_file}")

        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
        except ET.ParseError as exc:
            raise ET.ParseError(f"Error al parsear XML: {exc}") from exc

        # Namespace del Catastro
        ns = {"cat": "http://www.catastro.meh.es/"}

        resultados: List[Dict[str, Optional[object]]] = []

        # Buscar todos los inmuebles
        for inmueble in root.findall(".//cat:INMUEBLE", ns):
            rc_elem = inmueble.find("cat:RC", ns)
            sup_elem = inmueble.find("cat:SUP", ns)
            anyo_elem = inmueble.find("cat:ANYO", ns)
            plantas_elem = inmueble.find("cat:PLANTAS", ns)
            direccion_elem = inmueble.find("cat:DIRECCION", ns)

            resultado: Dict[str, Optional[object]] = {
                "referencia_catastral": rc_elem.text.strip() if rc_elem is not None and rc_elem.text else None,
                "superficie_m2": float(sup_elem.text) if sup_elem is not None and sup_elem.text else None,
                "ano_construccion": int(anyo_elem.text) if anyo_elem is not None and anyo_elem.text else None,
                "plantas": int(plantas_elem.text) if plantas_elem is not None and plantas_elem.text else None,
                "direccion_normalizada": direccion_elem.text.strip() if direccion_elem is not None and direccion_elem.text else None,
            }

            resultados.append(resultado)

        logger.info("Parseados %s inmuebles del fichero XML", len(resultados))
        return resultados

    def generate_instructions(self, xml_input: Path) -> str:
        """
        Genera instrucciones para usar el fichero XML generado.

        Args:
            xml_input: Ruta del fichero XML de entrada generado.

        Returns:
            Texto con instrucciones paso a paso.
        """
        instructions = f"""
================================================================================
INSTRUCCIONES PARA CONSULTA MASIVA OFICIAL DEL CATASTRO
================================================================================

1. REGISTRO EN SEDE ELECTRÓNICA
   - Accede a: {self.config.sede_url}
   - Regístrate o inicia sesión (no requiere certificado digital para datos NO protegidos)

2. SUBIR FICHERO XML
   - Opción: "Enviar consulta masiva de datos NO protegidos"
   - Sube el fichero: {xml_input.absolute()}

3. ESPERAR PROCESAMIENTO
   - El sistema procesa la consulta de forma asíncrona
   - Tiempo estimado: 1-2 horas (depende de carga del sistema)
   - Recibirás notificación por email cuando esté listo

4. DESCARGAR RESULTADOS
   - Opción: "Descargar resultados de consulta masiva al Catastro"
   - Guarda el fichero XML de salida en: {self.config.output_dir}

5. PROCESAR RESULTADOS
   - Usa el método parse_output_xml() para convertir XML a DataFrame
   - Ejemplo:
     ```python
     from catastro_oficial_client import CatastroOficialClient
     client = CatastroOficialClient()
     resultados = client.parse_output_xml(Path("consulta_masiva_salida.xml"))
     ```

================================================================================
VENTAJAS DEL SERVICIO OFICIAL:
- Fuente oficial (D.G. del Catastro)
- No requiere API key de terceros
- Datos actualizados directamente del Catastro

DESVENTAJAS:
- Requiere registro en Sede Electrónica
- Procesamiento asíncrono (1-2 horas)
- Formato XML más complejo de procesar

ALTERNATIVA RÁPIDA PARA SPIKE:
- Usar catastro-api.es (más rápido, requiere API key)
- Ver: extract_catastro_gracia.py
================================================================================
"""
        return instructions


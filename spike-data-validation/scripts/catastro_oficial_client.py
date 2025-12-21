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
        fecha: Optional[str] = None,
        finalidad: Optional[str] = None,
    ) -> Path:
        """
        Genera el fichero XML de entrada para consulta masiva.

        Formato según documentación oficial (Anexo 1, versión 1.5/1.6):
        - Root: <LISTADATOS> (obligatorio)
        - Etiquetas obligatorias: <FEC> (fecha), <FIN> (finalidad)
        - Cada referencia en bloque <DAT> con <RC>

        Args:
            referencias_catastrales: Lista de referencias catastrales (14, 18 o 20 caracteres).
            output_file: Ruta del fichero XML a generar. Si es None, usa nombre por defecto.
            fecha: Fecha en formato YYYY-MM-DD. Si es None, usa fecha actual.
            finalidad: Texto descriptivo de la finalidad. Si es None, usa valor por defecto.

        Returns:
            Ruta del fichero XML generado.

        Nota:
            Según la documentación oficial:
            - RC puede tener 14, 18 o 20 posiciones
            - Si se usa RC de 14 posiciones, el sistema devuelve todos los inmuebles de esa finca
            - Las etiquetas <FEC> y <FIN> son obligatorias

        Raises:
            ValueError: Si alguna referencia no tiene 14, 18 ni 20 caracteres.
        """
        from datetime import date

        if output_file is None:
            output_file = self.config.output_dir / "consulta_masiva_entrada.xml"

        # Validar formato de referencias (14, 18 o 20 según documentación oficial)
        for ref in referencias_catastrales:
            ref_clean = ref.strip()
            if len(ref_clean) not in (14, 18, 20):
                raise ValueError(
                    f"Referencia catastral inválida: '{ref_clean}' (debe tener 14, 18 o 20 caracteres, tiene "
                    f"{len(ref_clean)})",
                )

        # Usar fecha actual si no se proporciona
        if fecha is None:
            fecha = date.today().isoformat()

        # Usar finalidad por defecto si no se proporciona
        if finalidad is None:
            finalidad = "CONSULTA MASIVA DATOS NO PROTEGIDOS"

        # Crear estructura XML según esquema oficial del Catastro (Anexo 1)
        # Elemento raíz OBLIGATORIO: LISTADATOS
        root = ET.Element("LISTADATOS")

        # Etiquetas obligatorias según documentación oficial
        fec_element = ET.SubElement(root, "FEC")
        fec_element.text = fecha

        fin_element = ET.SubElement(root, "FIN")
        fin_element.text = finalidad

        # Cada referencia catastral va en un bloque DAT con RC
        for ref in referencias_catastrales:
            dat_element = ET.SubElement(root, "DAT")
            rc_element = ET.SubElement(dat_element, "RC")
            rc_element.text = ref.strip()

        # Formatear XML con indentación y encoding UTF-8
        xml_str = ET.tostring(root, encoding="unicode")
        dom = minidom.parseString(xml_str)
        # Asegurar que la declaración XML incluye encoding UTF-8
        pretty_xml = dom.toprettyxml(indent="  ", encoding="utf-8")
        # minidom.toprettyxml devuelve bytes cuando se especifica encoding
        if isinstance(pretty_xml, bytes):
            pretty_xml = pretty_xml.decode("utf-8")
        # Reemplazar la declaración XML para incluir encoding explícitamente
        if pretty_xml.startswith('<?xml version="1.0" ?>'):
            pretty_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + pretty_xml.split('\n', 1)[1]

        # Guardar fichero
        output_file.write_text(pretty_xml, encoding="utf-8")
        logger.info(
            "Fichero XML de entrada generado (formato LISTADATOS): %s (%s referencias)",
            output_file,
            len(referencias_catastrales),
        )

        return output_file

    def generate_input_xml_variants(
        self,
        referencias_catastrales: List[str],
        output_dir: Optional[Path] = None,
    ) -> Dict[str, Path]:
        """
        Genera múltiples variantes del XML de entrada para probar cuál acepta la Sede.

        El esquema XML exacto no está completamente documentado públicamente, por lo que
        este método genera varias variantes comunes para que el usuario pueda probar
        cuál funciona con la validación de la Sede Electrónica.

        Args:
            referencias_catastrales: Lista de referencias catastrales (14 o 20 caracteres).
            output_dir: Directorio donde guardar las variantes. Si es None, usa output_dir por defecto.

        Returns:
            Diccionario con nombres de variantes y rutas de los ficheros generados.

        Variantes generadas:
            - variant1_basic: CONSULTA con xmlns básico (sin schemaLocation)
            - variant2_with_schema: CONSULTA con xsi:schemaLocation
            - variant3_no_namespace: CONSULTA sin namespace (namespace por defecto)
            - variant4_consulta_municipiero: Formato alternativo con elemento wrapper
        """
        if output_dir is None:
            output_dir = self.config.output_dir

        # Validar referencias
        for ref in referencias_catastrales:
            ref_clean = ref.strip()
            if len(ref_clean) not in (14, 20):
                raise ValueError(
                    f"Referencia catastral inválida: '{ref_clean}' (debe tener 14 o 20 caracteres, tiene "
                    f"{len(ref_clean)})",
                )

        variants: Dict[str, Path] = {}

        # Variante 1: Básica (sin schemaLocation)
        root1 = ET.Element("CONSULTA", {"xmlns": "http://www.catastro.meh.es/"})
        for ref in referencias_catastrales:
            rc = ET.SubElement(root1, "RC")
            rc.text = ref.strip()
        xml1 = minidom.parseString(ET.tostring(root1, encoding="unicode")).toprettyxml(indent="  ")
        path1 = output_dir / "consulta_masiva_entrada_variant1_basic.xml"
        path1.write_text(xml1, encoding="utf-8")
        variants["variant1_basic"] = path1

        # Variante 2: Con schemaLocation
        root2 = ET.Element(
            "CONSULTA",
            {
                "xmlns": "http://www.catastro.meh.es/",
                "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "xsi:schemaLocation": "http://www.catastro.meh.es/ http://www.catastro.meh.es/ConsultaMasiva.xsd",
            },
        )
        for ref in referencias_catastrales:
            rc = ET.SubElement(root2, "RC")
            rc.text = ref.strip()
        xml2 = minidom.parseString(ET.tostring(root2, encoding="unicode")).toprettyxml(indent="  ")
        path2 = output_dir / "consulta_masiva_entrada_variant2_with_schema.xml"
        path2.write_text(xml2, encoding="utf-8")
        variants["variant2_with_schema"] = path2

        # Variante 3: Sin namespace (namespace por defecto vacío)
        root3 = ET.Element("CONSULTA")
        for ref in referencias_catastrales:
            rc = ET.SubElement(root3, "RC")
            rc.text = ref.strip()
        xml3 = minidom.parseString(ET.tostring(root3, encoding="unicode")).toprettyxml(indent="  ")
        path3 = output_dir / "consulta_masiva_entrada_variant3_no_namespace.xml"
        path3.write_text(xml3, encoding="utf-8")
        variants["variant3_no_namespace"] = path3

        # Variante 4: Formato alternativo (basado en error "consulta_municipiero")
        # Puede que el esquema espere un elemento wrapper diferente
        root4 = ET.Element("consulta_municipiero", {"xmlns": "http://www.catastro.meh.es/"})
        consulta = ET.SubElement(root4, "CONSULTA")
        for ref in referencias_catastrales:
            rc = ET.SubElement(consulta, "RC")
            rc.text = ref.strip()
        xml4 = minidom.parseString(ET.tostring(root4, encoding="unicode")).toprettyxml(indent="  ")
        path4 = output_dir / "consulta_masiva_entrada_variant4_wrapper.xml"
        path4.write_text(xml4, encoding="utf-8")
        variants["variant4_wrapper"] = path4

        logger.info("Generadas %s variantes de XML en %s", len(variants), output_dir)
        return variants

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


"""
Data Dictionary View - Reference for system metrics and datasets.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
from src.app.components import card_standard

def render() -> None:
    """
    Renderiza el diccionario de datos interactivo.
    """
    st.header("📖 DICCIONARIO DE DATOS")
    st.markdown(
        "Referencia detallada de las métricas de precio y fuentes de datos utilizadas en el analizador."
    )

    # Definición de las 11 métricas de precio
    price_metrics = [
        {
            "Métrica": "Venta: m² Promedio",
            "Etapa": "Transacción",
            "Categoría": "Todo",
            "Unidad": "€/m²",
            "Dataset ID": "bxtvnxvukh",
            "Descripción": "Precio medio por m² en transacciones reales de compraventa."
        },
        {
            "Métrica": "Venta: Precio Unitario",
            "Etapa": "Transacción",
            "Categoría": "Todo",
            "Unidad": "€/unidad",
            "Dataset ID": "hostlmjrdo",
            "Descripción": "Precio total medio por vivienda vendida."
        },
        {
            "Métrica": "Venta: Por Tipo",
            "Etapa": "Transacción",
            "Categoría": "Nueva vs. Segunda mano",
            "Unidad": "€/m²",
            "Dataset ID": "mrslyp5pcq",
            "Descripción": "Precios segmentados por tipología de propiedad."
        },
        {
            "Métrica": "Venta: Por Antigüedad",
            "Etapa": "Transacción",
            "Categoría": "Año Construcción",
            "Unidad": "€/m²",
            "Dataset ID": "idjhkx1ruj",
            "Descripción": "Precios según el año de construcción del edificio."
        },
        {
            "Métrica": "Venta: Registro m²",
            "Etapa": "Registrado",
            "Categoría": "Todo",
            "Unidad": "€/m²",
            "Dataset ID": "u25rr7oxh6",
            "Descripción": "Precio por m² según registros oficiales de la propiedad."
        },
        {
            "Métrica": "Venta: Registro Unitario",
            "Etapa": "Registrado",
            "Categoría": "Todo",
            "Unidad": "€/unidad",
            "Dataset ID": "la6s9fp57r",
            "Descripción": "Precio total por unidad según registros oficiales."
        },
        {
            "Métrica": "Venta: Registro por Estado",
            "Etapa": "Registrado",
            "Categoría": "Nueva vs. Usada",
            "Unidad": "Mix",
            "Dataset ID": "cq4causxvu",
            "Descripción": "Precios registrados segmentados por estado de la vivienda."
        },
        {
            "Métrica": "Venta: Precio Oferta",
            "Etapa": "Oferta",
            "Categoría": "Segunda Mano",
            "Unidad": "€/m²",
            "Dataset ID": "bhl3ulphi5",
            "Descripción": "Precio medio de salida/oferta en portales inmobiliarios."
        },
        {
            "Métrica": "Alquiler: Mensual",
            "Etapa": "Contrato",
            "Categoría": "Todo",
            "Unidad": "€/mes",
            "Dataset ID": "b37xv8wcjh",
            "Descripción": "Renta mensual media en nuevos contratos firmados."
        },
        {
            "Métrica": "Alquiler: m²",
            "Etapa": "Contrato",
            "Categoría": "Todo",
            "Unidad": "€/m²/mes",
            "Dataset ID": "5ibudgqbrb",
            "Descripción": "Renta por m² en nuevos contratos firmados."
        },
        {
            "Métrica": "Alquiler: Avanzado",
            "Etapa": "Contrato",
            "Categoría": "Percentiles/Tipos",
            "Unidad": "Mix",
            "Dataset ID": "4waxpjj3uo",
            "Descripción": "Distribución estadística detallada de precios de alquiler."
        }
    ]

    df_prices = pd.DataFrame(price_metrics)

    with card_standard(title="Métricas de Precio (fact_precios)", subtitle="11 dimensionadores clave"):
        st.dataframe(
            df_prices,
            column_config={
                "Métrica": st.column_config.TextColumn("Métrica", width="medium"),
                "Etapa": st.column_config.SelectboxColumn(
                    "Etapa",
                    options=["Transacción", "Registrado", "Oferta", "Contrato"]
                ),
                "Dataset ID": st.column_config.TextColumn("ID Fuente", help="Referencia interna del dataset"),
                "Descripción": st.column_config.TextColumn("Definición", width="large")
            },
            hide_index=True,
            width="stretch"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    
    with col1:
        with card_standard(title="Fuentes de Datos"):
            st.markdown("""
            - **Portal de Dades BCN**: Datos oficiales de transacciones, registros y alquileres.
            - **Idealista**: Datos de oferta de mercado y tendencias de búsqueda.
            - **IDESCAT**: Información socioeconómica y demografía detallada.
            - **Inside Airbnb**: Presión turística y licencias VUT.
            """)

    with col2:
        with card_standard(title="Glosario Términos"):
            st.markdown("""
            - **Transacción**: Precio final de venta cerrado.
            - **Oferta**: Precio publicado (el 'asking price').
            - **Vivienda Tipo**: Referencia estándar de 70m² para comparativas.
            - **Zona Tensionada**: Barrio bajo regulación de contención de rentas.
            """)

if __name__ == "__main__":
    render()

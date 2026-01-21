from __future__ import annotations

"""
Vista: Market Intelligence (Gap de Negociación + Riesgo de Gentrificación).

Usa la tabla maestra exportada para BI (CSV) y permite explorar:
- Gap de negociación (asking vs transacción)
- Semáforo de gentrificación (renta/gini + alquiler)
"""

from typing import Optional

import pandas as pd
import plotly.express as px
import streamlit as st

from src.app.data_loader import load_master_table_csv


def _safe_str_series(series: pd.Series) -> pd.Series:
    """Normaliza Series a string para evitar errores de nulls en filtros."""
    return series.fillna("").astype(str)


def render(distrito_filter: Optional[str] = None) -> None:
    """Renderiza la vista de Market Intelligence."""
    st.markdown("## 🧠 Market Intelligence")
    st.caption("Gap de negociación + semáforo de gentrificación desde `master_table_barcelona_housing.csv`.")

    df = load_master_table_csv()
    if df.empty:
        st.warning(
            "No se encontró el CSV maestro. Genera el export con "
            "`python scripts/create_master_table_for_looker.py`."
        )
        return

    # Filtros base
    if distrito_filter:
        df = df[df["distrito_nombre"] == distrito_filter].copy()

    # Selector propio de año (la sidebar global depende de métricas SQLite)
    years = sorted(df["anio"].dropna().unique().tolist())
    if not years:
        st.warning("El CSV maestro no contiene años válidos en la columna `anio`.")
        return

    default_year = int(max(years))
    selected_year = st.selectbox(
        "Año (tabla maestra)",
        options=sorted([int(y) for y in years], reverse=True),
        index=0,
        help="Este selector es independiente del slider principal del sidebar.",
    )
    df_y = df[df["anio"] == selected_year].copy()

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        avg_gap = df_y["negotiation_gap_pct"].dropna().mean()
        st.metric("Margen negociación (prom.)", f"{avg_gap:.2f}%" if pd.notna(avg_gap) else "N/A")
    with c2:
        avg_ads = df_y["avg_num_anuncios_venta"].dropna().mean()
        st.metric("Anuncios venta (prom.)", f"{avg_ads:.0f}" if pd.notna(avg_ads) else "N/A")
    with c3:
        crit = _safe_str_series(df_y.get("gentrification_risk_level", pd.Series(dtype=str))).str.contains("🔴")
        st.metric("Riesgo crítico (🔴)", int(crit.sum()) if len(crit) else 0)
    with c4:
        gini = df_y["indice_gini"].dropna().mean() if "indice_gini" in df_y.columns else None
        st.metric("Gini (prom.)", f"{gini:.1f}" if pd.notna(gini) else "N/A")

    tab_gap, tab_gent, tab_map = st.tabs(
        ["📉 Negotiation Gap", "🚦 Gentrificación", "🗺️ Mapa"]
    )

    with tab_gap:
        st.markdown("### Gap de negociación")

        # Dataset “limpio” para ranking
        df_gap = df_y.copy()
        if "negotiation_low_volume" in df_gap.columns:
            df_gap = df_gap[df_gap["negotiation_low_volume"] == 0]
        if "negotiation_extreme_gap" in df_gap.columns:
            df_gap = df_gap[df_gap["negotiation_extreme_gap"] == 0]

        df_gap = df_gap.dropna(subset=["negotiation_gap_pct"])
        df_gap = df_gap.sort_values("negotiation_gap_pct", ascending=False)

        left, right = st.columns([1, 1])
        with left:
            top_n = st.slider("TOP N (oportunidades)", min_value=5, max_value=30, value=15)
            fig = px.bar(
                df_gap.head(top_n),
                x="negotiation_gap_pct",
                y="barrio_nombre",
                orientation="h",
                color="negotiation_gap_pct",
                color_continuous_scale="RdYlGn",
                labels={"negotiation_gap_pct": "Gap (%)", "barrio_nombre": "Barrio"},
                title="Barrios con mayor margen (filtrado por calidad)",
            )
            fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), height=520)
            st.plotly_chart(fig, width='stretch')

        with right:
            st.markdown("#### Oferta vs transacción (€/m²)")
            df_scatter = df_y.dropna(subset=["asking_price_m2", "transaction_price_m2"]).copy()
            fig2 = px.scatter(
                df_scatter,
                x="asking_price_m2",
                y="transaction_price_m2",
                color="distrito_nombre",
                size="avg_num_anuncios_venta" if "avg_num_anuncios_venta" in df_scatter.columns else None,
                hover_name="barrio_nombre",
                labels={
                    "asking_price_m2": "Oferta (€/m²)",
                    "transaction_price_m2": "Transacción (€/m²)",
                },
            )
            fig2.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=520)
            st.plotly_chart(fig2, width='stretch')

        st.markdown("#### Datos (año seleccionado)")
        cols = [
            "barrio_nombre",
            "distrito_nombre",
            "asking_price_m2",
            "transaction_price_m2",
            "negotiation_gap_pct",
            "avg_num_anuncios_venta",
            "negotiation_low_volume",
            "negotiation_extreme_gap",
        ]
        cols = [c for c in cols if c in df_y.columns]
        st.dataframe(df_y[cols].sort_values("negotiation_gap_pct", ascending=False), width='stretch')

    with tab_gent:
        st.markdown("### Semáforo de gentrificación")

        if "gentrification_risk_level" not in df_y.columns:
            st.warning("No existe la columna `gentrification_risk_level` en el CSV maestro.")
            return

        df_g = df_y.copy()
        df_g["gentrification_risk_level"] = _safe_str_series(df_g["gentrification_risk_level"])

        # Conteo por nivel
        counts = df_g["gentrification_risk_level"].value_counts(dropna=False).reset_index()
        counts.columns = ["nivel_riesgo", "count"]

        fig = px.pie(
            counts,
            values="count",
            names="nivel_riesgo",
            title="Distribución de riesgo (año seleccionado)",
        )
        st.plotly_chart(fig, width='stretch')

        cols = [
            "barrio_nombre",
            "distrito_nombre",
            "renta_bruta_llar",
            "indice_gini",
            "precio_mes_alquiler_promedio",
            "gentrification_rent_increase_pct",
            "gentrification_risk_level",
        ]
        cols = [c for c in cols if c in df_g.columns]
        st.dataframe(
            df_g[cols].sort_values("gentrification_rent_increase_pct", ascending=False),
            width='stretch',
            height=520,
        )

    with tab_map:
        st.markdown("### Mapa (gap + riesgo)")
        required = {"centroide_lat", "centroide_lon"}
        if not required.issubset(df_y.columns):
            st.info("No hay coordenadas de centroides en el CSV maestro para renderizar el mapa.")
            return

        df_map = df_y.dropna(subset=["centroide_lat", "centroide_lon"]).copy()
        fig = px.scatter_map(
            df_map,
            lat="centroide_lat",
            lon="centroide_lon",
            color="negotiation_gap_pct",
            size="avg_num_anuncios_venta" if "avg_num_anuncios_venta" in df_map.columns else None,
            hover_name="barrio_nombre",
            hover_data=["distrito_nombre", "gentrification_risk_level"],
            zoom=11,
            height=650,
            map_style="carto-positron",
            title="Mapa de calor: margen de negociación (color) y volumen (tamaño)",
        )
        fig.update_layout(margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig, width='stretch')


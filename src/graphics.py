# src/graphics.py

from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd

from src.model import NEUTRAL_COLORS


def _outfits_to_df(rec_data: dict) -> pd.DataFrame:
    """
    Convierte la salida de recomendar_outfits() en un DataFrame plano
    (una fila por prenda, con info del outfit).
    """
    outfits = rec_data.get("outfits", [])
    rows = []
    for idx, o in enumerate(outfits):
        o_score = o.get("score", None)
        o_type = o.get("type", "")
        for item in o.get("items", []):
            row = {
                "outfit_idx": idx + 1,
                "outfit_type": o_type,
                "outfit_score": o_score,
                "slot": item.get("slot", ""),
                "nombre": item.get("nombre", ""),
                "color_base": str(item.get("color_base", "") or "").lower(),
                "formalidad": item.get("formalidad", ""),
                "temporada": item.get("temporada", ""),
                "nivel_abrigo": item.get("nivel_abrigo", None),
            }
            rows.append(row)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def _build_scores_chart(df: pd.DataFrame):
    """Bar chart con el score de cada outfit."""
    if df.empty or "outfit_score" not in df.columns:
        return html.Div("No hay datos suficientes para el gráfico de scores.", className="text-muted")

    scores = (
        df[["outfit_idx", "outfit_score"]]
        .drop_duplicates()
        .sort_values("outfit_idx")
    )

    fig = px.bar(
        scores,
        x="outfit_idx",
        y="outfit_score",
        text="outfit_score",
        labels={"outfit_idx": "Outfit", "outfit_score": "Score"},
    )
    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig.update_layout(
        title="Calidad relativa de cada outfit",
        xaxis_title="Outfit",
        yaxis_title="Score (más alto = mejor ajuste)",
        margin=dict(t=60, l=40, r=20, b=40),
    )
    return dcc.Graph(figure=fig)


def _build_abrigo_chart(df: pd.DataFrame, temp_c: float):
    """
    Distribución de nivel de abrigo de las prendas vs lo que pediría la temperatura.
    Nivel 1 = ligero, 2 = medio, 3 = abrigado.
    """
    if df.empty or "nivel_abrigo" not in df.columns:
        return html.Div("No hay información de abrigo suficiente.", className="text-muted")

    abrigo = df.dropna(subset=["nivel_abrigo"]).copy()
    if abrigo.empty:
        return html.Div("No hay información de abrigo suficiente.", className="text-muted")

    # target sencillo en función de temperatura (mismo criterio que tu modelo)
    if temp_c >= 24:
        target = 1
    elif temp_c >= 15:
        target = 2
    else:
        target = 3

    counts = (
        abrigo["nivel_abrigo"]
        .astype(int)
        .value_counts()
        .rename_axis("nivel_abrigo")
        .reset_index(name="num_prendas")
        .sort_values("nivel_abrigo")
    )

    fig = px.bar(
        counts,
        x="nivel_abrigo",
        y="num_prendas",
        labels={"nivel_abrigo": "Nivel de abrigo", "num_prendas": "Número de prendas"},
    )
    fig.update_layout(
        title=f"Nivel de abrigo de las prendas (objetivo ≈ {target})",
        xaxis=dict(
            tickmode="array",
            tickvals=[1, 2, 3],
            ticktext=["Ligero", "Medio", "Abrigado"],
        ),
        margin=dict(t=60, l=40, r=20, b=40),
        shapes=[
            dict(
                type="line",
                x0=target,
                x1=target,
                y0=0,
                y1=float(counts["num_prendas"].max()) * 1.1,
                line=dict(dash="dash"),
            )
        ],
        annotations=[
            dict(
                x=target,
                y=float(counts["num_prendas"].max()) * 1.1,
                text="Objetivo por temperatura",
                showarrow=False,
                yanchor="bottom",
            )
        ],
    )
    return dcc.Graph(figure=fig)


def _build_colors_chart(df: pd.DataFrame):
    """Gráfico de colores usados (neutros vs fuertes)."""
    if df.empty:
        return html.Div("No hay información de colores suficiente.", className="text-muted")

    df = df.copy()
    df["tipo_color"] = df["color_base"].apply(
        lambda c: "Neutro" if c in NEUTRAL_COLORS else ("Sin info" if c == "" else "Color fuerte")
    )

    counts = (
        df["tipo_color"]
        .value_counts()
        .rename_axis("tipo_color")
        .reset_index(name="num_prendas")
    )

    fig = px.pie(
        counts,
        names="tipo_color",
        values="num_prendas",
        hole=0.4,
    )
    fig.update_layout(
        title="Equilibrio de colores en los outfits",
        margin=dict(t=60, l=20, r=20, b=40),
    )
    return dcc.Graph(figure=fig)


def _build_slot_coverage_chart(df: pd.DataFrame):
    """Cuántos outfits contienen cada slot (top, bottom, dress, shoes)."""
    if df.empty or "slot" not in df.columns:
        return html.Div("No hay información de slots suficiente.", className="text-muted")

    counts = (
        df.groupby("slot")["outfit_idx"]
        .nunique()
        .reset_index(name="num_outfits")
        .sort_values("num_outfits", ascending=False)
    )

    fig = px.bar(
        counts,
        x="slot",
        y="num_outfits",
        labels={"slot": "Slot", "num_outfits": "Número de outfits"},
    )
    fig.update_layout(
        title="Cobertura de slots en los outfits (cuántos outfits incluyen cada tipo)",
        margin=dict(t=60, l=40, r=20, b=40),
    )
    return dcc.Graph(figure=fig)


def _build_item_reuse_chart(df: pd.DataFrame, top_n: int = 10):
    """Prendas que más se repiten entre los outfits (número de outfits donde aparece cada prenda)."""
    if df.empty or "nombre" not in df.columns:
        return html.Div("No hay información de prendas suficiente.", className="text-muted")

    reuse = (
        df.groupby("nombre")["outfit_idx"]
        .nunique()
        .reset_index(name="num_outfits")
        .sort_values("num_outfits", ascending=False)
    )

    if reuse.empty:
        return html.Div("No hay datos de reutilización de prendas.", className="text-muted")

    top = reuse.head(top_n)
    fig = px.bar(
        top,
        x="nombre",
        y="num_outfits",
        labels={"nombre": "Prenda", "num_outfits": "# Outfits"},
    )
    fig.update_layout(
        title=f"Top {top_n} prendas más reutilizadas entre los outfits",
        xaxis_tickangle=-45,
        margin=dict(t=60, l=40, r=20, b=80),
    )
    return dcc.Graph(figure=fig)


def _candidates_to_df(rec_data: dict) -> pd.DataFrame:
    """
    Convierte el diccionario 'candidates' de rec_data en un DataFrame plano.
    """
    cand = rec_data.get("candidates", {}) or {}
    rows = []
    for slot, items in cand.items():
        for it in items:
            row = {
                "slot": slot,
                "nombre": it.get("nombre", ""),
                "color_base": str(it.get("color_base", "") or "").lower(),
                "formalidad": it.get("formalidad", ""),
                "temporada": it.get("temporada", ""),
                "nivel_abrigo": it.get("nivel_abrigo", None),
                "fabric_type": it.get("fabric_type", "") or it.get("fabric", ""),
                "candidate_score": it.get("__score__", it.get("candidate_score", None)),
            }
            rows.append(row)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def _build_candidates_score_hist(df: pd.DataFrame):
    """Histograma de scores de los candidatos (por slot)."""
    if df.empty or "candidate_score" not in df.columns:
        return html.Div("No hay datos de candidatos suficientes para el histograma.", className="text-muted")

    fig = px.histogram(df, x="candidate_score", nbins=20, color="slot", marginal="rug")
    fig.update_layout(title="Distribución de score entre candidatos (por slot)", margin=dict(t=60, l=40, r=20, b=40))
    return dcc.Graph(figure=fig)


def _build_candidates_fabric_chart(df: pd.DataFrame):
    """Distribución de tipos de tejido entre los candidatos."""
    if df.empty or "fabric_type" not in df.columns:
        return html.Div("No hay información de tejidos en candidatos.", className="text-muted")

    df = df.copy()
    df["fabric_type"] = df["fabric_type"].fillna("unknown").astype(str)
    counts = df["fabric_type"].value_counts().reset_index(name="count").rename(columns={"index": "fabric_type"})
    fig = px.pie(counts, names="fabric_type", values="count", hole=0.35)
    fig.update_layout(title="Distribución de tejidos en el pool de candidatos", margin=dict(t=60, l=20, r=20, b=40))
    return dcc.Graph(figure=fig)


def _build_candidate_slot_coverage(df: pd.DataFrame):
    """Cobertura por slot para el pool de candidatos (nº candidatos por slot)."""
    if df.empty or "slot" not in df.columns:
        return html.Div("No hay información de slots en candidatos.", className="text-muted")

    counts = (
        df["slot"]
        .value_counts()
        .reset_index(name="num_candidates")
        .rename(columns={"index": "slot"})
        .sort_values("num_candidates", ascending=False)
    )

    fig = px.bar(
        counts,
        x="slot",
        y="num_candidates",
        labels={"slot": "Slot", "num_candidates": "Número de candidatos"},
    )
    fig.update_layout(
        title="Cobertura de slots en el pool de candidatos (nº candidatos por slot)",
        margin=dict(t=60, l=40, r=20, b=40),
    )
    return dcc.Graph(figure=fig)


def build_analytics_layout(rec_data: dict):
    """
    Construye el layout que se mostrará en la pestaña
    'Análisis (gráficos)' a partir de la recomendación.
    """
    if not rec_data:
        return html.Div("No hay recomendaciones todavía. Genera primero un outfit.")

    df = _outfits_to_df(rec_data)
    meta = rec_data.get("meta", {})
    temp_c = float(meta.get("temp_c", 20.0))
    rainy = bool(meta.get("rainy", False))
    city = meta.get("city", "Tu ciudad")
    used_date = meta.get("used_date", "")

    # candidatos (top-K por slot) para análisis más rico
    cand_df = _candidates_to_df(rec_data)

    header = html.Div(
        [
            html.H4("Análisis de la recomendación", className="mb-2"),
            html.P(
                f"Ciudad: {city} · {temp_c:.1f}°C · lluvia {'sí' if rainy else 'no'} · día usado: {used_date}",
                className="text-muted small",
            ),
        ],
        className="mb-3",
    )

    scores_chart = _build_scores_chart(df)
    colors_chart = _build_colors_chart(df)
    abrigo_chart = _build_abrigo_chart(df, temp_c)
    slot_chart = _build_slot_coverage_chart(df)
    reuse_chart = _build_item_reuse_chart(df)

    # gráficos basados en pool de candidatos (si hay datos)
    cand_score_hist = _build_candidates_score_hist(cand_df)
    cand_fabric_chart = _build_candidates_fabric_chart(cand_df)
    cand_slot_coverage = _build_candidate_slot_coverage(cand_df)

    children = [header]

    # Mostrar información del pool de candidatos (si existe)
    if not cand_df.empty:
        children.append(
            html.Div(
                [
                    html.H5("Análisis del pool de candidatos (top-K por slot)", className="mb-2"),
                    dbc.Row(
                        [
                            dbc.Col(cand_score_hist, md=6),
                            dbc.Col(cand_fabric_chart, md=6),
                        ],
                        className="mb-4",
                    ),
                    dbc.Row([dbc.Col(cand_slot_coverage, md=12)], className="mb-4"),
                ]
            )
        )

    children.extend(
        [
            dbc.Row(
                [
                    dbc.Col(scores_chart, md=6),
                    dbc.Col(colors_chart, md=6),
                ],
                className="mb-4",
            ),
            dbc.Row(
                [
                    dbc.Col(slot_chart, md=6),
                    dbc.Col(reuse_chart, md=6),
                ],
                className="mb-4",
            ),
            html.H5("Nivel de abrigo de las prendas", className="mb-2"),
            abrigo_chart,
        ]
    )

    return html.Div(children)

# src/catalog_graphics.py

from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd


# ========= helpers internos =========

def _cluster_size_chart(df: pd.DataFrame):
    """Número de prendas por cluster de estilo."""
    if "style_cluster" not in df.columns:
        return html.Div(
            "No hay columna 'style_cluster' en el catálogo.",
            className="text-muted",
        )

    counts = (
        df["style_cluster"]
        .value_counts()
        .sort_index()
        .reset_index()
    )
    # Queremos columnas explícitas: style_cluster, num_prendas
    counts.columns = ["style_cluster", "num_prendas"]

    fig = px.bar(
        counts,
        x="style_cluster",
        y="num_prendas",
        text="num_prendas",
        labels={
            "style_cluster": "Cluster de estilo",
            "num_prendas": "Número de prendas",
        },
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        title="Tamaño de cada cluster de estilo",
        margin=dict(t=60, l=40, r=20, b=40),
        height=400,
        autosize=False,
    )
    return dcc.Graph(figure=fig, config={'displayModeBar': False}, style={'height': '400px', 'width': '100%'})


def _cluster_segment_chart(df: pd.DataFrame):
    """Distribución de segmentos (mujer/hombre/niño) dentro de cada cluster."""
    if "style_cluster" not in df.columns or "segment" not in df.columns:
        return html.Div("No hay información suficiente de segmento/cluster.", className="text-muted")

    agg = (
        df.groupby(["style_cluster", "segment"])["id"]
        .count()
        .reset_index(name="num_prendas")
    )

    fig = px.bar(
        agg,
        x="style_cluster",
        y="num_prendas",
        color="segment",
        barmode="stack",
        labels={
            "style_cluster": "Cluster de estilo",
            "num_prendas": "Número de prendas",
            "segment": "Segmento",
        },
    )
    fig.update_layout(
        title="Segmento (mujer/hombre/niño) por cluster de estilo",
        margin=dict(t=60, l=40, r=20, b=40),
        legend_title="Segmento",
        height=400,
        autosize=False,
    )
    return dcc.Graph(figure=fig, config={'displayModeBar': False}, style={'height': '400px', 'width': '100%'})


def _cluster_formality_chart(df: pd.DataFrame):
    """Formalidad por cluster (casual/intermedio/formal)."""
    if "style_cluster" not in df.columns or "formalidad" not in df.columns:
        return html.Div("No hay información suficiente de formalidad/cluster.", className="text-muted")

    agg = (
        df.groupby(["style_cluster", "formalidad"])["id"]
        .count()
        .reset_index(name="num_prendas")
    )

    fig = px.bar(
        agg,
        x="style_cluster",
        y="num_prendas",
        color="formalidad",
        barmode="stack",
        labels={
            "style_cluster": "Cluster de estilo",
            "num_prendas": "Número de prendas",
            "formalidad": "Formalidad",
        },
    )
    fig.update_layout(
        title="Nivel de formalidad por cluster de estilo",
        margin=dict(t=60, l=40, r=20, b=40),
        legend_title="Formalidad",
        height=400,
        autosize=False,
    )
    return dcc.Graph(figure=fig, config={'displayModeBar': False}, style={'height': '400px', 'width': '100%'})


def _cluster_temporada_chart(df: pd.DataFrame):
    """Temporada (invierno/verano/neutra) por cluster."""
    if "style_cluster" not in df.columns or "temporada" not in df.columns:
        return html.Div("No hay información suficiente de temporada/cluster.", className="text-muted")

    agg = (
        df.groupby(["style_cluster", "temporada"])["id"]
        .count()
        .reset_index(name="num_prendas")
    )

    fig = px.bar(
        agg,
        x="style_cluster",
        y="num_prendas",
        color="temporada",
        barmode="stack",
        labels={
            "style_cluster": "Cluster de estilo",
            "num_prendas": "Número de prendas",
            "temporada": "Temporada",
        },
    )
    fig.update_layout(
        title="Temporada dominante por cluster de estilo",
        margin=dict(t=60, l=40, r=20, b=40),
        legend_title="Temporada",
        height=400,
        autosize=False,
    )
    return dcc.Graph(figure=fig, config={'displayModeBar': False}, style={'height': '400px', 'width': '100%'})


def _cluster_slot_chart(df: pd.DataFrame):
    """Distribución de tipos de prenda (slot) por cluster."""
    if "style_cluster" not in df.columns or "slot" not in df.columns:
        return html.Div("No hay información suficiente de slots/cluster.", className="text-muted")

    agg = (
        df.groupby(["style_cluster", "slot"])["id"]
        .count()
        .reset_index(name="num_prendas")
    )

    fig = px.bar(
        agg,
        x="style_cluster",
        y="num_prendas",
        color="slot",
        barmode="stack",
        labels={
            "style_cluster": "Cluster de estilo",
            "num_prendas": "Número de prendas",
            "slot": "Tipo de prenda",
        },
    )
    fig.update_layout(
        title="Tipo de prenda por cluster (top, bottom, dress, shoes…)",
        margin=dict(t=60, l=40, r=20, b=40),
        legend_title="Slot",
        height=450,
        autosize=False,
    )
    return dcc.Graph(figure=fig, config={'displayModeBar': False}, style={'height': '450px', 'width': '100%'})


def _cluster_examples(df: pd.DataFrame, max_per_cluster: int = 4):
    """Muestra algunas prendas ejemplo por cluster (solo texto para explicar el estilo)."""
    if "style_cluster" not in df.columns:
        return html.Div("No hay columna 'style_cluster' en el catálogo.", className="text-muted")

    children = []
    for cluster_id in sorted(df["style_cluster"].unique()):
        subset = df[df["style_cluster"] == cluster_id].head(max_per_cluster)

        items = []
        for _, row in subset.iterrows():
            nombre = str(row.get("nombre", "")).title()
            tipo = row.get("tipo", "")
            col = row.get("color_base", row.get("color", ""))
            form = row.get("formalidad", "")
            temp = row.get("temporada", "")

            items.append(
                html.Li(
                    f"{nombre} · {tipo} · color {col} · {form} · {temp}"
                )
            )

        if not items:
            continue

        children.append(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H6(f"Cluster {cluster_id}", className="mb-2"),
                            html.Ul(items, className="mb-0 small"),
                        ]
                    ),
                    className="h-100",
                ),
                md=6,
                lg=3,
                className="mb-3",
            )
        )

    if not children:
        return html.Div("No hay ejemplos para mostrar.", className="text-muted")

    return dbc.Row(children, className="mt-2")


# ========= layout principal para la página de catálogo =========

def build_catalog_layout(df: pd.DataFrame):
    """
    Construye el layout de la página 'Catálogo y estilos'
    a partir del DataFrame completo (con style_cluster).
    """
    if df is None or df.empty:
        return html.Div("No hay datos de catálogo disponibles.", className="text-muted")

    if "style_cluster" not in df.columns:
        return html.Div(
            "El catálogo no tiene todavía la columna 'style_cluster'. "
            "Ejecuta primero el script de clustering.",
            className="text-muted",
        )

    n_prendas = len(df)
    n_clusters = df["style_cluster"].nunique()

    header = dbc.Container(
        [
            html.H2("Catálogo y clusters de estilo", className="mb-2"),
            html.P(
                f"Catálogo de {n_prendas:,} prendas agrupadas automáticamente "
                f"en {n_clusters} clusters de estilo mediante K-Means "
                "(sobre color, formalidad, temporada, slot…).",
                className="text-muted",
            ),
        ],
        fluid=True,
        className="mb-4",
    )

    cluster_size = _cluster_size_chart(df)
    cluster_segment = _cluster_segment_chart(df)
    cluster_formality = _cluster_formality_chart(df)
    cluster_temporada = _cluster_temporada_chart(df)
    cluster_slot = _cluster_slot_chart(df)
    examples = _cluster_examples(df)

    body = dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(cluster_size, md=6),
                    dbc.Col(cluster_segment, md=6),
                ],
                className="mb-4",
            ),
            dbc.Row(
                [
                    dbc.Col(cluster_formality, md=6),
                    dbc.Col(cluster_temporada, md=6),
                ],
                className="mb-4",
            ),
            dbc.Row(
                [
                    dbc.Col(cluster_slot, md=12),
                ],
                className="mb-4",
            ),
            html.H4("Ejemplos de prendas por cluster", className="mb-2"),
            html.P(
                "Estos ejemplos te permiten interpretar cada cluster como un estilo "
                "dominante (más casual, más formal, invernal, veraniego, etc.).",
                className="text-muted",
            ),
            examples,
        ],
        fluid=True,
    )

    return html.Div([header, body])

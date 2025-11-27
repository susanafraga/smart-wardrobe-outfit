# src/catalog_graphics.py

from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np


# ========= helpers para análisis de clusters =========

def analyze_cluster_characteristics(df, cluster_id):
    """Analiza las características dominantes de un cluster."""
    cluster_data = df[df["style_cluster"] == cluster_id]
    
    if cluster_data.empty:
        return {}
    
    characteristics = {
        'size': len(cluster_data),
        'formalidad': {},
        'temporada': {},
        'color_base': {},
        'fabric_type': {},
        'nivel_abrigo_avg': cluster_data["nivel_abrigo"].mean(),
    }
    
    # Top 3 valores más comunes para cada característica
    for col in ['formalidad', 'temporada', 'color_base', 'fabric_type']:
        if col in cluster_data.columns:
            value_counts = cluster_data[col].value_counts().head(3)
            characteristics[col] = {
                val: (count, count / len(cluster_data) * 100)
                for val, count in value_counts.items()
            }
    
    return characteristics


def get_cluster_label(characteristics):
    """Genera una etiqueta descriptiva para el cluster."""
    if not characteristics:
        return "Sin datos"
    
    temporada = list(characteristics.get('temporada', {}).keys())
    formalidad = list(characteristics.get('formalidad', {}).keys())
    fabric = list(characteristics.get('fabric_type', {}).keys())
    
    parts = []
    if temporada:
        parts.append(temporada[0].title())
    if formalidad:
        parts.append(formalidad[0].title())
    if fabric and fabric[0] != 'unknown':
        parts.append(fabric[0].title())
    
    return " ".join(parts) if parts else "Estilo"


# ========= gráficos mejorados =========

def _cluster_size_chart(df: pd.DataFrame):
    """Número de prendas por cluster con etiquetas descriptivas."""
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
    counts.columns = ["style_cluster", "num_prendas"]
    
    # Añadir etiquetas descriptivas
    cluster_labels = []
    for cluster_id in counts["style_cluster"]:
        characteristics = analyze_cluster_characteristics(df, cluster_id)
        label = get_cluster_label(characteristics)
        cluster_labels.append(f"Cluster {cluster_id}: {label}")
    
    counts["cluster_label"] = cluster_labels

    fig = px.bar(
        counts,
        x="style_cluster",
        y="num_prendas",
        text="num_prendas",
        labels={
            "style_cluster": "Cluster",
            "num_prendas": "Número de prendas",
        },
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig.update_layout(
        title="Tamaño de cada cluster de estilo",
        xaxis=dict(
            tickmode='array',
            tickvals=counts["style_cluster"],
            ticktext=[f"C{int(c)}" for c in counts["style_cluster"]]
        ),
        margin=dict(t=60, l=40, r=20, b=40),
        height=400,
        autosize=False,
    )
    return dcc.Graph(figure=fig, config={'displayModeBar': False}, style={'height': '400px', 'width': '100%'})


def _cluster_profile_heatmap(df: pd.DataFrame):
    """Heatmap mostrando el perfil de características de cada cluster."""
    if "style_cluster" not in df.columns:
        return html.Div("No hay columna 'style_cluster' en el catálogo.", className="text-muted")
    
    # Preparar datos para el heatmap
    clusters = sorted(df["style_cluster"].unique())
    features = ['formalidad', 'temporada', 'color_base', 'fabric_type']
    
    # Calcular porcentaje de cada valor por cluster
    heatmap_data = []
    
    for cluster_id in clusters:
        cluster_data = df[df["style_cluster"] == cluster_id]
        row = {'cluster': f"Cluster {cluster_id}"}
        
        for feature in features:
            if feature in cluster_data.columns:
                # Obtener el valor más común
                most_common = cluster_data[feature].mode()
                if len(most_common) > 0:
                    value = most_common[0]
                    pct = (cluster_data[feature] == value).sum() / len(cluster_data) * 100
                    row[feature] = pct
                else:
                    row[feature] = 0
            else:
                row[feature] = 0
        
        heatmap_data.append(row)
    
    heatmap_df = pd.DataFrame(heatmap_data)
    heatmap_df = heatmap_df.set_index('cluster')
    
    fig = px.imshow(
        heatmap_df.T,
        labels=dict(x="Cluster", y="Característica", color="% Dominancia"),
        color_continuous_scale="Blues",
        aspect="auto",
        text_auto=".1f",
    )
    fig.update_layout(
        title="Perfil de características por cluster (% de prendas con valor dominante)",
        margin=dict(t=60, l=100, r=20, b=60),
        height=350,
        autosize=False,
    )
    return dcc.Graph(figure=fig, config={'displayModeBar': False}, style={'height': '350px', 'width': '100%'})


def _cluster_characteristics_radar(df: pd.DataFrame):
    """Gráfico radar mostrando el perfil de cada cluster."""
    if "style_cluster" not in df.columns:
        return html.Div("No hay columna 'style_cluster' en el catálogo.", className="text-muted")
    
    clusters = sorted(df["style_cluster"].unique())
    
    fig = go.Figure()
    
    # Normalizar características para el radar
    for cluster_id in clusters:
        cluster_data = df[df["style_cluster"] == cluster_id]
        
        # Calcular valores normalizados
        values = []
        categories = []
        
        # Formalidad (casual=1, intermedio=2, formal=3)
        if 'formalidad' in cluster_data.columns:
            formal_map = {'casual': 1, 'intermedio': 2, 'formal': 3}
            formal_mode = cluster_data['formalidad'].mode()[0] if len(cluster_data['formalidad'].mode()) > 0 else 'intermedio'
            values.append(formal_map.get(formal_mode, 2))
            categories.append('Formalidad')
        
        # Nivel de abrigo (ya es numérico 1-3)
        if 'nivel_abrigo' in cluster_data.columns:
            values.append(cluster_data['nivel_abrigo'].mean())
            categories.append('Abrigo')
        
        # Temporada (convertir a numérico: verano=1, primavera=2, neutra=2.5, otoño=2.5, invierno=3)
        if 'temporada' in cluster_data.columns:
            temp_map = {'verano': 1, 'primavera': 2, 'neutra': 2.5, 'otono': 2.5, 'invierno': 3}
            temp_mode = cluster_data['temporada'].mode()[0] if len(cluster_data['temporada'].mode()) > 0 else 'neutra'
            # Normalizar 'otono' a 'otono' (sin tilde por compatibilidad)
            if temp_mode == 'otoño':
                temp_mode = 'otono'
            values.append(temp_map.get(temp_mode, 2.5))
            categories.append('Temporada')
        
        # Color (neutros=1, colores fuertes=2)
        if 'color_base' in cluster_data.columns:
            neutral_colors = {'black', 'white', 'grey', 'gray', 'beige', 'brown', 'other'}
            color_mode = cluster_data['color_base'].mode()[0] if len(cluster_data['color_base'].mode()) > 0 else 'other'
            color_val = 1 if color_mode in neutral_colors else 2
            values.append(color_val)
            categories.append('Color')
        
        # Cerrar el círculo
        values.append(values[0])
        categories.append(categories[0])
        
        characteristics = analyze_cluster_characteristics(df, cluster_id)
        label = get_cluster_label(characteristics)
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=f"Cluster {cluster_id}: {label}",
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 3]
            )),
        showlegend=True,
        title="Perfil comparativo de clusters (radar)",
        margin=dict(t=60, l=20, r=20, b=40),
        height=500,
        autosize=False,
    )
    return dcc.Graph(figure=fig, config={'displayModeBar': False}, style={'height': '500px', 'width': '100%'})


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
            "style_cluster": "Cluster",
            "num_prendas": "Número de prendas",
            "formalidad": "Formalidad",
        },
        color_discrete_map={
            "casual": "#FF6B6B",
            "intermedio": "#4ECDC4",
            "formal": "#45B7D1",
        }
    )
    fig.update_layout(
        title="Distribución de formalidad por cluster",
        margin=dict(t=60, l=40, r=20, b=40),
        legend_title="Formalidad",
        height=400,
        autosize=False,
    )
    return dcc.Graph(figure=fig, config={'displayModeBar': False}, style={'height': '400px', 'width': '100%'})


def _cluster_temporada_chart(df: pd.DataFrame):
    """Temporada por cluster."""
    if "style_cluster" not in df.columns or "temporada" not in df.columns:
        return html.Div("No hay información suficiente de temporada/cluster.", className="text-muted")

    agg = (
        df.groupby(["style_cluster", "temporada"])["id"]
        .count()
        .reset_index(name="num_prendas")
    )

    # Ordenar temporadas lógicamente
    temp_order = ['invierno', 'otono', 'primavera', 'verano', 'neutra']
    # Normalizar 'otoño' a 'otono' si existe
    agg['temporada'] = agg['temporada'].str.replace('otoño', 'otono', regex=False)
    agg['temporada'] = pd.Categorical(agg['temporada'], categories=temp_order, ordered=True)
    agg = agg.sort_values(['style_cluster', 'temporada'])

    fig = px.bar(
        agg,
        x="style_cluster",
        y="num_prendas",
        color="temporada",
        barmode="stack",
        labels={
            "style_cluster": "Cluster",
            "num_prendas": "Número de prendas",
            "temporada": "Temporada",
        },
        color_discrete_map={
            "invierno": "#2C3E50",
            "otono": "#E67E22",
            "primavera": "#27AE60",
            "verano": "#3498DB",
            "neutra": "#95A5A6",
        }
    )
    fig.update_layout(
        title="Distribución de temporada por cluster",
        margin=dict(t=60, l=40, r=20, b=40),
        legend_title="Temporada",
        height=400,
        autosize=False,
    )
    return dcc.Graph(figure=fig, config={'displayModeBar': False}, style={'height': '400px', 'width': '100%'})


def _cluster_color_chart(df: pd.DataFrame):
    """Colores dominantes por cluster."""
    if "style_cluster" not in df.columns or "color_base" not in df.columns:
        return html.Div("No hay información suficiente de color/cluster.", className="text-muted")

    # Top 5 colores por cluster
    cluster_colors = []
    for cluster_id in sorted(df["style_cluster"].unique()):
        cluster_data = df[df["style_cluster"] == cluster_id]
        top_colors = cluster_data["color_base"].value_counts().head(5)
        
        for color, count in top_colors.items():
            cluster_colors.append({
                'cluster': f"Cluster {cluster_id}",
                'color': color,
                'count': count,
                'pct': count / len(cluster_data) * 100
            })
    
    colors_df = pd.DataFrame(cluster_colors)
    
    fig = px.bar(
        colors_df,
        x="cluster",
        y="pct",
        color="color",
        labels={
            "cluster": "Cluster",
            "pct": "% de prendas",
            "color": "Color",
        },
        title="Top 5 colores por cluster (% de prendas)",
    )
    fig.update_layout(
        margin=dict(t=60, l=40, r=20, b=40),
        legend_title="Color",
        height=400,
        autosize=False,
    )
    return dcc.Graph(figure=fig, config={'displayModeBar': False}, style={'height': '400px', 'width': '100%'})


def _cluster_fabric_chart(df: pd.DataFrame):
    """Tejidos dominantes por cluster."""
    if "style_cluster" not in df.columns or "fabric_type" not in df.columns:
        return html.Div("No hay información suficiente de tejido/cluster.", className="text-muted")

    # Top 5 tejidos por cluster
    cluster_fabrics = []
    for cluster_id in sorted(df["style_cluster"].unique()):
        cluster_data = df[df["style_cluster"] == cluster_id]
        top_fabrics = cluster_data["fabric_type"].value_counts().head(5)
        
        for fabric, count in top_fabrics.items():
            if fabric != 'unknown':  # Filtrar unknown
                cluster_fabrics.append({
                    'cluster': f"Cluster {cluster_id}",
                    'fabric': fabric,
                    'count': count,
                    'pct': count / len(cluster_data) * 100
                })
    
    fabrics_df = pd.DataFrame(cluster_fabrics)
    
    if fabrics_df.empty:
        return html.Div("No hay información de tejidos suficiente.", className="text-muted")
    
    fig = px.bar(
        fabrics_df,
        x="cluster",
        y="pct",
        color="fabric",
        labels={
            "cluster": "Cluster",
            "pct": "% de prendas",
            "fabric": "Tejido",
        },
        title="Top 5 tejidos por cluster (% de prendas)",
    )
    fig.update_layout(
        margin=dict(t=60, l=40, r=20, b=40),
        legend_title="Tejido",
        height=400,
        autosize=False,
    )
    return dcc.Graph(figure=fig, config={'displayModeBar': False}, style={'height': '400px', 'width': '100%'})


def _cluster_summary_cards(df: pd.DataFrame):
    """Tarjetas resumen con características dominantes de cada cluster."""
    if "style_cluster" not in df.columns:
        return html.Div("No hay columna 'style_cluster' en el catálogo.", className="text-muted")
    
    clusters = sorted(df["style_cluster"].unique())
    cards = []
    
    for cluster_id in clusters:
        characteristics = analyze_cluster_characteristics(df, cluster_id)
        label = get_cluster_label(characteristics)
        
        # Obtener valores dominantes
        formalidad = list(characteristics.get('formalidad', {}).keys())
        temporada = list(characteristics.get('temporada', {}).keys())
        color = list(characteristics.get('color_base', {}).keys())
        fabric = list(characteristics.get('fabric_type', {}).keys())
        
        card_content = [
            html.H5(f"Cluster {cluster_id}: {label}", className="mb-3"),
            html.P(f"{characteristics['size']:,} prendas", className="mb-2 fw-bold"),
        ]
        
        if temporada:
            temp_pct = characteristics['temporada'][temporada[0]][1]
            card_content.append(html.P(f"Temporada: {temporada[0].title()} ({temp_pct:.1f}%)", className="mb-1 small"))
        
        if formalidad:
            form_pct = characteristics['formalidad'][formalidad[0]][1]
            card_content.append(html.P(f"Formalidad: {formalidad[0].title()} ({form_pct:.1f}%)", className="mb-1 small"))
        
        if color:
            color_pct = characteristics['color_base'][color[0]][1]
            card_content.append(html.P(f"Color: {color[0].title()} ({color_pct:.1f}%)", className="mb-1 small"))
        
        if fabric and fabric[0] != 'unknown':
            fabric_pct = characteristics['fabric_type'][fabric[0]][1]
            card_content.append(html.P(f"Tejido: {fabric[0].title()} ({fabric_pct:.1f}%)", className="mb-1 small"))
        
        abrigo_avg = characteristics.get('nivel_abrigo_avg', 2)
        abrigo_text = "Ligero" if abrigo_avg < 1.5 else ("Medio" if abrigo_avg < 2.5 else "Abrigado")
        card_content.append(html.P(f"Abrigo: {abrigo_text} ({abrigo_avg:.2f})", className="mb-0 small"))
        
        cards.append(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(card_content),
                    className="h-100",
                ),
                md=4,
                lg=4,
                className="mb-3",
            )
        )
    
    # Dividir en dos filas: 3 arriba, 2 abajo (centrados)
    row1_cards = cards[:3]
    row2_cards = cards[3:]
    
    # Para la segunda fila, centrar los 2 clusters
    if len(row2_cards) == 2:
        # Crear una nueva fila con offset para centrar (2 cards de 4 columnas = 8, offset de 2 a cada lado)
        row2_centered = dbc.Row(
            [
                dbc.Col(width=2),  # Offset izquierdo
                row2_cards[0],
                row2_cards[1],
                dbc.Col(width=2),  # Offset derecho
            ],
            className="mt-2 g-3",
        )
    else:
        row2_centered = dbc.Row(row2_cards, className="mt-2 g-3 justify-content-center") if row2_cards else None
    
    return html.Div([
        dbc.Row(row1_cards, className="mt-2 g-3 justify-content-center"),
        row2_centered
    ])


# ========= layout principal =========

def build_catalog_layout(df: pd.DataFrame):
    """
    Construye el layout de la página 'Catálogo'
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
            html.H2("Catálogo", className="mb-2"),
            html.P(
                f"Catálogo de {n_prendas:,} prendas agrupadas automáticamente "
                f"en {n_clusters} clusters de estilo mediante K-Means "
                "(basado en formalidad, temporada, color, tejido y nivel de abrigo).",
                className="text-muted",
            ),
        ],
        fluid=True,
        className="mb-4",
    )

    # Gráficos mejorados
    cluster_size = _cluster_size_chart(df)
    cluster_profile = _cluster_profile_heatmap(df)
    cluster_radar = _cluster_characteristics_radar(df)
    cluster_formality = _cluster_formality_chart(df)
    cluster_temporada = _cluster_temporada_chart(df)
    cluster_color = _cluster_color_chart(df)
    cluster_fabric = _cluster_fabric_chart(df)
    cluster_cards = _cluster_summary_cards(df)

    body = dbc.Container(
        [
            html.H4("Resumen de clusters", className="mb-3 mt-4"),
            cluster_cards,
            
            html.H4("Análisis de características", className="mb-3 mt-5"),
            html.P(
                "Los siguientes gráficos muestran cómo se distribuyen las características "
                "de estilo en cada cluster, permitiendo entender qué define cada grupo.",
                className="text-muted mb-4",
            ),
            
            dbc.Row(
                [
                    dbc.Col(cluster_size, md=6),
                    dbc.Col(cluster_profile, md=6),
                ],
                className="mb-4",
            ),
            
            dbc.Row(
                [
                    dbc.Col(cluster_radar, md=12),
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
                    dbc.Col(cluster_color, md=6),
                    dbc.Col(cluster_fabric, md=6),
                ],
                className="mb-4",
            ),
        ],
        fluid=True,
    )

    return html.Div([header, body])

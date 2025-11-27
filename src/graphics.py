# src/graphics.py

from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

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
                "style_cluster": item.get("style_cluster", None),
                "fabric_type": item.get("fabric_type", ""),
            }
            rows.append(row)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def _build_outfit_selection_detailed(rec_data: dict):
    """Gráfico detallado de selección de outfits con pie charts de clusters."""
    if not rec_data or "all_outfits" not in rec_data:
        return html.Div("No hay información de selección.", className="text-muted")
    
    all_outfits = rec_data.get("all_outfits", [])
    selected_outfits = rec_data.get("outfits", [])
    
    if not all_outfits:
        return html.Div("No hay datos disponibles.", className="text-muted")
    
    # Obtener scores de los seleccionados
    selected_scores = {o.get("score", 0) for o in selected_outfits}
    
    # Preparar datos con información de tipo y clusters
    outfits_data = []
    cluster_data_list = []  # Lista para mantener el orden
    
    for idx, outfit in enumerate(all_outfits[:20]):  # Top 20
        score = outfit.get("score", 0)
        is_selected = score in selected_scores
        
        # Determinar tipo de outfit basado en prendas
        items = outfit.get("items", [])
        slots = [item.get("slot", "") for item in items]
        
        if "dress" in slots:
            outfit_type = "Vestido"
        elif "top" in slots and "bottom" in slots:
            outfit_type = "Conjunto"
        else:
            outfit_type = "Otro"
        
        # Analizar clusters en este outfit
        clusters = {}
        for item in items:
            cluster_id = item.get("style_cluster")
            if cluster_id is not None:
                cluster_key = f"Cluster {int(cluster_id)}"
                clusters[cluster_key] = clusters.get(cluster_key, 0) + 1
        
        outfits_data.append({
            "score": score,
            "selected": "Sí" if is_selected else "No",
            "type": outfit_type,
            "num_items": len(items),
            "original_idx": idx,  # Guardar índice original
        })
        
        # Guardar datos de clusters en lista (mantener orden)
        cluster_data_list.append(clusters)
    
    outfits_df = pd.DataFrame(outfits_data)
    
    # Ordenar por score descendente
    outfits_df = outfits_df.sort_values("score", ascending=False).reset_index(drop=True)
    outfits_df["rank"] = range(1, len(outfits_df) + 1)
    
    # Mapear clusters al ranking correcto usando el índice original
    cluster_data_sorted = {}
    for rank, row in outfits_df.iterrows():
        original_idx = row["original_idx"]
        cluster_data_sorted[rank] = cluster_data_list[original_idx] if original_idx < len(cluster_data_list) else {}
    
    # Calcular min y max para el eje Y (con margen para ver diferencias)
    score_min = outfits_df["score"].min()
    score_max = outfits_df["score"].max()
    score_range = score_max - score_min
    
    # Ajustar el rango del eje Y para ver mejor las diferencias
    y_min = max(0, score_min - (score_range * 0.1))
    y_max = score_max + (score_range * 0.1)
    
    # Crear gráfico agrupado por tipo
    fig = go.Figure()
    
    tipos = outfits_df["type"].unique()
    colors_map = {"Vestido": "#9B59B6", "Conjunto": "#3498DB", "Otro": "#95A5A6"}
    
    for tipo in tipos:
        tipo_subset = outfits_df[outfits_df["type"] == tipo]
        
        # Separar seleccionados y no seleccionados
        selected = tipo_subset[tipo_subset["selected"] == "Sí"]
        not_selected = tipo_subset[tipo_subset["selected"] == "No"]
        
        if len(not_selected) > 0:
            fig.add_trace(go.Bar(
                name=f"{tipo} (No seleccionado)",
                x=not_selected["rank"],
                y=not_selected["score"],
                marker_color=colors_map.get(tipo, "#95A5A6"),
                marker_opacity=0.5,
                text=not_selected["score"].round(3).astype(str),
                textposition="outside",
                hovertemplate="<b>Ranking %{x}</b><br>Tipo: %{fullData.name}<br>Score: %{y:.3f}<br><extra></extra>",
            ))
        
        if len(selected) > 0:
            fig.add_trace(go.Bar(
                name=f"{tipo} (Seleccionado)",
                x=selected["rank"],
                y=selected["score"],
                marker_color=colors_map.get(tipo, "#27AE60"),
                marker_line=dict(color="#27AE60", width=3),
                text=selected["score"].round(3).astype(str),
                textposition="outside",
                hovertemplate="<b>Ranking %{x}</b><br>Tipo: %{fullData.name}<br>Score: %{y:.3f}<br>✓ SELECCIONADO<extra></extra>",
            ))
    
    fig.update_layout(
        title="Top 20 outfits evaluados (ordenados por score, agrupados por tipo)",
        xaxis_title="Ranking (ordenado por score)",
        yaxis_title="Score",
        margin=dict(t=60, l=40, r=200, b=40),  # Más margen derecho para la leyenda
        height=450,
        autosize=True,
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),  # Leyenda a la derecha
        barmode="group",
        yaxis=dict(range=[y_min, y_max]),
    )
    
    # Crear un solo pie chart con todos los clusters de los 20 outfits combinados
    all_clusters_combined = {}
    
    # Combinar todos los clusters de los 20 outfits
    for rank in range(1, 21):
        clusters = cluster_data_sorted.get(rank, {})
        for cluster_key, count in clusters.items():
            all_clusters_combined[cluster_key] = all_clusters_combined.get(cluster_key, 0) + count
    
    # Crear pie chart único con todos los clusters
    if not all_clusters_combined:
        fig_pie = go.Figure()
        fig_pie.add_annotation(
            text="Sin datos de clusters",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="gray"),
        )
        fig_pie.update_layout(
            title="Distribución de clusters en los 20 outfits",
            margin=dict(t=60, l=20, r=20, b=20),
            height=400,
            autosize=True,
            showlegend=False,
        )
    else:
        labels = list(all_clusters_combined.keys())
        values = list(all_clusters_combined.values())
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            textinfo='label+percent',
            hovertemplate="<b>%{label}</b><br>Prendas: %{value}<br>Porcentaje: %{percent}<extra></extra>",
            marker=dict(colors=px.colors.qualitative.Set3[:len(labels)]),
        )])
        
        fig_pie.update_layout(
            title="Distribución de clusters en los 20 outfits (todas las prendas combinadas)",
            margin=dict(t=60, l=20, r=20, b=20),
            height=400,
            autosize=True,
            showlegend=True,
        )
    
    # Explicación mejorada del score
    explanation = html.Div(
        [
            html.P(
                [
                    html.Strong("Explicación del score: "),
                    "El score combina múltiples factores: "
                ],
                className="text-muted small mt-3 mb-1",
                style={"fontSize": "13px", "lineHeight": "1.6"},
            ),
            html.Ul(
                [
                    html.Li("Adecuación al clima: temperatura y condiciones meteorológicas", className="text-muted small", style={"fontSize": "12px"}),
                    html.Li("Coherencia de estilo: prendas del mismo cluster tienen mayor coherencia", className="text-muted small", style={"fontSize": "12px"}),
                    html.Li("Formalidad: adecuación al tipo de evento", className="text-muted small", style={"fontSize": "12px"}),
                    html.Li("Combinación de colores: armonía cromática entre prendas", className="text-muted small", style={"fontSize": "12px"}),
                    html.Li("Tejidos: compatibilidad y adecuación al evento", className="text-muted small", style={"fontSize": "12px"}),
                ],
                className="mb-2",
            ),
            html.P(
                "Un score más alto indica un outfit mejor evaluado. Los 3 outfits seleccionados (marcados en verde) "
                "son los que tienen el mejor balance entre todos estos factores.",
                className="text-muted small",
                style={"fontSize": "12px", "lineHeight": "1.6"},
            ),
        ],
        className="mb-3",
    )
    
    return html.Div([
        dbc.Row([
            dbc.Col(
                dcc.Graph(figure=fig, config={'displayModeBar': False}, style={'height': '450px', 'width': '100%'}),
                width=12,
                className="px-0",
            ),
        ], className="mb-4 g-0"),
        html.H6("Distribución de clusters en los 20 outfits", className="mt-4 mb-3"),
        dbc.Row([
            dbc.Col(
                dcc.Graph(figure=fig_pie, config={'displayModeBar': False}, style={'height': '400px', 'width': '100%'}),
                width=12,
                className="px-0",
            ),
        ], className="mb-3 g-0"),
        explanation,
    ])


def _build_color_analysis_improved(df: pd.DataFrame):
    """Análisis mejorado de colores: pie chart general + barras por outfit."""
    if df.empty:
        return html.Div("No hay datos suficientes.", className="text-muted")
    
    # Pie chart: distribución general de colores
    all_colors = df["color_base"].value_counts()
    if len(all_colors) == 0:
        return html.Div("No hay datos de colores.", className="text-muted")
    
    # Preparar datos para pie chart
    pie_data = []
    for color, count in all_colors.items():
        pie_data.append({
            "color": color.title() if color else "N/A",
            "count": count,
        })
    
    pie_df = pd.DataFrame(pie_data)
    
    # Crear pie chart
    fig_pie = go.Figure(data=[go.Pie(
        labels=pie_df["color"],
        values=pie_df["count"],
        hole=0.4,
        textinfo='label+percent',
        hovertemplate="<b>%{label}</b><br>Cantidad: %{value}<br>Porcentaje: %{percent}<extra></extra>",
    )])
    
    fig_pie.update_layout(
        title="Distribución general de colores en todos los outfits",
        margin=dict(t=60, l=20, r=20, b=20),
        height=400,
        autosize=False,
        showlegend=True,
    )
    
    # Gráfico de barras: colores por outfit
    color_data = []
    for outfit_idx in sorted(df["outfit_idx"].unique()):
        outfit_data = df[df["outfit_idx"] == outfit_idx]
        
        # Distribución de colores
        colores = outfit_data["color_base"].value_counts()
        
        for color, count in colores.items():
            color_data.append({
                "outfit": f"Outfit {outfit_idx}",
                "color": color.title() if color else "N/A",
                "count": count,
            })
    
    color_df = pd.DataFrame(color_data)
    
    # Crear gráfico de barras agrupadas
    fig_bars = go.Figure()
    
    colores_unicos = sorted(color_df["color"].unique())
    colors_palette = px.colors.qualitative.Set3[:len(colores_unicos)]
    
    for i, color in enumerate(colores_unicos):
        color_subset = color_df[color_df["color"] == color]
        
        fig_bars.add_trace(go.Bar(
            name=color,
            x=color_subset["outfit"],
            y=color_subset["count"],
            marker_color=colors_palette[i % len(colors_palette)],
            text=color_subset["count"],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>%{fullData.name}: %{y} prendas<extra></extra>",
        ))
    
    fig_bars.update_layout(
        title="Distribución de colores por outfit (número de prendas)",
        xaxis_title="Outfit",
        yaxis_title="Número de prendas",
        barmode="group",
        margin=dict(t=60, l=40, r=20, b=40),
        height=400,
        autosize=False,
        legend_title="Color",
    )
    
    return dbc.Row([
        dbc.Col(
            dcc.Graph(figure=fig_pie, config={'displayModeBar': False}, style={'height': '400px', 'width': '100%'}),
            md=6,
            style={'padding': '0 15px'},
        ),
        dbc.Col(
            dcc.Graph(figure=fig_bars, config={'displayModeBar': False}, style={'height': '400px', 'width': '100%'}),
            md=6,
            style={'padding': '0 15px'},
        ),
    ], className="mb-4", style={'margin': '0'})


def build_analytics_layout(rec_data: dict):
    """
    Construye el layout que se mostrará en la pestaña
    'Análisis (gráficos)' a partir de la recomendación.
    """
    if not rec_data:
        return html.Div("No hay recomendaciones todavía. Genera primero un outfit.")
    
    df = _outfits_to_df(rec_data)
    meta = rec_data.get("meta", {})
    city = meta.get("city", "Tu ciudad")
    used_date = meta.get("used_date", "")
    
    header = html.Div(
        [
            html.H4("Análisis de la recomendación", className="mb-2"),
            html.P(
                f"Ciudad: {city} · día usado: {used_date}",
                className="text-muted small",
            ),
        ],
        className="mb-4",
    )
    
    # Gráficos mejorados
    color_chart = _build_color_analysis_improved(df)
    selection_chart = _build_outfit_selection_detailed(rec_data)
    
    return html.Div(
        [
            header,
            html.H5("Análisis de colores", className="mb-3 mt-4"),
            html.P(
                "Distribución general de colores y distribución por outfit.",
                className="text-muted mb-4",
            ),
            color_chart,
            html.H5("Selección de outfits", className="mb-3 mt-5"),
            html.P(
                "Top 20 outfits evaluados, ordenados por score y agrupados por tipo de prenda. "
                "El pie chart muestra la distribución de clusters en todos los outfits combinados.",
                className="text-muted mb-4",
            ),
            selection_chart,
        ],
        style={'width': '100%', 'maxWidth': '100%'},
    )

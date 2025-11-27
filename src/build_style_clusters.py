#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_style_clusters.py

Añade una columna `style_cluster` a articles_final.csv utilizando
un clustering K-Means sobre variables de estilo.

Mejoras incluidas:
- NO incluye 'slot' (tipo de prenda) - queremos agrupar por ESTILO
- Análisis detallado de características dominantes por cluster
- Por defecto usa 5 clusters

Uso:
    python -m src.build_style_clusters \
        --input data/raw/hm/articles_final.csv \
        --output data/raw/hm/articles_final_clustered.csv \
        --n_clusters 5  # Por defecto: 5
"""

import argparse
import os
import sys

import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.cluster import KMeans
from sklearn.pipeline import Pipeline

# Configurar codificación UTF-8 para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def build_parser():
    p = argparse.ArgumentParser(
        description="Crea clusters de ESTILO (no por tipo de prenda) a partir de articles_final.csv."
    )
    p.add_argument(
        "--input",
        "-i",
        default="articles_final.csv",
        help="Ruta al CSV de entrada (articles_final.csv)",
    )
    p.add_argument(
        "--output",
        "-o",
        default="articles_final_clustered.csv",
        help="Ruta al CSV de salida con style_cluster",
    )
    p.add_argument(
        "--n_clusters",
        "-k",
        type=int,
        default=5,
        help="Número de clusters de estilo (K en K-Means). Por defecto: 5.",
    )
    return p


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
    """Genera una etiqueta descriptiva para el cluster basada en sus características."""
    if not characteristics:
        return "Cluster sin datos"
    
    # Obtener valores dominantes
    formalidad = list(characteristics.get('formalidad', {}).keys())
    temporada = list(characteristics.get('temporada', {}).keys())
    color = list(characteristics.get('color_base', {}).keys())
    fabric = list(characteristics.get('fabric_type', {}).keys())
    
    # Construir etiqueta
    parts = []
    
    if temporada:
        parts.append(temporada[0].title())
    
    if formalidad:
        parts.append(formalidad[0].title())
    
    if fabric and fabric[0] != 'unknown':
        parts.append(fabric[0].title())
    
    if not parts:
        parts.append("Estilo")
    
    return " ".join(parts)


def main():
    args = build_parser().parse_args()

    if not os.path.exists(args.input):
        raise FileNotFoundError(f"No encuentro el archivo de entrada: {args.input}")

    print(f"[*] Leyendo datos desde: {args.input}")
    df = pd.read_csv(args.input, low_memory=False)

    # ====== COLUMNAS PARA CLUSTERING DE ESTILO ======
    # IMPORTANTE: NO incluimos 'slot' porque queremos agrupar por ESTILO,
    # no por tipo de prenda. Un vestido casual veraniego debería estar
    # en el mismo cluster que una camiseta casual veraniega.
    feature_cols = [
        "formalidad",      # casual, intermedio, formal
        "temporada",       # invierno, otoño, primavera, verano, neutra
        "nivel_abrigo",    # 1=ligero, 2=medio, 3=abrigado
        "color_base",      # black, white, blue, etc.
        "fabric_type",     # cotton, wool, linen, etc.
        # NO incluimos:
        # - "slot": tipo de prenda - NO queremos agrupar por esto
        # - "desc_length": longitud de descripción - no es relevante para estilo
    ]

    for c in feature_cols:
        if c not in df.columns:
            raise ValueError(f"Falta la columna '{c}' en el CSV de entrada.")

    X = df[feature_cols].copy()

    # ====== relleno de NaN con valores razonables ======
    # numéricas
    X["nivel_abrigo"] = X["nivel_abrigo"].fillna(2)

    # categóricas
    X["formalidad"] = X["formalidad"].fillna("intermedio").astype(str)
    X["temporada"] = X["temporada"].fillna("neutra").astype(str)
    X["color_base"] = X["color_base"].fillna("other").astype(str)
    X["fabric_type"] = X["fabric_type"].fillna("unknown").astype(str)

    numeric_features = ["nivel_abrigo"]
    categorical_features = ["formalidad", "temporada", "color_base", "fabric_type"]

    # ====== Pipeline de preprocesamiento y clustering ======
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ]
    )

    kmeans = KMeans(
        n_clusters=args.n_clusters,
        random_state=42,
        n_init=10,  # Más inicializaciones para mejor resultado
        max_iter=300,
    )

    model = Pipeline(
        steps=[
            ("preprocess", preprocessor),
            ("kmeans", kmeans),
        ]
    )

    print(f"[*] Entrenando K-Means con {args.n_clusters} clusters...")
    print(f"   Features: {', '.join(feature_cols)}")
    clusters = model.fit_predict(X)

    # ====== Evaluación de calidad ======
    inertia = model.named_steps['kmeans'].inertia_
    
    print(f"\n[*] Calidad del clustering:")
    print(f"   Inertia: {inertia:.2f} (suma de distancias al centroide, mas bajo = mejor)")

    df["style_cluster"] = clusters

    # ====== Análisis de clusters ======
    print(f"\n[*] Distribucion de prendas por cluster de estilo:")
    counts = df["style_cluster"].value_counts().sort_index()
    for c, n in counts.items():
        pct = (n / len(df)) * 100
        print(f"  - Cluster {c}: {n:,} prendas ({pct:.1f}%)")

    # ====== Características dominantes por cluster ======
    print(f"\n[*] Caracteristicas dominantes por cluster:")
    cluster_labels = {}
    for cluster_id in sorted(df["style_cluster"].unique()):
        characteristics = analyze_cluster_characteristics(df, cluster_id)
        label = get_cluster_label(characteristics)
        cluster_labels[cluster_id] = label
        
        print(f"\n  Cluster {cluster_id} - {label} ({characteristics['size']:,} prendas):")
        
        if characteristics.get('formalidad'):
            top_form = list(characteristics['formalidad'].keys())[0]
            form_pct = characteristics['formalidad'][top_form][1]
            print(f"    Formalidad: {top_form} ({form_pct:.1f}%)")
        
        if characteristics.get('temporada'):
            top_temp = list(characteristics['temporada'].keys())[0]
            temp_pct = characteristics['temporada'][top_temp][1]
            print(f"    Temporada: {top_temp} ({temp_pct:.1f}%)")
        
        if characteristics.get('color_base'):
            top_color = list(characteristics['color_base'].keys())[0]
            color_pct = characteristics['color_base'][top_color][1]
            print(f"    Color: {top_color} ({color_pct:.1f}%)")
        
        if characteristics.get('fabric_type'):
            top_fabric = list(characteristics['fabric_type'].keys())[0]
            fabric_pct = characteristics['fabric_type'][top_fabric][1]
            print(f"    Tejido: {top_fabric} ({fabric_pct:.1f}%)")
        
        abrigo_avg = characteristics.get('nivel_abrigo_avg', 2)
        print(f"    Nivel abrigo promedio: {abrigo_avg:.2f}")

    # Guardar
    os.makedirs(os.path.dirname(args.output), exist_ok=True) if os.path.dirname(args.output) else None
    df.to_csv(args.output, index=False, encoding="utf-8")

    print(f"\n[OK] CSV con style_cluster generado")
    print(f"   Ruta salida: {args.output}")
    print(f"   Clusters: {args.n_clusters}")


if __name__ == "__main__":
    main()

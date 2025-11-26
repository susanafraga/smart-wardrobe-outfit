#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_style_clusters.py

Añade una columna `style_cluster` a articles_final.csv utilizando
un clustering K-Means sobre variables de estilo.

Uso:
    python -m src.build_style_clusters \
        --input data/raw/hm/articles_final.csv \
        --output data/raw/hm/articles_final_clustered.csv \
        --n_clusters 4
"""

import argparse
import os

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.cluster import KMeans
from sklearn.pipeline import Pipeline


def build_parser():
    p = argparse.ArgumentParser(
        description="Crea clusters de estilo (style_cluster) a partir de articles_final.csv."
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
        default=4,
        help="Número de clusters de estilo (K en K-Means). Por defecto: 4.",
    )
    return p


def main():
    args = build_parser().parse_args()

    if not os.path.exists(args.input):
        raise FileNotFoundError(f"No encuentro el archivo de entrada: {args.input}")

    print(f"📥 Leyendo datos desde: {args.input}")
    df = pd.read_csv(args.input)

    # ====== columnas a usar para el clustering ======
    feature_cols = [
        "slot",
        "formalidad",
        "temporada",
        "nivel_abrigo",
        "color_base",
        "fabric_type",
        "desc_length",
    ]

    for c in feature_cols:
        if c not in df.columns:
            raise ValueError(f"Falta la columna '{c}' en el CSV de entrada.")

    X = df[feature_cols].copy()

    # ====== relleno de NaN con valores razonables ======
    # numéricas
    X["nivel_abrigo"] = X["nivel_abrigo"].fillna(2)
    X["desc_length"] = X["desc_length"].fillna(X["desc_length"].median())

    # categóricas
    X["slot"] = X["slot"].fillna("other").astype(str)
    X["formalidad"] = X["formalidad"].fillna("intermedio").astype(str)
    X["temporada"] = X["temporada"].fillna("neutra").astype(str)
    X["color_base"] = X["color_base"].fillna("other").astype(str)
    X["fabric_type"] = X["fabric_type"].fillna("unknown").astype(str)

    numeric_features = ["nivel_abrigo", "desc_length"]
    categorical_features = ["slot", "formalidad", "temporada", "color_base", "fabric_type"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ]
    )

    kmeans = KMeans(
        n_clusters=args.n_clusters,
        random_state=42,
        n_init="auto",   # para evitar warnings en versiones nuevas de sklearn
    )

    model = Pipeline(
        steps=[
            ("preprocess", preprocessor),
            ("kmeans", kmeans),
        ]
    )

    print("🔧 Entrenando K-Means...")
    clusters = model.fit_predict(X)

    df["style_cluster"] = clusters

    # Pequeño resumen
    counts = df["style_cluster"].value_counts().sort_index()
    print("📊 Distribución de prendas por cluster de estilo:")
    for c, n in counts.items():
        print(f"  - Cluster {c}: {n} prendas")

    # Guardar
    os.makedirs(os.path.dirname(args.output), exist_ok=True) if os.path.dirname(args.output) else None
    df.to_csv(args.output, index=False, encoding="utf-8")

    print("✅ CSV con style_cluster generado")
    print(f"   Ruta salida: {args.output}")


if __name__ == "__main__":
    main()

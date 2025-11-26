# src/etl.py
import os
import pandas as pd


def _build_image_asset(article_id):
    """
    Construye la ruta relativa dentro de assets.

    Asumo que tus imágenes están en:
        assets/010/0108775015.jpg
    Es decir:
        - id numérico -> zfill(10) -> '0108775015'
        - carpeta = primeros 3 dígitos ('010')
        - fichero = id completo + '.jpg'

    Si las tienes en otra estructura, solo cambia este return.
    """
    s = str(int(article_id)).zfill(10)   # 10 dígitos: 0108775015
    folder = s[:3]
    filename = f"{s}.jpg"
    return f"{folder}/{filename}"        # assets/<folder>/<filename>


def load_articles(csv_path: str) -> pd.DataFrame:
    """
    Lee articles_final.csv (generado por prep_articles.py) y añade image_asset.
    NO recalcula ni segment ni slot (ya vienen en el csv).
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"No se encuentra el archivo: {csv_path}")

    df = pd.read_csv(csv_path)

    if "id" not in df.columns:
        raise ValueError("El CSV debe tener columna 'id'.")

    df["id"] = pd.to_numeric(df["id"], errors="coerce")
    df = df.dropna(subset=["id"]).reset_index(drop=True)

    df["image_asset"] = df["id"].apply(_build_image_asset)

    return df

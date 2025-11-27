#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prep_articles.py

Crea un articles_final.csv consistente a partir de articles.csv (H&M original).

Uso:
    python prep_articles.py --input data/raw/hm/articles.csv --output data/raw/hm/articles_final.csv
    (ajusta rutas según tu estructura real)
"""

import argparse
import os
import re
import sys
import pandas as pd

# Configurar codificación UTF-8 para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# ========= helpers texto =========

def norm_text(x: str) -> str:
    if not isinstance(x, str):
        return ""
    x = x.strip().lower()
    x = re.sub(r"\s+", " ", x)
    return x


def clean_desc(x: str) -> str:
    if not isinstance(x, str):
        return ""
    # mantengo letras, números y espacios; todo en minúsculas
    return re.sub(r"[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑüÜ ]", " ", x).strip().lower()


COLOR_MAP = {
    "black": "black",
    "white": "white",
    "grey": "grey",
    "gray": "grey",
    "blue": "blue",
    "green": "green",
    "red": "red",
    "yellow": "yellow",
    "brown": "brown",
    "pink": "pink",
    "purple": "purple",
    "beige": "beige",
    "orange": "orange",
    "turquoise": "blue",
    "gold": "yellow",
    "silver": "grey",
    "multi": "multi",
    "other": "other",
}


def color_base(perceived_master, colour_group):
    pm = norm_text(perceived_master)
    if pm in COLOR_MAP:
        return COLOR_MAP[pm]
    cg = norm_text(colour_group)
    for key in COLOR_MAP.keys():
        if key in cg:
            return COLOR_MAP[key]
    return "other"


# ========= macro_categoria / temporada / abrigo / formalidad =========

def macro_categoria(row):
    pg = row["product_group_name"]
    if pg == "Garment Upper body":
        return "topwear"
    if pg == "Garment Lower body":
        return "bottomwear"
    if pg == "Garment Full body":
        return "dresswear"
    if pg == "Shoes":
        return "shoes"
    if pg in ["Accessories", "Bags", "Cosmetic", "Fun", "Furniture",
              "Interior textile", "Stationery", "Garment and Shoe care", "Items"]:
        return "accessories"
    if pg in ["Underwear", "Underwear/nightwear", "Nightwear",
              "Socks & Tights", "Swimwear"]:
        return "underwear"
    return "other"


def temporada(row):
    """
    Determina la temporada usando una combinación de:
    - Tipo de tejido (fabric_type)
    - Palabras clave en descripción/nombre
    - Tipo de prenda
    
    Temporadas: invierno, otoño, primavera, verano, neutra
    """
    text = " ".join([
        str(row["product_type_name"]),
        str(row["garment_group_name"]),
        str(row["detail_desc"]),
    ]).lower()
    
    # Extraer el tipo de tejido inline (similar a extract_fabric)
    txt = " ".join([
        str(row.get("detail_desc", "")),
        str(row.get("product_type_name", "")),
        str(row.get("garment_group_name", "")),
    ]).lower()
    
    fabric_mapping = {
        "linen": "linen", "lino": "linen",
        "cotton": "cotton", "algod": "cotton",
        "wool": "wool", "cashmere": "wool",
        "velvet": "velvet", "velour": "velvet",
        "satin": "satin", "silk": "silk",
        "lace": "lace", "chiffon": "chiffon",
        "crepe": "crepe", "denim": "denim",
        "leather": "leather", "faux fur": "fur", "fur": "fur",
        "nylon": "nylon", "polyester": "polyester",
        "viscose": "viscose", "suede": "suede",
    }
    
    fabric = "unknown"
    for k, v in fabric_mapping.items():
        if k in txt:
            fabric = v
            break
    
    # ====== TEJIDOS POR TEMPORADA ======
    # Tejidos muy abrigosos = invierno/otoño
    tejidos_invierno = ["wool", "cashmere", "fur", "velvet", "suede", "leather"]
    # Tejidos ligeros = verano/primavera
    tejidos_verano = ["linen", "chiffon", "silk"]
    # Tejidos intermedios = primavera/otoño
    tejidos_intermedios = ["cotton", "denim", "viscose", "polyester", "nylon"]
    
    # ====== PALABRAS CLAVE POR TEMPORADA ======
    # Invierno: prendas muy abrigadas
    palabras_invierno = [
        "coat", "parka", "puffer", "down", "quilted", "thermal",
        "wool", "cashmere", "fleece", "fuzzy", "furry", "suede",
        "turtleneck", "mock neck", "high neck"
    ]
    
    # Otoño: prendas abrigadas pero no extremas
    palabras_otono = [
        "cardigan", "sweater", "knit", "jumper", "pullover",
        "blazer", "trench", "windbreaker", "jacket", "hoodie"
    ]
    
    # Primavera: prendas ligeras pero no extremas
    palabras_primavera = [
        "light", "breathable", "transitional", "layering",
        "long sleeve", "button down", "shirt"
    ]
    
    # Verano: prendas muy ligeras
    palabras_verano = [
        "shorts", "tank", "cropped", "swim", "bikini", "beach",
        "sleeveless", "strapless", "linen", "chiffon", "silk",
        "t-shirt", "tee", "camisole", "halter"
    ]
    
    # ====== LÓGICA DE DECISIÓN ======
    # Prioridad 1: Tejido muy específico
    if fabric in tejidos_invierno:
        # Si tiene palabras de otoño, puede ser otoño; si no, invierno
        if any(w in text for w in palabras_otono):
            return "otoño"
        return "invierno"
    
    if fabric in tejidos_verano:
        # Si tiene palabras de primavera, puede ser primavera; si no, verano
        if any(w in text for w in palabras_primavera):
            return "primavera"
        return "verano"
    
    # Prioridad 2: Palabras clave muy específicas
    if any(w in text for w in palabras_invierno):
        return "invierno"
    
    if any(w in text for w in palabras_verano):
        return "verano"
    
    if any(w in text for w in palabras_otono):
        # Si el tejido es intermedio, puede ser primavera u otoño
        if fabric in tejidos_intermedios:
            # Otoño si tiene palabras como "warm", "cozy", "knit"
            if any(w in text for w in ["warm", "cozy", "knit", "wool"]):
                return "otoño"
            return "primavera"
        return "otoño"
    
    if any(w in text for w in palabras_primavera):
        return "primavera"
    
    # Prioridad 3: Tejidos intermedios sin palabras clave claras
    if fabric in tejidos_intermedios:
        # Si tiene palabras de abrigo, otoño; si no, primavera
        if any(w in text for w in ["warm", "cozy", "thick", "heavy"]):
            return "otoño"
        if any(w in text for w in ["light", "breathable", "thin", "airy"]):
            return "primavera"
        # Por defecto, primavera para tejidos intermedios
        return "primavera"
    
    # Por defecto: neutra
    return "neutra"


def nivel_abrigo_from_temp(temp_cat):
    """Calcula nivel de abrigo basado en temporada."""
    mapping = {
        "invierno": 3,  # Muy abrigado
        "otoño": 2.5,   # Abrigado (redondeado a 3)
        "primavera": 1.5,  # Ligero (redondeado a 2)
        "verano": 1,    # Muy ligero
        "neutra": 2,    # Medio
    }
    abrigo = mapping.get(temp_cat, 2)
    # Redondear a entero (1, 2 o 3)
    return int(round(abrigo))


TOPWORDS_FORMAL = ["blazer", "suit", "dress", "shirt", "oxford", "chinos", "trench"]
TOPWORDS_CASUAL = ["t-shirt", "tee", "hoodie", "sweat", "jeans", "shorts", "cargo"]


def formalidad(row):
    text = " ".join([
        str(row["prod_name"]),
        str(row["product_type_name"]),
        str(row["garment_group_name"]),
    ]).lower()
    if any(w in text for w in TOPWORDS_FORMAL):
        return "formal"
    if any(w in text for w in TOPWORDS_CASUAL):
        return "casual"
    return "intermedio"


# ========= segment (mujer / hombre / niño) =========

def segment(row):
    ig = row["index_group_name"]
    if ig in ["Ladieswear", "Divided"]:
        return "women"
    if ig == "Menswear":
        return "men"
    if ig == "Baby/Children":
        return "kids"
    return "other"


# ========= slot (top / bottom / dress / outer / etc.) =========

SLOT_BY_PGROUP = {
    "Garment Upper body": "top",
    "Garment Lower body": "bottom",
    "Garment Full body":  "dress",
    "Shoes":              "shoes",

    "Accessories":            "accessory",
    "Bags":                   "accessory",
    "Cosmetic":               "accessory",
    "Fun":                    "accessory",
    "Furniture":              "accessory",
    "Interior textile":       "accessory",
    "Stationery":             "accessory",
    "Garment and Shoe care":  "accessory",
    "Items":                  "accessory",

    "Underwear":           "underwear",
    "Underwear/nightwear": "underwear",
    "Nightwear":           "underwear",
    "Socks & Tights":      "underwear",
    "Swimwear":            "underwear",

    "Unknown": "other",
}


def slot(row):
    """
    slot base a partir de product_group_name y refinamiento para outer
    usando garment_group_name + product_type_name.
    """
    pg = row["product_group_name"]
    base = SLOT_BY_PGROUP.get(pg, "other")

    # outer = abrigos (pueden venir como "Garment Upper body")
    if base == "top":
        gg = row["garment_group_name"]
        pt = row["product_type_name"]
        txt = f"{gg} {pt}".lower()
        if any(w in txt for w in [
            "outdoor", "jacket", "coat", "parka", "blazer",
            "trench", "anorak", "puffer", "windbreaker"
        ]):
            return "outer"
    return base


def extract_fabric(row):
    """Extrae un tipo de tejido/material simple desde la descripción.

    Busca palabras clave en `detail_desc` y en `product_type_name`.
    Devuelve un valor normalizado como 'linen', 'cotton', 'wool', etc.,
    o 'unknown' si no se detecta.
    """
    txt = " ".join([
        str(row.get("detail_desc", "")),
        str(row.get("product_type_name", "")),
        str(row.get("garment_group_name", "")),
    ])
    t = txt.lower()

    mapping = {
        "linen": "linen",
        "lino": "linen",
        "cotton": "cotton",
        "algod": "cotton",
        "wool": "wool",
        "cashmere": "wool",
        "velvet": "velvet",
        "velour": "velvet",
        "satin": "satin",
        "silk": "silk",
        "lace": "lace",
        "chiffon": "chiffon",
        "crepe": "crepe",
        "denim": "denim",
        "leather": "leather",
        "faux fur": "fur",
        "fur": "fur",
        "nylon": "nylon",
        "polyester": "polyester",
        "viscose": "viscose",
        "suede": "suede",
    }

    for k, v in mapping.items():
        if k in t:
            return v
    return "unknown"


# ========= pipeline principal =========

def build_parser():
    p = argparse.ArgumentParser(description="Crea articles_final.csv desde articles.csv (H&M).")
    p.add_argument("--input", "-i", default="articles.csv", help="Ruta al articles.csv original")
    p.add_argument("--output", "-o", default="articles_final.csv", help="Ruta al CSV de salida")
    return p


def main():
    args = build_parser().parse_args()

    if not os.path.exists(args.input):
        raise FileNotFoundError(f"No encuentro el archivo de entrada: {args.input}")

    # Leer CSV con low_memory=False para evitar warnings de tipos mixtos
    df = pd.read_csv(args.input, low_memory=False)

    # ---- df_final con columnas limpias ----
    df_final = pd.DataFrame()

    df_final["id"] = df["article_id"]
    df_final["nombre"] = df["prod_name"].map(norm_text)
    df_final["tipo"] = df["product_type_name"].map(norm_text)
    df_final["categoria"] = df["garment_group_name"].map(norm_text)
    df_final["color"] = df["colour_group_name"].map(norm_text)
    df_final["color_general"] = df["perceived_colour_master_name"].map(norm_text)
    df_final["color_base"] = [
        color_base(pm, cg)
        for pm, cg in zip(df["perceived_colour_master_name"], df["colour_group_name"])
    ]
    df_final["descripcion"] = df["detail_desc"].map(clean_desc)
    df_final["desc_length"] = df_final["descripcion"].apply(
        lambda x: len(x.split()) if isinstance(x, str) else 0
    )

    df_final["macro_categoria"] = df.apply(macro_categoria, axis=1)
    
    # IMPORTANTE: Extraer fabric_type ANTES de temporada porque temporada lo usa
    df_final["fabric_type"] = df.apply(extract_fabric, axis=1)
    
    # Ahora calcular temporada (que usa fabric_type)
    df_final["temporada"] = df.apply(temporada, axis=1)
    df_final["nivel_abrigo"] = df_final["temporada"].map(nivel_abrigo_from_temp)
    df_final["formalidad"] = df.apply(formalidad, axis=1)

    df_final["product_group_name"] = df["product_group_name"]
    df_final["department_name"] = df["department_name"]
    df_final["index_group_name"] = df["index_group_name"]
    df_final["section_name"] = df["section_name"]

    df_final["segment"] = df.apply(segment, axis=1)
    df_final["slot"] = df.apply(slot, axis=1)

    # fabric_type ya se extrajo antes (necesario para temporada)

    # quitar duplicados por id por seguridad
    df_final = df_final.drop_duplicates(subset="id").reset_index(drop=True)

    df_final.to_csv(args.output, index=False, encoding="utf-8")
    print("[OK] articles_final.csv generado")
    print(f"   Rutas: {args.output}")
    print(f"   Filas: {len(df_final):,}")
    print("   segment:", df_final["segment"].value_counts().to_dict())
    print("   slot:", df_final["slot"].value_counts().to_dict())


if __name__ == "__main__":
    main()

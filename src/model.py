# src/model.py
import pandas as pd
import numpy as np

FORMAL_MAP = {"casual": 1, "intermedio": 2, "formal": 3}
NEUTRAL_COLORS = {"black", "white", "grey", "gray", "beige", "brown", "other", "multi", "silver"}


# ========= scoring básicos =========

def _formal_score(objetivo, prenda):
    f_obj = FORMAL_MAP.get(objetivo, 2)
    f_pr = FORMAL_MAP.get(prenda, 2)
    diff = abs(f_obj - f_pr)
    # pequeño bonus si ambos son formal/ambos casual para reforzar la señal
    if f_obj == 3 and f_pr == 3:
        return 1.15
    if f_obj == 1 and f_pr == 1:
        return 1.08
    return 1.0 / (1.0 + diff)


def _target_nivel_abrigo(temp_c):
    if temp_c >= 24:
        return 1  # ropa ligera
    if temp_c >= 15:
        return 2
    return 3       # más abrigo


def _abrigo_score(temp_c, nivel_abrigo):
    if pd.isna(nivel_abrigo):
        return 0.7
    target = _target_nivel_abrigo(temp_c)
    diff = abs(int(nivel_abrigo) - target)
    return 1.0 / (1.0 + diff)


def _cluster_coherence_score(items):
    """
    Calcula un bonus de coherencia basado en si las prendas pertenecen al mismo cluster.
    Si todas las prendas están en el mismo cluster, hay un bonus significativo.
    Si hay 2 clusters diferentes, un bonus menor.
    Si hay 3+ clusters, sin bonus (o pequeño penalty).
    """
    if not items:
        return 1.0
    
    clusters = []
    for item in items:
        cluster = item.get("style_cluster")
        if cluster is not None and not pd.isna(cluster):
            clusters.append(int(cluster))
    
    if not clusters:
        return 1.0  # Sin información de cluster, sin bonus
    
    unique_clusters = len(set(clusters))
    total_items = len(clusters)
    
    if unique_clusters == 1:
        # Todas las prendas del mismo cluster -> máximo bonus
        return 1.20  # 20% bonus por coherencia de estilo
    elif unique_clusters == 2 and total_items >= 3:
        # 2 clusters en un outfit de 3+ prendas -> bonus moderado
        return 1.10  # 10% bonus
    elif unique_clusters == 2:
        # 2 clusters en outfit pequeño -> pequeño bonus
        return 1.05  # 5% bonus
    else:
        # 3+ clusters -> sin bonus (outfit muy mezclado)
        return 0.95  # Pequeño penalty por falta de coherencia


def _cluster_match_score(items, target_cluster=None):
    """
    Bonus adicional si las prendas coinciden con un cluster objetivo.
    Útil para cuando el usuario quiere un estilo específico.
    """
    if target_cluster is None:
        return 1.0
    
    if not items:
        return 1.0
    
    matches = 0
    for item in items:
        cluster = item.get("style_cluster")
        if cluster is not None and not pd.isna(cluster) and int(cluster) == int(target_cluster):
            matches += 1
    
    if matches == 0:
        return 1.0
    
    # Bonus proporcional al número de prendas que coinciden
    match_ratio = matches / len(items)
    return 1.0 + (match_ratio * 0.15)  # Hasta 15% bonus si todas coinciden


def _event_color_score(color, event_preferences):
    """
    Calcula un bonus/penalty basado en las preferencias de color del evento.
    """
    if not event_preferences:
        return 1.0
    
    color = str(color or "").strip().lower()
    if not color:
        return 1.0
    
    preferred_colors = event_preferences.get("preferred_colors", [])
    avoid_colors = event_preferences.get("avoid_colors", [])
    
    # Bonus si el color está en preferidos
    if preferred_colors and any(pref in color for pref in preferred_colors):
        return 1.15  # 15% bonus
    
    # Penalty si el color está en evitados
    if avoid_colors and any(avoid in color for avoid in avoid_colors):
        return 0.75  # 25% penalty
    
    return 1.0


def _event_fabric_score(fabric, event_preferences):
    """
    Calcula un bonus/penalty basado en las preferencias de tejido del evento.
    """
    if not event_preferences:
        return 1.0
    
    fabric = str(fabric or "").strip().lower()
    if not fabric:
        return 1.0
    
    preferred_fabrics = event_preferences.get("preferred_fabrics", [])
    avoid_fabrics = event_preferences.get("avoid_fabrics", [])
    
    # Bonus si el tejido está en preferidos
    if preferred_fabrics and any(pref in fabric for pref in preferred_fabrics):
        return 1.12  # 12% bonus
    
    # Penalty si el tejido está en evitados
    if avoid_fabrics and any(avoid in fabric for avoid in avoid_fabrics):
        return 0.80  # 20% penalty
    
    return 1.0


def _score_prenda(row, temp_c, formalidad_obj, event_preferences=None):
    """
    Score de una prenda teniendo en cuenta formalidad, nivel de abrigo,
    calidad de descripción y preferencias del evento.
    """
    f = _formal_score(formalidad_obj, row.get("formalidad", "intermedio"))
    a = _abrigo_score(temp_c, row.get("nivel_abrigo", 2))

    desc_len = row.get("desc_length", 5) or 5
    l = min(desc_len / 60.0, 1.0)

    base_score = f * a * (0.7 + 0.3 * l)

    # Bonus heurístico por tejido cuando buscamos formalidad
    desc = str(row.get("descripcion", "") or "").lower()
    formal_fabrics = ["satin", "silk", "lace", "velvet", "chiffon", "crepe"]
    if formalidad_obj == "formal" and any(w in desc for w in formal_fabrics):
        base_score *= 1.08

    # Pequeño penalty si no hay color base conocido (menos info)
    color = str(row.get("color_base", "") or "").strip().lower()
    if color == "":
        base_score *= 0.92
    
    # Aplicar preferencias del evento (color y tejido)
    if event_preferences:
        color_score = _event_color_score(color, event_preferences)
        fabric = str(row.get("fabric_type", "") or "").strip().lower()
        if not fabric:
            # Intentar extraer de descripción
            for k in ["linen", "lino", "satin", "silk", "lace", "chiffon", "wool", "denim", "velvet", "leather", "suede", "cotton", "polyester"]:
                if k in desc:
                    fabric = k if k != "lino" else "linen"
                    break
        
        fabric_score = _event_fabric_score(fabric, event_preferences)
        base_score *= color_score * fabric_score

    return float(base_score)


# ========= color conjunto =========

def _color_combo_score(items):
    colors = []
    for r in items:
        c = str(r.get("color_base", "") or "").lower()
        if c:
            colors.append(c)

    if not colors:
        return 1.0

    strong = [c for c in colors if c not in NEUTRAL_COLORS]
    strong_set = set(strong)

    if len(strong_set) == 0:
        return 1.05  # todo neutro
    if len(strong_set) == 1:
        return 1.1   # un color fuerte + neutros
    return 0.85      # demasiados colores fuertes


# ========= helpers de selección =========

def _sorted_candidates(df, slot, temp_c, formalidad_obj, target_cluster=None, event_preferences=None):
    """
    Candidatos ordenados por score, con bonus si pertenecen al cluster objetivo.
    """
    cand = df[df["slot"] == slot].copy()
    if cand.empty:
        return cand
    
    cand["__score__"] = cand.apply(
        lambda r: _score_prenda(r, temp_c, formalidad_obj, event_preferences), axis=1
    )
    
    # Bonus si hay cluster objetivo y la prenda pertenece a ese cluster
    if target_cluster is not None and "style_cluster" in cand.columns:
        cluster_mask = cand["style_cluster"].notna() & (cand["style_cluster"] == target_cluster)
        cand.loc[cluster_mask, "__score__"] *= 1.15  # 15% bonus por coincidencia de cluster
    
    return cand.sort_values("__score__", ascending=False)


# ========= construcción de outfits =========

def _build_dress_outfit(df, temp_c, formalidad_obj, used_ids, target_cluster=None, event_preferences=None):
    """
    Vestido + zapatos (sin abrigos ni accesorios).
    """
    dresses = _sorted_candidates(df, "dress", temp_c, formalidad_obj, target_cluster, event_preferences)
    shoes   = _sorted_candidates(df, "shoes", temp_c, formalidad_obj, target_cluster, event_preferences)

    dress = _pick_best_not_used(dresses, used_ids)
    shoe  = _pick_best_not_used(shoes, used_ids)

    if dress is None or shoe is None:
        return None

    items = [dress, shoe]
    used_ids.update([dress["id"], shoe["id"]])

    base = sum(_score_prenda(r, temp_c, formalidad_obj, event_preferences) for r in items) / len(items)
    color_factor = _color_combo_score(items)
    cluster_coherence = _cluster_coherence_score(items)
    cluster_match = _cluster_match_score(items, target_cluster)
    score = base * color_factor * cluster_coherence * cluster_match

    return {
        "type": "dress_outfit",
        "items": [r.to_dict() for r in items],
        "score": score,
    }


def _build_separates_outfit(df, temp_c, formalidad_obj, used_ids, target_cluster=None, event_preferences=None):
    """
    Parte de arriba + parte de abajo + zapatos (sin abrigos ni accesorios).
    """
    tops    = _sorted_candidates(df, "top", temp_c, formalidad_obj, target_cluster, event_preferences)
    bottoms = _sorted_candidates(df, "bottom", temp_c, formalidad_obj, target_cluster, event_preferences)
    shoes   = _sorted_candidates(df, "shoes", temp_c, formalidad_obj, target_cluster, event_preferences)

    top    = _pick_best_not_used(tops, used_ids)
    bottom = _pick_best_not_used(bottoms, used_ids)
    shoe   = _pick_best_not_used(shoes, used_ids)

    if top is None or bottom is None or shoe is None:
        return None

    items = [top, bottom, shoe]
    used_ids.update([top["id"], bottom["id"], shoe["id"]])

    base = sum(_score_prenda(r, temp_c, formalidad_obj, event_preferences) for r in items) / len(items)
    color_factor = _color_combo_score(items)
    cluster_coherence = _cluster_coherence_score(items)
    cluster_match = _cluster_match_score(items, target_cluster)
    score = base * color_factor * cluster_coherence * cluster_match

    return {
        "type": "separates_outfit",
        "items": [r.to_dict() for r in items],
        "score": score,
    }


def _pick_best_not_used(df_slot, used_ids):
    if df_slot.empty:
        return None
    for _, row in df_slot.iterrows():
        if row["id"] not in used_ids:
            return row
    return None


def _suggest_extras(df, slot, temp_c, formalidad_obj, rainy, max_items=3, target_cluster=None, event_preferences=None):
    """
    Sugerencias de abrigos o accesorios. No se meten dentro del outfit.
    """
    cand = df[df["slot"] == slot].copy()
    if cand.empty:
        return []

    cand["__score__"] = cand.apply(
        lambda r: _score_prenda(r, temp_c, formalidad_obj, event_preferences), axis=1
    )

    # pequeño bonus si llueve para prendas de invierno
    if rainy:
        cand["__score__"] = cand["__score__"] * cand["temporada"].apply(
            lambda t: 1.1 if str(t) == "invierno" else 1.0
        )
    
    # Bonus si hay cluster objetivo
    if target_cluster is not None and "style_cluster" in cand.columns:
        cluster_mask = cand["style_cluster"].notna() & (cand["style_cluster"] == target_cluster)
        cand.loc[cluster_mask, "__score__"] *= 1.10

    cand = cand.sort_values("__score__", ascending=False)
    top = cand.head(max_items)
    return [r._asdict() if hasattr(r, "_asdict") else r.to_dict() for _, r in top.iterrows()]


# ========= función principal =========

def recomendar_outfits(df, temp_c, formalidad_obj, rainy, n_outfits=3, target_cluster=None, event_preferences=None):
    """
    df: DataFrame ya filtrado por segmento (women/men/kids/any).
    target_cluster: (opcional) ID del cluster objetivo para generar outfits coherentes.

    Devuelve un dict con:
      - "outfits": lista de outfits (cada uno con type, items[], score)
      - "outers": lista de abrigos sugeridos (dicts de prenda)
      - "accessories": lista de accesorios sugeridos (dicts de prenda)
    """
    if df.empty:
        return {"outfits": [], "outers": [], "accessories": []}

    # core: sin lencería, solo slots de outfit principal
    core_slots = {"top", "bottom", "dress", "shoes"}
    df_core = df[df["slot"].isin(core_slots)].copy()
    if df_core.empty:
        return {"outfits": [], "outers": [], "accessories": []}

    # segmento dominante
    segment = "any"
    if "segment" in df_core.columns and not df_core["segment"].isna().all():
        try:
            segment = df_core["segment"].mode().iloc[0]
        except Exception:
            segment = "any"

    # En lugar de construir outfits de forma codiciosa, generamos todas las
    # combinaciones válidas y devolvemos las mejores por score. Esto permite
    # seleccionar los 3 mejores outfits entre todas las combinaciones posibles.
    outfits = []

    def _score_items_list(items):
        # items: lista de Series/rows
        # aplicamos penalizaciones/bonos según tejido y clima (rain/temp)
        per_item_scores = []
        for r in items:
            s = _score_prenda(r, temp_c, formalidad_obj, event_preferences)
            # obtener fabric desde fila (si existe) o desde descripcion
            fabric = None
            try:
                fabric = str(r.get("fabric_type", "") or "").lower()
            except Exception:
                fabric = ""
            if not fabric:
                # intentar heurística simple desde descripcion
                desc = str(r.get("descripcion", "") or "").lower()
                for k in ["linen", "lino", "satin", "silk", "lace", "chiffon", "wool", "denim", "velvet", "leather", "suede"]:
                    if k in desc:
                        fabric = k if k != "lino" else "linen"
                        break

            mult = 1.0
            # lluvia: penalizamos tejidos que se estropean o mojados incómodos
            rain_sensitive = {"linen", "silk", "suede", "chiffon"}
            if "is_rainy" in globals() and globals().get("is_rainy"):
                # Nota: no confiamos en globales; el valor real se pasa mediante el closure below
                pass
            # we'll apply the rainy/temp penalties using outer variables (passed below)
            per_item_scores.append((s, fabric))

        # compute average, applying weather-based multipliers
        adjusted_scores = []
        for s, fabric in per_item_scores:
            m = 1.0
            if rainy:
                if fabric in {"linen", "silk", "suede", "chiffon"}:
                    m *= 0.7
            if temp_c <= 10:
                if fabric in {"linen", "chiffon", "satin", "viscose"}:
                    m *= 0.75
            if temp_c >= 24:
                if fabric in {"wool", "velvet", "fur"}:
                    m *= 0.75
            adjusted_scores.append(s * m)

        base = sum(adjusted_scores) / len(adjusted_scores)
        color_factor = _color_combo_score(items)
        
        # NUEVO: Bonus por coherencia de cluster
        cluster_coherence = _cluster_coherence_score(items)
        cluster_match = _cluster_match_score(items, target_cluster)
        
        return base * color_factor * cluster_coherence * cluster_match

    # Prefiltrado por slot: limitamos candidatos a top-K por slot para evitar
    # explosión combinatoria en armarios grandes. Reducido a 30 para más rapidez.
    TOP_K = 30

    def _top_k(slot_name, k=TOP_K):
        cand = df_core[df_core["slot"] == slot_name].copy()
        if cand.empty:
            return cand
        cand["__score__"] = cand.apply(lambda r: _score_prenda(r, temp_c, formalidad_obj, event_preferences), axis=1)
        
        # Bonus si hay cluster objetivo
        if target_cluster is not None and "style_cluster" in cand.columns:
            cluster_mask = cand["style_cluster"].notna() & (cand["style_cluster"] == target_cluster)
            cand.loc[cluster_mask, "__score__"] *= 1.15
        
        return cand.sort_values("__score__", ascending=False).head(k)


    def _passes_heuristics(items, formalidad_obj, temp_c, rainy):
        """Heurísticas simples que descartan outfits que no tienen sentido.

        Reglas implementadas (conservadoras):
         - Si llueve y existe tejido sensible a la lluvia -> descartar.
         - Si es formal y hay denim en items -> descartar.
         - Si es formal: al menos la mitad de las prendas deben ser de tejidos "formales" (satin/silk/lace/velvet/crepe/chiffon).
         - Si hace frío (temp_c <= 10) y la media de nivel_abrigo de las prendas es demasiado baja -> descartar.
         - Si hay demasiados colores fuertes (más de 2) y es formal -> descartar.
        """
        fabrics = []
        niveles = []
        colors = []
        slots = []
        for it in items:
            fabrics.append(str(it.get("fabric_type", "") or "").lower())
            niveles.append(int(it.get("nivel_abrigo", 2) or 2))
            colors.append(str(it.get("color_base", "") or "").lower())
            slots.append(str(it.get("slot", "")))

        # regla lluvia
        if rainy:
            rain_sensitive = {"linen", "silk", "suede", "chiffon"}
            if any(f in rain_sensitive for f in fabrics if f):
                return False

        # regla formal + denim
        if formalidad_obj == "formal":
            if any(f == "denim" for f in fabrics if f):
                return False
            formal_fabrics = {"satin", "silk", "lace", "velvet", "crepe", "chiffon"}
            num_formal = sum(1 for f in fabrics if f in formal_fabrics)
            if num_formal < (len(items) / 2.0):
                return False

        # regla frio
        if temp_c <= 10:
            avg_nivel = sum(niveles) / len(niveles) if niveles else 2
            target = _target_nivel_abrigo(temp_c)
            if avg_nivel < target:
                return False

        # regla colores fuertes en formal
        if formalidad_obj == "formal":
            strong = [c for c in colors if c and c not in NEUTRAL_COLORS]
            if len(set(strong)) > 2:
                return False

        return True

    # Dress outfits (dress + shoes)
    dresses = _top_k("dress")
    shoes = _top_k("shoes")
    if not dresses.empty and not shoes.empty:
        for _, d in dresses.iterrows():
            for _, s in shoes.iterrows():
                if d["id"] == s["id"]:
                    continue
                items = [d, s]
                score = _score_items_list(items)
                outfits.append({
                    "type": "dress_outfit",
                    "items": [d.to_dict(), s.to_dict()],
                    "score": score,
                })

    # Separates outfits (top + bottom + shoes)
    tops = _top_k("top")
    bottoms = _top_k("bottom")
    if not tops.empty and not bottoms.empty and not shoes.empty:
        for _, t in tops.iterrows():
            for _, b in bottoms.iterrows():
                if t["id"] == b["id"]:
                    continue
                for _, s in shoes.iterrows():
                    if s["id"] in {t["id"], b["id"]}:
                        continue
                    items = [t, b, s]
                    score = _score_items_list(items)
                    outfits.append({
                        "type": "separates_outfit",
                        "items": [t.to_dict(), b.to_dict(), s.to_dict()],
                        "score": score,
                    })

    # Filtrar outfits según heurísticas; si el filtrado deja vacío, ignoramos el filtro.
    filtered = [o for o in outfits if _passes_heuristics(o.get("items", []), formalidad_obj, temp_c, rainy)]
    if filtered:
        outfits = filtered

    # Ordenar por score
    outfits = sorted(outfits, key=lambda x: x["score"], reverse=True)
    
    # Guardar todos los outfits evaluados para análisis (top 20)
    all_outfits_evaluated = outfits[:20] if len(outfits) > 20 else outfits

    # Selección de outfits disjuntos: elegimos greedily top-N sin compartir prendas
    selected = []
    used_ids = set()
    for o in outfits:
        ids = {it.get("id") for it in o.get("items", [])}
        if ids & used_ids:
            continue
        selected.append(o)
        used_ids.update(ids)
        if len(selected) >= n_outfits:
            break

    # Si no alcanzamos n_outfits (poca diversidad), rellenamos permitiendo reuse
    if len(selected) < n_outfits:
        for o in outfits:
            if o in selected:
                continue
            selected.append(o)
            if len(selected) >= n_outfits:
                break

    outfits = selected

    # Sugerencias de abrigos y accesorios (independientes)
    outers = _suggest_extras(df, "outer", temp_c, formalidad_obj, rainy, max_items=3, target_cluster=target_cluster, event_preferences=event_preferences)
    accessories = _suggest_extras(df, "accessory", temp_c, formalidad_obj, rainy, max_items=4, target_cluster=target_cluster, event_preferences=event_preferences)

    # Incluir los candidatos (top-K por slot) en el resultado para análisis
    try:
        candidates = {
            "dress": [r.to_dict() for _, r in dresses.iterrows()] if ("dresses" in locals() and not dresses.empty) else [],
            "top": [r.to_dict() for _, r in tops.iterrows()] if ("tops" in locals() and not tops.empty) else [],
            "bottom": [r.to_dict() for _, r in bottoms.iterrows()] if ("bottoms" in locals() and not bottoms.empty) else [],
            "shoes": [r.to_dict() for _, r in shoes.iterrows()] if ("shoes" in locals() and not shoes.empty) else [],
        }
    except Exception:
        candidates = {"dress": [], "top": [], "bottom": [], "shoes": []}

    return {
        "outfits": outfits[:n_outfits],
        "all_outfits": all_outfits_evaluated,  # Top 10 para análisis
        "outers": outers,
        "accessories": accessories,
        "candidates": candidates,
    }

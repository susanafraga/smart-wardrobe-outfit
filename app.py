from datetime import date

from dash import Dash, html, dcc, Input, Output, State, no_update
import dash_bootstrap_components as dbc

from src.etl import load_articles
from src.model import recomendar_outfits
from src.weather_api import get_weather
from src.graphics import build_analytics_layout   # gráficos
from src.catalog_graphics import build_catalog_layout  # <<--- NUEVO


# ======================= datos =======================

# ANTES: CSV_PATH = "data/raw/hm/articles_final.csv"
CSV_PATH = "data/raw/hm/articles_final_clustered.csv"  # <<--- NUEVO: mismo esquema + columna style_cluster
df = load_articles(CSV_PATH)

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],  # Tema minimalista estilo Zara
    suppress_callback_exceptions=True,
)
app.title = "Smart Wardrobe"


# ======================= helpers de modelo =======================

EVENT_OPTIONS = [
    {"label": "Plan casual (turismo, recados…)", "value": "casual_day"},
    {"label": "Trabajo / oficina",               "value": "work"},
    {"label": "Cena / evento semi-formal",       "value": "semi_formal"},
    {"label": "Boda / ceremonia formal",         "value": "wedding"},
    {"label": "Fiesta / noche",                  "value": "party"},
    {"label": "Plan deportivo / aire libre",     "value": "sport"},
]

SEGMENT_OPTIONS = [
    {"label": "Mujer", "value": "women"},
    {"label": "Hombre", "value": "men"},
    {"label": "Niño/a", "value": "kids"},
    {"label": "Cualquiera", "value": "any"},
]


def map_event_to_formality(event_type):
    mapping = {
        "casual_day": "casual",
        "work": "intermedio",
        "semi_formal": "intermedio",
        "wedding": "formal",
        "party": "intermedio",
        "sport": "casual",
    }
    return mapping.get(event_type, "intermedio")


def filter_by_profile(df_base, segment):
    if not segment or segment == "any":
        return df_base
    if "segment" not in df_base.columns:
        return df_base
    return df_base[df_base["segment"] == segment].copy()


# ======================= NAVBAR =======================

def navbar():
    return dbc.Navbar(
        dbc.Container(
            [
                html.A(
                    dbc.Row(
                        [
                            dbc.Col(
                                html.Div(
                                    "SMART WARDROBE",
                                    className="fw-bold navbar-brand",
                                )
                            ),
                        ],
                        align="center",
                        className="g-1",
                    ),
                    href="/",
                    style={"textDecoration": "none"},
                ),
                dbc.Nav(
                    [
                        dbc.NavLink("Inicio", href="/", active="exact"),
                        dbc.NavLink(
                            "Configurar outfit", href="/config", active="exact", className="ms-3"
                        ),
                        dbc.NavLink(  # <<--- NUEVO
                            "Catálogo y estilos", href="/catalog", active="exact", className="ms-3"
                        ),
                        dbc.NavItem(
                            dbc.NavLink(
                                [html.Span("Carrito", className="me-1"), html.Span("🛒")],
                                href="/cart",
                                className="ms-4 text-muted",
                            )
                        ),
                    ],
                    className="ms-auto",
                    navbar=True,
                ),
            ],
            fluid=True,
        ),
        color="light",
        className="mb-3 shadow-sm",
    )


# ======================= HOME (tu versión original) =======================

def layout_home():
    hero = dbc.Container(
        dbc.Row(
            [
                # Columna izquierda: texto
                dbc.Col(
                    [
                        html.Div(
                            "Smart wardrobe assistant",
                            className="home-kicker mb-2",
                        ),
                        html.H1(
                            "Descubre qué ponerte sin perder tiempo",
                            className="home-title mb-3",
                        ),
                        html.P(
                            "Combinamos previsión meteorológica y dress code del evento "
                            "con un catálogo real de prendas para proponerte tres outfits "
                            "listos para llevar.",
                            className="home-subtitle mb-4",
                        ),
                        dbc.Button(
                            "Configurar mi próximo evento",
                            href="/config",
                            color="dark",
                            size="lg",
                            className="home-cta-btn",
                        ),
                        html.Div(
                            "Versión demo",
                            className="home-note mt-3",
                        ),
                    ],
                    md=7,
                    className="mb-4 mb-md-0",
                ),
                # Columna derecha: tarjetita resumen
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H6("Ideal para", className="home-card-title mb-3"),
                                html.Ul(
                                    [
                                        html.Li("Bodas, cenas y eventos especiales."),
                                        html.Li("Entrevistas y días clave en la oficina."),
                                        html.Li("Escapadas de finde y viajes con maleta pequeña."),
                                    ],
                                    className="home-card-list",
                                ),
                                html.Hr(),
                                html.Div(
                                    [
                                        
                                        html.Span("En menos de 30 segundos tienes 3 propuestas completas."),
                                    ],
                                    className="home-card-foot",
                                ),
                            ]
                        ),
                        className="home-hero-card",
                    ),
                    md=5,
                ),
            ],
            className="align-items-center",
        ),
        fluid=True,
        className="home-hero",
    )

    features = dbc.Container(
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H5("Ahorra tiempo", className="feature-title mb-2"),
                                html.P(
                                    "Deja de probar combinaciones al azar. "
                                    "Te mostramos pocas opciones, pero muy filtradas "
                                    "en función de tu evento.",
                                    className="feature-text",
                                ),
                            ]
                        ),
                        className="feature-card h-100",
                    ),
                    md=4,
                    className="mb-3",
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H5("Clima y dress code", className="feature-title mb-2"),
                                html.P(
                                    "Integramos la previsión de temperatura y lluvia con el nivel "
                                    "de formalidad para ajustar tejidos, capas y calzado.",
                                    className="feature-text",
                                ),
                            ]
                        ),
                        className="feature-card h-100",
                    ),
                    md=4,
                    className="mb-3",
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H5("Pensado para e-commerce", className="feature-title mb-2"),
                                html.P(
                                    "Las prendas proceden de un catálogo real. "
                                    "La siguiente iteración sería conectar con compra directa "
                                    "en la web de la marca o trasladarlo a tu propio armario.",
                                    className="feature-text",
                                ),
                            ]
                        ),
                        className="feature-card h-100",
                    ),
                    md=4,
                    className="mb-3",
                ),
            ],
            className="g-3",
        ),
        fluid=True,
        className="mb-4",
    )

    steps = dbc.Container(
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("¿Cómo funciona?", className="feature-title mb-3"),
                    html.Ol(
                        [
                            html.Li("Indicas ciudad, fecha, tipo de evento y perfil (mujer, hombre, niño)."),
                            html.Li("Consultamos el tiempo y filtramos las prendas de la base de datos."),
                            html.Li("Generamos 3 outfits completos y sugerimos abrigos opcionales."),
                            html.Li("Eliges tu favorito y lo añades al carrito (demo)."),
                        ],
                        className="steps-list mb-0",
                    ),
                ]
            ),
            className="steps-card",
        ),
        fluid=True,
        className="mb-5",
    )

    return html.Div([hero, features, steps])


# ======================= CONFIGURAR OUTFIT =======================

def layout_config():
    controls = dbc.Card(
        dbc.CardBody(
            [
                html.H2("Configurar outfit", className="mb-3"),
                html.P(
                    "Cuéntanos dónde y cuándo es tu evento y te proponemos varias combinaciones.",
                    className="text-muted mb-4",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Label("Ciudad"),
                                dcc.Input(
                                    id="city",
                                    type="text",
                                    placeholder="Madrid, Barcelona…",
                                    value="Madrid",
                                    className="form-control",
                                ),
                            ],
                            md=3,
                        ),
                        dbc.Col(
                            [
                                dbc.Label("Fecha"),
                                dcc.DatePickerSingle(
                                    id="date",
                                    date=date.today(),
                                    display_format="DD/MM/YYYY",
                                    className="w-100",
                                ),
                            ],
                            md=3,
                        ),
                        dbc.Col(
                            [
                                dbc.Label("Tipo de evento"),
                                dcc.Dropdown(
                                    id="event_type",
                                    options=EVENT_OPTIONS,
                                    value="casual_day",
                                    clearable=False,
                                ),
                            ],
                            md=3,
                        ),
                        dbc.Col(
                            [
                                dbc.Label("Perfil"),
                                dcc.Dropdown(
                                    id="segment",
                                    options=SEGMENT_OPTIONS,
                                    value="women",
                                    clearable=False,
                                ),
                            ],
                            md=3,
                        ),
                    ],
                    className="mb-3",
                ),
                html.Div(
                    [
                        dbc.Button(
                            "RECOMENDAR OUTFIT",
                            id="btn",
                            color="dark",
                            className="mt-2 px-4",
                        ),
                        html.Div(
                            "La previsión meteorológica se obtiene automáticamente mediante la API de Open-Meteo.",
                            className="text-muted fst-italic mt-2",
                        ),
                    ],
                    className="text-center",
                ),
            ]
        ),
        className="shadow-sm card-controls mb-4",
    )

    resultados_tabs = html.Div(
        [
            dcc.Tabs(
                id="result-tabs",
                value="tab-outfits",
                children=[
                    dcc.Tab(label="Outfits recomendados", value="tab-outfits"),
                    dcc.Tab(label="Análisis (gráficos)", value="tab-analytics"),
                ],
                className="mb-3",
            ),
            dcc.Loading(
                id="loading-results",
                type="circle",
                children=html.Div(
                    [
                        html.Div(id="resultados"),
                        html.Div("Updating…", className="loading-caption"),
                    ],
                    style={"position": "relative"},
                ),
                fullscreen=False,
            ),
            html.Div(id="cart-message", className="mt-3 text-center text-success"),
        ]
    )

    return dbc.Container([controls, resultados_tabs], fluid=True)


# ======================= CARRITO =======================

def layout_cart(cart_data):
    if not cart_data:
        return dbc.Container(
            [
                html.H2("Carrito", className="mb-3"),
                html.P(
                    "Tu carrito está vacío. Añade primero un outfit desde “Configurar outfit”.",
                    className="text-muted",
                ),
            ],
            fluid=True,
        )

    outfit_items = cart_data.get("outfit_items", [])
    outers = cart_data.get("outers", [])
    outfit_num = cart_data.get("outfit_idx", 0) + 1

    return dbc.Container(
        [
            html.H2("Carrito", className="mb-3"),
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H5(f"Outfit #{outfit_num}", className="mb-2"),
                        html.P("Prendas seleccionadas:", className="fw-bold mb-1"),
                        html.Ul([html.Li(n.title()) for n in outfit_items]),
                        html.Hr(),
                        html.P("Abrigos añadidos:", className="fw-bold mb-1"),
                        html.Ul(
                            [html.Li(n.title()) for n in outers]
                            or [html.Li("Ninguno")]
                        ),
                        html.Hr(),
                        dbc.Button(
                            "Comprar ahora",
                            id="btn_checkout",
                            color="dark",
                            className="mt-2",
                        ),
                        html.Div(id="checkout-message", className="mt-3 text-success"),
                    ]
                ),
                className="shadow-sm card-controls",
            ),
        ],
        fluid=True,
    )


# ======================= CATÁLOGO / CLUSTERS (NUEVO) =======================

def layout_catalog():
    """
    Nueva página: análisis de catálogo y clusters.
    Usa el DataFrame global df (con columna style_cluster) y delega
    en build_catalog_layout() para los gráficos.
    """
    return build_catalog_layout(df)  # <<--- NUEVO


# ======================= COMPONENTES VISUALES =======================

def prenda_thumb(item):
    image_asset = item.get("image_asset")
    img_src = app.get_asset_url(image_asset) if image_asset else None

    label = item.get("slot", "").upper()
    nombre = item.get("nombre", "(sin nombre)").title()

    img = html.Div("Sin imagen", className="no-image text-center text-muted")
    if img_src:
        img = html.Img(src=img_src, className="img-fluid rounded-3 outfit-image")

    metas = [
        ("Tipo", item.get("tipo", "")),
        ("Color", item.get("color_base", item.get("color", ""))),

        ("Formalidad", item.get("formalidad", "")),
        ("Temporada", item.get("temporada", "")),
    ]
    meta_lines = [html.Div([html.Strong(f"{k}: "), html.Span(str(v))]) for k, v in metas]

    return dbc.Card(
        [
            dbc.CardHeader(f"{label} — {nombre}", className="prenda-header"),
            dbc.CardBody([img, html.Div(meta_lines, className="mt-2 prenda-meta")]),
        ],
        className="h-100 prenda-card",
    )


def outfit_card(outfit, rank, temp_c, rainy, city, used_date):
    outfit_type = outfit.get("type", "")
    items = outfit.get("items", [])

    tipo_texto = "Vestido" if outfit_type == "dress_outfit" else "Dos piezas"
    cols = [dbc.Col(prenda_thumb(it), lg=4, md=4, sm=12, className="mb-3") for it in items]

    return dbc.Card(
        [
            dbc.CardHeader(
                html.Div(
                    [
                        html.Div(f"Outfit #{rank} — {tipo_texto}", className="fw-bold"),
                        html.Div(
                            f"{temp_c:.1f}°C · lluvia {'sí' if rainy else 'no'} · {city or 'tu ciudad'} · {used_date}",
                            className="text-muted small",
                        ),
                    ]
                ),
                className="outfit-header",
            ),
            dbc.CardBody(dbc.Row(cols), className="outfit-body"),
        ],
        className="mb-3 outfit-card",
    )


def extra_prenda_card(item):
    return dbc.Col(prenda_thumb(item), lg=3, md=4, sm=6, className="mb-3")


# ======================= LAYOUT GLOBAL =======================

# Provide a validation_layout including all pages so client-side validation
# does not complain about ids that only exist in some routes (eg. `btn`).
try:
    app.validation_layout = html.Div([
        layout_home(),
        layout_config(),
        layout_catalog(),  # <<--- NUEVO
        layout_cart({}),
    ])
except Exception:
    # If building the full layouts fails for any reason, keep running with
    # suppress_callback_exceptions=True to avoid breaking the app during dev.
    pass


app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        navbar(),
        dcc.Store(id="recommendation-store"),
        dcc.Store(id="cart-store"),
        html.Div(id="page-content"),
    ],
    className="app-bg",   # <<--- FONDO BONITO
)


# ======================= CALLBACKS =======================

# Routing entre páginas
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
    State("cart-store", "data"),
)
def render_page(pathname, cart_data):
    if pathname == "/config":
        return layout_config()
    if pathname == "/catalog":          # <<--- NUEVO
        return layout_catalog()
    if pathname == "/cart":
        return layout_cart(cart_data)
    return layout_home()


# 1) Guardar recomendación
@app.callback(
    Output("recommendation-store", "data"),
    Input("btn", "n_clicks"),
    State("city", "value"),
    State("date", "date"),
    State("event_type", "value"),
    State("segment", "value"),
    prevent_initial_call=True,
)
def on_recomendar(_, city, picked_date, event_type, segment):

    if not city:
        return None

    try:
        w = get_weather(city, date.fromisoformat(picked_date))
        temp_c = float(w.get("temp_c", 20.0))
        rainy = bool(w.get("is_rainy", False))
        used_date = w.get("used_date", picked_date)
    except Exception:
        temp_c = 20.0
        rainy = False
        used_date = picked_date

    formalidad = map_event_to_formality(event_type)
    df_used = filter_by_profile(df, segment or "any")

    if df_used.empty:
        return None

    res = recomendar_outfits(df_used, temp_c, formalidad, rainy, n_outfits=3)

    res["meta"] = {
        "temp_c": temp_c,
        "rainy": rainy,
        "city": city,
        "used_date": used_date,
        "formalidad_obj": formalidad,
    }

    return res


# Actualiza las opciones de tipo de evento según el perfil/segmento y el
# inventario disponible: si no hay prendas formales suficientes, quitamos
# la opción de 'wedding' porque no sería representativa.
@app.callback(
    Output("event_type", "options"),
    Output("event_type", "value"),
    Input("segment", "value"),
)
def update_event_options(segment):
    df_seg = filter_by_profile(df, segment or "any")

    allow_wedding = False
    try:
        # Si hay al menos un vestido formal, permitimos boda
        if not df_seg[(df_seg["slot"] == "dress") & (df_seg["formalidad"] == "formal")].empty:
            allow_wedding = True
        else:
            # O si hay top+bottom+shoes formales
            tops = df_seg[(df_seg["slot"] == "top") & (df_seg["formalidad"] == "formal")].shape[0]
            bottoms = df_seg[(df_seg["slot"] == "bottom") & (df_seg["formalidad"] == "formal")].shape[0]
            shoes = df_seg[(df_seg["slot"] == "shoes") & (df_seg["formalidad"] == "formal")].shape[0]
            if tops > 0 and bottoms > 0 and shoes > 0:
                allow_wedding = True
    except Exception:
        allow_wedding = False

    options = [o for o in EVENT_OPTIONS if not (o["value"] == "wedding" and not allow_wedding)]
    # Asegurar un valor por defecto válido
    value = options[0]["value"] if options else "casual_day"
    return options, value


# 2) Mostrar resultados según pestaña
@app.callback(
    Output("resultados", "children"),
    Input("result-tabs", "value"),
    Input("recommendation-store", "data"),
)
def update_resultados(active_tab, rec_data):
    if not rec_data:
        # Para evitar un error
        if active_tab == "tab-analytics":
            return html.P("Genera una recomendación para ver los gráficos.")
        else:
            return html.P("Pulsa RECOMENDAR OUTFIT para ver opciones.")

    outfits = rec_data.get("outfits", [])
    outers = rec_data.get("outers", [])

    meta = rec_data.get("meta", {})
    temp_c = float(meta.get("temp_c", 20.0))
    rainy = bool(meta.get("rainy", False))
    city = meta.get("city", "tu ciudad")
    used_date = meta.get("used_date", "")

    # ---------- GRÁFICOS ----------
    if active_tab == "tab-analytics":
        return build_analytics_layout(rec_data)

    # ---------- OUTFITS ----------
    if not outfits:
        return html.P("No he encontrado outfits compatibles 😢")

    header = html.Div(
        [
            html.H4("Outfits recomendados", className="mb-1"),
            html.Small(
                f"{temp_c:.1f}°C · lluvia {'sí' if rainy else 'no'} · {city}",
                className="text-muted",
            ),
        ],
        className="mb-3",
    )

    cards = [
        outfit_card(o, i + 1, temp_c, rainy, city, used_date)
        for i, o in enumerate(outfits)
    ]
    children = [header, html.Div(cards)]

    # Abrigos opcionales
    if outers:
        children.append(
            html.Div(
                [
                    html.H5("Abrigos opcionales", className="mt-4 mb-2"),
                    dbc.Row([extra_prenda_card(it) for it in outers]),
                    dcc.Checklist(
                        id="selected_outers",
                        options=[
                            {"label": o["nombre"].title(), "value": idx}
                            for idx, o in enumerate(outers)
                        ],
                        value=[],
                        labelStyle={"display": "block"},
                    ),
                ]
            )
        )
    else:
        children.append(
            dcc.Checklist(id="selected_outers", options=[], value=[], style={"display": "none"})
        )

    # Selección de outfit
    children.append(
        html.Div(
            [
                html.Hr(),
                html.P("Selecciona tu outfit favorito:"),
                dcc.RadioItems(
                    id="selected_outfit",
                    options=[{"label": f"Outfit #{i+1}", "value": i} for i in range(len(outfits))],
                    value=0,
                    inline=True,
                ),
                dbc.Button(
                    "AÑADIR AL CARRITO",
                    id="btn_add_cart",
                    color="success",
                    className="mt-3 px-4",
                ),
            ],
            className="text-center mt-4",
        )
    )

    return html.Div(children)


# 3) Añadir al carrito
@app.callback(
    Output("cart-message", "children"),
    Output("cart-store", "data"),
    Input("btn_add_cart", "n_clicks"),
    State("selected_outfit", "value"),
    State("selected_outers", "value"),
    State("recommendation-store", "data"),
    prevent_initial_call=True,
)
def on_add_to_cart(_, selected_outfit, selected_outers, rec_data):
    if not rec_data or selected_outfit is None:
        return "", no_update

    outfits = rec_data.get("outfits", [])
    outers_all = rec_data.get("outers", [])

    outfit_idx = int(selected_outfit)
    outfit = outfits[outfit_idx]

    outfit_items = [it.get("nombre", "") for it in outfit.get("items", [])]

    selected_outers = selected_outers or []
    outers_names = [
        outers_all[i]["nombre"] for i in selected_outers if i < len(outers_all)
    ]

    return "", {
        "outfit_idx": outfit_idx,
        "outfit_items": outfit_items,
        "outers": outers_names,
    }


# 4) Checkout
@app.callback(
    Output("checkout-message", "children"),
    Input("btn_checkout", "n_clicks"),
    prevent_initial_call=True,
)
def on_checkout(_):
    return "Compra realizada con éxito. En menos de 5 días estará en tu casa."


if __name__ == "__main__":
    app.run(debug=True)

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, callback, Input, Output, State
from dashboard_transicion.metrics.queries_transicion import *
from dashboard_transicion.graphics.graphics import *
import plotly.express as px
import plotly.graph_objects as go
import json
import requests
import os

mapeo_regiones = {
    "RM": "Región Metropolitana de Santiago",
    "MAG": "Región de Magallanes y Antártica Chilena",
    "AYSEN": "Región de Aysén del Gral.Ibañez del Campo",
    "AYP": "Región de Arica y Parinacota",
    "RIOS": "Región de Los Ríos",
    "LGBO": "Región del Libertador Bernardo O'Higgins",
    "BBIO": "Región del Bío-Bío",
    "COQ": "Región de Coquimbo",
    "LAGOS": "Región de Los Lagos",
    "VALPO": "Región de Valparaíso",
    "NUBLE": "Región de Ñuble",
    "ANTOF": "Región de Antofagasta",
    "ATCMA": "Región de Atacama",
    "TPCA": "Región de Tarapacá",
    "ARAUC": "Región de La Araucanía",
    "MAULE": "Región del Maule"
}

current_dir = os.path.dirname(os.path.abspath(__file__)) 

root_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))

path_regiones = os.path.join(root_dir, "regiones_edit.geojson")
path_comunas = os.path.join(root_dir, "Comunas_de_Chile.geojson")

with open(path_regiones, encoding='utf-8') as f:
    geojson_regiones = json.load(f)
with open(path_comunas, encoding='utf-8') as f:
    geojson_comunas = json.load(f)


MAP_CARD_STYLE = {
    "borderRadius": "20px", 
    "border": "none", 
    "boxShadow": "0 4px 15px rgba(0, 0, 0, 0.05)",
    "marginBottom": "20px",
    "overflow": "hidden",
    "backgroundColor": "white",
}

# --- LAYOUT PRINCIPAL ---
layout = dbc.Container([

    dcc.Store(id='selected-region-store', data=None),
    # Encabezado
    dbc.Row([
        dbc.Col([
            html.H4("Análisis de transición academica", className="border-bottom pb-2"),
            dbc.Button("← Volver a Chile", id="btn-reset-map", color="link", className="p-0 text-decoration-none small")
        ])
    ], className="mb-3"),

    dbc.Row([
    # 1. Filtro Institución
        dbc.Col([
            html.Label("Institución", className="small fw-bold"),
            dcc.Dropdown(
                id="filtro-institucion",
                options=[
                    {"label": "ECAS", "value": 104},
                    {"label": "Competencia", "value": "comp"},
                    {"label": "Todas", "value": "all"}
                ],
                value=104,
                clearable=False
            )
        ], width=2),

        # 2. Rango de Cohorte
        dbc.Col([
            html.Label("Rango de Cohorte", className="small fw-bold"),
            dcc.RangeSlider(
                id="filtro-cohorte",
                min=2007, max=2025, step=1,
                marks={i: str(i) for i in range(2007, 2026, 3)},
                value=[2018, 2023]
            )
        ], width=4),

        # 3. Jornada
        dbc.Col([
            html.Label("Jornada", className="small fw-bold"),
            dcc.Dropdown(
                id="filtro-jornada",
                options=[
                    {"label": "Todas", "value": "Todas"},
                    {"label": "Diurna", "value": "Diurna"},
                    {"label": "Vespertina", "value": "Vespertina"}
                ],
                value="Todas",
                clearable=False
            )
        ], width=2),

        # 4. Género
        dbc.Col([
            html.Label("Género", className="small fw-bold"),
            dcc.Dropdown(
                id="filtro-genero",
                options=[
                    {"label": "Todos", "value": "Todos"},
                    {"label": "Hombre", "value": "Hombre"},
                    {"label": "Mujer", "value": "Mujer"}
                ],
                value="Todos",
                clearable=False
            )
        ], width=2),
        
        # Botón de Acción (Opcional)
        dbc.Col([
            html.Br(),
            dbc.Button("Actualizar", id="btn-update", color="primary", className="w-100 mt-1")
        ], width=2)

    ], className="mb-4 p-3 bg-white rounded shadow-sm mx-0 align-items-center"),

    dbc.Row([
        dbc.Col([
            html.H4(id="titulo-mapa", className="text-center mb-3"),
            dbc.Button("← Volver a Chile", id="btn-reset-map", color="secondary", size="sm", className="mb-2"),
            dcc.Loading(dcc.Graph(id="mapa-interactivo", style={"height": "700px"}))
        ])
    ])

], fluid=True, style={"backgroundColor": "#f4f6f9", "minHeight": "100vh", "padding": "2rem"})

@callback(
    [Output("mapa-interactivo", "figure"),
     Output("selected-region-store", "data"),
     Output("titulo-mapa", "children")],
    [Input("mapa-interactivo", "clickData"),
     Input("btn-reset-map", "n_clicks")],
    [State("selected-region-store", "data"),
     State("filtro-cohorte", "value"),
     State("filtro-institucion", "value")]
)
def update_map(clickData, n_clicks, current_region_stored, cohorte, inst):
    ctx = dash.callback_context
    trigger = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    # Determinar región actual
    if trigger == "btn-reset-map":
        region_actual = None
    elif trigger == "mapa-interactivo" and clickData:
        region_actual = clickData['points'][0]['location']
    else:
        region_actual = current_region_stored

    # Obtener datos de tu base de datos
    df = get_data_geografica_unificada_rango(cohorte, inst) 
    
    # Generar gráfico
    fig, titulo = generar_figura_mapa(
        region_actual, 
        df, 
        geojson_regiones, 
        geojson_comunas, 
        mapeo_regiones
    )
    
    return fig, region_actual, titulo
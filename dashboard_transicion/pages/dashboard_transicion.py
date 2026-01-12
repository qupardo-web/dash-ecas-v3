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

COORDENADAS_REGIONES = {
    "15": {"lat": -18.50, "lon": -69.80, "zoom": 7.5}, # Arica y Parinacota
    "1":  {"lat": -20.20, "lon": -69.30, "zoom": 7.0}, # Tarapacá
    "2":  {"lat": -23.65, "lon": -69.20, "zoom": 6.0}, # Antofagasta
    "3":  {"lat": -27.30, "lon": -70.30, "zoom": 6.5}, # Atacama
    "4":  {"lat": -30.60, "lon": -70.80, "zoom": 7.0}, # Coquimbo
    "5":  {"lat": -32.80, "lon": -71.20, "zoom": 7.5}, # Valparaíso
    "13": {"lat": -33.60, "lon": -70.66, "zoom": 8.0}, # Metropolitana
    "6":  {"lat": -34.40, "lon": -71.10, "zoom": 7.5}, # O'Higgins
    "7":  {"lat": -35.50, "lon": -71.40, "zoom": 7.5}, # Maule
    "16": {"lat": -36.70, "lon": -72.10, "zoom": 8.0}, # Ñuble
    "8":  {"lat": -37.40, "lon": -72.40, "zoom": 7.5}, # Biobío
    "9":  {"lat": -38.70, "lon": -72.50, "zoom": 7.5}, # Araucanía
    "14": {"lat": -40.00, "lon": -72.30, "zoom": 8.0}, # Los Ríos
    "10": {"lat": -41.70, "lon": -72.80, "zoom": 7.0}, # Los Lagos
    "11": {"lat": -46.50, "lon": -73.00, "zoom": 6.0}, # Aysén
    "12": {"lat": -53.00, "lon": -71.00, "zoom": 5.5}, # Magallanes
}

current_dir = os.path.dirname(os.path.abspath(__file__)) 

root_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))

path_regiones = os.path.join(root_dir, "Regional.geojson")
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
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col(html.Span("Distribución Territorial de Matrícula", className="fw-bold"), width=8),
                        dbc.Col(
                            dbc.Badge("Vista: Nacional", id="badge-nivel", color="info", className="float-end"),
                            width=4
                        )
                    ])
                ], className="bg-white border-bottom-0 pt-3"),
                dbc.CardBody([
                    dcc.Loading(
                        type="circle",
                        children=dcc.Graph(
                            id="mapa-interactivo", 
                            config={
                                'scrollZoom': True,      # Permite zoom con la rueda del 
                            },
                            style={"height": "650px"}
                        )
                    )
                ])
            ], style=MAP_CARD_STYLE)
        ], width=12)
    ], className="mx-0"),

], fluid=True, style={"backgroundColor": "#f4f6f9", "minHeight": "100vh", "padding": "2rem"})

@callback(
    Output("mapa-interactivo", "figure"),
    Output("selected-region-store", "data"),
    Output("badge-nivel", "children"),
    Output("badge-nivel", "color"),
    Input("btn-update", "n_clicks"),
    Input("mapa-interactivo", "clickData"),
    Input("btn-reset-map", "n_clicks"),
    State("filtro-cohorte", "value"),
    State("filtro-institucion", "value"),
    State("filtro-jornada", "value"),
    State("filtro-genero", "value"),
    State("selected-region-store", "data")
)
def update_geographic_map(n_upd, clickData, n_reset, cohorte, inst, jornada, genero, current_region):
    ctx = dash.callback_context
    trigger = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    # 1. OBTENER LOS DATOS REALES
    df_raw = get_data_geografica_unificada_rango(cohorte, inst, jornada, genero)

    # 2. Lógica de Navegación (Drill-down)
    region_id = current_region
    if trigger == "mapa-interactivo" and clickData:
        loc = str(clickData['points'][0]['location'])
        if loc in COORDENADAS_REGIONES:
            region_id = loc
    elif trigger == "btn-reset-map":
        region_id = None

    
    if region_id and region_id in COORDENADAS_REGIONES:
        
        comunas_geojson = [
            {
                "cod_comuna": str(f["properties"]["cut"]),
                "nomb_comuna": f["properties"]["comuna"]
            } 
            for f in geojson_comunas["features"] 
            if str(f["properties"]["region"]) == region_id
        ]
        df_base = pd.DataFrame(comunas_geojson)
        

        # B. Unimos con los datos reales
        if df_raw is not None and not df_raw.empty:
            df_raw['cod_comuna'] = df_raw['cod_comuna'].astype(str)
            df_plot = pd.merge(df_base, df_raw[['cod_comuna', 'cantidad']], on="cod_comuna", how="left")
        else:
            df_plot = df_base.copy()
            df_plot['cantidad'] = 0

        # C. Llenamos los nulos con 0
        df_plot['cantidad'] = df_plot['cantidad'].fillna(0)
        print(df_plot)
        
        fig = px.choropleth_mapbox(
            data_frame=df_plot,
            geojson=geojson_comunas,
            locations="cod_comuna",
            featureidkey="properties.cut",
            color="cantidad",
            hover_name="nomb_comuna",
            mapbox_style="white-bg",
            color_continuous_scale="Viridis",
            range_color=[0, df_plot['cantidad'].max() if df_plot['cantidad'].max() > 0 else 10] # Evita escala errónea si todo es 0
        )
        
        centro = {"lat": COORDENADAS_REGIONES[region_id]["lat"], "lon": COORDENADAS_REGIONES[region_id]["lon"]}
        zoom_nivel = COORDENADAS_REGIONES[region_id]["zoom"]
        badge_text, badge_color = f"Región: {region_id}", "success"
        
    else:
    
        regiones_base = [
            {
                "cod_region": str(f["properties"]["codregion"]), 
                "nomb_region": f["properties"]["Region"]
            } 
            for f in geojson_regiones["features"]
        ]
        df_base = pd.DataFrame(regiones_base)

        # B. Agrupar datos reales
        if df_raw is not None and not df_raw.empty:
            df_raw['cod_region'] = df_raw['cod_region'].astype(str)
            df_real_reg = df_raw.groupby('cod_region')['cantidad'].sum().reset_index()
            df_plot = pd.merge(df_base, df_real_reg, on="cod_region", how="left")
        else:
            df_plot = df_base.copy()
            df_plot['cantidad'] = 0

        df_plot['cantidad'] = df_plot['cantidad'].fillna(0)

        fig = px.choropleth_mapbox(
            data_frame=df_plot,
            geojson=geojson_regiones,
            locations="cod_region",
            featureidkey="properties.codregion",
            color="cantidad",
            hover_name="nomb_region",
            mapbox_style="white-bg",
            color_continuous_scale="Viridis"
        )
        centro = {"lat": -33.45, "lon": -71.5}
        zoom_nivel = 3.8
        badge_text, badge_color = "Vista: Nacional", "info"

    # 4. Ajustes finales de Layout
    fig.update_layout(
        mapbox=dict(
            center=centro,
            zoom=zoom_nivel,
            bounds={"west": -76, "east": -65, "south": -56, "north": -17}
        ),
        dragmode="zoom",
        margin={"r":0,"t":0,"l":0,"b":0}
    )
    
    return fig, region_id, badge_text, badge_color
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
    "overflowY": "scroll"
}

def render_kpi_card_with_icon(id_valor, titulo, icono_class):
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                # Columna del Icono
                dbc.Col(
                    html.I(className=f"fas {icono_class} fa-2x", style={"color": "#162f8a"}), 
                    width=3, 
                    className="d-flex justify-content-center"
                ),
                # Columna del Texto y Valor
                dbc.Col([
                    html.P(titulo, className="text-muted mb-1 small", style={"fontWeight": "600"}),
                    dbc.Spinner(
                        html.H4("0", id=id_valor, className="fw-bold mb-0", style={"color": "#2c3e50"}),
                        size="sm", 
                        color="primary",
                        spinner_style={"float": "left"}
                    ),
                ], width=9),
            ], align="center")
        ], className="p-3")
    ], style={
        "borderRadius": "15px", 
        "border": "none", 
        "boxShadow": "0 4px 12px rgba(0,0,0,0.08)",
        "height": "100%" # Para asegurar que todas midan lo mismo en la fila
    })

df_competencia = get_info_competencia()
lista_jornadas = get_jornadas_disponibles()

# Formatear opciones para Dropdowns
opciones_institucion = [
    {"label": row["nomb_inst"], "value": row["cod_inst"]} 
    for _, row in df_competencia.iterrows()
]
# Agregamos la opción "Todas" si es necesario
opciones_institucion.insert(0, {"label": "Todas", "value": "all"})

opciones_jornada = [{"label": j, "value": j} for j in lista_jornadas]
if "Todas" not in lista_jornadas:
    opciones_jornada.insert(0, {"label": "Todas", "value": "Todas"})

# --- LAYOUT PRINCIPAL ---
layout = dbc.Container([

    dcc.Store(id='selected-region-store', data=None),
    # Encabezado
    dbc.Row([
        dbc.Col([
            html.H4("Análisis de transición academica", className="border-bottom pb-2"),
        ])
    ], className="mb-3"),

    dbc.Row([
    # 1. Filtro Institución
        dbc.Col([
        html.Label("Institución", className="small fw-bold"),
        dcc.Dropdown(
            id="filtro-institucion",
            options=opciones_institucion,
            value=104,  # ECAS por defecto
            clearable=False,
            style={'minHeight': '50px'}, 
            optionHeight=80
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
                options=opciones_jornada,
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
        # COLUMNA IZQUIERDA: Mapa (Mantiene su altura de 650px)
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col(html.Span("Distribución Territorial de Matrícula", className="fw-bold"), width=8),
                        dbc.Col(
                            dbc.Badge("Vista: Nacional", id="badge-nivel", color="info", className="float-end"),
                            width=4
                        ),
                        dbc.Button("← Volver a Chile", id="btn-reset-map", color="link", className="p-0 text-decoration-none small")
                    ])
                ], className="bg-white border-bottom-0 pt-3"),
                dbc.CardBody([
                    dcc.Loading(
                        type="circle",
                        children=dcc.Graph(
                            id="mapa-interactivo", 
                            config={'scrollZoom': True},
                            style={"height": "650px"}
                        )
                    )
                ])
            ], style=MAP_CARD_STYLE)
        ], width=8),

        # COLUMNA DERECHA: Ahora centrada verticalmente
        dbc.Col([
            # Contenedor con d-flex y flex-column para distribuir el espacio
            html.Div([
                # Bloque de 4 KPIs (2x2)
                html.Div([
                    dbc.Row([
                        dbc.Col(render_kpi_card_with_icon("id-kpi-1", "Total Matriculados", "fa-users"), width=6, className="pb-3"),
                        dbc.Col(render_kpi_card_with_icon("id-kpi-2", "Total Titulados", "fa-graduation-cap"), width=6, className="pb-3"),
                    ], className="g-3"), # g-3 añade espacio uniforme entre columnas
                ], className="mb-3"), # Espacio entre KPIs y gráfico

                # Gráfico Lateral con altura ajustada para llenar el vacío
                dbc.Card([
                    dbc.CardHeader("Indice de ruralidad", className="fw-bold small"),
                    dbc.CardBody([
                        dcc.Loading(
                            dcc.Graph(
                                id="graph-lateral-detalle", 
                                style={"height": "430px"} # Aumentamos altura para balancear
                            )
                        )
                    ])
                ], style=MAP_CARD_STYLE)
            ], 
            className="d-flex flex-column justify-content-center h-100" 
            )
        ], width=4)
    ], className="mx-0 align-items-stretch"),

    dbc.Row([
    # Columna 1: Dependencia Administrativa
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Dependencia Colegio de Origen", className="fw-bold small"),
                dbc.CardBody([
                    dcc.Loading(dcc.Graph(id="graph-dependencia", style={"height": "350px"}))
                ])
            ], style=MAP_CARD_STYLE)
        ], width=4),

        # Columna 2: Tipo de Enseñanza (Sugerido para completar la fila)
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Tipo de Enseñanza Media", className="fw-bold small"),
                dbc.CardBody([
                    dcc.Loading(dcc.Graph(id="graph-ensenianza", style={"height": "350px"}))
                ])
            ], style=MAP_CARD_STYLE)
        ], width=4),

        # Columna 3: Demora Ingreso (Sugerido para completar la fila)
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Origen Escolar de Titulados (Dependencia)", className="fw-bold small"),
                dbc.CardBody([
                    dcc.Loading(dcc.Graph(
                        id="grafico-dependencia-titulados",
                        style={"height": "350px"}, 
                    ))
                ])
            ], style=MAP_CARD_STYLE)
        ], width=4),
    ], className="mx-0 mt-4"),

    dbc.Row([
        # Gráfico Persistencia vs NEM
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Persistencia al 2do Año vs NEM", className="fw-bold small"),
                dbc.CardBody([
                    dcc.Loading(dcc.Graph(id="graph-nem-persistencia", style={"height": "350px"}))
                ])
            ], style=MAP_CARD_STYLE)
        ], width=6),

        # Gráfico Titulación Oportuna vs NEM
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Tasa de Titulación Oportuna vs NEM", className="fw-bold small"),
                dbc.CardBody([
                    dcc.Loading(dcc.Graph(id="graph-nem-titulacion", style={"height": "350px"}))
                ])
            ], style=MAP_CARD_STYLE)
        ], width=6),
    ], className="mx-0 mt-4"),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Años de Demora Ingreso ES", className="fw-bold small"),
                dbc.CardBody([
                    dcc.Loading(dcc.Graph(id="graph-demora", style={"height": "350px"}))
                ])
            ], style=MAP_CARD_STYLE)
        ], width=12),
        
        # Puedes agregar aquí otros dos Cols de width=4 si quieres completar esta fila
    ], className="mx-0 mt-4"),

], fluid=True, style={"backgroundColor": "#f4f6f9", "minHeight": "100vh", "padding": "2rem"})

@callback(
    Output("filtro-carrera", "options"),
    Input("filtro-institucion", "value")
)
def update_carreras_dropdown(cod_inst_sel):
    if cod_inst_sel == "all":
        # Traer todas las carreras únicas de la base
        return [{"label": "Todas", "value": "Todas"}]
    
    # Filtrar el DF de competencia por la institución seleccionada
    carreras_string = df_competencia[df_competencia['cod_inst'] == cod_inst_sel]['carreras'].iloc[0]
    lista_carreras = carreras_string.split(', ')
    
    return [{"label": c, "value": c} for c in lista_carreras]
    

@callback(
    Output("id-kpi-1", "children"), # Total Matriculados
    Output("id-kpi-2", "children"), # Total Titulados
    Input("selected-region-store", "data"), # <--- Gatillo inmediato al hacer clic
    Input("btn-update", "n_clicks"),
    State("filtro-cohorte", "value"),
    State("filtro-institucion", "value"),
    State("filtro-jornada", "value"),
    State("filtro-genero", "value")
)
def update_kpi_cards(region_id, n_clicks, cohorte, inst, jornada, genero):
    # La función get_total_titulados_y_matriculados ya recibe el region_id
    data = get_total_titulados_y_matriculados(cohorte, inst, jornada, genero, region_id)
    
    def fmt(val): 
        return f"{val:,}".replace(",", ".")

    return fmt(data['total_m']), fmt(data['total_t'])

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
def update_dashboard_map(n_upd, clickData, n_reset, cohorte, inst, jornada, genero, current_region):
    ctx = dash.callback_context
    trigger = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    # 1. Obtención de datos
    df_raw = get_data_geografica_unificada_rango(cohorte, inst, jornada, genero)

    # 2. Lógica de Navegación
    region_id = current_region
    if trigger == "mapa-interactivo" and clickData:
        loc = str(clickData['points'][0]['location'])
        if loc in COORDENADAS_REGIONES:
            region_id = loc
    elif trigger == "btn-reset-map":
        region_id = None

    # 3. Preparación de DataFrames y Renderizado
    if region_id and region_id in COORDENADAS_REGIONES:
        # --- VISTA COMUNAL ---
        comunas_geojson = [
            {"cod_comuna": str(f["properties"]["cut"]), "nomb_comuna": f["properties"]["comuna"]} 
            for f in geojson_comunas["features"] if str(f["properties"]["region"]) == region_id
        ]
        df_base = pd.DataFrame(comunas_geojson).drop_duplicates(subset=['cod_comuna'])
        
        if df_raw is not None and not df_raw.empty:
            df_raw['cod_comuna'] = df_raw['cod_comuna'].astype(str)
            df_plot = pd.merge(df_base, df_raw[['cod_comuna', 'cantidad']], on="cod_comuna", how="left")
        else:
            df_plot = df_base.copy()
            df_plot['cantidad'] = 0

        df_plot['cantidad'] = df_plot['cantidad'].fillna(0)

        # Configuramos vista regional desde el diccionario
        config_region = COORDENADAS_REGIONES.get(region_id)
        
        fig = create_interactive_map(
            df_plot=df_plot,
            geojson=geojson_comunas,
            is_comuna=True,
            centro_dict=config_region,
            zoom_nivel=config_region["zoom"] 
        )

        return fig, region_id, f"Región: {region_id}", "success"

    else:
        # --- VISTA NACIONAL ---
        regiones_base = [
            {"cod_region": str(f["properties"]["codregion"]), "nomb_region": f["properties"]["Region"]} 
            for f in geojson_regiones["features"]
        ]
        df_base = pd.DataFrame(regiones_base)

        if df_raw is not None and not df_raw.empty:
            df_raw['cod_region'] = df_raw['cod_region'].astype(str)
            df_real_reg = df_raw.groupby('cod_region')['cantidad'].sum().reset_index()
            df_plot = pd.merge(df_base, df_real_reg, on="cod_region", how="left")
        else:
            df_plot = df_base.copy()
            df_plot['cantidad'] = 0

        df_plot['cantidad'] = df_plot['cantidad'].fillna(0)

        # Definimos una configuración fija para todo Chile (Sin usar config_region)
        config_nacional = {"lat": -39.5, "lon": -71.5, "zoom": 3.8}

        fig = create_interactive_map(
            df_plot=df_plot,
            geojson=geojson_regiones, # Usamos regiones
            is_comuna=False,          # No son comunas
            centro_dict=config_nacional,
            zoom_nivel=config_nacional["zoom"] 
        )
        
        return fig, None, "Vista: Nacional", "info"

# @callback(
#     Output("graph-dependencia", "figure"),
#     Output("graph-ensenianza", "figure"),
#     Output("graph-demora", "figure"),
#     Output("graph-nem-persistencia", "figure"),
#     Output("graph-nem-titulacion", "figure"),
#     Output("graph-lateral-detalle", "figure"),
#     Output("grafico-dependencia-titulados", "figure"),
#     Input("selected-region-store", "data"),
#     Input("btn-update", "n_clicks"),
#     State("filtro-cohorte", "value"),
#     State("filtro-institucion", "value"),
#     State("filtro-jornada", "value"),
#     State("filtro-genero", "value"),
# )
# def update_statistical_graphs(region_id, n_clicks, cohorte, inst, jornada, genero):
    
#     df_dep = get_distribucion_dependencia_rango(cohorte, inst, genero, jornada, region_id=region_id)
#     df_ens = get_tasas_articulacion_tipo_establecimiento_rango(cohorte, inst, jornada, "Todas", genero, region_id=region_id)
#     df_dem = get_demora_ingreso_total(cohorte, inst, "Todas", genero, jornada, region_id=region_id)
#     df_nem_per = get_correlacion_nem_persistencia_rango(cohorte, inst, jornada, "Todas", genero, region_id=region_id)
#     df_nem_tit = get_correlacion_nem_titulacion_rango(cohorte, inst, jornada, "Todas", genero, region_id=region_id)
#     df_rural = get_kpi_ruralidad_seguimiento_rango(cohorte, inst, jornada, genero, region_id=region_id)
#     df_tit_dep = get_titulados_por_dependencia_rango(cohorte, inst, jornada, genero, region_id=region_id)

#     fig_dep = create_donut_chart(df_dep)
#     fig_ens = create_bar_ensenianza(df_ens)
#     fig_dem = create_line_demora(df_dem)
#     fig_nem_per = create_nem_persistence_chart(df_nem_per)
#     fig_nem_tit = create_nem_titulacion_chart(df_nem_tit)
#     fig_rural = create_ruralidad_comparison_chart(df_rural)
#     periodo_texto = f"Cohortes {cohorte[0]}-{cohorte[1]}"
#     fig_tit_dep = graficar_dependencia_titulados(df_tit_dep, periodo_texto)

#     return fig_dep, fig_ens, fig_dem, fig_nem_per, fig_nem_tit, fig_rural, fig_tit_dep

@callback(
    Output("graph-dependencia", "figure"),
    Output("graph-ensenianza", "figure"),
    Output("graph-demora", "figure"),
    Output("graph-nem-persistencia", "figure"),
    Output("graph-nem-titulacion", "figure"),
    Output("graph-lateral-detalle", "figure"),
    Output("grafico-dependencia-titulados", "figure"), # Nuevo Output agregado
    Input("selected-region-store", "data"),
    Input("btn-update", "n_clicks"),
    State("filtro-cohorte", "value"),
    State("filtro-institucion", "value"),
    State("filtro-jornada", "value"),
    State("filtro-genero", "value"),
)
def update_statistical_graphs(region_id, n_clicks, cohorte, inst, jornada, genero):
    # 1. Obtención de datos (incluyendo el nuevo de titulados)
    df_dep = get_distribucion_dependencia_rango(cohorte, inst, genero, jornada, region_id=region_id)
    df_ens = get_tasas_articulacion_tipo_establecimiento_rango(cohorte, inst, jornada, "Todas", genero, region_id=region_id)
    df_dem = get_demora_ingreso_total(cohorte, inst, "Todas", genero, jornada, region_id=region_id)
    df_nem_per = get_correlacion_nem_persistencia_rango(cohorte, inst, jornada, "Todas", genero, region_id=region_id)
    df_nem_tit = get_correlacion_nem_titulacion_rango(cohorte, inst, jornada, "Todas", genero, region_id=region_id)
    df_rural = get_kpi_ruralidad_seguimiento_rango(cohorte, inst, jornada, genero, region_id=region_id)
    df_tit_dep = get_titulados_por_dependencia_rango(cohorte, inst, genero, jornada, region_id)

    # 2. Creación de figuras
    fig_dep = create_donut_chart(df_dep)
    fig_ens = create_bar_ensenianza(df_ens)
    fig_dem = create_line_demora(df_dem)
    fig_nem_per = create_nem_persistence_chart(df_nem_per)
    fig_nem_tit = create_nem_titulacion_chart(df_nem_tit)
    fig_rural = create_ruralidad_comparison_chart(df_rural)
    periodo_texto = f"Cohortes {cohorte[0]}-{cohorte[1]}"
    fig_tit_dep = graficar_dependencia_titulados(df_tit_dep, periodo_texto)

    # 3. Retornar todas las figuras en el orden de los Outputs
    return fig_dep, fig_ens, fig_dem, fig_nem_per, fig_nem_tit, fig_rural, fig_tit_dep
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, callback, Output, Input, State
from dashboard_titulados.metrics.queries_titulados import *
from dashboard_titulados.graphics.graphics import *

SIDEBAR_STYLE = {
    "height": "calc(100vh - 56px)",
    "overflow-y": "auto",
    "background-color": "#f8f9fa",
    "padding": "2rem 1rem",
    "border-right": "1px solid #dee2e6"
}

CONTENT_STYLE = {
    "height": "calc(100vh - 56px)",
    "overflow-y": "auto",
    "padding": "2rem 1rem",
    "background-color": "#ffffff"
}

# --- FUNCIÓN GENERADORA DE TARJETAS KPI ---
def crear_card_metric_estatica(id_valor, titulo, icono_class):
    return dbc.Card(
        dbc.CardBody([
            dbc.Row([
                # Icono decorativo en color naranja ECAS/Warning
                dbc.Col(html.I(className=f"fas {icono_class} fa-2x", style={"color": "#f39c12"}), width=3),
                dbc.Col([
                    html.P(titulo, className="text-muted mb-0", style={"fontSize": "1.1rem", "fontWeight": "600"}),
                    # Spinner que envuelve el valor mientras carga el callback
                    dbc.Spinner(
                        html.H4(id=id_valor, className="mb-0", style={"fontWeight": "bold"}),
                        size="sm", 
                        color="warning",
                        spinner_style={"float": "left"}
                    ),
                ], width=9),
            ], align="center")
        ]), className="shadow-sm border-0 rounded"
    )

# --- DEFINICIÓN DEL LAYOUT ---
layout = dbc.Container([
    # Stores para manejo de datos en memoria si es necesario
    dcc.Store(id='store-datos-competencia'),
    dcc.Store(id='store-datos-permanencia'),

    dbc.Row([
        # --- COLUMNA IZQUIERDA: PANEL DE CONTROL (Filtros) ---
        dbc.Col([
            html.Div([
                html.H4("Parámetros de Análisis", className="text-primary mb-4"),
                html.Hr(),

                html.Label("Población:", className="fw-bold"),
                dbc.RadioItems(
                    id='radio-poblacion-ex-alumnos',
                    options=[
                        {"label": "Todos", "value": "Todos"},
                        {"label": "Titulados", "value": "Titulados"},
                        {"label": "Desertores", "value": "Desertores"},
                    ],
                    value="Todos",
                    className="mb-4",
                    inline=True
                ),
                
                # Rango de Años
                html.Label("Rango de Cohortes (Ingreso):", className="fw-bold"),
                dcc.RangeSlider(
                    id='slider-años-desertores',
                    min=2007, max=2025, step=1,
                    value=[2007, 2007],
                    marks={i: str(i) for i in range(2007, 2026, 3)},
                    className="mb-4"
                ),

                html.Label("Cantidad de resultados (Top N):", className="fw-bold"),
                dcc.Slider(
                    id='slider-top-n-desertores',
                    min=5, max=20, step=5,
                    value=10,
                    marks={5: '5', 10: '10', 15: '15', 20: '20'},
                    className="mb-4"
                ),
                
                # Jornada
                html.Label("Jornada ECAS:", className="fw-bold"),
                dbc.RadioItems(
                    id='radio-jornada-desertores',
                    options=[
                        {"label": "Ambas", "value": "Todas"},
                        {"label": "Diurna", "value": "Diurna"},
                        {"label": "Vespertina", "value": "Vespertina"},
                    ],
                    value="Todas",
                    className="mb-4",
                    inline=True
                ),

                # Género
                html.Label("Género:", className="fw-bold"),
                dbc.RadioItems(
                    id='radio-genero-desertores',
                    options=[
                        {"label": "Todos", "value": "Todos"},
                        {"label": "Hombre", "value": "Hombre"},
                        {"label": "Mujer", "value": "Mujer"},
                    ],
                    value="Todos",
                    className="mb-4",
                    inline=True
                ),
            ])
        ], width=3, style=SIDEBAR_STYLE),

        # --- COLUMNA DERECHA: VISUALIZACIONES (Scrollable) ---
        dbc.Col([
            # Cabecera
            dbc.Row([
                dbc.Col([
                    html.H2("Seguimiento de EX Estudiantes ECAS", className="border-bottom pb-2"),
                    html.P("Evaluación de educación continua que incluye tanto a titulados de ECAS como Desertores", className="lead text-muted")
                ])
            ], className="mb-4"),

            # Fila de KPIs Superiores (Tarjetas Estáticas)
            dbc.Row([
                dbc.Col(crear_card_metric_estatica("val-cohorte", "Total Cohorte", "fa-users"), width=4),
                dbc.Col(crear_card_metric_estatica("val-titulados", "Total Titulados", "fa-graduation-cap"), width=4),
                dbc.Col(crear_card_metric_estatica("val-desertores", "Total Desertores", "fa-door-open"), width=4),
            ], className="mb-4"),

            # Fila 1: Gráfico Principal de Ingresos
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.I(className="fas fa-exclamation me-2"),
                            "Reingreso inmediato"
                        ], className="fw-bold bg-primary text-white"),
                        dbc.CardBody([
                            dcc.Loading(
                                id="loading-ingresos",
                                type="circle",
                                children=dcc.Graph(id='grafico-reingreso-inmediato', style={"height": "450px"}),
                                color="#FF6600"
                            )
                        ])
                    ], className="shadow-sm mb-4")
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.I(className="fas fa-briefcase me-2"),
                            "Reingreso máximo"
                        ], className="fw-bold bg-primary text-white"),
                        dbc.CardBody([
                            dcc.Loading(
                                id="loading-ingresos",
                                type="circle",
                                children=dcc.Graph(id='grafico-reingreso-maximo', style={"height": "450px"}),
                                color="#FF6600"
                            )
                        ])
                    ], className="shadow-sm mb-4")
                ], width=6)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            dbc.Row([
                                dbc.Col("Análisis de Destino Detallado", width=4, className="align-self-center"),
                                dbc.Col([
                                    # Selector de Nivel (solo relevante cuando se ve 'Carreras')
                                    html.Span("Nivel: ", className="small me-2"),
                                    dbc.Select(
                                        id="selector-nivel-carrera",
                                        options=[
                                            {"label": "Todos", "value": "Todos"},
                                            {"label": "Pregrado", "value": "Pregrado"},
                                            {"label": "Postítulo", "value": "Postítulo"},
                                            {"label": "Postgrado", "value": "Postgrado"},
                                        ],
                                        value="Todos", size="sm",
                                        style={"width": "140px", "display": "inline-block", "margin-right": "15px"}
                                    ),
                                ], width=8, className="text-end")
                            ])
                        ], className="fw-bold"),
                        dbc.CardBody([
                            # Sistema de Pestañas para elegir qué gráfico ver
                            dbc.Tabs([
                                dbc.Tab(label="Top Instituciones", tab_id="tab-instituciones"),
                                dbc.Tab(label="Top Carreras", tab_id="tab-carreras"),
                                dbc.Tab(label="Tipo de Institución", tab_id="tab-tipo-inst"),
                            ], id="tabs-fuga", active_tab="tab-instituciones", className="mb-3"),
                            
                            # Contenedor único para el gráfico seleccionado
                            dcc.Loading(
                                dcc.Graph(id="grafico-destino-unificado", style={"height": "500px"})
                            )
                        ])
                    ], className="shadow-sm mb-4")
                ], width=12)
            ]),
            
            # Espacio final
            html.Div(style={"height": "50px"})

        ], width=9, style=CONTENT_STYLE)
    ])
], fluid=True)

@callback(
    [Output("val-cohorte", "children"),
     Output("val-titulados", "children"),
     Output("val-desertores", "children")],
    [Input("slider-años-desertores", "value"),
     Input("radio-jornada-desertores", "value"),
     Input("radio-genero-desertores", "value")]
)
def update_kpi_cards(rango_anios, jornada, genero):
    # Obtener los valores desde la DB
    total_ingreso, total_tit, total_des = get_kpis_cabecera(rango_anios, jornada, genero)
    
    # Formatear con separador de miles
    return (
        f"{total_ingreso:,}".replace(",", "."),
        f"{total_tit:,}".replace(",", "."),
        f"{total_des:,}".replace(",", ".")
    )

@callback(
    [Output('grafico-reingreso-inmediato', 'figure'),
     Output('grafico-reingreso-maximo', 'figure')],
    [Input('slider-años-desertores', 'value'),
     Input('radio-poblacion-ex-alumnos', 'value'), # "Todos", "Titulados" o "Desertores"
     Input('radio-jornada-desertores', 'value'),
     Input('radio-genero-desertores', 'value')]
)
def update_reingreso_graphs(rango_anios, poblacion, jornada, genero):
    # 1. Llamada a Query Unificada para Reingreso Inmediato (Primero)
    df_inmediato = get_nivel_post_salida(
        rango_anios=rango_anios, 
        tipo_poblacion=poblacion,  # Pasamos "Todos" directamente
        criterio="Primero", 
        jornada=jornada, 
        genero=genero
    )
    
    # 2. Llamada a Query Unificada para Reingreso Máximo (Maximo)
    df_maximo = get_nivel_post_salida(
        rango_anios=rango_anios, 
        tipo_poblacion=poblacion, 
        criterio="Maximo", 
        jornada=jornada, 
        genero=genero
    )

    # 3. Llamada a Generadores de Gráficos
    # Los generadores ya están preparados para recibir el DataFrame y el nombre de la población
    fig_inm = crear_grafico_reingreso_inmediato(df_inmediato, poblacion)
    fig_max = crear_grafico_reingreso_maximo(df_maximo, poblacion)

    return fig_inm, fig_max

@callback(
    Output("grafico-destino-unificado", "figure"),
    [Input("tabs-fuga", "active_tab"),
     Input("slider-años-desertores", "value"),
     Input("radio-poblacion-ex-alumnos", "value"),
     Input("radio-jornada-desertores", "value"),
     Input("radio-genero-desertores", "value"),
     Input("slider-top-n-desertores", "value"),
     Input("selector-nivel-carrera", "value")]
)
def update_destino_unificado(tab_activa, rango, poblacion, jornada, genero, top_n, nivel):
    # Lógica para determinar qué dimensión consultar
    if tab_activa == "tab-instituciones":
        dimension = "inst_destino"
        titulo = f"Top {top_n} Instituciones de Destino"
        es_horizontal = True
        nivel_query = "Todos" # En instituciones vemos todo el universo
        
    elif tab_activa == "tab-carreras":
        dimension = "carrera_destino"
        titulo = f"Top {top_n} Carreras ({nivel})"
        es_horizontal = True
        nivel_query = nivel
        
    else: # tab-tipo-inst
        dimension = "tipo_inst_1"
        titulo = "Distribución por Tipo de Institución"
        es_horizontal = False
        nivel_query = "Todos"

    # Llamada a la query unificada (la que creamos en el paso anterior)
    df = get_top_destinos_filtrado(
        rango_anios=rango,
        tipo_poblacion=poblacion,
        dimension=dimension,
        nivel=nivel_query,
        jornada=jornada,
        genero=genero,
        top_n=top_n
    )

    # Generación del gráfico usando tu función de plots
    # Si es Institución o Carrera -> Barras Horizontales
    # Si es Tipo Inst -> Pie Chart
    return crear_grafico_top_destinos(df, titulo, es_horizontal=es_horizontal)
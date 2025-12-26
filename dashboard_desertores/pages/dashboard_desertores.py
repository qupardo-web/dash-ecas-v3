import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, callback, Output, Input, State
from dashboard_desertores.metrics.queries_desertores import *
from dashboard_desertores.graphics.graphics import *
import pandas as pd

# --- ESTILOS PERSONALIZADOS ---
# Ajustamos el alto considerando la Navbar (aprox 56px)
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

# --- DEFINICIÓN DEL LAYOUT ---
layout = dbc.Container([

    dcc.Store(id='store-datos-competencia'),

    dbc.Row([
        # --- COLUMNA IZQUIERDA: PANEL DE CONTROL (Filtros) ---
        dbc.Col([
            html.Div([
                html.H4("Parámetros de Análisis", className="text-primary mb-4"),
                html.Hr(),
                
                # Selector de Instituciones (Comparativa)
                html.Label("Instituciones de Competencia:", className="fw-bold"),
                dcc.Dropdown(
                    id='selector-instituciones-competencia', # Este es el ID que Dash reconoce ahora
                    options=[], # Se poblarán mediante el callback que creamos antes
                    multi=True,
                    placeholder="Seleccione para comparar...",
                    className="mb-4"
                ),
                
                # Rango de Años (Cohortes)
                html.Label("Rango de Cohortes (Ingreso):", className="fw-bold"),
                dcc.RangeSlider(
                    id='slider-años-desertores',
                    min=2007, max=2025, step=1,
                    value=[2018, 2024],
                    marks={i: str(i) for i in range(2007, 2026, 3)},
                    className="mb-4"
                ),
                
                # Selector de Top N
                html.Label("Mostrar Top N del Mercado:", className="fw-bold"),
                dcc.Slider(
                    id='slider-top-n-desertores',
                    min=5, max=20, step=5,
                    value=10,
                    marks={i: f"Top {i}" for i in [5, 10, 15, 20]},
                    className="mb-4"
                ),
                
                # Filtro de Jornada
                html.Label("Jornada:", className="fw-bold"),
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

                dbc.Button(
                    "Aplicar Filtros", 
                    id='boton-aplicar-filtros', 
                    color="primary", 
                    className="w-100 mt-3 shadow-sm"
                ),
                
                html.Div(className="mt-5 p-3 bg-white border rounded shadow-sm", children=[
                    html.Small("Nota: ECAS (Cód. 104) se incluye automáticamente en todas las comparativas para propósitos de referencia institucional.", 
                               className="text-muted italic")
                ])
            ])
        ], width=3, style=SIDEBAR_STYLE),

        # --- COLUMNA DERECHA: VISUALIZACIONES (Scrollable) ---
        dbc.Col([
            # Cabecera de la página
            dbc.Row([
                dbc.Col([
                    html.H2("Análisis de Deserción y Competencia", className="border-bottom pb-2"),
                    html.P("Seguimiento longitudinal de cohortes y benchmarking de mercado.", className="lead text-muted")
                ])
            ], className="mb-4"),

            # Fila 1: Gráfico Principal de Ingresos
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.I(className="fas fa-chart-line me-2"),
                            "Evolución Histórica de Matrícula (Ingresos por Cohorte)"
                        ], className="fw-bold bg-primary text-white"),
                        dbc.CardBody([
                            dcc.Loading(
                                id="loading-ingresos",
                                type="circle",
                                children=dcc.Graph(id='grafico-ingresos-competencia', style={"height": "450px"}),
                                color="#FF6600" # Naranja ECAS
                            )
                        ])
                    ], className="shadow-sm mb-4")
                ], width=12)
            ]),

            # Fila 2: Gráficos Secundarios (Lado a Lado)
            dbc.Row([
                # Comparativa de Deserción Real
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Tasa de Deserción Anual (%)", className="fw-bold"),
                        dbc.CardBody([
                            dcc.Graph(id='grafico-tasa-desercion', style={"height": "350px"})
                        ])
                    ], className="shadow-sm mb-4")
                ], width=6),
                
                # Distribución de la Selección
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Composición por Jornada (Selección)", className="fw-bold"),
                        dbc.CardBody([
                            dcc.Graph(id='grafico-pie-jornada', style={"height": "350px"})
                        ])
                    ], className="shadow-sm mb-4")
                ], width=6)
            ]),

            # Fila 3: Tabla de Datos Detallada
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Detalle de Matrícula por Institución y Carrera", className="fw-bold"),
                        dbc.CardBody([
                            html.Div(id='tabla-detalle-competencia')
                        ])
                    ], className="shadow-sm mb-5")
                ], width=12)
            ]),
            
            # Espacio extra al final para mejorar la sensación de scroll
            html.Div(style={"height": "50px"})

        ], width=9, style=CONTENT_STYLE)
    ]) # g=0 elimina los gutters para un look más integrado
], fluid=True)

@callback(
    [Output('selector-instituciones-competencia', 'options'),
     Output('selector-instituciones-competencia', 'value')],
    Input('url', 'pathname') # Se ejecuta al cargar la página
)
def poblar_selector_competencia(_):
    nombres_top = get_nombres_top_competencia(top_n=10)
    
    options = [{'label': nombre, 'value': nombre} for nombre in nombres_top]
    
    return options, []

# 1. CALLBACK DE CARGA INICIAL (Datos en Memoria)
@callback(
    Output('store-datos-competencia', 'data'),
    Input('url', 'pathname'), # Se dispara una sola vez al cargar la página
)
def inicializar_datos_dash(_):
    # Cargamos el Top 10 histórico por defecto para tener datos inmediatos
    df_inicial = get_ingresos_competencia_parametrizado(top_n=10, anio_min=2007, anio_max=2025)
    return df_inicial.to_dict('records')

# 2. CALLBACK DEL GRÁFICO (Controlado por Botón)
@callback(
    Output('grafico-ingresos-competencia', 'figure'),
    Input('boton-aplicar-filtros', 'n_clicks'),
    [State('store-datos-competencia', 'data'),
     State('slider-años-desertores', 'value'),
     State('slider-top-n-desertores', 'value'),
     State('radio-jornada-desertores', 'value'),
     State('selector-instituciones-competencia', 'value')],
    prevent_initial_call=False
)
def update_dashboard_competencia(n_clicks, data_cache, rango_anios, top_n, jornada, inst_manuales):
    # Si es la carga inicial (n_clicks es None o 0)
    if not n_clicks:
        df = pd.DataFrame(data_cache)
    else:
        # Solo consultamos la DB si el usuario presionó el botón para cambiar parámetros
        df = get_ingresos_competencia_parametrizado(
            top_n=top_n, 
            anio_min=rango_anios[0], 
            anio_max=rango_anios[1],
            jornada=jornada
        )
    
    # Filtrado manual adicional por Dropdown (Pandas es instantáneo aquí)
    if inst_manuales:
        df = df[(df['nomb_inst'].isin(inst_manuales)) | (df['cod_inst'] == 104)]
        
    return create_ingresos_line_chart(df)
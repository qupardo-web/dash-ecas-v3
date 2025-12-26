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
    dcc.Store(id='store-datos-permanencia'),

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
                        dbc.CardHeader("Permanencia N → N+1 (%)", className="fw-bold"),
                        dbc.CardBody([
                            dcc.Loading(
                                type="circle",
                                children=dcc.Graph(
                                    id='grafico-permanencia-n1',
                                    style={"height": "350px"}
                                )
                            )
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

@callback(
    Output('store-datos-permanencia', 'data'),
    Input('url', 'pathname'), # Se dispara al cargar la página
)
def inicializar_permanencia_dash(_):
    # Cargamos el Top 10 histórico de permanencia (2007-2025)
    # Usamos la query optimizada que no restringe cohorte == periodo
    df_inicial = get_permanencia_n_n1_competencia(
        anio_min=2007, 
        anio_max=2024, # Máximo 2024 para poder evaluar el retorno en 2025
        jornada="Todas"
    )
    return df_inicial.to_dict('records')

@callback(
    Output('grafico-ingresos-competencia', 'figure'),
    Input('boton-aplicar-filtros', 'n_clicks'),
    [State('slider-años-desertores', 'value'),
     State('slider-top-n-desertores', 'value'),
     State('radio-jornada-desertores', 'value'),
     State('selector-instituciones-competencia', 'value')],
    prevent_initial_call=True  # IMPORTANTE: Evita la carga al inicio
)
def update_ingresos_on_click(n_clicks, rango_anios, top_n, jornada, inst_manuales):
    if n_clicks is None:
        return go.Figure()
        
    # Consultamos la DB solo al hacer click
    df = get_ingresos_competencia_parametrizado(
        top_n=top_n, 
        anio_min=rango_anios[0], 
        anio_max=rango_anios[1],
        jornada=jornada
    )
    
    # Filtrado manual en Python (opcional si la query ya lo hace)
    if inst_manuales:
        df = df[(df['nomb_inst'].isin(inst_manuales)) | (df['nomb_inst'].str.contains("ESCUELA DE CONTADORES", case=False))]
        
    return create_ingresos_line_chart(df)

@callback(
    Output('grafico-permanencia-n1', 'figure'),
    Input('boton-aplicar-filtros', 'n_clicks'),
    [State('slider-años-desertores', 'value'),
     State('slider-top-n-desertores', 'value'),
     State('selector-instituciones-competencia', 'value'),
     State('radio-jornada-desertores', 'value')],
    prevent_initial_call=True
)
def update_permanencia_on_click(n_clicks, rango, top_n, inst_manuales, jornada):
    if n_clicks is None:
        return go.Figure()

    # 1. Obtener datos crudos
    df_full = get_permanencia_n_n1_competencia(rango[0], rango[1], jornada)
    
    if df_full.empty:
        return go.Figure().update_layout(title="Sin datos para la selección")

    # 2. CALCULAR LA TASA (Aquí faltaba asegurar que la columna exista)
    df_full['tasa_permanencia_pct'] = (df_full['retenidos_n1'] * 100.0 / df_full['base_n'].replace(0, pd.NA)).fillna(0).round(2)

    # 3. Lógica de Filtrado en Python
    # Normalizamos a Mayúsculas para evitar errores de coincidencia
    df_full['nomb_inst_upper'] = df_full['nomb_inst'].str.upper()
    mask_ecas = df_full['nomb_inst_upper'].str.contains("ESCUELA DE CONTADORES|ECAS", na=False)

    if inst_manuales:
        # Filtrar por selección + ECAS
        df_final = df_full[df_full['nomb_inst'].isin(inst_manuales) | mask_ecas].copy()
    else:
        # Top N dinámico
        df_competencia = df_full[~mask_ecas]
        ranking = df_competencia.groupby('nomb_inst')['base_n'].mean().sort_values(ascending=False).head(top_n).index.tolist()
        df_final = df_full[df_full['nomb_inst'].isin(ranking) | mask_ecas].copy()

    # 4. Generar gráfico
    return create_permanencia_line_chart(df_final)
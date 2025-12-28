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
                                    style={
                                        "maxHeight": "350px", 
                                        "width": "100%",
                                        "overflowY": "auto", 
                                        "overflowX": "hidden",  # Corta cualquier desborde visual
                                        "padding-bottom": "20px" # Espacio de seguridad
                                    }
                                )
                            )
                        ])
                    ], className="shadow-sm mb-4")
                ], width=6),
                
                # Distribución de la Selección
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Permanencia por jornada (ECAS)", className="fw-bold"),
                        dbc.CardBody([
                            dcc.Loading(
                                type="circle",
                                children=dcc.Graph(
                                    id='grafico-permanencia-jornada',
                                    style={
                                        "maxHeight": "350px", 
                                        "width": "100%",
                                        "overflowY": "auto", 
                                        "overflowX": "hidden",  # Corta cualquier desborde visual
                                        "padding-bottom": "20px" # Espacio de seguridad
                                    }
                                )
                            )
                        ])
                    ], className="shadow-sm mb-4")
                ], width=6)
            ], className="mb-5"),

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
    [Input('radio-jornada-desertores', 'value'),
     Input('slider-top-n-desertores', 'value')]
)
def actualizar_opciones_selector(jornada, top_n):

    df_ranking = get_ingresos_competencia_parametrizado(
        top_n=top_n, 
        anio_min=2007, # Ranking basado en datos recientes (últimos 5 años)
        anio_max=2025, 
        jornada=jornada
    )
    
    if df_ranking.empty:
        return [], []

    nombres_top = [n for n in df_ranking['nomb_inst'].unique() 
                   if "ESCUELA DE CONTADORES" not in n.upper()]
    
    options = [{'label': nombre, 'value': nombre} for nombre in nombres_top]
    
    return options, []

@callback(
    [Output('grafico-ingresos-competencia', 'figure'),
     Output('grafico-permanencia-n1', 'figure')],
     Output('grafico-permanencia-jornada', 'figure'),
    Input('boton-aplicar-filtros', 'n_clicks'),
    [State('slider-años-desertores', 'value'),
     State('slider-top-n-desertores', 'value'),
     State('radio-jornada-desertores', 'value'),
     State('selector-instituciones-competencia', 'value')],
    prevent_initial_call=True
)
def update_full_dashboard(n_clicks, rango, top_n, jornada, inst_manuales):
    if not n_clicks:
        return go.Figure(), go.Figure()

    df_ingresos_raw = get_ingresos_competencia_parametrizado(top_n, rango[0], rango[1], jornada)
    df_perm_raw = get_permanencia_n_n1_competencia(rango[0], rango[1], jornada)
    df_cambio = get_distribucion_cambio_jornada_ecas(rango[0], rango[1], jornada)

    # --- PROCESAMIENTO OPTIMIZADO DE PANDAS ---
    # Definimos una función interna de filtrado para no repetir código
    def filtrar_df(df, is_perm=False):
        if df.empty: return df
        
        # Identificar ECAS de forma robusta
        mask_ecas = df['nomb_inst'].str.upper().str.contains("ESCUELA DE CONTADORES|ECAS", na=False)
        
        if inst_manuales:
            return df[df['nomb_inst'].isin(inst_manuales) | mask_ecas].copy()
        else:
            # Ranking basado en la métrica principal de cada tabla
            metrica = 'base_n' if is_perm else 'total_ingresos'
            ranking = df[~mask_ecas].groupby('nomb_inst')[metrica].mean()\
                                    .sort_values(ascending=False).head(top_n).index.tolist()
            return df[df['nomb_inst'].isin(ranking) | mask_ecas].copy()

    # --- CÁLCULOS Y GRÁFICOS ---
    # Procesar Permanencia
    df_perm_raw['tasa_permanencia_pct'] = (df_perm_raw['retenidos_n1'] * 100.0 / 
                                           df_perm_raw['base_n'].replace(0, pd.NA)).fillna(0).round(2)
    
    #Filtrado
    df_perm_final = filtrar_df(df_perm_raw, is_perm=True)
    df_ing_final = filtrar_df(df_ingresos_raw, is_perm=False)

    fig_ing= create_ingresos_line_chart(df_ing_final)
    fig_perm= create_permanencia_line_chart(df_perm_final)
    fig_cambio = create_cambio_jornada_charts(df_cambio)
    

    return fig_ing, fig_perm, fig_cambio
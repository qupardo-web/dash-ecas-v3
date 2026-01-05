import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, callback, Output, Input, State
from dashboard_desertores.metrics.queries_desertores import *
from dashboard_desertores.metrics.metrics_desertores import *
from dashboard_desertores.graphics.graphics import *
import pandas as pd
import numpy as np

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
                    value=[2007, 2007],
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
                        dbc.CardHeader([
                            dbc.Row([
                                dbc.Col("Tasas de supervivencia y titulación por cohorte", width=8),
                                dbc.Col(
                                    dcc.Dropdown(
                                        id='selector-inst-supervivencia',
                                        placeholder="Filtrar institución...",
                                        className="text-dark"
                                    ), width=4
                                )
                            ])
                        ], className="fw-bold"),
                        dbc.CardBody([
                            dcc.Graph(id='grafico-supervivencia-titulacion')
                        ])
                    ], className="shadow-sm mb-4")
                ], width=12)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            dbc.Row([
                                dbc.Col("Análisis de Destino (Fuga)", width=6),
                                dbc.Col([
                                    dbc.RadioItems(
                                        id="radio-dimension-fuga",
                                        options=[
                                            {"label": "Institución", "value": "inst_destino"},
                                            {"label": "Carrera", "value": "carrera_destino"},
                                            {"label": "Área", "value": "area_conocimiento_destino"},
                                        ],
                                        value="inst_destino",
                                        inline=True,
                                    )
                                ], width=6, className="text-end")
                            ])
                        ]),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col(dcc.Graph(id="pie-fuga-1"), width=4),
                                dbc.Col(dcc.Graph(id="pie-fuga-2"), width=4),
                                dbc.Col(dcc.Graph(id="pie-fuga-3"), width=4),
                            ])
                        ])
                    ], className="shadow-sm mb-4")
                ], width=12)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.I(className="fas fa-history me-2"),
                            "Distribución de Tiempo de Descanso (Post-ECAS)"
                        ], className="fw-bold bg-light"),
                        dbc.CardBody([
                            html.P(
                                "Mide el tiempo transcurrido desde que el alumno abandona ECAS "
                                "hasta que se registra su primera matrícula en otra institución.",
                                className="text-muted small mb-4"
                            ),
                            dcc.Loading(
                                type="circle",
                                children=dcc.Graph(
                                    id='grafico-tiempo-descanso',
                                    style={"height": "400px"}
                                ),
                                color="#FF6600"
                            )
                        ])
                    ], className="shadow-sm mb-4")
                ], width=12)
            ], className="mb-4"),

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Comparativa de Éxito Académico (Trayectorias)", className="fw-bold bg-light"),
                        dbc.CardBody([
                            dbc.Row([
                                # GAUGE 1: Los que se FUERON de ECAS y se titularon fuera
                                dbc.Col([
                                    dcc.Loading(dcc.Graph(id='grafico-gauge-titulacion-ext'))
                                ], width=6, className="border-right"),
                                
                                # GAUGE 2: Los que VINIERON de fuera y se titularon en ECAS
                                dbc.Col([
                                    dcc.Loading(dcc.Graph(id='grafico-gauge-exito-captacion'))
                                ], width=6),
                            ]),
                            html.Hr(),
                            html.P(
                                "Izquierda: Desertores de ECAS que terminaron su carrera en otra institución. "
                                "Derecha: Alumnos que venían de otras instituciones y lograron titularse en ECAS.",
                                className="text-muted small text-center"
                            )
                        ])
                    ], className="shadow-sm mb-4")
                ], width=12)
            ]),
            
            # Espacio extra al final para mejorar la sensación de scroll
            html.Div(style={"height": "50px"})


        ], width=9, style=CONTENT_STYLE)
    ]) # g=0 elimina los gutters para un look más integrado
], fluid=True)

@callback(
    [Output('selector-inst-supervivencia', 'options'),
     Output('selector-inst-supervivencia', 'value')],
    [Input('selector-instituciones-competencia', 'options')],
    [State('selector-inst-supervivencia', 'value')]
)
def sync_survival_dropdown(options_globales, valor_actual):
    NOMBRE_ECAS = "IP ESCUELA DE CONTADORES AUDITORES DE SANTIAGO"
    
    nombres_existentes = [opt['value'] for opt in options_globales]
    nuevas_opciones = options_globales.copy()
    
    if NOMBRE_ECAS not in nombres_existentes:
        nuevas_opciones.insert(0, {'label': NOMBRE_ECAS, 'value': NOMBRE_ECAS})
    
    if not valor_actual or valor_actual not in [o['value'] for o in nuevas_opciones]:
        return nuevas_opciones, NOMBRE_ECAS
    
    return nuevas_opciones, valor_actual

@callback(
    [Output('selector-instituciones-competencia', 'options'),
     Output('selector-instituciones-competencia', 'value')],
    [Input('radio-jornada-desertores', 'value'),
     Input('slider-top-n-desertores', 'value')]
)
def actualizar_opciones_selector(jornada, top_n):
    # Nombre exacto de la institución según tu base de datos
    NOMBRE_ECAS = "IP ESCUELA DE CONTADORES AUDITORES DE SANTIAGO"

    df_ranking = get_ingresos_competencia_parametrizado(
        top_n=top_n, 
        anio_min=2007, 
        anio_max=2025, 
        jornada=jornada
    )
    
    if df_ranking.empty:
        options_solo_ecas = [{'label': NOMBRE_ECAS, 'value': NOMBRE_ECAS}]
        return options_solo_ecas, []

    nombres_competencia = [n for n in df_ranking['nomb_inst'].unique() 
                          if NOMBRE_ECAS not in n.upper()]
    
    options = [{'label': nombre, 'value': nombre} for nombre in nombres_competencia]
    
    options.insert(0, {'label': NOMBRE_ECAS, 'value': NOMBRE_ECAS})
    
    return options, []

@callback(
    [Output('grafico-ingresos-competencia', 'figure'),
     Output('grafico-permanencia-n1', 'figure'),
     Output('grafico-permanencia-jornada', 'figure'),
     Output('grafico-tiempo-descanso', 'figure')],
    [Input('slider-años-desertores', 'value'),
     Input('slider-top-n-desertores', 'value'),
     Input('radio-jornada-desertores', 'value'),
     Input('radio-genero-desertores', 'value'), # Nuevo Input
     Input('selector-instituciones-competencia', 'value')]
)
def update_full_dashboard_reactive(rango, top_n, jornada, genero, inst_manuales):
    # Pasamos 'genero' a todas las funciones de métricas SQL
    df_ingresos_raw = get_ingresos_competencia_parametrizado(top_n, rango[0], rango[1], jornada, genero)
    df_perm_raw = get_permanencia_n_n1_competencia(rango[0], rango[1], jornada, genero)
    df_cambio = get_distribucion_cambio_jornada_ecas(rango[0], rango[1], jornada, genero)
    
    # Nota: El Excel de descanso debe tener columna de género para filtrar aquí
    df_descanso = get_tiempo_de_descanso_procesado(rango, jornada, genero)

    def filtrar_df(df, is_perm=False):
        if df is None or df.empty: return pd.DataFrame()
        if inst_manuales and len(inst_manuales) > 0:
            return df[df['nomb_inst'].isin(inst_manuales)].copy()
        else:
            mask_ecas = df['nomb_inst'].str.upper().str.contains("ESCUELA DE CONTADORES|ECAS", na=False)
            metrica = 'base_n' if is_perm else 'total_ingresos'
            ranking = df[~mask_ecas].groupby('nomb_inst')[metrica].mean()\
                                    .sort_values(ascending=False).head(top_n).index.tolist()
            return df[df['nomb_inst'].isin(ranking) | mask_ecas].copy()

    df_ing_final = filtrar_df(df_ingresos_raw, is_perm=False)
    df_perm_final = filtrar_df(df_perm_raw, is_perm=True)

    # Lógica de Título Dinámico con Género
    label_genero = f" ({genero})" if genero != "Todos" else ""
    titulo_ingresos = f"Evolución Histórica de Matrícula{label_genero}"
    
    instituciones_unicas = df_ing_final['nomb_inst'].unique()
    if len(instituciones_unicas) == 1:
        nombre_inst = instituciones_unicas[0]
        promedio_ingreso = df_ing_final['total_ingresos'].mean()
        titulo_ingresos = f"Matrícula{label_genero}: {nombre_inst} (Promedio: {promedio_ingreso:.0f})"

    fig_ing = create_ingresos_line_chart(df_ing_final)
    fig_ing.update_layout(title=titulo_ingresos)

    return (
        fig_ing,
        create_permanencia_line_chart(df_perm_final),
        create_cambio_jornada_charts(df_cambio),
        create_tiempo_descanso_horiz_chart(df_descanso)
    )

@callback(
    [Output('grafico-supervivencia-titulacion', 'figure'),
     Output('pie-fuga-1', 'figure'),
     Output('pie-fuga-2', 'figure'),
     Output('pie-fuga-3', 'figure'),
     Output('grafico-gauge-titulacion-ext', 'figure'),
     Output('grafico-gauge-exito-captacion', 'figure')],
    [Input('slider-años-desertores', 'value'),
     Input('selector-inst-supervivencia', 'value'),
     Input('radio-dimension-fuga', 'value'),
     Input('radio-jornada-desertores', 'value'),
     Input('radio-genero-desertores', 'value')] 
)
def update_bottom_section_reactive(rango, inst_surv, dim_fuga, jornada, genero):
    
    target_inst = inst_surv if inst_surv else "IP ESCUELA DE CONTADORES AUDITORES DE SANTIAGO"
    df_survival = get_supervivencia_vs_titulacion_data(rango, [target_inst], genero, jornada)
    fig_surv = create_survival_graduation_chart(df_survival, target_inst)

    df_metrica_ext = get_metrica_titulacion_externa(rango, jornada, genero)
    fig_gauge = create_gauge_titulacion_externa(df_metrica_ext)

    df_captacion = get_metrica_exito_captacion(rango, jornada, genero)
    fig_gauge_int = create_gauge_exito_captacion(df_captacion)

    # 3. Análisis de Destino (Fuga)
    figs_fuga = []
    titulos = ["1er Destino", "2do Destino", "3er Destino"]
    for i in range(1, 4):
        df_f = get_fuga_por_rango(
            columna=dim_fuga, 
            orden=i, 
            rango_anios=rango, 
            jornada=jornada, 
            genero=genero, 
            top_n=5
        )
        figs_fuga.append(create_fuga_pie_chart(df_f, titulos[i-1]))

    return fig_surv, figs_fuga[0], figs_fuga[1], figs_fuga[2], fig_gauge, fig_gauge_int
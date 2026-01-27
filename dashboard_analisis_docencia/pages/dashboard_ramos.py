import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, callback, Output, Input, State
from dashboard_analisis_docencia.metrics.queries_ramos import *
from dashboard_analisis_docencia.graphics.graphics import *

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

layout = dbc.Container([

    dbc.Row([
        dbc.Col([
            html.Div([
                html.H4("Parámetros de Análisis", className="text-primary mb-4"),
                html.Hr(),
                
                html.Label("Rango de Cohortes (Ingreso):", className="fw-bold"),
                dcc.RangeSlider(
                    id='slider-años',
                    min=2015, max=2025, step=1,
                    value=[2020, 2020],
                    marks={i: str(i) for i in range(2015, 2026, 2)},
                    className="mb-4"
                ),
                
                html.Label("Jornada:", className="fw-bold"),
                dbc.RadioItems(
                    id='radio-jornada',
                    options=[
                        {"label": "Ambas", "value": "Todas"},
                        {"label": "Diurna", "value": "D"},
                        {"label": "Vespertina", "value": "V"},
                    ],
                    value="Todas",
                    className="mb-4",
                    inline=True
                ),

                html.Label("Género:", className="fw-bold"),
                dbc.RadioItems(
                    id='radio-genero',
                    options=[
                        {"label": "Todos", "value": "Todos"},
                        {"label": "Hombre", "value": "M"},
                        {"label": "Mujer", "value": "F"},
                    ],
                    value="Todos",
                    className="mb-4",
                    inline=True
                ),
            ])
        ], width=3, style=SIDEBAR_STYLE),

        dbc.Col([
            dbc.Row([
                dbc.Col([
                    html.H2("Analisis General por rangos", className="border-bottom pb-2"),
                    html.P("Dashboard para el analisis de matriculas, vacantes, ramos y docentes de ECAS.", className="lead text-muted")
                ])
            ], className="mb-4"),

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        # Header con título dinámico y selectores
                        dbc.CardHeader([
                            dbc.Row([
                                dbc.Col([
                                    html.I(className="fas fa-users me-2"),
                                    html.Span("Matrículas Totales", id="titulo-dinamico-matriculas") # ID para el título
                                ], width=8, className="mt-1 d-flex align-items-center"),
                                
                                dbc.Col([
                                    dbc.RadioItems(
                                        id="radio-tipo-matricula",
                                        options=[
                                            {"label": "Nuevas", "value": "Nuevas"},
                                            {"label": "Totales", "value": "Totales"},
                                        ],
                                        value="Totales",
                                        inline=True,
                                        className="mt-2 text-white small",
                                        input_class_name="me-1",
                                        label_class_name="me-3"
                                    )
                                ], width=4, className="d-flex align-items-center justify-content-end"),
                            ])
                        ], style={"background-color": "#162f8a"}, className="fw-bold text-white"),

                        dbc.CardBody([
                            dcc.Loading(
                                id="loading-ingresos",
                                type="circle",
                                children=[
                                    html.Div(id='contenedor-matriculas', children=[
                                        dcc.Graph(id='grafico-matriculas')
                                    ], className="mb-4"),
                                    dbc.Row(id='contenedor-matriculas-2', children=[], className="mt-4")
                                ],
                                color="#FF6600"
                            )
                        ])
                    ], className="shadow-sm mb-4")
                ], width=12)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            dbc.Row([
                                dbc.Col([
                                    html.I(className="fas fa-users me-2"),
                                    html.Span("Retención v/s titulación") # ID para el título
                                ], width=12, className="d-flex align-items-center"),
                            ])
                        ], style={"background-color": "#162f8a"}, className="fw-bold text-white"),

                        dbc.CardBody([
                            dcc.Loading(
                                id="loading-retencion-titulacion",
                                type="circle",
                                children=[
                                    html.Div(id='contenedor-retencion-titulacion', children=[
                                        dcc.Graph(id='grafico-retencion-titulacion')
                                    ], className="mb-4"),
                                ],
                                color="#FF6600"
                            )
                        ])
                    ], className="shadow-sm mb-4")
                ], width=12)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            dbc.Row([
                                dbc.Col([
                                    html.I(className="fas fa-users me-2"),
                                    html.Span("Vacantes") # ID para el título
                                ], width=12, className="d-flex align-items-center"),
                            ])
                        ], style={"background-color": "#162f8a"}, className="fw-bold text-white"),

                        dbc.CardBody([
                            dcc.Loading(
                                id="loading-vacantes",
                                type="circle",
                                color="#FF6600",
                                children=[
                                    dbc.Row([
                                        dbc.Col([
                                            dcc.Graph(id='grafico-vacantes-barras')
                                        ], width=6),
                                
                                        dbc.Col([
                                            dcc.Graph(id='grafico-vacantes-pie')
                                        ], width=6)
                                    ])
                                ]
                            )
                        ])
                    ], className="shadow-sm mb-4")
                ], width=12)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            dbc.Row([
                                dbc.Col([
                                    html.I(className="fas fa-users me-2"),
                                    html.Span("Docentes"),
                                ],  width=12, className="align-self-center")
                            ])
                        ], style={"background-color": "#162f8a"},
                        className="fw-bold text-white"),
                        dbc.CardBody([
                            dbc.Tabs([
                                dbc.Tab(label="Area de formación", tab_id="tab-area-formacion"),
                                dbc.Tab(label="Horario", tab_id="tab-horario"),
                                dbc.Tab(label="Contrato", tab_id="tab-contrato"),
                                dbc.Tab(label="Tasa de rotación", tab_id="tab-rotacion"),
                            ], id="tabs-docentes", active_tab="tab-area-formacion", className="mb-3"),
                            
                            # Contenedor único para el gráfico seleccionado
                            dcc.Loading(
                                dcc.Graph(id="grafico-docentes", style={"height": "500px"})
                            )
                        ])
                    ], className="shadow-sm mb-4")
                ], width=12)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                        dbc.Row([
                            dbc.Col([
                                html.I(className="fas fa-close me-2"),
                                "Reprobados al primer año"], 
                            width=9),
                            dbc.Col([
                                dcc.Dropdown(
                                    id='dropdown-ramos-primer-año',
                                    options=[{'label': 'Todos los Ramos', 'value': 'Todos'}],
                                    value='Todos',
                                    clearable=False,
                                    style={"width": "100%", "color": "#FFFFFF"},
                                    className="text-dark"
                                )
                            ], width=3)])
                            
                        ], style={"background-color": "#162f8a"},
                        className="fw-bold text-white"),
                        dbc.CardBody([
                            dcc.Loading(
                                id="loading-ingresos",
                                type="circle",
                                children = [
                                    html.Div(
                                        id='contenedor-barra-reprobados', 
                                        children=[
                                            dcc.Graph(id='grafico-reprobados-primer-año')
                                            ], className="mb-4"),
                                    dbc.Row(
                                        id='contenedor-pies-reprobados', 
                                        children=[], 
                                        className="mt-4")
                                ],
                            color="#FF6600"
                            )
                        ])
                    ], className="shadow-sm mb-4")
                ], width=12)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                        dbc.Row([
                            dbc.Col([
                                html.I(className="fas fa-close me-2"),
                                "Reprobados totales"], 
                            width=9),
                            dbc.Col([
                                dcc.Dropdown(
                                    id='dropdown-ramos-reprobados-totales',
                                    options=[{'label': 'Todos los Ramos', 'value': 'Todos'}],
                                    value='Todos',
                                    clearable=False,
                                    style={"width": "100%", "color": "#FFFFFF"},
                                    className="text-dark"
                                )
                            ], width=3)])
                            
                        ], style={"background-color": "#162f8a"},
                        className="fw-bold text-white"),
                        dbc.CardBody([
                            dcc.Loading(
                                id="loading-reprobados-totales",
                                type="circle",
                                children = [
                                    html.Div(
                                        id='contenedor-barra-reprobados-totales', 
                                        children=[
                                            dcc.Graph(id='grafico-reprobados-totales')
                                            ], className="mb-4"),
                                    dbc.Row(
                                        id='contenedor-pies-reprobados-totales', 
                                        children=[], 
                                        className="mt-4")
                                ],
                            color="#FF6600"
                            )
                        ])
                    ], className="shadow-sm mb-4")
                ], width=12)
            ]),
            
            html.Div(style={"height": "50px"})

        ], width=9, style=CONTENT_STYLE)
    ])
], fluid=True)

@callback(
    [Output('grafico-reprobados-primer-año', 'figure'),
     Output('dropdown-ramos-primer-año', 'options'),
     Output('contenedor-barra-reprobados', 'style'),
     Output('contenedor-pies-reprobados', 'children')],
    [Input('slider-años', 'value'),
     Input('radio-jornada', 'value'),
     Input('radio-genero', 'value'),
     Input('dropdown-ramos-primer-año', 'value')]
)
def manejar_dashboard_reprobados_primer_año(años, jornada, genero, ramo_sel):
   
    df_base = query_reprobados_primer_anio_filtrada(jornada=jornada, genero=genero)
    
    df_rango = df_base[
        (df_base['COHORTE'] >= años[0]) & 
        (df_base['COHORTE'] <= años[1])
    ].copy()

    df_agrupado = df_rango.groupby(['COHORTE', 'CODRAMO'])['CANTIDAD_REPROBACIONES'].sum().reset_index()

    top_10_ramos = (
        df_agrupado.groupby('CODRAMO')['CANTIDAD_REPROBACIONES']
        .sum()
        .nlargest(10)
        .index.tolist()
    )

    ramos_disponibles = sorted(df_rango['CODRAMO'].unique())
    opciones_dropdown = [{'label': 'Top 10 Ramos', 'value': 'Todos'}]
    opciones_dropdown += [{'label': r, 'value': r} for r in ramos_disponibles]

    if ramo_sel == 'Todos' or ramo_sel is None or ramo_sel not in ramos_disponibles:

        df_top = df_agrupado[df_agrupado['CODRAMO'].isin(top_10_ramos)]

        fig_barra = generar_grafico_historico_apilado(df_top.rename(columns={'COHORTE': 'ANIO'}))
        
        suffix = f"({años[0]})" if años[0] == años[1] else f"({años[0]}-{años[1]})"
        fig_barra.update_layout(title=f"Top 10 Ramos con más Reprobaciones al 1er Año {suffix}")

        return fig_barra, opciones_dropdown, {'display': 'block'}, []
    
    else:
        df_especifico = df_rango[df_rango['CODRAMO'] == ramo_sel]
        fig_pies = crear_pie_charts_reprobados(df_especifico, ramo_sel, titulo="Análisis de Reprobación 1er Año")
        
        return go.Figure(), opciones_dropdown, {'display': 'none'}, dcc.Graph(figure=fig_pies)

@callback(
    [Output('grafico-reprobados-totales', 'figure'),
     Output('dropdown-ramos-reprobados-totales', 'options'),
     Output('contenedor-barra-reprobados-totales', 'style'),
     Output('contenedor-pies-reprobados-totales', 'children')],
    [Input('slider-años', 'value'),
     Input('radio-jornada', 'value'),
     Input('radio-genero', 'value'),
     Input('dropdown-ramos-reprobados-totales', 'value')]
)
def manejar_reprobados_totales(años, jornada, genero, ramo_sel):
    # 1. Obtener datos filtrados de la base de datos
    df_base = query_reprobados_historico_simple(jornada=jornada, genero=genero)
    
    df_rango = df_base[
        (df_base['ANIO'] >= años[0]) & 
        (df_base['ANIO'] <= años[1])
    ].copy()

    df_agrupado = df_rango.groupby(['ANIO', 'CODRAMO'])['CANTIDAD_REPROBACIONES'].sum().reset_index()

    ramos_disponibles = sorted(df_agrupado['CODRAMO'].unique())

    top_10_ramos = (
        df_agrupado.groupby('CODRAMO')['CANTIDAD_REPROBACIONES']
        .sum()
        .nlargest(10)
        .index.tolist()
    )

    opciones = [{'label': 'Top 10 Ramos', 'value': 'Todos'}]
    for r in ramos_disponibles:
        opciones.append({'label': r, 'value': r})

    if ramo_sel == 'Todos' or ramo_sel is None:
        df_top = df_agrupado[df_agrupado['CODRAMO'].isin(top_10_ramos)]
        
        fig_barra = generar_grafico_historico_apilado(df_top)

        if años[0] == años[1]:
            fig_barra.update_layout(title=f"Top 10 de Ramos con más reprobaciones ({años[0]})")
        else:
            fig_barra.update_layout(title=f"Top 10 de Ramos con más reprobaciones ({años[0]}-{años[1]})")
        
        return fig_barra, opciones, {'display': 'block'}, []
    
    else:
        df_especifico = df_rango[df_rango['CODRAMO'] == ramo_sel]
        fig_pies = crear_pie_charts_reprobados(df_especifico, ramo_sel, titulo="Reprobados Totales")
        
        return go.Figure(), opciones, {'display': 'none'}, dcc.Graph(figure=fig_pies)

@callback(
    [Output("titulo-dinamico-matriculas", "children"),
     Output("grafico-matriculas", "figure")],
    [Input("radio-tipo-matricula", "value"),
     Input("slider-años", "value"),
     Input("radio-jornada", "value"),
     Input("radio-genero", "value")]
)
def update_seccion_matriculas(tipo_mat, rango_años, jornada, genero):
    if tipo_mat == "Totales":
        df_totales = query_matriculas_totales()
        df_f = df_totales[
            (df_totales['COHORTE'] >= rango_años[0]) & 
            (df_totales['COHORTE'] <= rango_años[1])
        ].sort_values('COHORTE')
        
        fig = generar_grafico_matriculas_totales(df_f)
        titulo = "Matrículas Totales: Nuevos vs. Antiguos"
        
    else:
        df_nuevos = query_alumnos_nuevos(jornada=jornada, genero=genero)
        
        df_f = df_nuevos[
            (df_nuevos['COHORTE'] >= rango_años[0]) & 
            (df_nuevos['COHORTE'] <= rango_años[1])
        ].sort_values('COHORTE')
        
        fig = generar_grafico_matriculas_nuevas_dinamico(df_f, jornada, genero)
        titulo = "Análisis Detallado de Alumnos Nuevos"

    return titulo, fig

@callback(
    Output('grafico-retencion-titulacion', 'figure'),
    [Input('slider-años', 'value'),
     Input('radio-jornada', 'value'),
     Input('radio-genero', 'value')]
)
def manejar_trayectoria_promedio(años, jornada, genero):

    df_p = obtener_persistencia_retencion_historica(jornada=jornada, genero=genero)
    df_t = query_distribucion_demora_titulacion(jornada=jornada, genero=genero)
    
    return generar_grafico_persistencia_titulación(df_p, df_t, años)

@callback(
    [Output('grafico-vacantes-barras', 'figure'),
     Output('grafico-vacantes-pie', 'figure')],
    [Input('slider-años', 'value')]
)
def actualizar_seccion_vacantes(rango_años):
    df = obtener_metricas_vias_admision_vacantes()
    df['COHORTE'] = df['COHORTE'].astype(int)
    
    df_rango = df[(df['COHORTE'] >= rango_años[0]) & (df['COHORTE'] <= rango_años[1])].copy()
    
    if df_rango.empty:
        vacio = go.Figure().update_layout(title="Sin datos")
        return vacio, vacio

    fig_barras = generar_barras_vacantes(df_rango, rango_años)
    fig_pie = generar_pie_vias(df_rango)
    
    return fig_barras, fig_pie

@callback(
    Output("grafico-docentes", "figure"),
    [Input("tabs-docentes", "active_tab"),
     Input("slider-años", "value")]
)
def actualizar_grafico_docentes(tab_activa, rango_años):
    # Diccionario de mapeo para evitar múltiples IF
    if tab_activa == "tab-area-formacion":
        df = query_docentes_area_formacion()
        return generar_grafico_area_formacion(df, rango_años)
    
    elif tab_activa == "tab-contrato":
        df = query_docentes_tipo_contrato()
        return generar_grafico_contrato(df, rango_años)
    
    elif tab_activa == "tab-rotacion":
        df = query_docentes_tasa_rotacion()
        return generar_grafico_rotacion(df, rango_años)
    
    elif tab_activa == "tab-horario":
        df = query_docentes_horario()
        return generar_grafico_horario(df, rango_años)
    
    return go.Figure()
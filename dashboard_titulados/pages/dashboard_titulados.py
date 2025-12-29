import dash_bootstrap_components as dbc
from dash import dcc, html

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
                
                # Instituciones
                html.Label("Instituciones de Competencia:", className="fw-bold"),
                dcc.Dropdown(
                    id='selector-instituciones-competencia',
                    options=[], # Se puebla vía callback
                    multi=True,
                    placeholder="Seleccione para comparar...",
                    className="mb-4"
                ),
                
                # Rango de Años
                html.Label("Rango de Cohortes (Ingreso):", className="fw-bold"),
                dcc.RangeSlider(
                    id='slider-años-desertores',
                    min=2007, max=2025, step=1,
                    value=[2018, 2024],
                    marks={i: str(i) for i in range(2007, 2026, 3)},
                    className="mb-4"
                ),
                
                # Top N
                html.Label("Mostrar Top N del Mercado:", className="fw-bold"),
                dcc.Slider(
                    id='slider-top-n-desertores',
                    min=5, max=20, step=5,
                    value=10,
                    marks={i: f"Top {i}" for i in [5, 10, 15, 20]},
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
                    html.P("Evaluación de educación continua incluyendo a titulados de ECAS como Desertores", className="lead text-muted")
                ])
            ], className="mb-4"),

            # Fila de KPIs Superiores (Tarjetas Estáticas)
            dbc.Row([
                dbc.Col(crear_card_metric_estatica("val-titulados", "Total Cohorte", "fa-graduation-cap"), width=6),
                dbc.Col(crear_card_metric_estatica("val-abandono", "Total Titulados", "fa-door-open"), width=6),
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

            # Fila 2: Permanencia y Jornada
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Permanencia N → N+1 (%)", className="fw-bold"),
                        dbc.CardBody([
                            dcc.Graph(id='grafico-permanencia-n1', style={"height": "350px"})
                        ])
                    ], className="shadow-sm mb-4")
                ], width=6),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Permanencia por jornada (ECAS)", className="fw-bold"),
                        dbc.CardBody([
                            dcc.Graph(id='grafico-permanencia-jornada', style={"height": "350px"})
                        ])
                    ], className="shadow-sm mb-4")
                ], width=6)
            ]),

            # Fila 3: Supervivencia vs Titulación
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            dbc.Row([
                                dbc.Col("Tasas de supervivencia y titulación por cohorte", width=8),
                                dbc.Col(dcc.Dropdown(id='selector-inst-supervivencia', placeholder="Filtrar institución..."), width=4)
                            ])
                        ], className="fw-bold"),
                        dbc.CardBody([
                            dcc.Graph(id='grafico-supervivencia-titulacion')
                        ])
                    ], className="shadow-sm mb-4")
                ], width=12)
            ]),

            # Fila 4: Análisis de Destino (Fuga)
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            dbc.Row([
                                dbc.Col("Análisis de Destino (Fuga)", width=6),
                                dbc.Col(dbc.RadioItems(
                                    id="radio-dimension-fuga",
                                    options=[
                                        {"label": "Institución", "value": "institucion_destino"},
                                        {"label": "Carrera", "value": "carrera_destino"},
                                        {"label": "Área", "value": "area_conocimiento_destino"},
                                    ],
                                    value="institucion_destino",
                                    inline=True,
                                ), width=6, className="text-end")
                            ])
                        ], className="fw-bold"),
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

            # Fila 5: Tiempo de Descanso
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.I(className="fas fa-history me-2"),
                            "Distribución de Tiempo de Descanso (Post-ECAS)"
                        ], className="fw-bold bg-light"),
                        dbc.CardBody([
                            html.P("Años transcurridos hasta el primer reingreso al sistema.", className="text-muted small"),
                            dcc.Graph(id='grafico-tiempo-descanso', style={"height": "400px"})
                        ])
                    ], className="shadow-sm mb-4")
                ], width=12)
            ]),

            # Fila 6: Gauges de Trayectoria (Balance de Éxito)
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Balance de Éxito Académico (Titulaciones)", className="fw-bold bg-light"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    dcc.Loading(dcc.Graph(id='grafico-gauge-titulacion-ext'))
                                ], width=6, className="border-right"),
                                dbc.Col([
                                    dcc.Loading(dcc.Graph(id='grafico-gauge-exito-captacion'))
                                ], width=6),
                            ]),
                            html.Hr(),
                            html.P("Comparativa entre desertores que se titulan fuera vs. captados que se titulan en ECAS.", 
                                   className="text-muted small text-center")
                        ])
                    ], className="shadow-sm mb-4")
                ], width=12)
            ]),
            
            # Espacio final
            html.Div(style={"height": "50px"})

        ], width=9, style=CONTENT_STYLE)
    ])
], fluid=True)
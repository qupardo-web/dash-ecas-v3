import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, callback, Output, Input, State
from dashboard_acreditacion.metrics.queries_acreditacion import *
from dashboard_acreditacion.graphics.graphics import *
import pandas as pd
import numpy as np

def crear_card_kpi_moderna(id_prefijo, titulo):
    return dbc.Card([
        dbc.CardBody([
            html.P(titulo, className="text-muted small mb-1"),
            # El valor principal tiene un ID único
            html.H3(id=f"{id_prefijo}-valor", children="---", className="fw-bold mb-1", style={"fontSize": "1.4rem"}),
            # El badge de variación tiene su propio ID
            html.Div(id=f"{id_prefijo}-badge"),
            html.P("vs periodo anterior", className="text-muted extra-small mt-2", style={"fontSize": "0.7rem"})
        ])
    ], className="border-0 shadow-sm")

layout= dbc.Container([
    # Envolvemos todo el contenido en un Div que controle el ancho máximo y el centrado
    html.Div([
        
        dbc.Row([
            html.H3("Análisis de Acreditación", className="border-bottom pb-2"),
            html.P("Seguimiento de los destinos de desertores respecto a su acreditación", className="lead text-muted")
        ], className="mb-4 p-3 bg-white shadow-sm rounded mx-0"),

        # --- FILA 0: FILTROS SUPERIORES ---
        dbc.Row([
            # Dropdown de Periodo (2007 a 2025)
            dbc.Col(dcc.Dropdown(
                id='f-anio',
                options=[{'label': str(anio), 'value': anio} for anio in range(2007, 2026)],
                value=2024, # Valor inicial por defecto
                placeholder="Seleccione Periodo",
                clearable=False
            ), width=3),

            # Dropdown de Jornada
            dbc.Col(dcc.Dropdown(
                id='f-jornada',
                options=[
                    {'label': 'Todas', 'value': 'Todas'},
                    {'label': 'Diurna', 'value': 'Diurna'},
                    {'label': 'Vespertina', 'value': 'Vespertina'}
                ],
                value='Todas',
                placeholder="Jornada",
                clearable=False
            ), width=3),

            # Dropdown de Tipo Institución (puedes poblarlo según tus datos)
            dbc.Col(dcc.Dropdown(
                id='f-tipo',
                options=[
                    {'label': 'Todas', 'value': 'Todas'},
                    {'label': 'Universidad', 'value': 'Universidades'},
                    {'label': 'IP', 'value': 'Institutos Profesionales'},
                    {'label': 'CFT', 'value': 'Centros de Formación Técnica'}
                ],
                value='Todas',
                placeholder="Tipo Institución"
            ), width=3),
        ], className="mb-4 p-3 bg-white shadow-sm rounded mx-0"),

        dbc.Row([
            dbc.Col([
                dbc.Row([
                    dbc.Col(
                        dbc.Card([
                            dbc.CardHeader([
                                html.I(className="fas fa-chart-line me-2"),
                                "Instituciones de destino por acreditación"
                            ], className="fw-bold bg-primary text-white"),
                            dbc.CardBody([
                                dcc.Loading(
                                    id="loading-instituciones-por-acreditacion",
                                    type="circle",
                                    children=[dcc.Graph(id='mini-bar-1')],
                                    color="#FF6600" # Naranja 
                                )
                            ])
                        ]),
                    width=12),
                ]),
            ], width=7),
            
            dbc.Col([
                dbc.Row([
                    dbc.Col(crear_card_kpi_moderna("acred", "Acreditación ECAS"), width=6),
                    dbc.Col(crear_card_kpi_moderna("acred-inst", "Años de acreditación"), width=6),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col(crear_card_kpi_moderna("retencion", "Tasa Retención ECAS"), width=6),
                    dbc.Col(crear_card_kpi_moderna("desertores", "Desertores del periodo"), width=6),
                ]),
            ], width=5),
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-university me-2"),
                        "Detalle de Instituciones de Destino por Impacto de Acreditación"
                    ], className="fw-bold bg-dark text-white"),
                    dbc.CardBody([
                        dbc.Row([
                            # Selector de categoría dentro de la tarjeta
                            dbc.Col([
                                html.Label("Seleccione impacto para filtrar instituciones:", 
                                         className="small text-muted mb-1"),
                                dcc.Dropdown(
                                    id='f-categoria-movilidad',
                                    options=[
                                        {'label': 'Más Acreditadas', 'value': 'Más Acreditada'},
                                        {'label': 'Igual Acreditación', 'value': 'Igual Acreditación'},
                                        {'label': 'Menos Acreditadas', 'value': 'Menos Acreditada'},
                                        {'label': 'No Acreditadas', 'value': 'No Acreditada'}
                                    ],
                                    value='Más Acreditada',
                                    clearable=False,
                                    className="small shadow-sm"
                                )
                            ], width=4, className="mb-3"),
                        ]),
                        
                        dcc.Loading(
                            id="loading-detalle-fuga",
                            type="circle",
                            children=[
                                dcc.Graph(id='graph-detalle-instituciones')
                            ],
                            color="#162f8a"
                        )
                    ])
                ], className="border-0 shadow-sm"),
                width=12 # Ocupa todo el ancho del bloque central
            )
        ], className="mb-4"),
        
    ], style={
        "maxWidth": "1200px",  # Define el ancho máximo del bloque central
        "margin": "0 auto",     # Centra el bloque horizontalmente
        "paddingTop": "2rem",   # Margen superior
        "paddingBottom": "2rem" # Margen inferior para que no pegue al suelo
    })

], fluid=True, style={
    "backgroundColor": "#f4f7f9", # Fondo gris claro para toda la página
    "minHeight": "100vh"          # Asegura que el fondo cubra toda la pantalla
})

@callback(
    [Output("acred-valor", "children"), Output("acred-badge", "children"),
     Output("acred-inst-valor", "children"), Output("acred-inst-badge", "children"),
     Output("retencion-valor", "children"), Output("retencion-badge", "children"),
     Output("desertores-valor", "children"), Output("desertores-badge", "children")],
    [Input("f-anio", "value"), Input("f-jornada", "value")]
)
def update_metrics_dashboard(periodo_sel, jornada_sel):
    if not periodo_sel:
        return ["---"] * 8

    data = get_metrics_acreditacion(periodo_sel, jornada_sel)

    # 1. Acreditación ECAS - Valor Cuantitativo (Años)
    acred_act_anio = data['acreditacion_ecas_anio'] if pd.notnull(data['acreditacion_ecas_anio']) else 99
    acred_prev_anio = data['acreditacion_anterior_anio'] if pd.notnull(data['acreditacion_anterior_anio']) else 99
    
    txt_acred_anios = f"{int(acred_act_anio)} años" if acred_act_anio < 99 else "0 años"
    diff_acred = (acred_act_anio - acred_prev_anio) if (acred_act_anio < 99 and acred_prev_anio < 99) else 0

    # 2. Acreditación ECAS - Estado Cualitativo
    # Tomamos directamente el campo de la base de datos
    estado_acred = data['acreditada_inst_ecas'] if pd.notnull(data['acreditada_inst_ecas']) else "SIN INF."
    
    # Formateo estético del estado
    if estado_acred in ['SÍ', 'ACREDITADA']:
        txt_estado = "ACREDITADA"
        color_estado = "text-success"
    else:
        txt_estado = "NO ACREDITADA"
        color_estado = "text-danger"

    # Helper para Badges
    def crear_badge(texto, subtexto, color_class="text-success", icono="fa-arrow-up"):
        return html.Span([
            html.I(className=f"fas {icono} me-1"),
            html.Span(f" {subtexto}", style={"fontSize": "0.75rem", "fontWeight": "normal"})
        ], className=f"{color_class} fw-bold", style={"fontSize": "0.85rem"})

    # Definición de salidas para las tarjetas
    badge_anios = crear_badge(f"↑ {diff_acred}" if diff_acred >= 0 else f"↓ {abs(diff_acred)}", "vs anterior")
    
    # Badge para el estado (simplemente repite info o muestra tendencia)
    badge_estado = html.Span(
        txt_estado, 
        className=f"{color_estado} fw-bold", 
        style={"fontSize": "0.75rem"} # Reducción explícita para que no compita con el valor principal
    )

    tasa_ret_val = f"{data['tasa_retencion']:.1f}%" if pd.notnull(data['tasa_retencion']) else "0%"
    badge_ret = crear_badge("Excl.", "Titulados", "text-success", "fa-check-circle")
    
    cant_des_val = f"{int(data['cant_desertores'])}" if pd.notnull(data['cant_desertores']) else "0"
    badge_des = crear_badge("Fuga", "Neta", "text-teal", "fa-door-open")

    return ( # Tarjeta años
        txt_estado, badge_estado,
        txt_acred_anios, badge_anios,      # Tarjeta estado cualitativo
        tasa_ret_val, badge_ret,
        cant_des_val, badge_des
    )

@callback(
    Output('mini-bar-1', 'figure'),
    [Input('f-anio', 'value'),
     Input('f-jornada', 'value'),
     Input('f-tipo', 'value')]
)
def update_mini_bar_destino(anio, jornada, tipo_inst):
    if not anio:
        return go.Figure()
        
    # 1. Llamada a la query estricta que definimos (comparación año vs año+1)
    # Esta función ya incluye la lógica del 99 como "No Acreditada"
    df = get_movilidad_acreditacion_estricta(
        anio_seleccionado=anio, 
        jornada=jornada, 
        tipo_inst=tipo_inst
    )
    
    # 2. Retornar el gráfico procesado
    return crear_mini_bar_acreditacion(df)

@callback(
    Output('graph-detalle-instituciones', 'figure'),
    [Input('f-anio', 'value'),
     Input('f-jornada', 'value'),
     Input('f-categoria-movilidad', 'value')]
)
def update_detalle_instituciones(anio, jornada, categoria):
    if not anio:
        return go.Figure()
    
    # 1. Obtener datos mediante la query lógica
    df = get_detalle_instituciones_fuga(anio, categoria, jornada)
    
    # 2. Llamar a la función del archivo externo para generar el gráfico
    return crear_grafico_detalle_fuga(df, categoria)
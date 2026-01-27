import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, callback, Output, Input, State
from dashboard_analisis_docencia.metrics.queries_analisis_cohorte import *
from dashboard_analisis_docencia.graphics.graphics_cohorte import *
from dash import callback_context

CONTENT_STYLE = {
    "min-height": "100vh",
    "padding": "2rem",
    "background-color": "#f8f9fa" 
}

CARD_STYLE = {
    "padding": "1.5rem",
    "border-radius": "10px",
    "border": "none",
    "box-shadow": "0 4px 6px rgba(0, 0, 0, 0.1)",
    "margin-bottom": "20px",
}

layout = dbc.Container([

    dcc.Store(id='store-data'),

    html.Div(id='trigger-carga-inicial', style={'display': 'none'}),
    
    dbc.Row([
        dbc.Col(html.H4("Análisis General por Cohorte", className="text-center mb-4 border-bottom pb-2"), width=12)
    ]),

    dbc.Row([
        
        dbc.Col([
            html.Label("Cohorte", className="small fw-bold"),
            dcc.Dropdown(
                id="filtro-cohorte-analisis",
                options=[],
                clearable=False,
                style={
                    "border-radius": "15px",
                    "border": "1px solid #dee2e6",
                },
                placeholder="Seleccione una cohorte"
            )
        ], width=4),

        dbc.Col([
            html.Label("Jornada", className="small fw-bold"),
            dcc.Dropdown(
                id="filtro-jornada-cohortes",
                options=[
                    {"label": "Todas", "value": "Todas"},
                    {"label": "Diurna", "value": "D"},
                    {"label": "Vespertina", "value": "V"}],
                value="Todas",
                clearable=False,
                placeholder="Seleccione una jornada",
                style={
                    "border-radius": "15px",
                    "border": "1px solid #dee2e6",
                }
            )
        ], width=2),

        dbc.Col([
            html.Label("Género", className="small fw-bold"),
            dcc.Dropdown(
                id="filtro-genero-cohortes",
                options=[
                    {"label": "Todos", "value": "Todos"},
                    {"label": "Hombre", "value": "M"},
                    {"label": "Mujer", "value": "F"}
                ],
                value="Todos",
                clearable=False,
                placeholder="Seleccione un género",
                style={
                    "border-radius": "15px",
                    "border": "1px solid #dee2e6",
                }

            )
        ], width=2),

    ], className="mb-4 p-3 bg-white rounded shadow-sm mx-0 align-items-center", justify="center"),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                html.H5("Distribución de ingreso", className="fw-bold text-center"),
                dcc.Graph(id='grafico-ingresos') 
            ], style=CARD_STYLE)
        ], lg=6, md=12),
        
        dbc.Col([
            dbc.Card([
                html.H5("Distribución por nacionalidad", className="fw-bold text-center"),
                dcc.Graph(id='grafico-nacionalidad')
            ], style=CARD_STYLE)
        ], lg=6, md=12),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                html.H5("Distribución por comuna", className="fw-bold text-center"),
                dcc.Graph(id='grafico-comunas')
            ], style=CARD_STYLE)
        ], lg=6, md=12),

        dbc.Col([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        html.H5("Distribución por vía de admisión", className="fw-bold text-center"),
                        dcc.Graph(id='grafico-via-admision')
                    ], style=CARD_STYLE)
                ], width=12)
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        html.H5("Distribución por modalidad de origen", className="fw-bold text-center"),
                        dcc.Graph(id='grafico-modalidad-origen')
                    ], style=CARD_STYLE)
                ], width=12)
            ]),
        ], lg=6, md=12),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                html.H5("Distribución por edad", className="fw-bold text-center"),
                dcc.Graph(id='grafico-edad')
            ], style=CARD_STYLE)
        ], width=12)
    ], className="mb-4"),

], style=CONTENT_STYLE, fluid=True) 

#Callbacks para actualizar los graficos

@callback(
    [Output("store-data", "data"),
     Output("filtro-cohorte-analisis", "options"),
     Output("filtro-cohorte-analisis", "value")],
    Input("trigger-carga-inicial", "children") 
)
def inicializar_dashboard(_):
    df_ingreso = obtener_distribucion_historica_ingreso()
    df_nacionalidad = obtener_distribucion_nacionalidad_ingreso()
    df_comuna = obtener_distribucion_comuna_historica()
    df_admision = obtener_distribucion_via_admision_historica()
    df_modalidad = obtener_distribucion_modalidad_historica()
    df_edad = obtener_distribucion_edad_historica()
    
    data_consolidada = {
        "ingreso": df_ingreso.to_dict('records'),
        "nacionalidad": df_nacionalidad.to_dict('records'),
        "comuna": df_comuna.to_dict('records'),
        "via_admision": df_admision.to_dict('records'),
        "modalidad_origen": df_modalidad.to_dict('records'),
        "edad": df_edad.to_dict('records'),
    }
    
    cohortes = sorted(df_ingreso['COHORTE'].unique(), reverse=True)
    options = [{"label": c, "value": c} for c in cohortes]
    
    return data_consolidada, options, cohortes[0] if cohortes else None


@callback(
    [Output('grafico-ingresos', 'figure'),
     Output('grafico-nacionalidad', 'figure'),
     Output('grafico-comunas', 'figure'),
     Output('grafico-via-admision', 'figure'),
     Output('grafico-modalidad-origen', 'figure'),
     Output('grafico-edad', 'figure')],
    [Input('filtro-cohorte-analisis', 'value'),
     Input('filtro-jornada-cohortes', 'value'),
     Input('filtro-genero-cohortes', 'value')],
    State('store-data', 'data'),
    prevent_initial_call=True
)
def update_all_charts(cohorte, jornada, genero, data_stored):
    if not data_stored or not cohorte:
        return {}, {}

    df_ing = pd.DataFrame(data_stored['ingreso'])
    df_nac = pd.DataFrame(data_stored['nacionalidad'])
    df_com = pd.DataFrame(data_stored['comuna'])
    df_adm = pd.DataFrame(data_stored['via_admision'])
    df_mod = pd.DataFrame(data_stored['modalidad_origen'])
    df_edad = pd.DataFrame(data_stored['edad'])
    
    def filtrar(df_target):
        if df_target.empty:
            return df_target
            
        df_target['COHORTE'] = df_target['COHORTE'].astype(str)
        val_cohorte = str(int(float(cohorte)))
        
        m = (df_target['COHORTE'] == val_cohorte)
        
        if jornada != "Todas": 
            m &= (df_target['JORNADA'] == jornada)
        if genero != "Todos": 
            m &= (df_target['GENERO'] == genero)
            
        return df_target[m]

    fig_ingreso = crear_subplot_ingresos(filtrar(df_ing), jornada, genero)
    fig_nacionalidad = crear_grafico_nacionalidad(filtrar(df_nac), jornada, genero)
    fig_comuna = crear_grafico_comunas(filtrar(df_com), jornada, genero)
    fig_admision = crear_grafico_via_admision(filtrar(df_adm), jornada, genero)
    fig_modalidad = crear_grafico_modalidad_origen(filtrar(df_mod), jornada, genero)
    fig_edad = crear_grafico_edad(filtrar(df_edad), jornada, genero)

    return fig_ingreso, fig_nacionalidad, fig_comuna, fig_admision, fig_modalidad, fig_edad
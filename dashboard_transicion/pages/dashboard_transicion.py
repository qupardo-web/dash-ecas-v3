import dash_bootstrap_components as dbc
from dash import dcc, html

SMALL_CARD_STYLE = {

    "borderRadius": "15px", 
    "border": "none", 
    "boxShadow": "0 4px 6px rgba(0, 0, 0, 0.1)",
    "marginBottom": "20px",
}

BIG_CARD_STYLE = {
    "borderRadius": "20px", 
    "border": "none", 
    "boxShadow": "0 4px 15px rgba(0, 0, 0, 0.05)",
    "marginBottom": "20px",
    "overflow": "hidden", # <--- CLAVE: Esto asegura que se vea redondo arriba y abajo
    "backgroundColor": "white",
    "height": "260px"
}

layout = dbc.Container([
    # Fila de Encabezado (Ya la tienes)
    dbc.Row([
        html.H4("Análisis de Acreditación", className="border-bottom pb-2"),
        html.P("Seguimiento de los destinos de desertores respecto a su acreditación", className="lead text-muted")
    ], className="mb-4 p-3 bg-white rounded shadow-sm mx-0"),

    # FILA DE GRÁFICOS
    dbc.Row([
        # Columna 1
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Destinos Principales", className="bg-white border-0 fw-bold"),
                dbc.CardBody(dcc.Graph(figure={"data": [{"x": [1, 2, 3], "y": [4, 1, 2], "type": "bar"}]}))
            ], style=BIG_CARD_STYLE), width=3
        ),

        # Columna 2
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Distribución %", className="bg-white border-0 fw-bold"),
                dbc.CardBody(dcc.Graph(figure={"data": [{"values": [40, 30, 30], "type": "pie", "hole": .4}]}))
            ], style=BIG_CARD_STYLE), width=3
        ),

        # Columna 3
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Tendencia Anual", className="bg-white border-0 fw-bold"),
                dbc.CardBody(dcc.Graph(figure={"data": [{"x": [1, 2, 3], "y": [2, 4, 3], "type": "line"}]}))
            ], style=BIG_CARD_STYLE), width=3
        ),

        # Columna 4 (Con sub-columnas internas)
        dbc.Col([
            dbc.Row([
                dbc.Col(
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Total Fuga", className="text-muted small"),
                            html.H4("1,240", className="mb-0 text-primary")
                        ])
                    ], style=SMALL_CARD_STYLE)
                ),
                dbc.Col(
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Retención", className="text-muted small"),
                            html.H4("85%", className="mb-0 text-success")
                        ])
                    ], style=SMALL_CARD_STYLE)
                )
            ]),
            # Gráfico pequeño debajo de los indicadores
            dbc.Card([
                dbc.CardBody(dcc.Graph(figure={"data": [{"x": [1, 2], "y": [10, 20], "type": "bar"}]}, style={"height": "150px"}))
            ], style=BIG_CARD_STYLE)
        ], width=3),

    ])
], fluid=True, style={"backgroundColor": "#f4f6f9", "minHeight": "100vh", "padding": "2rem"})
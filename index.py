import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output
from dashboard_desertores.pages.dashboard_desertores import layout as layout_desertores
from dashboard_titulados.pages.dashboard_titulados import layout as layout_titulados

# Inicialización de la App
app = dash.Dash(
    __name__, 
    external_stylesheets=[dbc.themes.FLATLY, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True  # Necesario para multi-página
)

# --- NAVBAR GENÉRICA ---
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Deserción", href="/desertores")),
        dbc.NavItem(dbc.NavLink("Titulados", href="/titulados")),
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("Más Análisis", header=True),
                dbc.DropdownMenuItem("Permanencia", href="/permanencia"),
                dbc.DropdownMenuItem("Ranking Mercado", href="/mercado"),
            ],
            nav=True,
            in_navbar=True,
            label="Métricas Avanzadas",
        ),
    ],
    brand="ECAS - Analytics Hub",
    brand_href="/",
    color="primary",
    dark=True,
    className="mb-0" # Sin margen inferior para pegar con el contenido
)

# --- LAYOUT PRINCIPAL ---
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    navbar,
    # Contenedor donde se "inyectará" el contenido de cada página
    html.Div(id='page-content')
])

# --- CALLBACK DE ENRUTAMIENTO ---
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/desertores':
        return layout_desertores
    elif pathname == '/titulados':
        return layout_titulados
    elif pathname == '/' or pathname == '':
        return html.Div([
            dbc.Container([
                html.H1("Panel de Análisis Institucional", className="mt-5"),
                html.P("Seleccione una métrica en la barra superior para comenzar."),
                dbc.Row([
                    dbc.Col(dbc.Button("Ver Deserción", href="/desertores", color="primary"), width="auto"),
                    dbc.Col(dbc.Button("Ver Titulados", href="/titulados", color="secondary"), width="auto"),
                ])
            ], className="py-5")
        ])
    else:
        return html.H1("404 - Página no encontrada", className="text-danger text-center mt-5")

if __name__ == '__main__':
    app.run(debug=True, port=8050)
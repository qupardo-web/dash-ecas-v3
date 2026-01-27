import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output
from dashboard_desertores.pages.dashboard_desertores import layout as layout_desertores
from dashboard_titulados.pages.dashboard_titulados import layout as layout_titulados
from dashboard_acreditacion.pages.dashboard_acreditacion import layout as layout_acreditacion
from dashboard_transicion.pages.dashboard_transicion import layout as layout_transicion
from dashboard_analisis_docencia.pages.dashboard_ramos import layout as layout_rangos
from dashboard_analisis_docencia.pages.dashboard_analisis_cohorte import layout as layout_cohortes

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
        dbc.NavItem(dbc.NavLink("Acreditacion", href="/acreditacion")),
        dbc.NavItem(dbc.NavLink("Transición", href="/transicion")),
        dbc.NavItem(dbc.NavLink("Analisis General", href="/analisis_general")),
        dbc.NavItem(dbc.NavLink("Cohortes", href="/cohortes")),
    ],
    brand="ECAS - Analytics Hub",
    brand_href="/",
    color="#162f8a",
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
    elif pathname == '/acreditacion':
        return layout_acreditacion
    elif pathname == '/transicion':
        return layout_transicion
    elif pathname == '/analisis_general':
        return layout_rangos
    elif pathname == '/cohortes':
        return layout_cohortes
    elif pathname == '/' or pathname == '':
        return html.Div([
            dbc.Container([
                html.H1("Panel de Análisis Institucional", className="mt-5"),
                html.P("Seleccione una métrica en la barra superior para comenzar."),
                dbc.Row([
                    dbc.Col(dbc.Button("Dashboard Cohortes", href="/cohortes", color="primary"), width="auto"),
                    dbc.Col(dbc.Button("Dashboard Desercion", href="/desertores", color="primary"), width="auto"),
                    dbc.Col(dbc.Button("Dashboard Ex Estudiantes", href="/titulados", color="primary"), width="auto"),
                    dbc.Col(dbc.Button("Dashboard Acreditacion", href="/acreditacion", color="primary"), width="auto"),
                    dbc.Col(dbc.Button("Dashboard Transicion", href="/transicion", color="primary"), width="auto"),
                    dbc.Col(dbc.Button("Dashboard Analisis General", href="/analisis_general", color="primary"), width="auto"),
                ])
            ], className="py-5")
        ])
    else:
        return html.H1("404 - Página no encontrada", className="text-danger text-center mt-5")

if __name__ == '__main__':
    app.run(debug=True, port=8050)
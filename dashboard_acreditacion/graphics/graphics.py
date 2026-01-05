import plotly.express as px
import plotly.graph_objects as go

def crear_mini_bar_acreditacion(df):
    if df is None or df.empty:
        return go.Figure().update_layout(title="Sin datos en este periodo")

    # Mapeo de colores semánticos
    color_map = {
        "Más Acreditada": "#28a745",    # Verde: Mejora
        "Igual Acreditación": "#162f8a", # Azul: Estabilidad
        "Menos Acreditada": "#ffc107",  # Amarillo: Descenso
        "No Acreditada": "#dc3545"      # Rojo: Riesgo
    }

    fig = px.bar(
        df,
        x='categoria_movilidad',
        y='cantidad_alumnos',
        color='categoria_movilidad',
        text='cantidad_alumnos',
        color_discrete_map=color_map,
        category_orders={
            "categoria_movilidad": ["Más Acreditada", "Igual Acreditación", "Menos Acreditada", "No Acreditada"]
        }
    )

    fig.update_traces(textposition='outside', cliponaxis=False)
    fig.update_layout(
        template="plotly_white",
        showlegend=False,
        xaxis_title=None,
        yaxis_title="N° Alumnos",
        margin=dict(t=20, b=20, l=20, r=20),
        height=280, # Ajustado para el contenedor mini-bar
        font=dict(size=10)
    )
    return fig

def crear_grafico_detalle_fuga(df, categoria):
    """
    Genera un gráfico de barras horizontal con el detalle de instituciones.
    """
    if df is None or df.empty:
        # Retorna un gráfico vacío con un mensaje amigable
        fig = go.Figure()
        fig.add_annotation(text="No se registran traslados para esta categoría", 
                          showarrow=False, font=dict(size=14, color="gray"))
        fig.update_layout(xaxis={'visible': False}, yaxis={'visible': False}, template="plotly_white")
        return fig

    # Gráfico de barras horizontal (Top 15 para no saturar)
    fig = px.bar(
        df.head(15), 
        x='cantidad_alumnos', 
        y='inst_destino',
        orientation='h',
        text='cantidad_alumnos',
        color_discrete_sequence=['#162f8a'] # Azul corporativo
    )
    
    fig.update_layout(
        template="plotly_white",
        title=dict(
            text=f"Top Instituciones de Destino: {categoria}",
            font=dict(size=14)
        ),
        xaxis_title="Cantidad de Estudiantes",
        yaxis_title=None,
        margin=dict(t=50, b=10, l=10, r=40),
        height=450,
        font=dict(size=10), # Letra pequeña para nombres de instituciones
        yaxis={'categoryorder':'total ascending'} # Mayor frecuencia arriba
    )
    
    fig.update_traces(
        textposition='outside',
        marker_color='#162f8a',
        texttemplate='%{text}' # Muestra el número entero
    )
    
    return fig
import plotly.express as px

def crear_grafico_reingreso_inmediato(df, poblacion):
    """
    Genera un gráfico de barras para el primer nivel de reingreso con colores por nivel.
    """
    if df.empty:
        return px.bar(title="Sin datos para la selección")

    fig = px.bar(
        df, 
        x='nivel_global', 
        y='cantidad_alumnos',
        text='cantidad_alumnos',
        color='nivel_global',  # <--- ESTO activa los colores diferentes por categoría
        title=f"Primer Nivel de Reingreso ({poblacion})",
        # Opcional: Puedes usar una paleta de colores predefinida
        color_discrete_sequence=px.colors.qualitative.Prism 
    )
    
    fig.update_traces(textposition='outside')
    fig.update_layout(
        xaxis_title="Nivel Académico",
        yaxis_title="Cantidad de Alumnos",
        showlegend=False,  # Opcional: oculta la leyenda si no quieres repetir los nombres
        template="plotly_white",
        margin=dict(t=50, b=20, l=20, r=20)
    )
    return fig

def crear_grafico_reingreso_maximo(df, poblacion):
    """
    Genera un gráfico de donut para el máximo nivel alcanzado.
    """
    if df.empty:
        return px.pie(title="Sin datos para la selección")

    fig = px.pie(
        df, 
        values='cantidad_alumnos', 
        names='nivel_global',
        hole=0.4,
        title=f"Máximo Nivel Alcanzado ({poblacion})",
        color_discrete_sequence=px.colors.qualitative.Prism
    )
    
    fig.update_traces(textinfo='percent+label')
    fig.update_layout(
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
        margin=dict(t=50, b=20, l=20, r=20)
    )
    return fig

def crear_grafico_top_destinos(df, titulo, es_horizontal=True):
    if df.empty:
        return px.bar(title="Sin datos para la selección")

    if es_horizontal:
        fig = px.bar(df, y='destino', x='cantidad_alumnos', orientation='h',
                     text='cantidad_alumnos', color='destino',
                     color_discrete_sequence=px.colors.qualitative.Prism)
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
    else:
        fig = px.pie(df, values='cantidad_alumnos', names='destino', hole=0.3,
                     color_discrete_sequence=px.colors.qualitative.Safe)
    
    fig.update_layout(title=titulo, template="plotly_white", showlegend=False if es_horizontal else True)
    return fig
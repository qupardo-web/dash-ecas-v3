import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

COORDENADAS_REGIONES = {
    "15": {"lat": -18.50, "lon": -69.80, "zoom": 7.5}, # Arica y Parinacota
    "1":  {"lat": -20.20, "lon": -69.30, "zoom": 7.0}, # Tarapacá
    "2":  {"lat": -23.65, "lon": -69.20, "zoom": 6.0}, # Antofagasta
    "3":  {"lat": -27.30, "lon": -70.30, "zoom": 6.5}, # Atacama
    "4":  {"lat": -30.60, "lon": -70.80, "zoom": 7.0}, # Coquimbo
    "5":  {"lat": -32.80, "lon": -71.20, "zoom": 7.5}, # Valparaíso
    "13": {"lat": -33.60, "lon": -70.66, "zoom": 8.0}, # Metropolitana
    "6":  {"lat": -34.40, "lon": -71.10, "zoom": 7.5}, # O'Higgins
    "7":  {"lat": -35.50, "lon": -71.40, "zoom": 7.5}, # Maule
    "16": {"lat": -36.70, "lon": -72.10, "zoom": 8.0}, # Ñuble
    "8":  {"lat": -37.40, "lon": -72.40, "zoom": 7.5}, # Biobío
    "9":  {"lat": -38.70, "lon": -72.50, "zoom": 7.5}, # Araucanía
    "14": {"lat": -40.00, "lon": -72.30, "zoom": 8.0}, # Los Ríos
    "10": {"lat": -41.70, "lon": -72.80, "zoom": 7.0}, # Los Lagos
    "11": {"lat": -46.50, "lon": -73.00, "zoom": 6.0}, # Aysén
    "12": {"lat": -53.00, "lon": -71.00, "zoom": 5.5}, # Magallanes
}

def create_donut_chart(df, title=""):

    if df is None or df.empty:
        return go.Figure().update_layout(
            annotations=[{"text": "Sin datos para los filtros seleccionados", "showarrow": False}])
    
    fig = px.pie(
        df, 
        values='total_periodo', 
        names='tipo_establecimiento', 
        hole=0.2,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_traces(textinfo='percent', hovertemplate="<b>%{label}</b><br>Cant: %{value}<extra></extra>", textposition='inside')
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), showlegend=True,
                      legend=dict(orientation="h", y=-0.3, xanchor='center', x= 0.5))
    return fig

def create_bar_ensenianza(df):
    """
    Crea un gráfico de barras verticales filtrando categorías sin datos.
    """
    if df is None or df.empty:
        return go.Figure().update_layout(
            annotations=[{"text": "Sin datos para los filtros seleccionados", "showarrow": False}]
        )

    df_filtrado = df[df['Cant. Estudiantes'] > 0].copy()

    if df_filtrado.empty:
        return go.Figure().update_layout(
            annotations=[{"text": "No se registran estudiantes en esta categoría", "showarrow": False}]
        )

    # Gráfico de barras Vertical
    fig = px.bar(
        df_filtrado, 
        x='Tipo Enseñanza', 
        y='Cant. Estudiantes',
        color='Tipo Enseñanza',
        text='Cant. Estudiantes', # Muestra el número sobre la barra
        color_discrete_sequence=px.colors.qualitative.Prism
    )
    
    fig.update_traces(
        textposition='outside',
        hovertemplate="<b>%{x}</b><br>Cantidad: %{y}<extra></extra>"
    )

    fig.update_layout(
        margin=dict(l=20, r=20, t=30, b=80), # Más margen abajo para las leyendas
        height=450,
        xaxis_title=None,
        yaxis_title="Cantidad de Estudiantes",
        template="plotly_white",
        showlegend=False, # Ocultamos leyenda lateral porque ya está el nombre en el eje X
        xaxis={'tickangle': 45} # Inclinamos el texto si los nombres son muy largos
    )
    return fig

def create_line_demora(df):
    if df is None or df.empty:
        return go.Figure().update_layout(
            annotations=[{"text": "Sin datos para los filtros seleccionados", "showarrow": False}]
        )
    
    # Gráfico de líneas con puntos
    fig = px.line(
        df, 
        x='anios_demora', 
        y='total_alumnos_periodo',
        markers=True,
        line_shape='spline' # Línea suavizada
    )
    
    fig.update_traces(line_color='#ef553b', marker=dict(size=10))
    
    fig.update_layout(
        margin=dict(l=20, r=20, t=10, b=20),
        height=300,
        xaxis_title="Años de espera tras egreso media",
        yaxis_title="Cantidad de Alumnos",
        template="plotly_white",
        xaxis=dict(dtick=1) # Asegura que muestre años enteros (1, 2, 3...)
    )
    return fig

def create_interactive_map(df_plot, geojson, is_comuna, centro_dict, zoom_nivel=None):
    
    loc_col = "cod_comuna" if is_comuna else "cod_region"
    h_name = "nomb_comuna" if is_comuna else "nomb_region"
    
    if is_comuna:
        first_props = geojson['features'][0]['properties']
        if 'cut' in first_props:
            feat_key = "properties.cut"
        elif 'cod_comuna' in first_props:
            feat_key = "properties.cod_comuna"
        else:
            feat_key = "properties.cod_comuna" 
    else:
        feat_key = "properties.codregion"

    df_plot[loc_col] = pd.to_numeric(df_plot[loc_col], errors='coerce').fillna(0).astype(int)

    centro_limpio = {
        "lat": centro_dict.get("lat", -35),
        "lon": centro_dict.get("lon", -71)
    }
    
    zoom_final = zoom_nivel if zoom_nivel is not None else centro_dict.get("zoom", 4)

    fig = px.choropleth_mapbox(
        data_frame=df_plot,
        geojson=geojson,
        locations=loc_col,
        featureidkey=feat_key, # Ahora es dinámico
        color="cantidad",
        hover_name=h_name,
        mapbox_style="open-street-map",
        color_continuous_scale="tealrose",
        range_color=[0, df_plot['cantidad'].max() if df_plot['cantidad'].max() > 0 else 10],
        center=centro_limpio, 
        zoom=zoom_final     
    )

    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        mapbox=dict(
            # Aumentamos un poco los límites para que no se "escape" el mapa al navegar
            bounds={"west": -85, "east": -65, "south": -58, "north": -15}
        )
    )
    
    return fig

def create_nem_persistence_chart(df):
    if df is None or df.empty:
        return go.Figure().update_layout(
            annotations=[{"text": "Sin datos para los filtros seleccionados", "showarrow": False}]
        )

    df_plot = df[df['total_alumnos'] > 0].copy()

    fig = px.bar(
        df_plot,
        x='rango_nem',
        y='tasa_persistencia',
        text=df_plot['tasa_persistencia'].apply(lambda x: f'{x}%'),
        custom_data=['total_alumnos', 'cantidad_persisten'],
        color='tasa_persistencia',
        color_continuous_scale='Viridis'
    )

    # %{customdata[0]} accede a 'total_alumnos'
    fig.update_traces(
        textposition='outside',
        hovertemplate=(
            "<b>Rango NEM: %{x}</b><br>" +
            "Tasa Persistencia: %{y}%<br>" +
            "Total Cohorte: %{customdata[0]}<br>" +
            "Estudiantes que persisten: %{customdata[1]}" + # Llave cerrada correctamente
            "<extra></extra>" # El extra va una sola vez al final
        )
    )

    fig.update_layout(
        margin=dict(l=20, r=20, t=30, b=40),
        height=350,
        showlegend=False,
        coloraxis_showscale=False,
        yaxis=dict(range=[0, 115], title="Tasa de Persistencia (%)"),
        xaxis_title="Rango NEM",
        template="plotly_white"
    )
    return fig

def create_nem_titulacion_chart(df):
    if df is None or df.empty:
        return go.Figure().update_layout(
            annotations=[{"text": "Sin datos para los filtros seleccionados", "showarrow": False}]
        )

    df_plot = df[df['total_titulados'] > 0].copy()

    fig = px.bar(
        df_plot,
        x='rango_nem',
        y='tasa_titulacion_oportuna',
        text=df_plot['tasa_titulacion_oportuna'].apply(lambda x: f'{x}%'),
        # Pasamos 'total_titulados' como datos extra
        custom_data=['total_titulados', 'titulados_a_tiempo'],
        color='tasa_titulacion_oportuna',
        color_continuous_scale='Plasma'
    )

    fig.update_traces(
        textposition='outside',
        hovertemplate="<b>Rango NEM: %{x}</b><br>" +
                      "Titulación Oportuna: %{y}%<br>" +
                      "Total Titulados: %{customdata[0]}<br>"+
                      "Titulados a tiempo: %{customdata[1]}" +
                      "<extra></extra>"
    )

    fig.update_layout(
        margin=dict(l=20, r=20, t=30, b=40),
        height=350,
        showlegend=False,
        coloraxis_showscale=False,
        yaxis=dict(range=[0, 115], title="Titulación Oportuna (%)"),
        xaxis_title="Rango NEM",
        template="plotly_white"
    )
    return fig

def create_ruralidad_comparison_chart(df):
    """
    Crea un gráfico de barras agrupadas: Ingreso vs Titulados por Zona.
    """
    if df is None or df.empty:
        return go.Figure().update_layout(annotations=[{"text": "Sin datos", "showarrow": False}])

    # Transformamos el DataFrame para que sea compatible con barras agrupadas (long format)
    df_long = df.melt(
        id_vars=['Zona'], 
        value_vars=['total_ingreso', 'total_titulados'],
        var_name='Métrica', 
        value_name='Cantidad'
    )
    
    # Renombrar métricas para el usuario final
    df_long['Métrica'] = df_long['Métrica'].replace({
        'total_ingreso': 'Total Matriculados',
        'total_titulados': 'Total Titulados'
    })

    fig = px.bar(
        df_long,
        x='Zona',
        y='Cantidad',
        color='Métrica',
        barmode='group',
        text='Cantidad',
        color_discrete_map={
            'Total Matriculados': '#3498db', # Azul
            'Total Titulados': '#2ecc71'    # Verde
        }
    )

    fig.update_traces(textposition='outside')
    fig.update_layout(
        margin=dict(l=20, r=20, t=30, b=40),
        height=430, # Ajustado para tu columna lateral
        xaxis_title=None,
        yaxis_title="N° Estudiantes",
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        template="plotly_white"
    )
    
    return fig

def graficar_dependencia_titulados(df, titulo_adicional=""):
    if df is None or df.empty:
        return go.Figure().update_layout(title="Sin datos")

    df = df.sort_values('total_titulados_periodo', ascending=True)

    # Creamos la etiqueta antes de graficar
    df['etiqueta'] = df.apply(lambda r: f"{int(r['total_titulados_periodo']):,} ({r['porcentaje_del_periodo']}%)".replace(",", "."), axis=1)

    fig = px.bar(
        df, 
        x='total_titulados_periodo', 
        y='tipo_establecimiento', 
        orientation='h',
        text='etiqueta',
        custom_data=['promedio_anual_titulados'],
        color='tipo_establecimiento',
        color_discrete_sequence=px.colors.qualitative.Pastel

    )

    fig.update_traces(
        textposition='inside',
        hovertemplate="<b>%{y}</b><br>Titulados: %{x}<br>Promedio Anual: %{customdata[0]}<extra></extra>"
    )

    fig.update_layout(
        xaxis=dict(
            title="Cantidad de Titulados",
            showgrid=True,
            gridcolor='lightgray',
            # Añadimos margen extra a la derecha para que el texto de las barras no se corte
            range=[0, df['total_titulados_periodo'].max() * 1.25]
        ),
        yaxis=dict(title="Tipo de Establecimiento"),
        showlegend=False,
        plot_bgcolor='white',
        height=300,
        margin=dict(l=20, r=100, t=20, b=40)
    )

    return fig
import pandas as pd
import plotly.express as px

def generar_mapa_nacional(df_base, geojson_regiones, mapeo_regiones):
    # 1. Preparación de datos
    df = df_base.copy()
    
    # Mapeo de siglas (RM) a nombres largos del GeoJSON
    df['region_geo'] = df['nomb_region'].map(mapeo_regiones)
    
    # Agrupación por región para sumar la cantidad de alumnos
    df_plot = df.groupby('region_geo')['cantidad'].sum().reset_index()
    
    # 2. Creación del gráfico
    fig = px.choropleth_mapbox(
        df_plot,
        geojson=geojson_regiones,
        locations="region_geo",
        featureidkey="properties.Region", # Nombre exacto de la llave en tu GeoJSON
        color="cantidad",
        color_continuous_scale="Reds",
        mapbox_style="white-bg", # Elimina el fondo mundial
        opacity=1
    )

    # 3. CENTRADO Y ZOOM AUTOMÁTICO (Sin 'sourcetype' ni errores)
    # 'fitbounds' detecta los polígonos dibujados y los pone al medio.
    fig.update_geos(
        fitbounds="locations", 
        visible=False
    )

    # 4. Ajustes estéticos finales
    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        paper_bgcolor='white',
        # Eliminamos cualquier configuración manual de mapbox para que mande fitbounds
        mapbox=dict(
            layers=[{
                "below": 'traces',
                "sourcetype": "raster",
                "source": [""] 
            }]
        )
    )
    
    # Bordes finos para definir la silueta
    fig.update_traces(marker_line_width=0.5, marker_line_color="gray")

    return fig
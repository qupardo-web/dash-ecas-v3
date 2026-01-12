import pandas as pd
import plotly.express as px

def generar_figura_mapa(current_region, df_base, geojson_regiones, geojson_comunas, mapeo_regiones):
    df_base = df_base.copy()
    
    if current_region is None:
        df_base['region_geo'] = df_base['nomb_region'].map(mapeo_regiones)
        df_plot = df_base.groupby('region_geo')['cantidad'].sum().reset_index()
        
        geo = geojson_regiones
        locs = "region_geo"
        key = "properties.Region" # Verifica si en tu archivo es 'Region' o 'region'
        titulo = "Distribución Nacional de Alumnos"
        center_lat, center_lon = -35.6751, -71.5430
        zoom_level = 3
    else:
        # VISTA REGIONAL
        # Filtramos por el nombre de la región que viene del click
        df_base['region_geo'] = df_base['nomb_region'].map(mapeo_regiones)
        df_filtered = df_base[df_base['region_geo'] == current_region]
        
        df_plot = df_filtered.groupby('nomb_comuna')['cantidad'].sum().reset_index()
        # Normalizamos nombres de comuna para el match
        df_plot['nomb_comuna'] = df_plot['nomb_comuna'].str.upper().str.strip()
        
        geo = geojson_comunas
        locs = "nomb_comuna"
        key = "properties.comuna" # Verifica si en tu archivo es 'comuna' o 'COMUNA'
        titulo = f"Región: {current_region}"
        center_lat = df_filtered.get('lat', -33.4489) # Opcional si tienes lat/lon
        center_lon = df_filtered.get('lon', -70.6693)
        zoom_level = 7

    # 2. Creación del objeto gráfico
    fig = px.choropleth_mapbox(
        df_plot,
        geojson=geo,
        locations=locs,
        featureidkey=key,
        color="cantidad",
        color_continuous_scale="Reds",
        mapbox_style="carto-positron", # Cambiado de white-bg para asegurar renderizado
        opacity=0.7,
        center={"lat": -35.6751, "lon": -71.5430}, # Centro de Chile por defecto
        zoom=zoom_level,
        labels={'cantidad': 'Total Alumnos'}
    )

    # 3. Limpieza visual (Ocultar el mundo)
    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        mapbox=dict(
            # Si quieres que se vea TOTALMENTE blanco atrás, activa estas líneas:
            # style="white-bg",
            # layers=[{"sourcetype": "raster", "source": [""]}],
        )
    )
    
    # Esto fuerza a la cámara a ir a los polígonos
    fig.update_geos(fitbounds="locations", visible=False)

    return fig, titulo
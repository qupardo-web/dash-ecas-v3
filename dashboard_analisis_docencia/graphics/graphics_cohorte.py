import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

map_gen = {'F': 'Mujer', 'M': 'Hombre'}
map_jor = {'D': 'Diurna', 'V': 'Vespertina'}

def crear_subplot_ingresos(df, jornada_sel, genero_sel):
    if df.empty:
        return go.Figure().update_layout(title="Sin datos")

    if genero_sel != "Todos":
        df_jor = df.groupby('JORNADA')['CANTIDAD'].sum().reset_index()
        nombre_genero = map_gen.get(genero_sel, genero_sel)
        
        fig = go.Figure(data=[go.Pie(
            labels=[map_jor.get(x, x) for x in df_jor['JORNADA']],
            values=df_jor['CANTIDAD'],
            hole=.5,
            marker=dict(colors=['#565EB3', '#FEE35D']),
            textinfo='label+percent', 
            hovertemplate="<b>Jornada:</b> %{label}<br>" + 
                          "<b>Cantidad:</b> %{value}<extra></extra>",
            title=dict(
                text=f"Distribución por Jornada<br><b>{nombre_genero}</b>",
                font=dict(size=14),
                position="top center"
            )
        )])

    elif jornada_sel != "Todas":
        df_gen = df.groupby('GENERO')['CANTIDAD'].sum().reset_index()
        nombre_jornada = map_jor.get(jornada_sel, jornada_sel)
        
        fig = go.Figure(data=[go.Pie(
            labels=[map_gen.get(x, x) for x in df_gen['GENERO']],
            values=df_gen['CANTIDAD'],
            hole=.5,
            marker=dict(colors=['#162f8a', '#F4F1BB']),
            textinfo='label+percent', 
            hovertemplate="<b>Género:</b> %{label}<br><b>Cantidad:</b> %{value}<extra></extra>",
            title=dict(
                text=f"Distribución por Género<br><b>{nombre_jornada}</b>",
                font=dict(size=14),
                position="top center"
            )
        )])

    else:
        df_gen = df.groupby('GENERO')['CANTIDAD'].sum().reset_index()
        df_jor = df.groupby('JORNADA')['CANTIDAD'].sum().reset_index()

        fig = make_subplots(
            rows=1, cols=2, 
            specs=[[{'type': 'domain'}, {'type': 'domain'}]],
            subplot_titles=("Distribución por Género", "Distribución por Jornada")
        )

        fig.add_trace(go.Pie(
            labels=[map_gen.get(x, x) for x in df_gen['GENERO']], 
            values=df_gen['CANTIDAD'], hole=.4,
            textinfo='label+percent',
            marker=dict(colors=['#162f8a', '#F4F1BB']),
            hovertemplate="<b>Género:</b> %{label}<br><b>Cantidad:</b> %{value}<extra></extra>"
        ), 1, 1)

        fig.add_trace(go.Pie(
            labels=[map_jor.get(x, x) for x in df_jor['JORNADA']], 
            values=df_jor['CANTIDAD'], hole=.4,
            textinfo='label+percent',
            marker=dict(colors=['#565EB3', '#FEE35D']),
            hovertemplate="<b>Jornada:</b> %{label}<br><b>Cantidad:</b> %{value}<extra></extra>"
        ), 1, 2)

    fig.update_layout(
        height=450, 
        template="plotly_white", 
        margin=dict(t=30, b=20, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", xanchor="center", y=-0.2, x=0.5)
    )
    
    return fig

def crear_grafico_nacionalidad(df, jornada_sel, genero_sel):
    if df.empty:
        return go.Figure().update_layout(title="Sin datos de nacionalidad")

    if jornada_sel != "Todas" and genero_sel == "Todos":
        nombre_jornada = map_jor.get(jornada_sel, jornada_sel)
        df_plot = df.groupby(['NACIONALIDAD', 'GENERO'])['CANTIDAD'].sum().reset_index()
        df_plot['GENERO'] = df_plot['GENERO'].map(map_gen)
        
        subtitulo = f"<span style='font-size: 13px; color: #12246b;'>Jornada: {nombre_jornada}</span>"

        fig = px.bar(
            df_plot, x='CANTIDAD', y='NACIONALIDAD', color='GENERO',
            orientation='h', barmode='group',
            title=f"Nacionalidad por Género<br>{subtitulo}",
            color_discrete_map={'Mujer': '#162f8a', 'Hombre': '#F4F1BB'},
        )

    elif genero_sel != "Todos" and jornada_sel == "Todas":
        nombre_genero = map_gen.get(genero_sel, genero_sel)
        df_plot = df.groupby(['NACIONALIDAD', 'JORNADA'])['CANTIDAD'].sum().reset_index()
        df_plot['JORNADA'] = df_plot['JORNADA'].map(map_jor)

        subtitulo = f"<span style='font-size: 13px; color: #12246b;'>Género: {nombre_genero}</span>"
        
        fig = px.bar(
            df_plot, x='CANTIDAD', y='NACIONALIDAD', color='JORNADA',
            orientation='h', barmode='group',
            title=f"Nacionalidad por Jornada<br>{subtitulo}",
            color_discrete_map={'Diurna': '#565EB3', 'Vespertina': '#FEE35D'}
        )

    else:
        df_plot = df.groupby(['NACIONALIDAD', 'JORNADA'])['CANTIDAD'].sum().reset_index()
        df_plot['JORNADA'] = df_plot['JORNADA'].map(map_jor)
        
        fig = px.bar(
            df_plot, x='CANTIDAD', y='NACIONALIDAD', color='JORNADA',
            orientation='h', barmode='stack',
            title="Distribución General de Nacionalidad",
            color_discrete_map={'Diurna': '#162f8a', 'Vespertina': '#565EB3'}
        )

    fig.update_layout(
        height=450,
        template="plotly_white",
        margin=dict(t=60, b=20, l=20, r=20),
        yaxis_title=None,
        xaxis_title=None,
        legend=dict(title_text="", orientation="h", yanchor="bottom", xanchor="center", y=-0.15, x=0.5),
        hovermode="closest",
        xaxis=dict(showspikes=False),
        yaxis=dict(showspikes=False)
    )

    if jornada_sel != "Todas":
        etiqueta_extra = "Género"
    elif genero_sel != "Todos":
        etiqueta_extra = "Jornada"
    else:
        etiqueta_extra = "Jornada"

    fig.update_traces(
        hovertemplate=(
            "<b>Nacionalidad:</b> %{y}<br>"+
            f"<b>{etiqueta_extra}:</b> %{{fullData.name}}<br>"+
            "<b>Cantidad:</b> %{x}<br>"+
            "<extra></extra>"
        )
    )
    fig.update_yaxes(categoryorder='total ascending')

    return fig

def crear_grafico_comunas(df, jornada_sel, genero_sel):

    if df.empty:
        return go.Figure().update_layout(title="Sin datos de comunas")
    
    if jornada_sel != "Todas" and genero_sel == "Todos":
        nombre_jornada = map_jor.get(jornada_sel, jornada_sel)
        df_plot = df.groupby(['COMUNA', 'GENERO'])['CANTIDAD'].sum().reset_index()
        df_plot['GENERO'] = df_plot['GENERO'].map(map_gen)
        
        subtitulo = f"<span style='font-size: 13px; color: #12246b;'>Jornada: {nombre_jornada}</span>"
        etiqueta_extra = "Género"
        
        fig = px.bar(
            df_plot, x='CANTIDAD', y='COMUNA', color='GENERO',
            orientation='h', barmode='group',
            title=f"Comunas por Género<br>{subtitulo}",
            color_discrete_map={'Mujer': '#EE6D78', 'Hombre': '#1B998B'}
        )

    elif genero_sel != "Todos" and jornada_sel == "Todas":
        nombre_genero = map_gen.get(genero_sel, genero_sel)
        df_plot = df.groupby(['COMUNA', 'JORNADA'])['CANTIDAD'].sum().reset_index()
        df_plot['JORNADA'] = df_plot['JORNADA'].map(map_jor)

        subtitulo = f"<span style='font-size: 13px; color: #12246b;'>Género: {nombre_genero}</span>"
        etiqueta_extra = "Jornada"
        
        fig = px.bar(
            df_plot, x='CANTIDAD', y='COMUNA', color='JORNADA',
            orientation='h', barmode='group',
            title=f"Comunas por Jornada<br>{subtitulo}",
            color_discrete_map={'Diurna': '#565EB3', 'Vespertina': '#FEE35D'}
        )

    else:
        df_plot = df.groupby(['COMUNA', 'JORNADA'])['CANTIDAD'].sum().reset_index()
        df_plot['JORNADA'] = df_plot['JORNADA'].map(map_jor)
        etiqueta_extra = "Jornada"
        
        fig = px.bar(
            df_plot, x='CANTIDAD', y='COMUNA', color='JORNADA',
            orientation='h', barmode='stack',
            title="Distribución General por Comuna",
            color_discrete_map={'Diurna': '#162f8a', 'Vespertina': '#565EB3'}
        )

    fig.update_layout(
        height=900,
        template="plotly_white",
        margin=dict(t=80, b=40, l=20, r=20),
        yaxis_title=None,
        xaxis_title=None,
        legend=dict(title_text="", orientation="h", yanchor="bottom", xanchor="center", y=-0.1, x=0.5),
        hovermode="closest",
        xaxis=dict(showspikes=False),
        yaxis=dict(showspikes=False)
    )

    # --- CONFIGURACIÓN DE HOVER Y EJES ---
    
    fig.update_traces(
        hovertemplate=(
            "<b>Comuna:</b> %{y}<br>"+
            f"<b>{etiqueta_extra}:</b> %{{fullData.name}}<br>"+
            "<b>Cantidad:</b> %{x}<br>"+
            "<extra></extra>"
        )
    )

    fig.update_yaxes(
        tickfont=dict(size=10),
        categoryorder='total ascending'
    )

    return fig

def crear_grafico_via_admision(df, jornada_sel, genero_sel):
    if df.empty:
        return go.Figure().update_layout(title="Sin datos de vía de admisión")

    map_gen = {'F': 'Mujer', 'M': 'Hombre'}
    map_jor = {'D': 'Diurna', 'V': 'Vespertina'}

    if jornada_sel != "Todas" and genero_sel == "Todos":
        nombre_jornada = map_jor.get(jornada_sel, jornada_sel)
        df_plot = df.groupby(['VIA_ADMISION', 'GENERO'])['CANTIDAD'].sum().reset_index()
        df_plot['GENERO'] = df_plot['GENERO'].map(map_gen)
        
        sub = f"<span style='font-size: 13px; color: #12246b;'>Jornada: {nombre_jornada}</span>"
        etiqueta = "Género"
        fig = px.bar(df_plot, x='VIA_ADMISION', y='CANTIDAD', color='GENERO',
                     barmode='group', title=f"Admisión por Género<br>{sub}",
                     color_discrete_map={'Mujer': '#162f8a', 'Hombre': '#F4F1BB'})

    elif genero_sel != "Todos" and jornada_sel == "Todas":
        nombre_genero = map_gen.get(genero_sel, genero_sel)
        df_plot = df.groupby(['VIA_ADMISION', 'JORNADA'])['CANTIDAD'].sum().reset_index()
        df_plot['JORNADA'] = df_plot['JORNADA'].map(map_jor)

        sub = f"<span style='font-size: 13px; color: #12246b;'>Género: {nombre_genero}</span>"
        etiqueta = "Jornada"
        fig = px.bar(df_plot, x='VIA_ADMISION', y='CANTIDAD', color='JORNADA',
                     barmode='group', title=f"Admisión por Jornada<br>{sub}",
                     color_discrete_map={'Diurna': '#565EB3', 'Vespertina': '#FEE35D'})

    else:
        df_plot = df.groupby(['VIA_ADMISION', 'JORNADA'])['CANTIDAD'].sum().reset_index()
        df_plot['JORNADA'] = df_plot['JORNADA'].map(map_jor)
        etiqueta = "Jornada"
        fig = px.bar(df_plot, x='VIA_ADMISION', y='CANTIDAD', color='JORNADA',
                     barmode='stack', title="Distribución Vía de Admisión",
                     color_discrete_map={'Diurna': '#162f8a', 'Vespertina': '#565EB3'})

    fig.update_layout(
        height=350, template="plotly_white", margin=dict(t=80, b=20, l=20, r=20),
        showlegend=False,
        xaxis_title=None, yaxis_title="Cant. Alumnos",
        legend=dict(title_text="", orientation="h", yanchor="bottom", xanchor="center", y=-0.25, x=0.5),
        hovermode="closest",
    )

    fig.update_traces(
        hovertemplate=f"<b>Vía:</b> %{{x}}<br><b>{etiqueta}:</b> %{{fullData.name}}<br><b>Cantidad:</b> %{{y}}<extra></extra>"
    )
    fig.update_xaxes(categoryorder='total descending', showspikes=False)
    fig.update_yaxes(showspikes=False)

    return fig

def crear_grafico_modalidad_origen(df, jornada_sel, genero_sel):
    if df.empty:
        return go.Figure().update_layout(title="Sin datos de modalidad")

    nombre_jornada = map_jor.get(jornada_sel, jornada_sel)
    nombre_genero = map_gen.get(genero_sel, genero_sel)

    # Caso 1: Género específico seleccionado (M o F) 
    if genero_sel != "Todos":
        df_plot = df.groupby('MODALIDAD')['CANTIDAD'].sum().reset_index()
        nombre_titulo = "Hombres" if genero_sel == "M" else "Mujeres"
        
        fig = go.Figure(data=[go.Pie(
            labels=df_plot['MODALIDAD'],
            values=df_plot['CANTIDAD'],
            marker=dict(colors=['#162f8a', '#565EB3', '#F4F1BB', '#FEE35D', '#12246b']),
            textinfo='label+percent',
            textposition='inside',
            insidetextorientation='radial',
            hovertemplate="<b>Modalidad:</b> %{label}<br><b>Cantidad:</b> %{value}<extra></extra>",
            title=dict(
                text=f"<b>{nombre_titulo}</b>",
                position="top center",
                font=dict(
                    family="Arial, sans-serif", 
                    size=18,                   
                    color="#162f8a"           
                )
            )
        )])

    # Caso 2: Género es "Todos", pero Jornada es específica 
    elif jornada_sel != "Todas":
        df_plot = df.groupby('MODALIDAD')['CANTIDAD'].sum().reset_index()
        nombre_jor = "Diurna" if jornada_sel == "D" else "Vespertina"
        
        fig = go.Figure(data=[go.Pie(
            labels=df_plot['MODALIDAD'],
            values=df_plot['CANTIDAD'],
            marker=dict(colors=['#162f8a', '#565EB3', '#F4F1BB', '#FEE35D', '#12246b']),
            textinfo='label+percent',
            textposition='inside',
            insidetextorientation='radial',
            hovertemplate="<b>Modalidad:</b> %{label}<br><b>Cantidad:</b> %{value}<extra></extra>",
            title=dict(
                text=f"<b>Jornada {nombre_jor}</b>",
                position="top center",
                font=dict(
                    family="Arial, sans-serif",
                    size=18,                   
                    color="#162f8a"            
                )
            )
        )])

    # Caso 3: Ambos en "Todos" -> Mostrar comparativo Hombres vs Mujeres
    else:
        df_m = df[df['GENERO'] == 'M'].groupby('MODALIDAD')['CANTIDAD'].sum().reset_index()
        df_f = df[df['GENERO'] == 'F'].groupby('MODALIDAD')['CANTIDAD'].sum().reset_index()

        fig = make_subplots(
            rows=1, cols=2, 
            specs=[[{'type': 'domain'}, {'type': 'domain'}]],
            subplot_titles=("Hombres", "Mujeres")
        )

        fig.add_trace(go.Pie(
            labels=df_m['MODALIDAD'], 
            values=df_m['CANTIDAD'],
            textinfo='label+percent',
            hovertemplate="<b>Hombres</b><br><b>Modalidad:</b> %{label}<br><b>Cantidad:</b> %{value}<extra></extra>",
            marker=dict(colors=['#162f8a', '#565EB3', '#F4F1BB', '#FEE35D']),
            textposition='inside',
            insidetextorientation='radial'
        ), 1, 1)

        fig.add_trace(go.Pie(
            labels=df_f['MODALIDAD'], 
            values=df_f['CANTIDAD'],
            textinfo='label+percent',
            hovertemplate="<b>Mujeres</b><br><b>Modalidad:</b> %{label}<br><b>Cant:</b> %{value}<extra></extra>",
            marker=dict(colors=['#162f8a', '#565EB3', '#F4F1BB', '#FEE35D']),
            textposition='inside',
            insidetextorientation='radial'
        ), 1, 2)

    fig.update_layout(
        height=450, 
        template="plotly_white", 
        margin=dict(t=30, b=20, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", xanchor="center", y=-0.2, x=0.5)
    )
    
    return fig

def crear_grafico_edad(df, jornada_sel, genero_sel):
    if df.empty:
        return go.Figure().update_layout(title="Sin datos de edad")
        
    df = df.copy

    # 1. Caso: Jornada específica -> Histograma por Género
    if jornada_sel != "Todas" and genero_sel == "Todos":
        nombre_jornada = map_jor.get(jornada_sel, jornada_sel)
        df['GENERO'] = df['GENERO'].map(map_gen)
        
        sub = f"<span style='font-size: 13px; color: #12246b;'>Jornada: {nombre_jornada}</span>"
        etiqueta = "Género"
        fig = px.histogram(df, x="EDAD", y="CANTIDAD", color="GENERO",
                           marginal="box", # Añade un diagrama de caja superior para ver medianas
                           title=f"Distribución de Edad por Género<br>{sub}",
                           color_discrete_map={'Mujer': '#162f8a', 'Hombre': '#F4F1BB'},
                           nbins=20)

    # 2. Caso: Género específico -> Histograma por Jornada
    elif genero_sel != "Todos" and jornada_sel == "Todas":
        nombre_genero = map_gen.get(genero_sel, genero_sel)
        df['JORNADA'] = df['JORNADA'].map(map_jor)

        sub = f"<span style='font-size: 13px; color: #12246b;'>Género: {nombre_genero}</span>"
        etiqueta = "Jornada"
        fig = px.histogram(df, x="EDAD", y="CANTIDAD", color="JORNADA",
                           marginal="box",
                           title=f"Distribución de Edad por Jornada<br>{sub}",
                           color_discrete_map={'Diurna': '#565EB3', 'Vespertina': '#FEE35D'},
                           nbins=20)

    else:
        df['JORNADA'] = df['JORNADA'].map(map_jor)
        etiqueta = "Jornada"
        fig = px.histogram(df, x="EDAD", y="CANTIDAD", color="JORNADA",
                           marginal="box",
                           title="Distribución General de Edad",
                           color_discrete_map={'Diurna': '#162f8a', 'Vespertina': '#565EB3'},
                           nbins=20)

    fig.update_layout(
        height=450, template="plotly_white", 
        margin=dict(t=80, b=20, l=20, r=20),
        xaxis_title="Edad (Años)", yaxis_title="Cantidad de Alumnos",
        legend=dict(title_text="", orientation="h", yanchor="bottom", xanchor="center", y=-0.3, x=0.5),
        bargap=0.1
    )

    fig.update_traces(
        hovertemplate=f"<b>Edad:</b> %{{x}} años<br><b>{etiqueta}:</b> %{{fullData.name}}<br><b>Cantidad:</b> %{{y}}<extra></extra>"
    )

    return fig


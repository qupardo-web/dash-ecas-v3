import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash_bootstrap_components as dbc
from dash import html
import pandas as pd

mapeo_gen = {'M': 'Hombre', 'F': 'Mujer'}
mapeo_jor = {'D': 'Diurna', 'V': 'Vespertina'}

def generar_grafico_apilado(df, color_by='GENERO'):
    if df.empty:
        return px.scatter(title="No hay datos disponibles para los filtros seleccionados")

    fig = px.bar(
        df,
        x="COHORTE",
        y="CANTIDAD_REPROBACIONES",
        color=color_by,
        title="Distribución de Reprobaciones al Primer Año",
        barmode='stack', 
        labels={
            "COHORTE": "Año de Ingreso",
            "CANTIDAD_REPROBACIONES": "N° Reprobaciones",
            "GENERO": "Género",
            "JORNADA": "Jornada"
        },
        template="plotly_white",
        custom_data=["CODRAMO", "TASA_REPROBACION_P1", color_by]
    )

    fig.update_traces(
        hovertemplate="<br>".join([
            "<b>Año de Ingreso:</b> %{x}",
            "<b>Ramo:</b> %{customdata[0]}",
            "<b>Segmento (" + color_by + "):</b> %{customdata[2]}",
            "<b>N° Reprobaciones:</b> %{y}",
            "<b>Tasa de Reprobación:</b> %{customdata[1]}%",
            "<extra></extra>" 
        ])
    )

    fig.update_layout(
        xaxis={'type': 'category'},
        font=dict(family="Arial", size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hoverlabel=dict(
            bgcolor="white", 
            font_size=13, 
            font_family="Arial",
            bordercolor="#162f8a" 
        )
    )
    
    return fig

def crear_pie_charts_reprobados(df, ramo_nombre, titulo, jornada_sel="Todas", genero_sel="Todos"):
    if df.empty:
        return go.Figure().update_layout(title="Sin datos de reprobación")

    # 1. Preparación de datos y mapeos
    df_plot = df.copy()
    df_plot['GENERO'] = df_plot['GENERO'].map(mapeo_gen).fillna(df_plot['GENERO'])
    df_plot['JORNADA'] = df_plot['JORNADA'].map(mapeo_jor).fillna(df_plot['JORNADA'])
    total_reprobaciones = int(df_plot['CANTIDAD_REPROBACIONES'].sum())

    # --- CASO 1: Género seleccionado (M o F) -> Mostrar Distribución por JORNADA ---
    if genero_sel != "Todos":
        df_jor = df_plot.groupby('JORNADA')['CANTIDAD_REPROBACIONES'].sum().reset_index()
        nombre_filtro = mapeo_gen.get(genero_sel, genero_sel)
        
        fig = go.Figure(data=[go.Pie(
            labels=df_jor['JORNADA'], 
            values=df_jor['CANTIDAD_REPROBACIONES'], 
            hole=.5,
            marker=dict(colors=['#565EB3', '#FEE35D']),
            textinfo='label+percent',
            hovertemplate="<b>Jornada:</b> %{label}<br><b>Cant:</b> %{value}<extra></extra>",
        )])
        annotations = [dict(text=f"Total<br><b>{total_reprobaciones}</b>", x=0.5, y=0.5, font_size=18, showarrow=False)]

    # --- CASO 2: Jornada seleccionada (D o V) -> Mostrar Distribución por GÉNERO ---
    elif jornada_sel != "Todas":
        df_gen = df_plot.groupby('GENERO')['CANTIDAD_REPROBACIONES'].sum().reset_index()
        nombre_filtro = mapeo_jor.get(jornada_sel, jornada_sel)
        
        fig = go.Figure(data=[go.Pie(
            labels=df_gen['GENERO'], 
            values=df_gen['CANTIDAD_REPROBACIONES'], 
            hole=.5,
            marker=dict(colors=['#162f8a', '#F4F1BB']),
            textinfo='label+percent',
            hovertemplate="<b>Género:</b> %{label}<br><b>Cant:</b> %{value}<extra></extra>",
        )])
        annotations = [dict(text=f"Total<br><b>{total_reprobaciones}</b>", x=0.5, y=0.5, font_size=18, showarrow=False)]

    # --- CASO 3: Sin filtros específicos -> Subplots comparativos ---
    else:
        df_gen = df_plot.groupby('GENERO')['CANTIDAD_REPROBACIONES'].sum().reset_index()
        df_jor = df_plot.groupby('JORNADA')['CANTIDAD_REPROBACIONES'].sum().reset_index()

        fig = make_subplots(
            rows=1, cols=2, 
            specs=[[{'type': 'domain'}, {'type': 'domain'}]],
            subplot_titles=("Distribución por Género", "Distribución por Jornada")
        )

        fig.add_trace(go.Pie(
            labels=df_gen['GENERO'], values=df_gen['CANTIDAD_REPROBACIONES'], 
            hole=.4, marker=dict(colors=['#162f8a', '#F4F1BB']),
            textinfo='label+percent',
            hovertemplate="<b>Género:</b> %{label}<br>Cant: %{value}<extra></extra>"
        ), 1, 1)

        fig.add_trace(go.Pie(
            labels=df_jor['JORNADA'], values=df_jor['CANTIDAD_REPROBACIONES'], 
            hole=.4, marker=dict(colors=['#565EB3', '#FEE35D']),
            textinfo='label+percent',
            hovertemplate="<b>Jornada:</b> %{label}<br>Cant: %{value}<extra></extra>"
        ), 1, 2)
        
        annotations = [
            dict(text=f"Total<br><b>{total_reprobaciones}</b>", x=0.222, y=0.45, font_size=16, showarrow=False),
            dict(text=f"Total<br><b>{total_reprobaciones}</b>", x=0.777, y=0.45, font_size=16, showarrow=False)
        ]

    # Ajustes finales del Layout
    fig.update_layout(
        title_text=f"<b>{titulo}</b>: {ramo_nombre}",
        title_x=0.5,
        template="plotly_white",
        height=450,
        showlegend=False,
        annotations=annotations,
        margin=dict(t=60, b=20, l=20, r=20)
    )
    
    return fig

def generar_grafico_historico_apilado(df, color_by='CODRAMO'):
    if df.empty:
        return go.Figure().update_layout(title="No hay datos históricos disponibles")

    fig = px.bar(
        df,
        x="ANIO",
        y="CANTIDAD_REPROBACIONES",
        color=color_by,
        title="Evolución Histórica de Reprobaciones (Desde 2000)",
        barmode='stack',
        template="plotly_white",
        labels={"ANIO": "Año Académico", 
                "CANTIDAD_REPROBACIONES": "N° Reprobaciones",
                "CODRAMO": "Ramo"},
        custom_data=["CODRAMO", "CANTIDAD_REPROBACIONES"]
    )

    fig.update_traces(
        hovertemplate="<br>".join([
            "<b>Año Académico:</b> %{x}",
            "<b>Ramo:</b> %{customdata[0]}",
            "<b>N° Reprobaciones:</b> %{y}",
            "<extra></extra>" 
        ])
    )

    fig.update_layout(
        xaxis={'type': 'category'},
        showlegend=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hoverlabel=dict(
            bgcolor="white", 
            font_size=13, 
            font_family="Arial",
            bordercolor="#162f8a" 
        )
    )
    
    return fig

def generar_grafico_matriculas_totales(df):
    df = df.copy()
    df['Antiguos'] = df['AntDiurnos_tot'] + df['AntVesp_tot']
    
    df = df.rename(columns={'nuevos': 'Nuevos'})
    
    df_plot = df.melt(
        id_vars=['COHORTE'], 
        value_vars=['Nuevos', 'Antiguos'],
        var_name='Segmento', 
        value_name='Alumnos'
    )

    fig = px.bar(
        df_plot, 
        x='COHORTE', 
        y='Alumnos', 
        color='Segmento',
        barmode='group', 
        color_discrete_map={
            'Nuevos': '#FEE35D',  
            'Antiguos': '#162f8a' 
        },
        text_auto='.3s',
        custom_data= ['Segmento']
    )

    fig.update_layout(
        template="plotly_white",
        xaxis=dict(title="Cohorte Académica", dtick=1),
        yaxis=dict(title="Cantidad de Alumnos"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            title=None
        ),
        margin=dict(l=10, r=10, t=50, b=10),
        height=450
    )
    
    fig.update_traces(
        textposition='outside', 
        cliponaxis=False,
        hovertemplate=(
            "<b>Segmento:</b> %{customdata[0]}<br>" +
            "<b>Cohorte:</b> %{x}<br>" +
            "<b>Cantidad de alumnos:</b> %{y:,.0f}<extra></extra>"  
        )
    )
    
    return fig

def generar_grafico_matriculas_nuevas_dinamico(df, jornada_sel, genero_sel):
    if df.empty:
        return go.Figure().update_layout(title="Sin datos en el rango seleccionado")

    if jornada_sel != "Todas" and genero_sel == "Todos":
        df_plot = df.groupby(['COHORTE', 'GENERO'])['CANTIDAD'].sum().reset_index()
        color_col = 'GENERO'
        labels_map = mapeo_gen
        titulo_segmento = f"Jornada: {mapeo_jor.get(jornada_sel, jornada_sel)}"

    elif genero_sel != "Todos" and jornada_sel == "Todas":
        df_plot = df.groupby(['COHORTE', 'JORNADA'])['CANTIDAD'].sum().reset_index()
        color_col = 'JORNADA'
        labels_map = mapeo_jor
        titulo_segmento = f"Género: {mapeo_gen.get(genero_sel, genero_sel)}"

    else:
        df_plot = df.groupby(['COHORTE', 'JORNADA'])['CANTIDAD'].sum().reset_index()
        color_col = 'JORNADA'
        labels_map = mapeo_jor
        titulo_segmento = "Distribución por Jornada"
    
    df_plot['SEGMENTO_TEXTO'] = df_plot[color_col].map(labels_map)

    fig = px.bar(
        df_plot,
        x='COHORTE',
        y='CANTIDAD',
        color=color_col,
        barmode='group',
        text_auto='.3s',
        custom_data=['SEGMENTO_TEXTO'],
        color_discrete_map={
            "M": "#162f8a", "F": "#F4F1BB",  
            "D": "#565EB3", "V": "#FEE35D"   
        },
        labels={color_col: "Segmento", "COHORTE": "Año"}
    )

    fig.for_each_trace(lambda t: t.update(name=labels_map.get(t.name, t.name)))

    fig.update_traces(
        textposition='outside',
        hovertemplate=(
            "<b>Segmento:</b> %{customdata[0]}<br>"
            "<b>Cohorte:</b> %{x}<br>"
            "<b>Cantidad de alumnos:</b> %{y}<br>"
            "<extra></extra>"
        )
    )

    fig.update_layout(
        template="plotly_white",
        title=f"Alumnos Nuevos - {titulo_segmento}",
        xaxis=dict(dtick=1),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        margin=dict(t=80, b=20, l=20, r=20),
        height=450
    )

    return fig

def generar_grafico_persistencia_titulación(df_persistencia, df_titulacion, rango_anios):
    if df_persistencia is None or df_persistencia.empty:
        return go.Figure().update_layout(title="Sin datos de retención")

    df_persistencia['COHORTE'] = df_persistencia['COHORTE'].astype(int)
    df_p = df_persistencia[
        (df_persistencia['COHORTE'] >= rango_anios[0]) & 
        (df_persistencia['COHORTE'] <= rango_anios[1])
    ].copy()

    if df_p.empty:
        return go.Figure().update_layout(title=f"Sin retención para el rango {rango_anios}")

    df_p_avg = df_p.groupby('ANIO_SEGUIMIENTO')['PORCENTAJE_PERSISTENCIA'].mean().reset_index()
    df_p_avg['ANIO_SEGUIMIENTO'] = pd.to_numeric(df_p_avg['ANIO_SEGUIMIENTO'])
    df_p_avg = df_p_avg.sort_values('ANIO_SEGUIMIENTO')

    fig = go.Figure()

    # Traza de Persistencia
    fig.add_trace(go.Scatter(
        x=df_p_avg['ANIO_SEGUIMIENTO'], 
        y=df_p_avg['PORCENTAJE_PERSISTENCIA'],
        name="Retención",
        line=dict(color="#162f8a", width=4),
        mode='lines+markers',
        hovertemplate=(
            "<b>Año de seguimiento:</b> %{x}<br>"+
            "<b>Tasa de retención al año %{x}:</b> %{y}"+
            "<extra></extra>"
        )
    ))

    if not df_titulacion.empty:
        df_titulacion['COHORTE'] = df_titulacion['COHORTE'].astype(int)
        df_t = df_titulacion[
            (df_titulacion['COHORTE'] >= rango_anios[0]) & 
            (df_titulacion['COHORTE'] <= rango_anios[1])
        ].copy()

        if not df_t.empty:
            df_ingresos = df_p[df_p['ANIO_SEGUIMIENTO'].astype(str) == '1'].groupby('COHORTE')['CANTIDAD_INICIAL'].sum().reset_index()
            
            if not df_ingresos.empty:
                df_t = df_t.merge(df_ingresos, on='COHORTE', how='left')
                df_t['CUM_TIT'] = df_t.groupby('COHORTE')['CANTIDAD_TITULADOS'].cumsum()
                df_t['PCT_TIT_COHORTE'] = (df_t['CUM_TIT'] / df_t['CANTIDAD_INICIAL']) * 100
                
                df_t_avg = df_t.groupby('ANIOS_DEMORA')['PCT_TIT_COHORTE'].mean().reset_index()
                
                rango_completo = pd.DataFrame({'ANIOS_DEMORA': range(1, 8)})
                df_t_final = pd.merge(rango_completo, df_t_avg, on='ANIOS_DEMORA', how='left')
                
                df_t_final['PCT_TIT_COHORTE'] = df_t_final['PCT_TIT_COHORTE'].ffill().fillna(0)
                
                fig.add_trace(go.Scatter(
                    x=df_t_final['ANIOS_DEMORA'], 
                    y=df_t_final['PCT_TIT_COHORTE'],
                    name="Titulación Acumulada",
                    line=dict(color="#ebc934", width=2, dash='dash'),
                    fill='tozeroy',
                    fillcolor='rgba(255, 205, 0, 0.22)',
                    mode='lines',
                    hovertemplate=(
                        "<b>Año de seguimiento:</b> %{x}<br>"+
                        "<b>Tasa de titulación al año %{x}</b> %{y}<br>"+
                        "<extra></extra>"
                    )
                    
                ))

    fig.update_layout(
        template="plotly_white",
        xaxis=dict(title="Años transcurridos (T+n)", dtick=1, range=[0.8, 7.2]),
        yaxis=dict(title="Porcentaje de la Cohorte", ticksuffix="%", range=[0, 105]),
        hovermode="closest",
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
        title=f"Tasas de retención v/s Titulación (Acumulada)"
    )

    return fig

def generar_barras_vacantes(df_rango, rango_años):
    vacantes = df_rango.groupby('COHORTE')['Total_Vacantes'].first().sum()
    matriculados = df_rango['CANTIDAD_MATRICULADOS'].sum()
    
    fig = go.Figure(go.Bar(
        x=['Vacantes', 'Matriculados'],
        y=[vacantes, matriculados],
        marker_color=['#162f8a', '#F4F1BB'],
        text=[f"{int(vacantes):,}", f"{int(matriculados):,}"],
        textposition='auto'
    ))
    
    fig.update_layout(
        title=f"Ocupación Total {rango_años[0]}-{rango_años[1]}",
        template="plotly_white",
        height=450,
        margin=dict(t=80, b=50, l=20, r=20),
    )

    fig.update_traces(
        textposition='outside',
        hovertemplate=(
            "<b>Categoria:</b> %{x}<br>" +
            "<b>Cantidad:</b> %{y:,.0f}<extra></extra>"
        )
    )
    return fig

def generar_pie_vias(df_rango):
    df_vias = df_rango.groupby('VIA_ADMISION')['CANTIDAD_MATRICULADOS'].sum().reset_index()
    
    fig = px.pie(
        df_vias, 
        names='VIA_ADMISION', 
        values='CANTIDAD_MATRICULADOS',
        hole=0.2,
        color_discrete_sequence=['#162f8a', '#F4F1BB', '#957AB8', '#ACD2ED', '#8093F1'],
        custom_data= ['VIA_ADMISION']
        
    )
    
    fig.update_layout(
        title="Distribución por Vía de Admisión",
        template="plotly_white",
        height=500,
        margin=dict(t=100, b=100, l=10, r=10),
        legend=dict(
            orientation="h",
            yanchor="top", y=-0.3,
            xanchor="center", x=0.5
        )
    )

    fig.update_traces(
        textposition='inside',
        hovertemplate=(
            "<b>Via de admisión:</b> %{customdata[0]}<br>" +
            "<b>Cantidad:</b> %{value}<extra></extra>"
        )
    )

    return fig

def generar_grafico_area_formacion(df, rango_años):
    
    df_filtrado = df[(df['AÑO'] >= rango_años[0]) & (df['AÑO'] <= rango_años[1])].sort_values('AÑO')
  
    df_melt = df_filtrado.melt(
        id_vars=['AÑO'], 
        value_vars=['PROFESIONAL', 'UNIVERSITARIO', 'DOCTORADO', 'MAGISTER', 'LICENCIADO'],
        var_name='Grado/Título', 
        value_name='Cantidad'
    )
    
    fig = px.bar(
        df_melt, 
        x='AÑO', 
        y='Cantidad', 
        color='Grado/Título',
        title="Distribución por Nivel de Formación Académica",
        barmode='group', 
        color_discrete_sequence=['#162f8a', '#F4F1BB', '#957AB8', '#ACD2ED', '#8093F1'],
        text_auto=True,
        custom_data=['Grado/Título']
    )

    fig.update_layout(
        template='plotly_white',
        xaxis=dict(dtick=1),
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
        margin=dict(t=100, b=50, l=20, r=20)
    )

    fig.update_traces(
        textposition='inside',
        hovertemplate=(
            "<b>Nivel de formación:</b> %{customdata[0]}<br>" +
            "<b>Cantidad de docentes:</b> %{y}<br>" +
            "<b>Año:</b> %{x}<br>" +
            "<extra></extra>" 

        )
    )

    return fig

def generar_grafico_contrato(df, rango_años):
    
    df_filtrado = df[(df['AÑO'] >= rango_años[0]) & (df['AÑO'] <= rango_años[1])].sort_values('AÑO')

    columnas_excluidas = ['AÑO', 'cantidad']
    columnas_contrato = [col for col in df_filtrado.columns if col not in columnas_excluidas]
    
    df_melt = df_filtrado.melt(
        id_vars=['AÑO'], 
        value_vars=columnas_contrato,
        var_name='Tipo de Contrato', 
        value_name='Cantidad'
    )
    
    fig = px.bar(
        df_melt, 
        x='AÑO', 
        y='Cantidad', 
        color='Tipo de Contrato',
        title="Distribución por tipo de contrato",
        barmode='group',
        color_discrete_sequence=['#162f8a', '#F4F1BB', '#957AB8', '#ACD2ED', '#8093F1'],
        text_auto=True,
        custom_data = ['Tipo de Contrato']
    )

    fig.update_layout(
        template='plotly_white',
        xaxis=dict(dtick=1),
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=-0.4, 
            xanchor="center", 
            x=0.5,
            title_text="" 
        ),
        margin=dict(t=100, b=50, l=20, r=20)
    )

    fig.update_traces(
        hovertemplate=(
            "<b>Tipo de contrato:</b> %{customdata[0]}<br>" +
            "<b>Cantidad de docentes: </b>%{y}<br>" +
            "<b>Año:</b> %{x}<br>"
            "<extra></extra>" 
        ),
    )

    return fig

def generar_grafico_rotacion(df, rango_años):
    df = df[(df['AÑO'] >= rango_años[0]) & (df['AÑO'] <= rango_años[1])].sort_values('AÑO')
    
    fig = go.Figure()
 
    fig.add_trace(
        go.Bar(
            x=df['AÑO'], 
            y=df['Total_Academicos'], 
            name="Total Académicos", 
            marker_color='rgba(22, 47, 138, 0.3)',
            hovertemplate=(
                "<b>Año:</b> %{x}<br>" +
                "<b>Cantidad de docentes:</b> %{y}<br>" +
                "<extra></extra>"
            )
        )
    )
    

    fig.add_trace(
        go.Scatter(
            x=df['AÑO'], 
            y=df['Tasa_Rotacion_Porcentaje'], 
            name="Tasa Rotación %",
            line=dict(
                color='#162f8a', 
                width=3), 
            yaxis='y2',
            hovertemplate=(
                "<b>Año:</b> %{x}<br>" +
                "<b>Tasa de rotación:</b> %{y}<br>" +
                "<extra></extra>"
            )
        )
    )
    
    fig.update_layout(
        title="Tasa de Rotación Docente Anual",
        yaxis=dict(
            title="Cantidad de Docentes"
        ),
        yaxis2=dict(
            title="Tasa de Rotación (%)", 
            overlaying='y', 
            side='right', 
            range=[0, 100]
        ),
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=1.02, 
            xanchor="right", 
            x=1
        ),
        template='plotly_white'
    )
    return fig

def generar_grafico_horario(df, rango_años):
    
    df = df[(df['AÑO'] >= rango_años[0]) & (df['AÑO'] <= rango_años[1])]
    
    if df.empty:
        return go.Figure().update_layout(title="Sin datos para este periodo")

    # Sumamos los totales del periodo seleccionado
    valores = [
        df['COMPLETA'].sum(),
        df['MEDIA'].sum(),
        df['HORAS'].sum()
    ]
    etiquetas = ['Jornada Completa', 'Media Jornada', 'Por Horas']

    fig = go.Figure(data=[go.Pie(
        labels=etiquetas,
        values=valores,
        hole=.4,
        marker=dict(colors=['#162f8a', '#565EB3', '#FEE35D']),
        textinfo='label+percent',
    )])

    fig.update_layout(
        title=f"Distribución de Carga Horaria ({rango_años[0]}-{rango_años[1]})",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5)
    )

    fig.update_traces(
        hovertemplate = (
            "<b>Tipo de horario:</b> %{label}<br>" +
            "<b>Cantidad de docentes:</b> %{value}" +
            "<extra></extra>" 

        )
    )

    return fig
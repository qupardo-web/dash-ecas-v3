import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

def create_dynamic_ingresos_chart(df: pd.DataFrame, rango: list, label_genero: str) -> go.Figure:
    """
    Decide entre Gráfico de Barras (Año único) o Líneas (Rango).
    Incluye lógica de resaltado ECAS y línea de promedio para institución única.
    """
    if df is None or df.empty: 
        return go.Figure().update_layout(title="Sin datos para los filtros seleccionados")

    es_año_unico = (rango[0] == rango[1])

    if es_año_unico:
        # --- MODO BARRAS (Un solo año) ---
        # Ordenamos por cantidad para que las barras se vean jerarquizadas
        df = df.sort_values('total_ingresos', ascending=False)
        
        fig = px.bar(
            df, 
            x='nomb_inst', 
            y='total_ingresos',
            color='nomb_inst', 
            text_auto='.0f',
            title=f"Matrícula {rango[0]}{label_genero}",
            labels={'nomb_inst': 'Institución', 'total_ingresos': 'Alumnos'},
        )
        
        # Resaltado ECAS en barras
        for trace in fig.data:
            if "ESCUELA DE CONTADORES" in trace.name.upper() or "ECAS" in trace.name.upper():
                trace.update(marker_color="#162f8a", opacity=1.0)
            else:
                trace.update(opacity=1.0)
                
        fig.update_layout(
            showlegend=True,
            xaxis=dict(showticklabels=False, title=None))

    else:
        eje_x = "cohorte" if "cohorte" in df.columns else "anio_ingreso"
        
        fig = px.line(
            df, 
            x=eje_x, 
            y="total_ingresos", 
            color="nomb_inst",
            markers=True, 
            title=f"Evolución Histórica de Matrícula{label_genero}",
            labels={eje_x: "Año de Ingreso", "total_ingresos": "Total Matriculados", "nomb_inst": "Institución"},
            color_discrete_sequence=px.colors.qualitative.Safe 
        )

        # Lógica de Línea de Promedio (Solo si hay una institución seleccionada)
        instituciones = df['nomb_inst'].unique()
        if len(instituciones) == 1:
            promedio = df['total_ingresos'].mean()
            fig.add_hline(
                y=promedio, 
                line_dash="dot", 
                line_color="red",
                annotation_text=f"Promedio: {promedio:.0f}", 
                annotation_position="top left"
            )

        # Configuración de TRAZAS (Estilo visual ECAS)
        fig.for_each_trace(lambda t: t.update(
            line=dict(
                width=3 if "ESCUELA DE CONTADORES" in t.name.upper() or "ECAS" in t.name.upper() else 2,
                color="#162f8a" if "ESCUELA DE CONTADORES" in t.name.upper() else None 
            )
        ))

    # --- CONFIGURACIÓN COMÚN DE LAYOUT ---
    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        legend=dict(
            orientation="h", 
            y=-0.3,
            x=0.5,
            xanchor="center",
        ),
        xaxis=dict(dtick=1) if not es_año_unico else dict(),
        margin=dict(t=80, b=100, l=50, r=50)
    )
    
    return fig


def create_dynamic_permanencia_chart(df: pd.DataFrame, rango: list) -> go.Figure:
    """
    Cerebro que decide entre Barras (año único) o Líneas (rango).
    Utiliza el estilo de resaltado ECAS.
    """
    if df.empty:
        return go.Figure().update_layout(title="Sin datos disponibles")

    es_año_unico = (rango[0] == rango[1])

    if es_año_unico:

        if 'tasa_permanencia_pct' not in df.columns:
            df = df.copy()
            df['tasa_permanencia_pct'] = (df['base_n1'] / df['base_n']) * 100

        fig = px.bar(
            df,
            x="nomb_inst",
            y="tasa_permanencia_pct",
            color="nomb_inst",
            text_auto='.1f',
            labels={
                "nomb_inst": "Institución",
                "tasa_permanencia_pct": "Tasa de Permanencia (%)"
            },
        )

        # Resaltar la barra de ECAS
        for trace in fig.data:
            if "ESCUELA DE CONTADORES" in trace.name.upper():
                trace.update(marker_color="#162f8a", opacity=1.0)
            else:
                trace.update(opacity=1)

        fig.update_layout(
            title=f"Tasa de Permanencia N a N+1 (Cohorte {rango[0]})",
            height=450,
            template="plotly_white",
            margin=dict(t=100, b=20, l=20, r=20),
            legend=dict(orientation="h", y=-0.1),
            yaxis=dict(showticklabels=False),
            xaxis=dict(showticklabels=False, title=None),
            showlegend=True # En barras el eje X ya dice el nombre
        )
        return fig

    else:
     
        df["cohorte"] = df["cohorte"].astype(int)

        fig = px.line(
            df,
            x="cohorte",
            y="tasa_permanencia_pct",
            color="nomb_inst",
            markers=True,
            labels={
                "cohorte": "Cohorte de Ingreso",
                "tasa_permanencia_pct": "Tasa de Permanencia (%)",
                "nomb_inst": "Institución"
            },
            color_discrete_sequence=px.colors.qualitative.Safe
        )

        # Aplicar tu lógica de resaltado robusta
        for trace in fig.data:
            if "ESCUELA DE CONTADORES" in trace.name.upper():
                trace.update(
                    line=dict(width=1, color="#162f8a"),
                    marker=dict(size=6),
                    opacity=1.0,
                    legendrank=1
                )
            else:
                trace.update(
                    line=dict(width=1, dash="solid"),
                    opacity=1.0,
                    marker=dict(size=6)
                )

        fig.update_layout(
            title=(
                "<b>Permanencia de Estudiantes Primer Año (N → N+1)</b><br>"
                "<sup>Comparativa longitudinal: % de alumnos que continúan</sup>"
            ),
            hovermode="x unified",
            yaxis=dict(ticksuffix="%", range=[0, 105], gridcolor="#eeeeee"),
            xaxis=dict(showticklabels=False, title=None),
            template="plotly_white",
            height=450,
            legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5),
            margin=dict(t=100, l=60, r=40, b=120)
        )
        return fig

def create_cambio_jornada_charts(df):
    if df.empty:
        return go.Figure().update_layout(title="Sin datos para el rango seleccionado")

    jornadas = df['jornada_origen'].unique()
    # Definimos colores fijos para consistencia
    colores = {
        'Mantiene Jornada': '#2ecc71', # Verde
        'Cambio de Jornada': '#3498db', # Azul
        'Deserción': '#e74c3c'          # Rojo
    }

    # Creamos subplots: 1 fila, N columnas (una por cada jornada de origen)
    fig = make_subplots(
        rows=1, cols=len(jornadas),
        subplot_titles=[f"Origen: {j}" for j in jornadas],
        shared_yaxes=True
    )

    for i, jornada in enumerate(jornadas):
        df_plot = df[df['jornada_origen'] == jornada]
        
        # Agregamos las barras apiladas por cada estado
        for estado in ['Mantiene Jornada', 'Cambio de Jornada', 'Deserción']:
            df_estado = df_plot[df_plot['estado_retencion'] == estado]
            
            fig.add_trace(
                go.Bar(
                    name=estado,
                    x=df_estado['cohorte'],
                    y=df_estado['cantidad_alumnos'],
                    marker_color=colores[estado],
                    showlegend=(i == 0), # Solo mostrar leyenda en el primer gráfico
                    hovertemplate="Cohorte %{x}<br>Cantidad: %{y}<extra></extra>"
                ),
                row=1, col=i+1
            )

    fig.update_layout(
        barmode='stack',
        title_text="Distribución de Permanencia y Cambio de Jornada",
        height=450,
        template="plotly_white",
        legend=dict(orientation="h", y=-0.2)
    )
    
    return fig

def create_survival_graduation_chart(df, nombre_inst):
    
    if df.empty:
        return go.Figure().update_layout(title="Sin datos para la selección")
        
    fig = go.Figure()

    # Curva de Supervivencia (Matrícula)
    fig.add_trace(go.Scatter(
        x=df['t_anios'], 
        y=df['pct_supervivencia'],
        name="Supervivencia (% Matrícula)",
        line=dict(color="#2c3e50", width=3),
        mode='lines+markers'
    ))

    # Curva de Titulación Acumulada
    fig.add_trace(go.Scatter(
        x=df['t_anios'], 
        y=df['pct_titulacion_acum'],
        name="Titulación Acumulada (%)",
        line=dict(color="#e67e22", width=3, dash='dash'),
        fill='tozeroy',
        mode='lines+markers'
    ))

    fig.update_layout(
        title=f"Trayectoria Académica: {nombre_inst}",
        xaxis_title="Años transcurridos desde el ingreso (T+n)",
        yaxis=dict(title="Porcentaje de la Cohorte", ticksuffix="%", range=[0, 105]),
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
    )
    
    return fig

def create_fuga_pie_chart(df, titulo):
    if df.empty:
        return px.pie(title="No hay datos para el periodo seleccionado")
    
    label_col = df.columns[0] # inst_destino, carrera_destino o area_conocimiento_destino
    
    fig = px.pie(
        df, 
        values='cant', 
        names=label_col,
        hole=0.4,  # Estilo Donut para mejor lectura
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        title=titulo,
        margin=dict(t=50, b=20, l=20, r=20),
        legend=dict(orientation="h", y=-0.1)
    )
    return fig

def create_tiempo_descanso_horiz_chart(df):
    if df.empty:
        return go.Figure().update_layout(title="Sin datos de reingreso")

    fig = px.bar(
        df,
        x='porcentaje',
        y='Rango_de_Descanso',
        orientation='h',
        color='Rango_de_Descanso',
        color_discrete_sequence=px.colors.qualitative.Prism,
        template="plotly_white"
    )

    fig.update_layout(
        title="Distribución de Tiempo de Descanso (Post-ECAS)",
        xaxis_title="Porcentaje de la Población (%)",
        yaxis_title=None,
        xaxis=dict(range=[0, 100]),
        showlegend=False,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    fig.update_traces(textposition='outside')
    
    return fig

def create_gauge_titulacion_externa(df_metrica):
    if df_metrica.empty:
        tasa = 0
        total_tit = 0
    else:
        tasa = df_metrica['tasa_exito_externo'].iloc[0]
        total_tit = df_metrica['total_titulados_ext'].iloc[0]

    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = tasa,
        number = {'suffix': "%", 'font': {'size': 40}, 'valueformat': '.1f'},
        title = {'text': f"Tasa de Éxito Externo<br><span style='font-size:0.8em;color:gray'>{total_tit} Titulados en otras Inst.</span>", 'font': {'size': 18}},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': "#d6b822"}, 
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 50], 'color': '#f8f9fa'},
                {'range': [50, 100], 'color': '#e9ecef'}
            ],
        }
    ))

    fig.update_layout(height=300, margin=dict(t=100, b=20, l=30, r=30))
    return fig

def create_gauge_exito_captacion(df):
    tasa = df['tasa_exito_interno'].iloc[0] if not df.empty else 0
    total = df['total_captados'].iloc[0] if not df.empty else 0
    total_tit = df['titulados_en_ecas'].iloc[0] if not df.empty else 0
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = tasa,
        number = {'suffix': "%", 'font': {'size': 40}, 'valueformat': '.1f'},
        title = {
            'text': f"Éxito de Captación (ECAS)<br><span style='font-size:0.8em;color:gray'>{total_tit} Titulados en ECAS.</span>", 
            'font': {'size': 18}, 'align': 'center'
        },
        gauge = {
            'axis': {'range': [0, 100]},
            'bar': {'color': "#2e65e6"}, # Color oscuro/azul para diferenciar del naranja
            'steps': [
                {'range': [0, 50], 'color': '#f8f9fa'},
                {'range': [50, 100], 'color': '#e9ecef'}
            ],
        }
    ))
    fig.update_layout(height=300, margin=dict(t=100, b=20, l=30, r=30))
    return fig
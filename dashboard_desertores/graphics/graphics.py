import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

def create_ingresos_line_chart(df):
    if df is None or df.empty: 
        return go.Figure().update_layout(title="Sin datos para los filtros seleccionados")

    # 1. Crear el gráfico base con una paleta de colores variada
    fig = px.line(
        df, 
        x="cohorte", 
        y="total_ingresos", 
        color="nomb_inst",
        markers=True, 
        template="plotly_white",
        color_discrete_sequence=px.colors.qualitative.Plotly # Colores distintos para cada línea
    )

    # 2. Configuración de TRAZAS (Estilo visual)
    fig.for_each_trace(lambda t: t.update(
        # Eliminamos "visible='legendonly'" para que todas nazcan visibles (True por defecto)
        # Resaltamos a ECAS por sobre las demás mediante el grosor de línea
        line=dict(
            width=5 if "ECAS" in t.name.upper() else 2,
            color="#FF6600" if "ECAS" in t.name.upper() else None # Color institucional para ECAS
        )
    ))

    # 3. Configuración de LAYOUT
    fig.update_layout(
        hovermode="x unified",
        legend=dict(
            orientation="h", 
            y=-0.3,
            x=0.5,
            xanchor="center",
            itemclick="toggle",
            itemdoubleclick="toggleothers"
        ),
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(title="Año de Ingreso (Cohorte)", tickmode='linear'),
        yaxis=dict(title="Total Matriculados")
    )
    
    return fig

def create_permanencia_line_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return go.Figure().update_layout(title="Sin datos disponibles")

    # Asegurar tipos de datos para el eje X
    df["cohorte"] = df["cohorte"].astype(int)

    # Definir paleta: Colores suaves para la competencia, naranja para ECAS
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
        color_discrete_sequence=px.colors.qualitative.Safe # Colores legibles
    )

    # Aplicar lógica de resaltado robusta
    for trace in fig.data:
        # Buscamos 'ESCUELA DE CONTADORES' o el código 104 para mayor seguridad
        if "ESCUELA DE CONTADORES" in trace.name.upper():
            trace.update(
                line=dict(width=5, color="#FF6600"), # Naranja ECAS
                marker=dict(size=10, symbol="diamond"),
                opacity=1.0,
                legendrank=1 # Asegura que aparezca primero en la leyenda
            )
        else:
            trace.update(
                line=dict(width=1.5, dash="solid"), # Sólida pero delgada
                opacity=0.5,
                marker=dict(size=6)
            )

    fig.update_layout(
        title=(
            "<b>Permanencia de Estudiantes Primer Año (N → N+1)</b><br>"
            "<sup>Comparativa longitudinal: % de alumnos que continúan tras su ingreso</sup>"
        ),
        hovermode="x unified",
        yaxis=dict(
            ticksuffix="%",
            range=[0, 105], # Fijar escala para evitar distorsiones visuales
            gridcolor="#eeeeee"
        ),
        xaxis=dict(
            title=None,
            tickmode='linear',
            dtick=1,
            gridcolor="#eeeeee"
        ),
        template="plotly_white",
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.4,
            xanchor="center",
            x=0.5
        ),
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
import plotly.express as px
import plotly.graph_objects as go
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
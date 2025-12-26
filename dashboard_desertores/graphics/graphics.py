import plotly.express as px
import plotly.graph_objects as go

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


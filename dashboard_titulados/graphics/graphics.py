import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import pandas as pd

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
        color='nivel_global',  
        title=f"Primer Nivel de Reingreso ({poblacion})",
        color_discrete_sequence=['#162f8a', '#565EB3', '#F4F1BB', '#FEE35D', '#12246b']
    )
    
    fig.update_traces(
        textposition='outside',
        hovertemplate=(
            "<b>Nivel global:</b> %{x}<br>"+
            "<b>Cantidad de alumnos:</b> %{y}"+
            "<extra></extra>"
        )
    )

    fig.update_layout(
        xaxis_title="Nivel Académico",
        yaxis_title="Cantidad de Alumnos",
        showlegend=False,  
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
        color_discrete_sequence=['#162f8a', '#565EB3', '#F4F1BB', '#FEE35D', '#12246b']
    )
    
    fig.update_traces(
        textinfo='percent+label', 
        textposition='inside',
        hovertemplate=(
            "<b>Nivel global:</b> %{label}<br>"+
            "<b>Cantidad de alumnos:</b> %{value}"+
            "<extra></extra>"
        )
    )

    fig.update_layout(
        template="plotly_white",
        legend=dict(orientation="h", y=-0.1, xanchor='center', x= 0.5),
        margin=dict(t=50, b=20, l=20, r=20)
    )
    return fig

def crear_grafico_top_destinos(df, titulo, es_horizontal=True, label_hover="Destino"):
    if df.empty:
        return px.bar(title="Sin datos para la selección")

    if es_horizontal:
        fig = px.bar(
            df, 
            y='destino', 
            x='cantidad_alumnos', 
            orientation='h',
            text='cantidad_alumnos', 
            color='destino',
            color_discrete_sequence=px.colors.qualitative.Prism)
        fig.update_traces(
            hovertemplate=(
                f"<b>{label_hover}:</b> %{{y}}<br>"
                "<b>Alumnos:</b> %{x}<br>"
                "<extra></extra>"
            )
        )
        fig.update_layout(
            yaxis={
                'categoryorder':'total ascending'
            }
        )


    else:
        fig = px.pie(
            df, 
            values='cantidad_alumnos', 
            names='destino', 
            hole=0.3,
            color_discrete_sequence=px.colors.qualitative.Safe)
        fig.update_traces(
            hovertemplate=(
                f"<b>{label_hover}:</b> %{{label}}<br>"
                "<b>Cantidad:</b> %{value}<br>"
                "<b>Porcentaje:</b> %{percent}"
                "<extra></extra>"
            )
        )
    
    fig.update_layout(
        title=titulo, 
        template="plotly_white", 
        showlegend=False if es_horizontal else True)

    return fig

def crear_pictograma_trayectoria(df, titulo):
    if df.empty:
        return go.Figure().update_layout(title=f"{titulo}: Sin datos")

    if 'trayectoria' in df.columns:
        df = df.rename(columns={'trayectoria': 'ruta_secuencial'})

    total_universo = int(df['cantidad'].sum())
    
    df_plot = df.sort_values('cantidad', ascending=False).head(4).copy()
    cantidad_top = int(df_plot['cantidad'].sum())

    cantidad_otros = total_universo - cantidad_top
    porc_otros = (cantidad_otros / total_universo) * 100 if total_universo > 0 else 0

    fig = go.Figure()
    x_coords = np.tile(np.arange(10), 10)
    y_coords = np.repeat(np.arange(9, -1, -1), 10)
    
    color_neutro = "#9ea2a8" 
    colores_rutas = ["#162f8a", "#FF6600", "#00CC96", "#AB63FA", "#EF553B"]
    icono_user = "\uf007" 
    
    current_idx = 0
    ruta_color_idx = 0
    
    for i, (_, row) in enumerate(df_plot.iterrows()):
        ruta = row['ruta_secuencial']
        porcentaje = row['porcentaje']
        cantidad = int(row['cantidad'])
        
        num_icons = int(round(porcentaje))
        end_idx = min(current_idx + num_icons, 100)
        
        if end_idx > current_idx:
            if any(x in ruta for x in ["Abandono", "Solo Pregrado", "Sin Continuidad"]):
                color = color_neutro
            else:
                color = colores_rutas[ruta_color_idx % len(colores_rutas)]
                ruta_color_idx += 1
            
            label_leyenda = f"{porcentaje:.1f}% ({cantidad:,}) - {ruta}".replace(",", ".")
            
            fig.add_trace(go.Scatter(
                x=x_coords[current_idx:end_idx], 
                y=y_coords[current_idx:end_idx],
                mode="text", 
                name=label_leyenda, 
                text=[icono_user] * (end_idx - current_idx),
                textfont=dict(
                    family=' "Font Awesome 6 Free", "Font Awesome 5 Free" ', 
                    size=22, 
                    color=color),
                hovertemplate=f"<b>{ruta}</b><br>Cant: {cantidad:,}<br>%: {porcentaje:.1f}%<extra></extra>".replace(",", ".")
            ))
            current_idx = end_idx

    if current_idx < 100 or cantidad_otros > 0:
        iconos_restantes = max(0, 100 - current_idx)
        label_otros = f"{porc_otros:.1f}% ({cantidad_otros:,}) - Otros".replace(",", ".")
        
        fig.add_trace(go.Scatter(
            x=x_coords[current_idx:100] if iconos_restantes > 0 else [None],
            y=y_coords[current_idx:100] if iconos_restantes > 0 else [None],
            mode="text", 
            name=label_otros,
            text=[icono_user] * iconos_restantes if iconos_restantes > 0 else [None],
            textfont=dict(
                family=' "Font Awesome 6 Free", "Font Awesome 5 Free" ', 
                size=22, 
                color="#E5ECF6"),
            hoverinfo="skip"
        ))

    fig.update_layout(
        title=dict(text=f"<b>{titulo}</b>", x=0.5, y=0.95),
        xaxis=dict(
            showgrid=False, 
            zeroline=False, 
            showticklabels=False, 
            range=[-1, 10]),
        yaxis=dict(
            showgrid=False, 
            zeroline=False, 
            showticklabels=False, 
            range=[-1, 10], 
            scaleanchor="x"),
        legend=dict(
            orientation="h", 
            yanchor="top", 
            y=-0.05, 
            xanchor="center", 
            x=0.5, 
            font=dict(size=10),
            itemsizing='constant'),
        margin=dict(t=80, b=100, l=20, r=20), 
        height=600, 
        plot_bgcolor='white'
        
    )

    return fig

def crear_pictograma_continuidad(df, titulo):
    if df is None or df.empty or df['cantidad'].sum() == 0:
        return go.Figure().update_layout(title="Sin datos para esta selección")

    df = df.sort_values('condicion')
    
    fig = go.Figure()
    x_coords = np.tile(np.arange(10), 10)
    y_coords = np.repeat(np.arange(9, -1, -1), 10)
    
    icono_user = "\uf007"
    colores = {"Continuó Estudios": "#162f8a", "No Continuó": "#E5ECF6"}
    
    current_idx = 0
    for _, row in df.iterrows():
        num_icons = int(round(row['porcentaje']))
        end_idx = min(current_idx + num_icons, 100)
        
        if end_idx > current_idx:
            fig.add_trace(go.Scatter(
                x=x_coords[current_idx:end_idx],
                y=y_coords[current_idx:end_idx],
                mode="text",
                name=f"{row['condicion']} ({row['porcentaje']:.1f}%)",
                text=[icono_user] * (end_idx - current_idx),
                textfont=dict(
                    family=' "Font Awesome 6 Free", "Font Awesome 5 Free", FreeSolid ',
                    size=22, color=colores.get(row['condicion'], "#gray")
                ),
                hovertemplate=f"<b>{row['condicion']}</b><br>{int(row['cantidad'])} alumnos ({row['porcentaje']:.1f}%)<extra></extra>"
            ))
            current_idx = end_idx

    fig.update_layout(
        title=dict(text=f"<b>{titulo}</b>", x=0.5, y=0.95),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1, 10]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1, 10], scaleanchor="x"),
        legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5, font=dict(size=10)),
        margin=dict(t=80, b=100, l=20, r=20), height=600, plot_bgcolor='white'
    )
    return fig

def crear_grafico_demora_reingreso(df, tipo_poblacion):
    if df is None or df.empty:
        return go.Figure().update_layout(
            annotations=[dict(text="Sin datos para los filtros seleccionados", showarrow=False)]
        )

    df = df.copy()
    def formatear_demora(x):
        if x == 0:
            return "Inmediato"
        elif x == 1:
            return "1 Año"
        elif 1 < x <= 5:
            return f"{int(x)} Años"
        else:
            return "6+ Años"

    df['grupo_demora'] = df['demora_anios'].apply(formatear_demora)

    df_plot = df.groupby('grupo_demora')['cantidad_alumnos'].sum().reset_index()
    
    orden_logico = ["Inmediato", "1 Año", "2 Años", "3 Años", "4 Años", "5 Años", "6+ Años"]
    df_plot['grupo_demora'] = pd.Categorical(df_plot['grupo_demora'], categories=orden_logico, ordered=True)
    df_plot = df_plot.sort_values('grupo_demora')
    
    total_alumnos = df_plot['cantidad_alumnos'].sum()

    fig = go.Figure(data=[go.Pie(
        labels=df_plot['grupo_demora'],
        values=df_plot['cantidad_alumnos'],
        hole=.6,
        textinfo='percent', 
        textposition='inside',
        insidetextorientation='horizontal',
        marker=dict(colors=['#162f8a', '#FFB563', '#A663CC', '#F88DAD', '#F9E9EC', '#FAC748', '#8390FA']),
        hoverinfo='label+value+percent'
    )])

    fig.update_traces(
        hovertemplate=(
            "<b>Tiempo de demora:</b> %{label}<br>"+
            "<b>Cantidad de alumnos:</b> %{value}"+
            "<extra></extra>"
        )
    )

    fig.update_layout(
        title=dict(
            text=f"<b>Distribución de Tiempo de Espera ({tipo_poblacion})</b>",
            x=0.5, xanchor='center'
        ),
        annotations=[dict(
            text=f'Total<br><b>{total_alumnos:,}</b>'.replace(',', '.'),
            x=0.5, y=0.5,
            font_size=20,
            showarrow=False
        )],
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5,
            font=dict(size=11)
        ),
        margin=dict(t=60, b=120, l=20, r=20)
    )

    return fig
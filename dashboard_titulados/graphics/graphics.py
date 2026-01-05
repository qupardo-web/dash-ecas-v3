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
        color='nivel_global',  # <--- ESTO activa los colores diferentes por categoría
        title=f"Primer Nivel de Reingreso ({poblacion})",
        # Opcional: Puedes usar una paleta de colores predefinida
        color_discrete_sequence=px.colors.qualitative.Prism 
    )
    
    fig.update_traces(textposition='outside')
    fig.update_layout(
        xaxis_title="Nivel Académico",
        yaxis_title="Cantidad de Alumnos",
        showlegend=False,  # Opcional: oculta la leyenda si no quieres repetir los nombres
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
        color_discrete_sequence=px.colors.qualitative.Prism
    )
    
    fig.update_traces(textinfo='percent+label')
    fig.update_layout(
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
        margin=dict(t=50, b=20, l=20, r=20)
    )
    return fig

def crear_grafico_top_destinos(df, titulo, es_horizontal=True):
    if df.empty:
        return px.bar(title="Sin datos para la selección")

    if es_horizontal:
        fig = px.bar(df, y='destino', x='cantidad_alumnos', orientation='h',
                     text='cantidad_alumnos', color='destino',
                     color_discrete_sequence=px.colors.qualitative.Prism)
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
    else:
        fig = px.pie(df, values='cantidad_alumnos', names='destino', hole=0.3,
                     color_discrete_sequence=px.colors.qualitative.Safe)
    
    fig.update_layout(title=titulo, template="plotly_white", showlegend=False if es_horizontal else True)
    return fig

def crear_pictograma_trayectoria(df, titulo):
    if df.empty:
        return go.Figure().update_layout(title=f"{titulo}: Sin datos")

    # 1. Ordenar por porcentaje para agrupar bloques de colores
    df_plot = df.sort_values('porcentaje', ascending=False).head(6).copy()
    
    fig = go.Figure()

    # Cuadrícula 10x10
    x_coords = np.tile(np.arange(10), 10)
    y_coords = np.repeat(np.arange(9, -1, -1), 10)
    
    colores_rutas = ["#162f8a", "#FF6600", "#00CC96", "#AB63FA", "#EF553B", "#FECB52"]
    icono_user = "\uf007" 
    
    current_idx = 0
    
    for i, (_, row) in enumerate(df_plot.iterrows()):
        ruta = row['ruta_secuencial']
        porcentaje = row['porcentaje']
        cantidad = int(row['cantidad'])
        
        # Cálculo de iconos para el Waffle Chart
        num_icons = int(round(porcentaje))
        end_idx = min(current_idx + num_icons, 100)
        
        if end_idx > current_idx:
            color = colores_rutas[i % len(colores_rutas)]
            
            # Formateamos el nombre para la leyenda con Cantidad y %
            label_leyenda = f"{porcentaje:.1f}% ({cantidad:,}) - {ruta}".replace(",", ".")
            
            fig.add_trace(go.Scatter(
                x=x_coords[current_idx:end_idx],
                y=y_coords[current_idx:end_idx],
                mode="text",
                name=label_leyenda,
                text=[icono_user] * (end_idx - current_idx),
                textfont=dict(
                    family=' "Font Awesome 6 Free", "Font Awesome 5 Free", FreeSolid ',
                    size=22,
                    color=color
                ),
                # Hover con información completa
                hovertemplate=(
                    f"<b>{ruta}</b><br>"
                    f"Cantidad: {cantidad:,}<br>"
                    f"Porcentaje: {porcentaje:.1f}%<extra></extra>"
                ).replace(",", ".")
            ))
            current_idx = end_idx

    # 2. RELLENO: Si sobran espacios
    if current_idx < 100:
        total_otros = int(df['cantidad'].sum() - df_plot['cantidad'].sum())
        porc_otros = 100 - df_plot['porcentaje'].sum()
        
        fig.add_trace(go.Scatter(
            x=x_coords[current_idx:100],
            y=y_coords[current_idx:100],
            mode="text",
            name=f"{porc_otros:.1f}% ({total_otros:,}) - Otros",
            text=[icono_user] * (100 - current_idx),
            textfont=dict(
                family=' "Font Awesome 6 Free", "Font Awesome 5 Free", FreeSolid ',
                size=22,
                color="#E5ECF6"
            ),
            hoverinfo="skip"
        ))

    fig.update_layout(
        title=dict(
            text=f"<b>{titulo}</b><br><span style='font-size:12px;color:gray'>Cada icono representa 1% del total seleccionado</span>",
            x=0.5, y=0.95
        ),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1, 10]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1, 10], scaleanchor="x"),
        legend=dict(
            orientation="h", 
            yanchor="top", 
            y=-0.1, # Bajamos un poco la leyenda para que no choque
            xanchor="center", 
            x=0.5,
            traceorder="normal",
            font=dict(size=10)
        ),
        margin=dict(t=80, b=120, l=20, r=20),
        height=650, # Aumentamos un poco el alto para dar espacio a la leyenda extendida
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
        title=dict(text=f"<b>{titulo}</b>", x=0.5),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1, 10]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1, 10], scaleanchor="x"),
        legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center"),
        margin=dict(t=50, b=50, l=20, r=20),
        height=650,
        plot_bgcolor='white'
    )
    return fig
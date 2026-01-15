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
    
    fig.update_traces(textinfo='percent+label', textposition='inside')
    fig.update_layout(
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="right", x=1),
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

    # Normalizar nombre de columna
    if 'trayectoria' in df.columns:
        df = df.rename(columns={'trayectoria': 'ruta_secuencial'})

    # 1. TOTAL UNIVERSO REAL (Debe dar 3.072 según tu DF)
    total_universo = int(df['cantidad'].sum())
    
    # 2. SELECCIONAR TOP 4 (Categorías principales a graficar)
    df_plot = df.sort_values('cantidad', ascending=False).head(4).copy()
    cantidad_top = int(df_plot['cantidad'].sum())

    # 3. CÁLCULO MATEMÁTICO DEL RESTO (Sin redondeos intermedios)
    # Esto garantiza que (Cantidad Top + Cantidad Otros) sea exactamente 3.072
    cantidad_otros = total_universo - cantidad_top
    porc_otros = (cantidad_otros / total_universo) * 100 if total_universo > 0 else 0

    fig = go.Figure()
    x_coords = np.tile(np.arange(10), 10)
    y_coords = np.repeat(np.arange(9, -1, -1), 10)
    
    color_neutro = "#D3D3D3" 
    colores_rutas = ["#162f8a", "#FF6600", "#00CC96", "#AB63FA", "#EF553B"]
    icono_user = "\uf007" 
    
    current_idx = 0
    ruta_color_idx = 0
    
    # 4. Dibujar categorías del Top
    for i, (_, row) in enumerate(df_plot.iterrows()):
        ruta = row['ruta_secuencial']
        porcentaje = row['porcentaje']
        cantidad = int(row['cantidad'])
        
        # Determinamos iconos visuales (1 icono = 1%)
        num_icons = int(round(porcentaje))
        end_idx = min(current_idx + num_icons, 100)
        
        if end_idx > current_idx:
            # Color gris para categorías de salida/abandono
            if any(x in ruta for x in ["Abandono", "Solo Pregrado", "Sin Continuidad"]):
                color = color_neutro
            else:
                color = colores_rutas[ruta_color_idx % len(colores_rutas)]
                ruta_color_idx += 1
            
            label_leyenda = f"{porcentaje:.1f}% ({cantidad:,}) - {ruta}".replace(",", ".")
            
            fig.add_trace(go.Scatter(
                x=x_coords[current_idx:end_idx], y=y_coords[current_idx:end_idx],
                mode="text", name=label_leyenda, text=[icono_user] * (end_idx - current_idx),
                textfont=dict(family=' "Font Awesome 6 Free", "Font Awesome 5 Free" ', size=22, color=color),
                hovertemplate=f"<b>{ruta}</b><br>Cant: {cantidad:,}<br>%: {porcentaje:.1f}%<extra></extra>".replace(",", ".")
            ))
            current_idx = end_idx

    # 5. BLOQUE DE "OTROS" (Diferencia absoluta forzada)
    # Rellenamos el espacio visual restante pero mostramos el TOTAL REAL de alumnos omitidos
    if current_idx < 100 or cantidad_otros > 0:
        iconos_restantes = max(0, 100 - current_idx)
        label_otros = f"{porc_otros:.1f}% ({cantidad_otros:,}) - Otros".replace(",", ".")
        
        fig.add_trace(go.Scatter(
            # Si no quedan iconos por redondeo, enviamos None para que solo aparezca la leyenda
            x=x_coords[current_idx:100] if iconos_restantes > 0 else [None],
            y=y_coords[current_idx:100] if iconos_restantes > 0 else [None],
            mode="text", name=label_otros,
            text=[icono_user] * iconos_restantes if iconos_restantes > 0 else [None],
            textfont=dict(family=' "Font Awesome 6 Free" ', size=22, color="#E5ECF6"),
            hoverinfo="skip"
        ))

    fig.update_layout(
        title=dict(text=f"<b>{titulo}</b>", x=0.5, y=0.95),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1, 10]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1, 10], scaleanchor="x"),
        legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5, font=dict(size=10)),
        margin=dict(t=80, b=100, l=20, r=20), height=600, plot_bgcolor='white'
    )

    # fig.update_layout(
    #     title=dict(text=f"<b>{titulo}</b>", x=0.5, y=0.95),
    #     xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1, 10]),
    #     yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1, 10], scaleanchor="x"),
    #     legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5, font=dict(size=10)),
    #     margin=dict(t=80, b=100, l=20, r=20),
    #     height=600,
    #     plot_bgcolor='white'
    # )

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

    # 1. Agrupamos los años de espera superiores a 5 para evitar demasiadas categorías
    # Esto limpia las etiquetas minúsculas de 0.03% que ensucian el gráfico
    df = df.copy()
    df['grupo_demora'] = df['demora_anios'].apply(
        lambda x: f"Año {int(x)}" if 0 < x <= 5 else ("Mismo año" if x == 0 else "6+ Años")
    )

    # 2. Consolidar cantidades por el nuevo grupo
    df_plot = df.groupby('grupo_demora')['cantidad_alumnos'].sum().reset_index()
    
    # Ordenar lógicamente: Mismo año, Año 1... Año 5, 6+ Años
    orden_logico = ["Mismo año", "Año 1", "Año 2", "Año 3", "Año 4", "Año 5", "6+ Años"]
    df_plot['grupo_demora'] = pd.Categorical(df_plot['grupo_demora'], categories=orden_logico, ordered=True)
    df_plot = df_plot.sort_values('grupo_demora')
    
    total_alumnos = df_plot['cantidad_alumnos'].sum()

    fig = go.Figure(data=[go.Pie(
        labels=df_plot['grupo_demora'],
        values=df_plot['cantidad_alumnos'],
        hole=.6,
        textinfo='percent', 
        # Forzamos a que el texto esté adentro y ocultamos etiquetas amontonadas
        textposition='inside',
        insidetextorientation='horizontal',
        marker=dict(colors=['#162f8a', '#FFB563', '#A663CC', '#F88DAD', '#F9E9EC', '#FAC748', '#8390FA']),
        hoverinfo='label+value+percent'
    )])

    fig.update_layout(
        title=dict(
            text=f"<b>Distribución de Tiempo de Espera ({tipo_poblacion})</b><br><span style='font-size:12px;color:gray'>Año 1 corresponde al año inmediato posterior a la titulación/desercion</span>",
            x=0.5, xanchor='center'
        ),
        annotations=[dict(
            text=f'Total<br><b>{total_alumnos:,}</b>'.replace(',', '.'),
            x=0.5, y=0.5,
            font_size=20, # Un poco más grande para destacar
            showarrow=False
        )],
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15, # Bajamos la leyenda un poco más
            xanchor="center",
            x=0.5,
            font=dict(size=11)
        ),
        # Aumentamos el margen inferior (b) para que la leyenda no se corte
        margin=dict(t=60, b=120, l=20, r=20)
    )

    return fig
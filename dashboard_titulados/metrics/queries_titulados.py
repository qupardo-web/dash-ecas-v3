from conn_db import get_db_engine
from sqlalchemy import text
import pandas as pd
from typing import Optional, List

db_engine = get_db_engine()

def get_kpis_cabecera(rango_anios, jornada="Todas", genero="Todos", rango_edad="Todos"):
    params = {
        "anio_min": rango_anios[0],
        "anio_max": rango_anios[1]
    }
    
    # Filtros comunes
    filtro_j = "AND jornada = :jornada" if jornada != "Todas" else ""
    if jornada != "Todas": params["jornada"] = jornada
    
    filtro_g = "AND genero = :genero" if genero != "Todos" else ""
    if genero != "Todos": params["genero"] = genero

    filtro_e = "AND rango_edad = :rango_edad" if rango_edad != "Todos" else ""
    if rango_edad != "Todos": params["rango_edad"] = rango_edad
    
    # 1. Total Titulados
    sql_titulados = f"SELECT COUNT(DISTINCT mrun) FROM tabla_dashboard_titulados WHERE cohorte BETWEEN :anio_min AND :anio_max {filtro_j} {filtro_g} {filtro_e} AND cod_inst=104"
    
    # 2. Total Desertores
    filtro_j_des = "AND jornada_ecas = :jornada" if jornada != "Todas" else ""
    sql_desertores = f"SELECT COUNT(DISTINCT mrun) FROM tabla_fuga_detallada_ecas WHERE anio_ingreso_ecas BETWEEN :anio_min AND :anio_max {filtro_j_des} {filtro_g} {filtro_e}"

    # 3. Universo Total de Cohorte
    sql_cohorte = f"SELECT COUNT(DISTINCT mrun) FROM tabla_matriculas_competencia_unificada WHERE cohorte BETWEEN :anio_min AND :anio_max {filtro_j} {filtro_g} {filtro_e} AND cod_inst=104"

    #4. Universo Total de abandono
    filtro_j_abandono = "AND jornada_ecas = :jornada" if jornada != "Todas" else ""
    sql_abandono =f"SELECT COUNT(DISTINCT mrun) FROM tabla_abandono_total_desertores WHERE anio_ingreso_ecas BETWEEN :anio_min AND :anio_max {filtro_j_abandono} {filtro_g} {filtro_e}"
    
    with db_engine.connect() as conn:
        total_tit = conn.execute(text(sql_titulados), params).scalar() or 0
        total_des = conn.execute(text(sql_desertores), params).scalar() or 0
        total_cohorte = conn.execute(text(sql_cohorte), params).scalar() or 0
        total_abandono = conn.execute(text(sql_abandono), params).scalar() or 0
        
    return total_cohorte, total_tit, total_des, total_abandono

def get_nivel_post_salida(rango_anios, tipo_poblacion="Todos", criterio="Primero", jornada="Todas", genero="Todos", rango_edad="Todos"):
    params = {"anio_min": rango_anios[0], "anio_max": rango_anios[1]}
    
    # Construcción de filtros
    filtros = []
    if jornada != "Todas":
        filtros.append("AND jornada_ecas = :jornada")
        params["jornada"] = jornada
    if genero != "Todos":
        filtros.append("AND genero = :genero")
        params["genero"] = genero
    if rango_edad != "Todos":
        filtros.append("AND rango_edad = :rango_edad")
        params["rango_edad"] = rango_edad

    filtro_sql = " ".join(filtros)
    order_by = "anio_matricula_post ASC"

    if tipo_poblacion == "Todos":
        subquery = "SELECT mrun, nivel_estudio_post, anio_matricula_post, anio_ingreso_ecas, genero, jornada_ecas, inst_destino, rango_edad FROM tabla_trayectoria_post_titulado UNION ALL SELECT mrun, nivel_estudio_post, anio_matricula_post, anio_ingreso_ecas, genero, jornada_ecas, inst_destino, rango_edad FROM tabla_fuga_detallada_ecas"
    else:
        tabla = "tabla_trayectoria_post_titulado" if tipo_poblacion == "Titulados" else "tabla_fuga_detallada_ecas"
        subquery = f"SELECT * FROM {tabla}"

    sql_query = f"""
    WITH universo AS ({subquery}),
    eventos_filtrados AS (
        SELECT mrun, nivel_estudio_post, ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY {order_by}) as rn
        FROM universo
        WHERE anio_ingreso_ecas BETWEEN :anio_min AND :anio_max
          {filtro_sql}
    )
    SELECT nivel_estudio_post as nivel_global, COUNT(DISTINCT mrun) as cantidad_alumnos
    FROM eventos_filtrados WHERE rn = 1
    GROUP BY nivel_estudio_post ORDER BY cantidad_alumnos DESC
    """
    return pd.read_sql(text(sql_query), db_engine, params=params)

#print(get_nivel_post_salida(rango_anios=[2007,2007], tipo_poblacion="Titulados", criterio="Primero"))

def get_top_destinos_filtrado(rango_anios, tipo_poblacion="Todos", dimension="inst_destino", nivel="Todos", jornada="Todas", genero="Todos", rango_edad="Todos", top_n=10):
    params = {"anio_min": rango_anios[0], "anio_max": rango_anios[1], "top_n": top_n}

    filtros = []
    if jornada != "Todas":
        filtros.append("AND jornada_ecas = :jornada"); params["jornada"] = jornada
    if genero != "Todos":
        filtros.append("AND genero = :genero"); params["genero"] = genero
    if nivel != "Todos":
        filtros.append("AND nivel_estudio_post = :nivel"); params["nivel"] = nivel
    if rango_edad != "Todos":
        filtros.append("AND rango_edad = :rango_edad"); params["rango_edad"] = rango_edad

    filtro_sql = " ".join(filtros)

    if tipo_poblacion == "Todos":
        subquery = f"""
        SELECT mrun, inst_destino, carrera_destino, tipo_inst_1, nivel_estudio_post, anio_matricula_post, 
        anio_ingreso_ecas, genero, jornada_ecas, rango_edad, area_conocimiento_destino
        FROM tabla_trayectoria_post_titulado 
        UNION ALL 
        SELECT mrun, inst_destino, carrera_destino, tipo_inst_1, nivel_estudio_post, anio_matricula_post, 
        anio_ingreso_ecas, genero, jornada_ecas, rango_edad, area_conocimiento_destino 
        FROM tabla_fuga_detallada_ecas"""
    else:
        tabla = "tabla_trayectoria_post_titulado" if tipo_poblacion == "Titulados" else "tabla_fuga_detallada_ecas"
        subquery = f"SELECT * FROM {tabla}"

    sql_query = f"""WITH universo AS ({subquery}), 
    primer_reingreso AS 
    (SELECT mrun, {dimension} AS destino, ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY anio_matricula_post ASC) as rn 
    FROM universo 
    WHERE anio_ingreso_ecas BETWEEN :anio_min AND :anio_max 
    AND inst_destino NOT LIKE 'IP ESCUELA DE CONTADORES AUDITORES DE SANTIAGO' {filtro_sql}) 
    SELECT TOP (:top_n) destino, COUNT(DISTINCT mrun) as cantidad_alumnos 
    FROM primer_reingreso WHERE rn = 1 GROUP BY destino ORDER BY cantidad_alumnos DESC"""

    return pd.read_sql(text(sql_query), db_engine, params=params)

def get_demora_reingreso(rango_anios, tipo_poblacion="Todos", nivel="Todos", jornada="Todas", genero="Todos", rango_edad="Todos"):
    """
    Calcula el tiempo de reingreso filtrado por cohorte, población, nivel, jornada, género y rango de edad de ingreso.
    """
    params = {
        "anio_min": rango_anios[0],
        "anio_max": rango_anios[1]
    }

    # 1. Construcción de filtros dinámicos
    filtros = []
    if jornada != "Todas":
        filtros.append("AND jornada_ecas = :jornada")
        params["jornada"] = jornada
    if genero != "Todos":
        filtros.append("AND genero = :genero")
        params["genero"] = genero
    if nivel != "Todos":
        filtros.append("AND nivel_estudio_post = :nivel")
        params["nivel"] = nivel
    if rango_edad != "Todos":
        filtros.append("AND rango_edad = :rango_edad")
        params["rango_edad"] = rango_edad

    filtro_str = " ".join(filtros)

    # 2. Definición de subquery según población
    # Es crucial incluir 'rango_edad' en el UNION ALL para que el filtro funcione en el universo 'Todos'
    if tipo_poblacion == "Todos":
        subquery = f"""
            SELECT mrun, anio_ingreso_ecas, nivel_estudio_post, tiempo_espera_post, 
                   anio_matricula_post, inst_destino, genero, jornada_ecas, rango_edad
            FROM tabla_trayectoria_post_titulado
            UNION ALL
            SELECT mrun, anio_ingreso_ecas, nivel_estudio_post, tiempo_espera_post, 
                   anio_matricula_post, inst_destino, genero, jornada_ecas, rango_edad
            FROM tabla_fuga_detallada_ecas
        """
    else:
        tabla = "tabla_trayectoria_post_titulado" if tipo_poblacion == "Titulados" else "tabla_fuga_detallada_ecas"
        subquery = f"SELECT * FROM {tabla}"

    # 3. Consulta final con agregación por demora
    sql_query = f"""
    WITH universo AS ({subquery}),
    eventos AS (
        SELECT 
            mrun,
            anio_ingreso_ecas as cohorte,
            nivel_estudio_post as nivel_global,
            tiempo_espera_post as demora_anios,
            ROW_NUMBER() OVER (
                PARTITION BY mrun, nivel_estudio_post 
                ORDER BY anio_matricula_post ASC
            ) as rn
        FROM universo
        WHERE anio_ingreso_ecas BETWEEN :anio_min AND :anio_max
          AND inst_destino NOT LIKE 'IP ESCUELA DE CONTADORES AUDITORES DE SANTIAGO'
          {filtro_str}
    )
    SELECT 
        cohorte, 
        nivel_global, 
        demora_anios, 
        COUNT(DISTINCT mrun) as cantidad_alumnos
    FROM eventos 
    WHERE rn = 1
    GROUP BY cohorte, nivel_global, demora_anios
    ORDER BY demora_anios ASC
    """
    
    df = pd.read_sql(text(sql_query), db_engine, params=params)

    return df

#print(get_demora_reingreso(rango_anios=[2007,2007], tipo_poblacion="Todos"))

def get_rutas_academicas_completas(rango_anios, tipo_poblacion="Titulados", jornada="Todas", genero="Todos", rango_edad="Todos"):
    params = {"anio_min": rango_anios[0], "anio_max": rango_anios[1], "cod_inst": 104}
    
    # Identificar la tabla maestra según la población (Igual que en continuidad)
    if tipo_poblacion == "Titulados":
        tabla_maestra = "tabla_dashboard_titulados"
        tabla_eventos = "tabla_trayectoria_post_titulado"
        col_jornada = "jornada"
        col_cohorte = "cohorte"
    else:
        tabla_maestra = "tabla_fuga_detallada_ecas"
        tabla_eventos = "tabla_fuga_detallada_ecas" # O la tabla de trayectoria de desertores
        col_jornada = "jornada_ecas"
        col_cohorte = "anio_ingreso_ecas"

    filtros = []
    if jornada != "Todas":
        filtros.append(f"AND u.{col_jornada} = :jornada")
        params["jornada"] = jornada
    if genero != "Todos":
        filtros.append("AND u.genero = :genero")
        params["genero"] = genero
    if rango_edad != "Todos":
        filtros.append("AND u.rango_edad = :rango_edad")
        params["rango_edad"] = rango_edad
    
    filtro_sql = " ".join(filtros)

    sql_query = f"""
    WITH UniversoMaestro AS (
        SELECT mrun, {col_cohorte} as cohorte, {col_jornada} as jornada, genero, rango_edad 
        FROM {tabla_maestra} u 
        WHERE {"u.cod_inst = :cod_inst" if tipo_poblacion == "Titulados" else "1=1"}
    ),
    EventosPost AS (
        -- IMPORTANTE: Para que cuadre con continuidad, NO filtramos ECAS aquí
        -- a menos que la query de continuidad también lo haga.
        SELECT mrun, anio_matricula_post, nivel_estudio_post 
        FROM {tabla_eventos}
    ),
    Cadenas AS (
        SELECT mrun, 'Pregrado > ' + STRING_AGG(nivel_estudio_post, ' > ') 
        WITHIN GROUP (ORDER BY anio_matricula_post ASC) as ruta
        FROM (
            SELECT mrun, nivel_estudio_post, anio_matricula_post,
                   LAG(nivel_estudio_post) OVER (PARTITION BY mrun ORDER BY anio_matricula_post ASC) as nivel_ant
            FROM EventosPost
        ) e WHERE nivel_ant IS NULL OR nivel_ant <> nivel_estudio_post
        GROUP BY mrun
    )
    SELECT 
        ISNULL(c.ruta, 'Solo Pregrado (No Continuó)') as ruta_secuencial,
        COUNT(DISTINCT u.mrun) as cantidad
    FROM UniversoMaestro u
    LEFT JOIN Cadenas c ON u.mrun = c.mrun
    WHERE u.cohorte BETWEEN :anio_min AND :anio_max
      {filtro_sql}
    GROUP BY ISNULL(c.ruta, 'Solo Pregrado (No Continuó)')
    ORDER BY cantidad DESC
    """
    df = pd.read_sql(text(sql_query), db_engine, params=params)
    if not df.empty:
        df['porcentaje'] = (df['cantidad'] / df['cantidad'].sum()) * 100
    return df

# print(get_rutas_academicas(rango_anios=[2007,2007], tipo_poblacion="Titulados"))

def get_continuidad_estudios(rango_anios, jornada="Todas", genero="Todos", rango_edad="Todos"):
    params = {"anio_min": rango_anios[0], "anio_max": rango_anios[1]}
    
    # Filtros dinámicos
    filtros = []
    if jornada != "Todas":
        filtros.append("AND t.jornada = :jornada"); params["jornada"] = jornada
    if genero != "Todos":
        filtros.append("AND t.genero = :genero"); params["genero"] = genero
    if rango_edad != "Todos":
        filtros.append("AND t.rango_edad = :rango_edad"); params["rango_edad"] = rango_edad
    
    filtro_sql = " ".join(filtros)

    sql_query = f"""
    SELECT 
        CASE 
            WHEN post.mrun IS NOT NULL THEN 'Continuó Estudios' 
            ELSE 'No Continuó' 
        END as condicion,
        COUNT(DISTINCT t.mrun) as cantidad
    FROM tabla_dashboard_titulados t
    LEFT JOIN (
        SELECT DISTINCT mrun FROM tabla_trayectoria_post_titulado
    ) post ON t.mrun = post.mrun
    WHERE t.cod_inst = 104 -- Solo ECAS
      AND t.cohorte BETWEEN :anio_min AND :anio_max
      {filtro_sql}
    GROUP BY CASE WHEN post.mrun IS NOT NULL THEN 'Continuó Estudios' ELSE 'No Continuó' END
    """
    df = pd.read_sql(text(sql_query), db_engine, params=params)
    
    # Calcular porcentajes para el pictograma
    total = df['cantidad'].sum()
    if total > 0:
        df['porcentaje'] = (df['cantidad'] / total) * 100
    else:
        df['porcentaje'] = 0
        
    return df

def get_trayectorias_titulados_completa(rango_anios, jornada="Todas", genero="Todos", rango_edad="Todos"):
    params = {
        "anio_min": rango_anios[0],
        "anio_max": rango_anios[1],
        "cod_inst_ecas": 104
    }
    
    filtros = []
    if jornada != "Todas":
        filtros.append("AND t.jornada = :jornada"); params["jornada"] = jornada
    if genero != "Todos":
        filtros.append("AND t.genero = :genero"); params["genero"] = genero
    if rango_edad != "Todos":
        filtros.append("AND t.rango_edad = :rango_edad"); params["rango_edad"] = rango_edad
    
    filtro_sql = " ".join(filtros)

    sql_query = f"""
    WITH UniversoTitulados AS (
        SELECT mrun, anio_titulacion 
        FROM tabla_dashboard_titulados t
        WHERE t.cod_inst = :cod_inst_ecas
          AND t.cohorte BETWEEN :anio_min AND :anio_max
          {filtro_sql}
    ),
    TrayectoriasFiltradas AS (
        -- Primero traemos todos los eventos relevantes
        SELECT 
            tp.mrun,
            tp.anio_matricula_post,
            tp.nivel_estudio_post,
            TRIM(tp.carrera_destino) as carrera_actual,
            tp.inst_destino as inst_actual,
            LAG(TRIM(tp.carrera_destino)) OVER (PARTITION BY tp.mrun ORDER BY tp.anio_matricula_post ASC) as carrera_anterior,
            LAG(tp.inst_destino) OVER (PARTITION BY tp.mrun ORDER BY tp.anio_matricula_post ASC) as inst_anterior
        FROM tabla_trayectoria_post_titulado tp
        WHERE EXISTS (SELECT 1 FROM UniversoTitulados u WHERE u.mrun = tp.mrun AND tp.anio_matricula_post >= u.anio_titulacion)
    ),
    CambiosDeCarrera AS (
        -- Filtramos para que Pregrado > Pregrado > Pregrado sea solo Pregrado (si es la misma carrera)
        -- Pero que Pregrado (ECAS) > Pregrado (Otra) sea un cambio.
        SELECT 
            mrun,
            anio_matricula_post,
            nivel_estudio_post
        FROM TrayectoriasFiltradas
        WHERE carrera_anterior IS NULL 
           OR carrera_actual <> carrera_anterior 
           OR inst_actual <> inst_anterior
    ),
    RutasConcatenadas AS (
        SELECT 
            mrun,
            'Pregrado > ' + STRING_AGG(nivel_estudio_post, ' > ') WITHIN GROUP (ORDER BY anio_matricula_post ASC) as trayectoria
        FROM (
            -- Subquery para quitar la primera instancia si es el mismo Pregrado de ECAS
            -- Esto evita que salga "Pregrado > Pregrado" cuando el primer registro post-título es su último año de ECAS
            SELECT *,
                   ROW_NUMBER() OVER(PARTITION BY mrun ORDER BY anio_matricula_post ASC) as rn
            FROM CambiosDeCarrera
        ) final
        -- Si quieres que la ruta SIEMPRE empiece con el Pregrado de ECAS, quitamos el filtro rn > 0
        -- Si el primer registro en la tabla post-título es la misma carrera de ECAS, lo ignoramos para no duplicar el inicio
        GROUP BY mrun
    )
    SELECT 
        ISNULL(r.trayectoria, 'Solo Pregrado (Sin Estudios Posteriores)') as trayectoria,
        COUNT(DISTINCT u.mrun) as cantidad,
        CAST(COUNT(DISTINCT u.mrun) AS FLOAT) * 100 / SUM(COUNT(DISTINCT u.mrun)) OVER() as porcentaje
    FROM UniversoTitulados u
    LEFT JOIN RutasConcatenadas r ON u.mrun = r.mrun
    GROUP BY ISNULL(r.trayectoria, 'Solo Pregrado (Sin Estudios Posteriores)')
    ORDER BY cantidad DESC
    """
    
    try:
        df = pd.read_sql(text(sql_query), db_engine, params=params)
        return df
    except Exception as e:
        print(f"Error en trayectorias titulados: {e}")
        return pd.DataFrame()

#print(get_trayectorias_titulados_completa(rango_anios=[2007,2025]))

def get_trayectorias_desertores_completa(rango_anios, jornada="Todas", genero="Todos", rango_edad="Todos"):
    params = {
        "anio_min": rango_anios[0],
        "anio_max": rango_anios[1]
    }
    
    # Filtros dinámicos (se aplican a ambas tablas para que el total sea coherente)
    filtros_fuga = []
    filtros_abandono = []
    
    if jornada != "Todas":
        filtros_fuga.append("AND jornada_ecas = :jornada")
        filtros_abandono.append("AND jornada_ecas = :jornada")
        params["jornada"] = jornada
    if genero != "Todos":
        filtros_fuga.append("AND genero = :genero")
        filtros_abandono.append("AND genero = :genero")
        params["genero"] = genero
    if rango_edad != "Todos":
        filtros_fuga.append("AND rango_edad = :rango_edad")
        filtros_abandono.append("AND rango_edad = :rango_edad")
        params["rango_edad"] = rango_edad
    
    sql_query = f"""
    WITH DatosCombinados AS (
        -- PARTE 1: Rutas de los que se movieron (Fuga)
        SELECT 
            mrun,
            'Pregrado > ' + STRING_AGG(nivel_estudio_post, ' > ') 
            WITHIN GROUP (ORDER BY anio_matricula_post ASC) as trayectoria
        FROM (
            SELECT mrun, nivel_estudio_post, anio_matricula_post,
                   LAG(nivel_estudio_post) OVER (PARTITION BY mrun ORDER BY anio_matricula_post ASC) as nivel_ant
            FROM tabla_fuga_detallada_ecas
            WHERE anio_ingreso_ecas BETWEEN :anio_min AND :anio_max
            {" ".join(filtros_fuga)}
        ) s 
        WHERE nivel_ant IS NULL OR nivel_ant <> nivel_estudio_post
        GROUP BY mrun

        UNION ALL

        -- PARTE 2: Los que abandonaron totalmente
        SELECT 
            mrun,
            'Abandono Total del Sistema' as trayectoria
        FROM tabla_abandono_total_desertores
        WHERE anio_ingreso_ecas BETWEEN :anio_min AND :anio_max
        {" ".join(filtros_abandono)}
    )
    SELECT 
        trayectoria,
        COUNT(DISTINCT mrun) as cantidad,
        CAST(COUNT(DISTINCT mrun) AS FLOAT) * 100 / SUM(COUNT(DISTINCT mrun)) OVER() as porcentaje
    FROM DatosCombinados
    GROUP BY trayectoria
    ORDER BY cantidad DESC
    """
    
    return pd.read_sql(text(sql_query), db_engine, params=params)

#print(get_trayectorias_desertores_completa(rango_anios=[2007,2025]))
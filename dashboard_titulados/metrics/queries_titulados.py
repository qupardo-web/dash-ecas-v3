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
    sql_desertores = f"SELECT COUNT(DISTINCT mrun) FROM tabla_fuga_detallada_desertores WHERE anio_ingreso_ecas BETWEEN :anio_min AND :anio_max AND inst_destino NOT LIKE 'IP ESCUELA DE CONTADORES AUDITORES DE SANTIAGO' {filtro_j_des} {filtro_g} {filtro_e}"

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
    order_by = "anio_matricula_post ASC" if criterio == "Primero" else \
               "CASE WHEN nivel_estudio_post LIKE '%Postgrado%' THEN 1 WHEN nivel_estudio_post LIKE '%Magister%' THEN 1 WHEN nivel_estudio_post LIKE '%Postítulo%' THEN 2 WHEN nivel_estudio_post LIKE '%Pregrado%' THEN 3 ELSE 4 END ASC, anio_matricula_post DESC"

    if tipo_poblacion == "Todos":
        subquery = "SELECT mrun, nivel_estudio_post, anio_matricula_post, anio_ingreso_ecas, genero, jornada_ecas, inst_destino, rango_edad FROM tabla_trayectoria_post_titulado UNION ALL SELECT mrun, nivel_estudio_post, anio_matricula_post, anio_ingreso_ecas, genero, jornada_ecas, inst_destino, rango_edad FROM tabla_fuga_detallada_desertores"
    else:
        tabla = "tabla_trayectoria_post_titulado" if tipo_poblacion == "Titulados" else "tabla_fuga_detallada_desertores"
        subquery = f"SELECT * FROM {tabla}"

    sql_query = f"""
    WITH universo AS ({subquery}),
    eventos_filtrados AS (
        SELECT mrun, nivel_estudio_post, ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY {order_by}) as rn
        FROM universo
        WHERE anio_ingreso_ecas BETWEEN :anio_min AND :anio_max
          AND inst_destino NOT LIKE 'IP ESCUELA DE CONTADORES AUDITORES DE SANTIAGO'
          {filtro_sql}
    )
    SELECT nivel_estudio_post as nivel_global, COUNT(DISTINCT mrun) as cantidad_alumnos
    FROM eventos_filtrados WHERE rn = 1
    GROUP BY nivel_estudio_post ORDER BY cantidad_alumnos DESC
    """
    return pd.read_sql(text(sql_query), db_engine, params=params)

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
        FROM tabla_fuga_detallada_desertores"""
    else:
        tabla = "tabla_trayectoria_post_titulado" if tipo_poblacion == "Titulados" else "tabla_fuga_detallada_desertores"
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
            FROM tabla_fuga_detallada_desertores
        """
    else:
        tabla = "tabla_trayectoria_post_titulado" if tipo_poblacion == "Titulados" else "tabla_fuga_detallada_desertores"
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
        tabla_maestra = "tabla_fuga_detallada_desertores"
        tabla_eventos = "tabla_fuga_detallada_desertores" # O la tabla de trayectoria de desertores
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
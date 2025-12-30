from conn_db import get_db_engine
from sqlalchemy import text
import pandas as pd
from typing import Optional, List

db_engine = get_db_engine()

def get_kpis_cabecera(rango_anios, jornada="Todas", genero="Todos"):
    params = {
        "anio_min": rango_anios[0],
        "anio_max": rango_anios[1]
    }
    
    # Filtros comunes
    filtro_jornada = "AND jornada_titulacion = :jornada" if jornada != "Todas" else ""
    if jornada != "Todas": params["jornada"] = jornada
    
    filtro_genero = "AND genero = :genero" if genero != "Todos" else ""
    if genero != "Todos": params["genero"] = genero
 
    # 1. Total Titulados
    sql_titulados = f"SELECT COUNT(DISTINCT mrun) FROM tabla_dashboard_titulados WHERE cohorte BETWEEN :anio_min AND :anio_max {filtro_jornada} {filtro_genero} AND cod_inst=104"
    
    # 2. Total Desertores (Ajustamos el nombre de la columna jornada si es distinto)
    filtro_jornada_des = "AND jornada_titulacion = :jornada" if jornada != "Todas" else ""
    sql_desertores = f"SELECT COUNT(DISTINCT mrun) FROM tabla_fuga_detallada_desertores WHERE anio_ingreso_ecas BETWEEN :anio_min AND :anio_max {filtro_jornada_des} {filtro_genero}"

    with db_engine.connect() as conn:
        total_tit = conn.execute(text(sql_titulados), params).scalar() or 0
        total_des = conn.execute(text(sql_desertores), params).scalar() or 0
        
    return total_tit + total_des, total_tit, total_des

def get_nivel_post_salida(rango_anios, tipo_poblacion="Titulados", criterio="Primero", jornada="Todas", genero="Todos"):
    """
    tipo_poblacion: 'Titulados' o 'Desertores'
    criterio: 'Primero' (cronológico) o 'Maximo' (jerárquico)
    """
    # Definimos la tabla de origen según el tipo
    tabla_origen = "tabla_trayectoria_post_titulado" if tipo_poblacion == "Titulados" else "tabla_fuga_detallada_desertores"
    
    # Definimos el orden de la ventana según el criterio
    if criterio == "Primero":
        order_by = "anio_matricula_post ASC"
    else:
        order_by = """CASE 
                    WHEN nivel_estudio_post LIKE '%Postgrado%' THEN 1
                    WHEN nivel_estudio_post LIKE '%Postítulo%' THEN 2
                    WHEN nivel_estudio_post LIKE '%Pregrado%' THEN 3
                    ELSE 4 END ASC, anio_matricula_post DESC"""

    params = {"anio_min": rango_anios[0], "anio_max": rango_anios[1]}
    
    filtro_jornada = "AND jornada_titulacion = :jornada" if tipo_poblacion == "Titulados" else "AND jornada_titulacion = :jornada"
    if jornada != "Todas": params["jornada"] = jornada
    
    filtro_genero = "AND genero = :genero"
    if genero != "Todos": params["genero"] = genero

    sql_query = f"""
    WITH eventos_filtrados AS (
        SELECT 
            mrun,
            nivel_estudio_post,
            ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY {order_by}) as rn
        FROM {tabla_origen}
        WHERE anio_ingreso_ecas BETWEEN :anio_min AND :anio_max
          AND inst_destino NOT LIKE 'IP ESCUELA DE CONTADORES AUDITORES DE SANTIAGO'
          {filtro_jornada if jornada != "Todas" else ""}
          {filtro_genero if genero != "Todos" else ""}
    )
    SELECT 
        nivel_estudio_post as nivel_global,
        COUNT(DISTINCT mrun) as cantidad_alumnos
    FROM eventos_filtrados
    WHERE rn = 1 
    GROUP BY nivel_estudio_post
    ORDER BY cantidad_alumnos DESC
    """

    df = pd.read_sql(text(sql_query), db_engine, params=params)
    
    return df

#print(get_nivel_post_salida(rango_anios=[2007,2025], tipo_poblacion="Titulados", criterio="Primero"))

def get_top_destinos_unificado(rango_anios, tipo_poblacion="Titulados", dimension="institucion", top_n=10):
    tabla_origen = "tabla_trayectoria_post_titulado" if tipo_poblacion == "Titulados" else "tabla_fuga_detallada_desertores"
    
    columna_map = {
        "institucion": "inst_destino",
        "carrera": "carrera_destino"
    }
    col_target = columna_map.get(dimension, "inst_destino")
    
    sql_query = f"""
    WITH primer_reingreso AS (
        SELECT 
            mrun,
            {col_target} AS destino,
            ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY anio_matricula_post ASC) as rn
        FROM {tabla_origen}
        WHERE anio_ingreso_ecas BETWEEN :anio_min AND :anio_max
          AND inst_destino NOT LIKE 'IP ESCUELA DE CONTADORES AUDITORES DE SANTIAGO'
    )
    SELECT TOP (:top_n)
        destino,
        COUNT(DISTINCT mrun) as cantidad_alumnos
    FROM primer_reingreso
    WHERE rn = 1
    GROUP BY destino
    ORDER BY cantidad_alumnos DESC
    """

    df = pd.read_sql(text(sql_query), db_engine, params={"anio_min": rango_anios[0], "anio_max": rango_anios[1], "top_n": top_n})

    return df

#print(get_top_destinos_unificado(rango_anios=[2007,2007], tipo_poblacion="Desertores", dimension="institucion"))

def get_demora_reingreso_unificada(rango_anios, tipo_poblacion="Titulados", nivel="Todos"):
    tabla_origen = "tabla_trayectoria_post_titulado" if tipo_poblacion == "Titulados" else "tabla_fuga_detallada_desertores"
    # Nota: Asegúrate que en desertores la columna se llame 'tiempo_espera_post' o 'años_fuga'
    col_espera = "tiempo_espera_post" if tipo_poblacion == "Titulados" else "tiempo_espera_post" 

    sql_query = f"""
    WITH eventos AS (
        SELECT 
            mrun,
            anio_ingreso_ecas as cohorte,
            nivel_estudio_post as nivel_global,
            {col_espera} as demora_anios,
            ROW_NUMBER() OVER (PARTITION BY mrun, nivel_estudio_post ORDER BY anio_matricula_post ASC) as rn
        FROM {tabla_origen}
        WHERE anio_ingreso_ecas BETWEEN :anio_min AND :anio_max
          AND inst_destino NOT LIKE 'IP ESCUELA DE CONTADORES AUDITORES DE SANTIAGO'
          {f"AND nivel_estudio_post = '{nivel}'" if nivel != "Todos" else ""}
    )
    SELECT cohorte, nivel_global, demora_anios, COUNT(DISTINCT mrun) as cantidad_alumnos
    FROM eventos WHERE rn = 1
    GROUP BY cohorte, nivel_global, demora_anios
    ORDER BY demora_anios ASC
    """
    return pd.read_sql(text(sql_query), db_engine, params={"anio_min": rango_anios[0], "anio_max": rango_anios[1]})

#print(get_demora_reingreso_unificada(rango_anios=[2007,2007], tipo_poblacion="Desertores"))

def get_rutas_academicas_unificadas(rango_anios, tipo_poblacion="Titulados", jornada="Todas", genero="Todos"):
    """
    Construye la secuencia de niveles educativos alcanzados tras salir de ECAS.
    Ejemplo: Pregrado -> Postítulo -> Magíster
    """
    tabla_origen = "tabla_trayectoria_post_titulado" if tipo_poblacion == "Titulados" else "tabla_fuga_detallada_desertores"
    
    params = {
        "anio_min": rango_anios[0],
        "anio_max": rango_anios[1]
    }

    # Ajuste de filtros según tabla
    col_jornada = "jornada_titulacion" if tipo_poblacion == "Titulados" else "jornada_titulacion"
    
    filtros = []
    if jornada != "Todas":
        filtros.append(f"AND {col_jornada} = :jornada")
        params["jornada"] = jornada
    if genero != "Todos":
        filtros.append("AND genero = :genero")
        params["genero"] = genero

    filtro_str = " ".join(filtros)

    sql_query = f"""
    WITH eventos_ordenados AS (
        -- 1. Obtenemos todos los eventos externos ordenados por fecha
        SELECT 
            mrun,
            anio_matricula_post,
            nivel_estudio_post,
            LAG(nivel_estudio_post) OVER (PARTITION BY mrun ORDER BY anio_matricula_post ASC) as nivel_anterior
        FROM {tabla_origen}
        WHERE anio_ingreso_ecas BETWEEN :anio_min AND :anio_max
          AND inst_destino NOT LIKE 'IP ESCUELA DE CONTADORES AUDITORES DE SANTIAGO'
          {filtro_str}
    ),
    eventos_sin_duplicados AS (
        -- 2. Filtramos niveles repetidos consecutivos (si hizo 2 años de lo mismo, solo queda 1)
        SELECT 
            mrun,
            nivel_estudio_post,
            anio_matricula_post
        FROM eventos_ordenados
        WHERE nivel_anterior IS NULL OR nivel_anterior <> nivel_estudio_post
    ),
    rutas_concatenadas AS (
        -- 3. Agrupamos por MRUN y concatenamos la ruta empezando por Pregrado
        -- Usamos STRING_AGG (disponible en SQL Server 2017+)
        SELECT 
            mrun,
            'Pregrado > ' + STRING_AGG(nivel_estudio_post, ' > ') WITHIN GROUP (ORDER BY anio_matricula_post ASC) as ruta_secuencial
        FROM eventos_sin_duplicados
        GROUP BY mrun
    ),
    universo_total AS (
        -- 4. Consideramos a los que NO tienen reingresos (su ruta es solo 'Pregrado')
        SELECT mrun, 'Pregrado' as ruta_secuencial
        FROM (SELECT DISTINCT mrun FROM {tabla_origen} WHERE anio_ingreso_ecas BETWEEN :anio_min AND :anio_max {filtro_str}) t
        WHERE mrun NOT IN (SELECT mrun FROM rutas_concatenadas)
        UNION ALL
        SELECT mrun, ruta_secuencial FROM rutas_concatenadas
    )
    SELECT 
        ruta_secuencial,
        COUNT(mrun) as cantidad,
        CAST(COUNT(mrun) AS FLOAT) * 100 / SUM(COUNT(mrun)) OVER() as porcentaje
    FROM universo_total
    GROUP BY ruta_secuencial
    ORDER BY cantidad DESC
    """

    with db_engine.connect() as conn:
        df = pd.read_sql(text(sql_query), conn, params=params)
    return df

#print(get_rutas_academicas_unificadas(rango_anios=[2007,2025], tipo_poblacion="Desertores"))

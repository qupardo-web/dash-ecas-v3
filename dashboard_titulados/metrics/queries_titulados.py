from conn_db import get_db_engine
from sqlalchemy import text
import pandas as pd
from typing import Optional, List

db_engine = get_db_engine()

def get_primer_ingreso_post_titulacion(rango_anios, jornada="Todas", genero="Todos"):
    params = {
        "anio_min": rango_anios[0],
        "anio_max": rango_anios[1]
    }

    filtro_jornada = "AND jornada_titulacion = :jornada" if jornada != "Todas" else ""
    if filtro_jornada: params["jornada"] = jornada
    
    filtro_genero = "AND genero = :genero" if genero != "Todos" else ""
    if filtro_genero: params["genero"] = genero

    sql_query = f"""
    WITH primer_reingreso AS (
        SELECT 
            mrun,
            nivel_estudio_post,
            ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY anio_matricula_post ASC) as rn
        FROM tabla_trayectoria_post_titulado
        WHERE anio_ingreso_ecas BETWEEN :anio_min AND :anio_max
          -- FILTRO CLAVE: Excluir reingresos a la misma ECAS
          AND inst_destino NOT LIKE 'IP ESCUELA DE CONTADORES AUDITORES DE SANTIAGO' 
        {filtro_jornada}
        {filtro_genero}
    )
    SELECT 
        nivel_estudio_post as nivel_global,
        COUNT(DISTINCT mrun) as cantidad_alumnos
    FROM primer_reingreso
    WHERE rn = 1 
    GROUP BY nivel_estudio_post
    ORDER BY cantidad_alumnos DESC
    """

    df = pd.read_sql(text(sql_query), db_engine, params=params)
    return df

def get_maximo_nivel_post_titulacion(rango_anios, jornada="Todas", genero="Todos"):
    params = {
        "anio_min": rango_anios[0],
        "anio_max": rango_anios[1]
    }

    filtro_jornada = "AND jornada_titulacion = :jornada" if jornada != "Todas" else ""
    if filtro_jornada: params["jornada"] = jornada
    
    filtro_genero = "AND genero = :genero" if genero != "Todos" else ""
    if filtro_genero: params["genero"] = genero

    sql_query = f"""
    WITH jerarquia_niveles AS (
        SELECT 
            mrun,
            nivel_estudio_post,
            ROW_NUMBER() OVER (
                PARTITION BY mrun 
                ORDER BY CASE 
                    WHEN nivel_estudio_post LIKE '%Postgrado%' THEN 1
                    WHEN nivel_estudio_post LIKE '%Magister%' THEN 1
                    WHEN nivel_estudio_post LIKE '%Postítulo%' THEN 2
                    WHEN nivel_estudio_post LIKE '%Pregrado%' THEN 3
                    ELSE 4 
                END ASC, 
                anio_matricula_post DESC
            ) as rn
        FROM tabla_trayectoria_post_titulado
        WHERE anio_ingreso_ecas BETWEEN :anio_min AND :anio_max
          -- FILTRO CLAVE: Excluir reingresos a la misma ECAS
          AND inst_destino NOT LIKE 'IP ESCUELA DE CONTADORES AUDITORES DE SANTIAGO'
        {filtro_jornada}
        {filtro_genero}
    )
    SELECT 
        nivel_estudio_post as nivel_global,
        COUNT(DISTINCT mrun) as cantidad_alumnos
    FROM jerarquia_niveles
    WHERE rn = 1 
    GROUP BY nivel_estudio_post
    ORDER BY cantidad_alumnos DESC
    """

    df = pd.read_sql(text(sql_query), db_engine, params=params)
    return df

def get_top_destinos_post_titulacion(rango_anios, dimension="institucion", jornada="Todas", genero="Todos", top_n=10):
    
    columna_map = {
        "institucion": "inst_destino",
        "carrera": "carrera_destino",
        "area": "area_conocimiento" # O area_conocimiento si la tienes en la tabla
    }
    
    col_target = columna_map.get(dimension, "inst_destino")
    
    params = {
        "anio_min": rango_anios[0],
        "anio_max": rango_anios[1],
        "top_n": top_n
    }

    filtro_jornada = "AND jornada_titulacion = :jornada" if jornada != "Todas" else ""
    if filtro_jornada: params["jornada"] = jornada
    
    filtro_genero = "AND genero = :genero" if genero != "Todos" else ""
    if filtro_genero: params["genero"] = genero

    sql_query = f"""
    WITH primer_reingreso_externo AS (
        SELECT 
            mrun,
            {col_target} AS destino,
            ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY anio_matricula_post ASC) as rn
        FROM tabla_trayectoria_post_titulado
        WHERE anio_ingreso_ecas BETWEEN :anio_min AND :anio_max
          AND inst_destino NOT LIKE 'IP ESCUELA DE CONTADORES AUDITORES DE SANTIAGO'
        {filtro_jornada}
        {filtro_genero}
    )
    SELECT TOP (:top_n)
        destino,
        COUNT(DISTINCT mrun) as cantidad_alumnos
    FROM primer_reingreso_externo
    WHERE rn = 1
    GROUP BY destino
    ORDER BY cantidad_alumnos DESC
    """

    df = pd.read_sql(text(sql_query), db_engine, params=params)

    return df

#print(get_top_destinos_post_titulacion(rango_anios=[2007,2007], dimension="institucion"))

def get_distribucion_demora_reingreso(rango_anios, jornada="Todas", genero="Todos", nivel="Todos"):
    """
    KPI 4.b: Obtiene cuántos años tardan los titulados en reingresar a 
    una institución externa, segmentado por nivel de estudio.
    """
    params = {
        "anio_min": rango_anios[0],
        "anio_max": rango_anios[1]
    }

    # Filtros dinámicos
    filtros = []
    if jornada != "Todas":
        filtros.append("AND jornada_titulacion = :jornada")
        params["jornada"] = jornada
    if genero != "Todos":
        filtros.append("AND genero = :genero")
        params["genero"] = genero
    if nivel != "Todos":
        filtros.append("AND nivel_estudio_post = :nivel")
        params["nivel"] = nivel

    filtro_str = " ".join(filtros)

    sql_query = f"""
    WITH primer_evento_externo AS (
        -- Buscamos el primer ingreso a CADA nivel para cada alumno fuera de ECAS
        SELECT 
            mrun,
            anio_ingreso_ecas as cohorte,
            nivel_estudio_post as nivel_global,
            tiempo_espera_post as demora_anios,
            ROW_NUMBER() OVER (
                PARTITION BY mrun, nivel_estudio_post 
                ORDER BY anio_matricula_post ASC
            ) as rn
        FROM tabla_trayectoria_post_titulado
        WHERE anio_ingreso_ecas BETWEEN :anio_min AND :anio_max
          AND inst_destino NOT LIKE 'IP ESCUELA DE CONTADORES AUDITORES DE SANTIAGO'
          {filtro_str}
    )
    SELECT 
        cohorte,
        nivel_global,
        demora_anios,
        COUNT(DISTINCT mrun) as cantidad_alumnos
    FROM primer_evento_externo
    WHERE rn = 1 -- Mantenemos la lógica de tu código: primera vez en ese nivel
    GROUP BY cohorte, nivel_global, demora_anios
    ORDER BY cohorte, nivel_global, demora_anios
    """

    with db_engine.connect() as conn:
        df = pd.read_sql(text(sql_query), conn, params=params)
    return df

#print(get_distribucion_demora_reingreso(rango_anios=[2007,2025]))




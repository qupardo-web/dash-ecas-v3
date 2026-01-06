from conn_db import get_db_engine
from sqlalchemy import text
import pandas as pd
from typing import Optional, List

db_engine = get_db_engine()

#Nota: Esta query ocupa un inner join que elimina a aquellos matriculados en ECAS que
#NO tienen un registro de egreso en la educación media.
def get_distribucion_dependencia_cohorte(cohorte_sel, cod_inst, jornada="Todas"):
    params = {"cohorte": cohorte_sel,
              "cod_inst": cod_inst}

    filtro_jornada = "AND jornada = :jornada" if jornada and jornada != "Todas" else ""
    if filtro_jornada: params["jornada"] = jornada
    
    sql_query = f"""
    WITH CohorteEstudiantes AS (
        -- Identificamos el año de ingreso (cohorte) de cada alumno en ECAS
        SELECT 
            mrun, 
            MIN(cohorte) as anio_ingreso
        FROM tabla_matriculas_competencia_unificada
        WHERE cod_inst = :cod_inst
        {filtro_jornada}
        GROUP BY mrun
    )
    SELECT 
        CASE 
            WHEN e.cod_dep_agrupado = 1 THEN 'Municipal'
            WHEN e.cod_dep_agrupado = 2 THEN 'Part. Subvencionado'
            WHEN e.cod_dep_agrupado = 3 THEN 'Part. Pagado'
            WHEN e.cod_dep_agrupado = 4 THEN 'Admin. Delegada'
            WHEN e.cod_dep_agrupado = 5 THEN 'SLEP'
            ELSE 'Otro'
        END AS tipo_establecimiento,
        COUNT(DISTINCT e.mrun) AS cantidad
    FROM tabla_alumnos_egresados_unificada e
    LEFT JOIN CohorteEstudiantes c ON e.mrun = c.mrun
    WHERE c.anio_ingreso = :cohorte
    GROUP BY e.cod_dep_agrupado
    ORDER BY cantidad DESC
    """
    
    df = pd.read_sql(text(sql_query), db_engine, params=params)

    return df

print(get_distribucion_dependencia_cohorte(cohorte_sel=2008, cod_inst=104, jornada='Diurna'))

def get_titulados_por_dependencia_cohorte(cohorte_sel, anio_titulacion_sel=None):
    # Definimos los parámetros base
    params = {"cohorte": cohorte_sel}
    
    # Construimos el filtro dinámico para el año de titulación
    filtro_anio_tit = ""
    if anio_titulacion_sel:
        filtro_anio_tit = "AND anio_titulacion = :anio_tit"
        params["anio_tit"] = anio_titulacion_sel
    
    sql_query = f"""
    WITH CohorteEstudiantes AS (
        -- Identificamos el año de ingreso (cohorte) real de cada alumno en ECAS
        SELECT 
            mrun, 
            MIN(cohorte) as anio_ingreso
        FROM tabla_matriculas_competencia_unificada
        WHERE cod_inst = 104
        GROUP BY mrun
    ),
    AlumnosTitulados AS (
        SELECT DISTINCT mrun
        FROM tabla_dashboard_titulados
        WHERE cod_inst = 104 
          {filtro_anio_tit}
    )
    SELECT 
        CASE 
            WHEN e.cod_dep_agrupado = 1 THEN 'Municipal'
            WHEN e.cod_dep_agrupado = 2 THEN 'Part. Subvencionado'
            WHEN e.cod_dep_agrupado = 3 THEN 'Part. Pagado'
            WHEN e.cod_dep_agrupado = 4 THEN 'Admin. Delegada'
            WHEN e.cod_dep_agrupado = 5 THEN 'SLEP'
            ELSE 'Otro / Sin Información'
        END AS tipo_establecimiento,
        COUNT(DISTINCT e.mrun) AS cantidad_titulados,
        ROUND(CAST(COUNT(DISTINCT e.mrun) AS FLOAT) * 100 / 
            NULLIF(SUM(COUNT(DISTINCT e.mrun)) OVER(), 0), 1) as porcentaje
    FROM tabla_alumnos_egresados_unificada e
    INNER JOIN AlumnosTitulados t ON e.mrun = t.mrun
    INNER JOIN CohorteEstudiantes c ON e.mrun = c.mrun
    WHERE c.anio_ingreso = :cohorte
    GROUP BY e.cod_dep_agrupado
    ORDER BY cantidad_titulados DESC
    """
    
    df = pd.read_sql(text(sql_query), db_engine, params=params)
    return df

print(get_titulados_por_dependencia_cohorte(cohorte_sel=2009))
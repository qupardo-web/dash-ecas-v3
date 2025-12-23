from conn_db import get_db_engine
from sqlalchemy import text
import pandas as pd

db_engine = get_db_engine()

def get_mruns_per_institucion(
    cohorte_n: int | None = None,
    nomb_carrera: str | None = None,
    nomb_inst: str | None = None,
    jornada: str | None = None,
    top_n: int | None = None
):  

    #Clausula de top (limitación de busquedas)
    sql_select = "SELECT TOP (:top_n) " if top_n else "SELECT "

    sql_base = f"""
    {sql_select} 
        nomb_carrera,
        nomb_inst,
        COUNT(DISTINCT mrun) AS total_mruns
    FROM vista_matricula_unificada
    WHERE nivel_global = 'Pregrado'
    AND tipo_inst_1 IN ('Institutos Profesionales', 'Centros de Formación Técnica')
    """
    
    params = {"top_n": top_n} if top_n else {}
    

    if nomb_inst:
        sql_base += " AND nomb_inst LIKE :inst"
        params["inst"] = nomb_inst

    if nomb_carrera:
        sql_base += " AND nomb_carrera LIKE :nomb_carrera"
        params["nomb_carrera"] = nomb_carrera
        
    if cohorte_n: 
        sql_base += " AND anio_ing_carr_ori = :anio"
        params["anio"] = cohorte_n
    
    if jornada:
        sql_base += " AND jornada = :jornada"
        params["jornada"] = jornada

    sql_base += " GROUP BY nomb_inst, nomb_carrera ORDER BY total_mruns DESC"

    df_mruns = pd.read_sql_query(text(sql_base), db_engine, params=params)
        
    return df_mruns

#print(get_mruns_per_institucion(cohorte_n="2008", nomb_carrera= "%AUDITOR%", top_n=5))

def get_ingresos_competencia_parametrizado(
    top_n: int = 10, 
    anio_min: int = 2007,
    anio_max: int = 2025
):
    """
    Versión optimizada que acepta parámetros dinámicos para el Dashboard.
    """

    sql_query = text("""
    WITH base AS (
        SELECT
            v.anio_ing_carr_ori AS cohorte,
            v.cod_inst,
            v.nomb_inst,
            COUNT(DISTINCT v.mrun) AS total_ingresos
        FROM vista_matricula_unificada v
        WHERE v.mrun IS NOT NULL
          AND v.anio_ing_carr_ori BETWEEN :anio_min AND :anio_max
          AND (v.nomb_carrera LIKE 'AUDITOR%' OR v.nomb_carrera LIKE 'CONTA%')
          AND v.region_sede = 'Metropolitana'
          AND (
                v.cod_inst = 104
                OR v.tipo_inst_1 IN ('Institutos Profesionales', 'Centros de Formación Técnica')
          )
        GROUP BY
            v.anio_ing_carr_ori,
            v.cod_inst,
            v.nomb_inst
    ),

    ranking AS (
        SELECT
            cod_inst,
            nomb_inst,
            AVG(total_ingresos) AS promedio_ingresos
        FROM base
        GROUP BY cod_inst, nomb_inst
    ),

    top_seleccionado AS (
        SELECT TOP (:top_n)
            cod_inst
        FROM ranking
        ORDER BY promedio_ingresos DESC
    )

    SELECT
        b.cohorte,
        b.cod_inst,
        b.nomb_inst,
        b.total_ingresos
    FROM base b
    JOIN top_seleccionado t
        ON b.cod_inst = t.cod_inst
    ORDER BY
        b.cohorte,
        b.total_ingresos DESC;
    """)

    params = {
        "top_n": top_n,
        "anio_min": anio_min,
        "anio_max": anio_max
    }

    df = pd.read_sql(sql_query, db_engine, params=params)
    
    return df

print(get_ingresos_competencia_parametrizado(top_n=5, anio_min=2007, anio_max=2025))

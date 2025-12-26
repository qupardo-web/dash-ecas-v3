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

def get_nombres_top_competencia(top_n=10):
    """
    Trae los nombres únicos de las instituciones que están en el Top N 
    sumando ambas jornadas (Diurna y Vespertina).
    """
    sql_query = text("""
    WITH base AS (
        SELECT 
            cod_inst, nomb_inst, anio_ing_carr_ori,
            COUNT(DISTINCT mrun) AS ingresos
        FROM vista_matricula_unificada
        WHERE region_sede = 'Metropolitana'
          AND (nomb_carrera LIKE 'AUDITOR%' OR nomb_carrera LIKE 'CONTA%')
          AND (cod_inst = 104 OR tipo_inst_1 IN ('Institutos Profesionales', 'Centros de Formación Técnica'))
        GROUP BY cod_inst, nomb_inst, anio_ing_carr_ori
    ),
    ranking AS (
        SELECT nomb_inst, AVG(CAST(ingresos AS FLOAT)) as prom
        FROM base
        GROUP BY nomb_inst
    )
    SELECT TOP (:top_n) nomb_inst FROM ranking ORDER BY prom DESC
    """)
    
    df = pd.read_sql(sql_query, db_engine, params={"top_n": top_n})
    
    return df['nomb_inst'].unique().tolist()

def get_ingresos_competencia_parametrizado(top_n=10, anio_min=2007, anio_max=2025, jornada=None):
    # 1. Definimos los parámetros base que SIEMPRE están presentes
    params = {
        "top_n": top_n,
        "anio_min": anio_min,
        "anio_max": anio_max
    }

    # 2. Construcción del string SQL
    # Iniciamos con la parte fija de la consulta
    sql_str = """
    WITH data_filtrada AS (
        SELECT anio_ing_carr_ori AS cohorte, cod_inst, nomb_inst, mrun
        FROM vista_matricula_unificada
        WHERE anio_ing_carr_ori BETWEEN :anio_min AND :anio_max
          AND region_sede = 'Metropolitana'
          AND (nomb_carrera LIKE 'AUDITOR%' OR nomb_carrera LIKE 'CONTA%')
          AND (cod_inst = 104 OR tipo_inst_1 IN ('Institutos Profesionales', 'Centros de Formación Técnica'))
          AND mrun IS NOT NULL
    """
    
    # 3. Lógica Dinámica: Solo agregamos el marcador si hay jornada
    if jornada and jornada != "Todas":
        sql_str += " AND jornada = :jornada "
        params["jornada"] = jornada  # Agregamos al diccionario solo si existe en el SQL

    # 4. Cerramos el resto de la consulta
    sql_str += """
    ),
    base AS (
        SELECT cohorte, cod_inst, nomb_inst, COUNT(DISTINCT mrun) AS total_ingresos
        FROM data_filtrada
        GROUP BY cohorte, cod_inst, nomb_inst
    ),
    ranking AS (
        SELECT TOP (:top_n) cod_inst, AVG(CAST(total_ingresos AS FLOAT)) AS prom
        FROM base GROUP BY cod_inst ORDER BY prom DESC
    )
    SELECT b.cohorte, b.cod_inst, b.nomb_inst, b.total_ingresos 
    FROM base b 
    INNER JOIN ranking r ON b.cod_inst = r.cod_inst
    ORDER BY b.cohorte, b.total_ingresos DESC;
    """

    # 5. IMPORTANTE: Convertir el string final a objeto text de SQLAlchemy

    # 6. Ejecución
    with db_engine.connect() as conn:
        df = pd.read_sql(text(sql_str), conn, params=params)
    
    return df
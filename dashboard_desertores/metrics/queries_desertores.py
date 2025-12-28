from conn_db import get_db_engine
from sqlalchemy import text
import pandas as pd
from typing import Optional, List

db_engine = get_db_engine()

def get_ingresos_competencia_parametrizado(top_n=10, anio_min=2007, anio_max=2025, jornada=None):
    params = {"top_n": top_n, "anio_min": anio_min, "anio_max": anio_max}
    
    filtro_jornada = "AND jornada = :jornada" if jornada and jornada != "Todas" else ""
    if filtro_jornada: params["jornada"] = jornada

    # Usamos la tabla física directamente (mucho más rápido que la vista)
    sql_str = f"""
    WITH base AS (
        SELECT cohorte, cod_inst, nomb_inst, COUNT(DISTINCT mrun) AS total_ingresos
        FROM tabla_dashboard_permanencia
        WHERE cohorte BETWEEN :anio_min AND :anio_max
        {filtro_jornada}
        GROUP BY cohorte, cod_inst, nomb_inst
    ),
    ranking AS (
        SELECT TOP (:top_n) cod_inst
        FROM base
        WHERE cod_inst <> 104 -- Excluimos ECAS del ranking
        GROUP BY cod_inst
        ORDER BY AVG(CAST(total_ingresos AS FLOAT)) DESC
    )
    SELECT b.cohorte, b.cod_inst, b.nomb_inst, b.total_ingresos 
    FROM base b 
    INNER JOIN ranking r ON b.cod_inst = r.cod_inst
    OR b.cod_inst = 104 -- Siempre incluimos ECAS
    ORDER BY b.cohorte, b.total_ingresos DESC;
    """

    with db_engine.connect() as conn:
        return pd.read_sql(text(sql_str), conn, params=params)

#print(get_ingresos_competencia_parametrizado(top_n=10, anio_min=2007, anio_max=2025))

def get_permanencia_n_n1_competencia(anio_min: int, anio_max: int, jornada: Optional[str] = None) -> pd.DataFrame:
    anio_max_ajustado = min(anio_max, 2024)
    
    params = {
        "anio_min": anio_min,
        "anio_max": anio_max_ajustado,
        "anio_max_ext": anio_max_ajustado + 1
    }

    # El filtro de jornada SOLO debe aplicar al universo inicial (Cohorte)
    filtro_jornada_cohorte = "AND jornada = :jornada" if jornada and jornada != "Todas" else ""
    if filtro_jornada_cohorte: params["jornada"] = jornada

    sql = f"""
    WITH universo_cohortes AS (
        -- Definimos quiénes entraron en la cohorte X con la jornada seleccionada
        SELECT DISTINCT mrun, cod_inst, nomb_inst, cohorte
        FROM tabla_dashboard_permanencia
        WHERE cohorte BETWEEN :anio_min AND :anio_max
        {filtro_jornada_cohorte}
    ),
    retencion_n1 AS (
        -- Buscamos si el alumno está matriculado el año siguiente en la institución
        -- NOTA: AQUÍ NO FILTRAMOS POR JORNADA para capturar cambios de jornada
        SELECT DISTINCT mrun, cod_inst, periodo
        FROM tabla_dashboard_permanencia
        WHERE periodo BETWEEN :anio_min + 1 AND :anio_max_ext
    )
    SELECT 
        u.nomb_inst, u.cohorte, 
        COUNT(DISTINCT u.mrun) AS base_n,
        COUNT(DISTINCT r.mrun) AS retenidos_n1
    FROM universo_cohortes u
    LEFT JOIN retencion_n1 r 
        ON u.mrun = r.mrun 
        AND u.cod_inst = r.cod_inst 
        AND r.periodo = u.cohorte + 1
    GROUP BY u.nomb_inst, u.cohorte;
    """
    
    with db_engine.connect() as conn:
        df = pd.read_sql(text(sql), conn, params=params)
    
    df['tasa_permanencia_pct'] = (df['retenidos_n1'] * 100.0 / df['base_n'].replace(0, pd.NA)).fillna(0).round(2)
    
    return df

#Cambios de jornada evaluados por cohorte
def get_distribucion_cambio_jornada_ecas(anio_min, anio_max, jornada_filtro=None):
    params = {
        "anio_min": anio_min, 
        "anio_max": min(anio_max, 2024),
    }
    
    # Filtro opcional por si el usuario seleccionó una jornada específica en el dashboard
    filtro_sql = ""
    if jornada_filtro and jornada_filtro != "Todas":
        filtro_sql = "AND t1.jornada = :jornada_filtro"
        params["jornada_filtro"] = jornada_filtro

    sql = f"""
    WITH cohorte_inicial AS (
        -- Estudiantes ECAS en su año de ingreso
        SELECT mrun, jornada AS jornada_origen, cohorte
        FROM tabla_dashboard_permanencia
        WHERE cod_inst = 104
          AND cohorte BETWEEN :anio_min AND :anio_max
          AND cohorte = periodo -- Aseguramos que es su registro de ingreso
    ),
    seguimiento_n1 AS (
        -- Buscamos su jornada en el año siguiente
        SELECT mrun, jornada AS jornada_destino, periodo
        FROM tabla_dashboard_permanencia
        WHERE cod_inst = 104
          AND periodo BETWEEN :anio_min + 1 AND :anio_max + 1
    )
    SELECT 
        t1.jornada_origen,
        t1.cohorte,
        CASE 
            WHEN t2.jornada_destino IS NULL THEN 'Deserción'
            WHEN t1.jornada_origen = t2.jornada_destino THEN 'Mantiene Jornada'
            ELSE 'Cambio de Jornada'
        END AS estado_retencion,
        COUNT(DISTINCT t1.mrun) AS cantidad_alumnos
    FROM cohorte_inicial t1
    LEFT JOIN seguimiento_n1 t2 
        ON t1.mrun = t2.mrun 
        AND t2.periodo = t1.cohorte + 1
    WHERE 1=1 {filtro_sql}
    GROUP BY t1.jornada_origen, t1.cohorte, 
             CASE 
                WHEN t2.jornada_destino IS NULL THEN 'Deserción'
                WHEN t1.jornada_origen = t2.jornada_destino THEN 'Mantiene Jornada'
                ELSE 'Cambio de Jornada'
             END
    """
    df = pd.read_sql(text(sql), db_engine, params=params)
    
    return df
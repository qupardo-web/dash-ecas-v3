from conn_db import get_db_engine
from sqlalchemy import text
import pandas as pd
from typing import Optional, List

db_engine = get_db_engine()

def get_movilidad_acreditacion_estricta(anio_seleccionado, jornada="Todas", tipo_inst="Todas"):
    params = {"anio_seleccionado": anio_seleccionado}
    
    f_jornada = "AND f.jornada_ecas = :jornada" if jornada != "Todas" else ""
    if jornada != "Todas": params["jornada"] = jornada
    
    f_tipo = "AND f.tipo_inst_1 = :tipo_inst" if tipo_inst != "Todas" else ""
    if tipo_inst != "Todas": params["tipo_inst"] = tipo_inst

    sql_query = f"""
    WITH Acred_ECAS AS (
        SELECT DISTINCT periodo, acre_inst_anio AS acred_ecas_periodo
        FROM tabla_dashboard_permanencia WHERE cod_inst = 104
    ),
    PrimerIngresoPost AS (
        SELECT 
            mrun, anio_matricula_post, inst_destino,
            acreditada_inst, acre_inst_anio,
            jornada_ecas, tipo_inst_1, anio_ultima_matricula_ecas,
            ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY anio_matricula_post ASC) as rn_ingreso
        FROM [DBMatriculas].[dbo].[tabla_fuga_detallada_desertores]
    )
    SELECT 
        CASE 
            -- 1. CASO ESPECIAL: ECAS no acreditada (99) y destino SÍ acreditado (aunque traiga 99 en años)
            WHEN e.acred_ecas_periodo >= 99 
                 AND (f.acreditada_inst IN ('SÍ', 'ACREDITADA') OR (f.acre_inst_anio > 0 AND f.acre_inst_anio < 99))
                 THEN 'Más Acreditada'

            -- 2. Regla general para No Acreditadas (si no cumplió lo anterior)
            WHEN f.acreditada_inst IN ('NO', 'SIN ACREDITACIÓN') 
                 OR ISNULL(f.acre_inst_anio, 0) = 0 
                 OR f.acre_inst_anio >= 99 
                 THEN 'No Acreditada'

            -- 3. Comparaciones estándar cuando ambos tienen años válidos
            WHEN f.acre_inst_anio > e.acred_ecas_periodo THEN 'Más Acreditada'
            WHEN f.acre_inst_anio = e.acred_ecas_periodo THEN 'Igual Acreditación'
            ELSE 'Menos Acreditada'
        END AS categoria_movilidad,
        COUNT(DISTINCT f.mrun) AS cantidad_alumnos
    FROM PrimerIngresoPost f
    INNER JOIN Acred_ECAS e ON f.anio_ultima_matricula_ecas = e.periodo
    WHERE f.rn_ingreso = 1 
      AND f.anio_ultima_matricula_ecas = :anio_seleccionado
      AND f.anio_matricula_post = (:anio_seleccionado + 1)
    {f_jornada} {f_tipo}
    GROUP BY 
        CASE 
            WHEN e.acred_ecas_periodo >= 99 
                 AND (f.acreditada_inst IN ('SÍ', 'ACREDITADA') OR (f.acre_inst_anio > 0 AND f.acre_inst_anio < 99))
                 THEN 'Más Acreditada'
            WHEN f.acreditada_inst IN ('NO', 'SIN ACREDITACIÓN') 
                 OR ISNULL(f.acre_inst_anio, 0) = 0 
                 OR f.acre_inst_anio >= 99 
                 THEN 'No Acreditada'
            WHEN f.acre_inst_anio > e.acred_ecas_periodo THEN 'Más Acreditada'
            WHEN f.acre_inst_anio = e.acred_ecas_periodo THEN 'Igual Acreditación'
            ELSE 'Menos Acreditada'
        END
    """
    df = pd.read_sql(text(sql_query), db_engine, params=params)
    return df

#print(get_movilidad_acreditacion_estricta(anio_seleccionado=2007))

def get_metrics_acreditacion(periodo_seleccionado, jornada_filtro="Todas"):
    periodo_actual = int(periodo_seleccionado)
    periodo_siguiente = periodo_actual + 1
    periodo_anterior = periodo_actual - 1
    
    params = {
        "periodo_actual": periodo_actual,
        "periodo_anterior": periodo_anterior,
        "periodo_siguiente": periodo_siguiente
    }

    f_jornada = "AND UltimaJornada.jornada = :jornada" if jornada_filtro != "Todas" else ""
    if jornada_filtro != "Todas":
        params["jornada"] = jornada_filtro

    sql_query = f"""
    WITH Titulados_ECAS AS (
        SELECT DISTINCT mrun FROM tabla_dashboard_titulados WHERE cod_inst = 104
    ),
    UltimaJornada AS (
        SELECT mrun, jornada, periodo
        FROM tabla_dashboard_permanencia
        WHERE cod_inst = 104 AND periodo = :periodo_actual
    ),
    Retencion AS (
        SELECT 
            COUNT(DISTINCT uj.mrun) as total_base,
            COUNT(DISTINCT t2.mrun) as total_permanecen
        FROM UltimaJornada uj
        LEFT JOIN Titulados_ECAS tit ON uj.mrun = tit.mrun
        LEFT JOIN tabla_dashboard_permanencia t2 
            ON uj.mrun = t2.mrun 
            AND t2.periodo = :periodo_siguiente
            AND t2.cod_inst = 104
        WHERE tit.mrun IS NULL 
          {f_jornada.replace('UltimaJornada', 'uj')}
    ),
    Desertores AS (
        SELECT COUNT(DISTINCT f.mrun) as total_desertores
        FROM tabla_fuga_detallada_desertores f
        INNER JOIN UltimaJornada uj ON f.mrun = uj.mrun
        LEFT JOIN Titulados_ECAS tit ON f.mrun = tit.mrun
        WHERE f.anio_ultima_matricula_ecas = :periodo_actual
          AND tit.mrun IS NULL 
          {f_jornada.replace('UltimaJornada', 'uj')}
    ),
    Acred AS (
        -- Seleccionamos también el estado cualitativo acreditada_inst
        SELECT TOP 2 acre_inst_anio, acreditada_inst, periodo
        FROM tabla_dashboard_permanencia
        WHERE cod_inst = 104 
          AND periodo IN (:periodo_actual, :periodo_anterior)
        ORDER BY periodo DESC
    )
    SELECT 
        (SELECT TOP 1 acre_inst_anio FROM Acred WHERE periodo = :periodo_actual) as acreditacion_ecas_anio,
        (SELECT TOP 1 acreditada_inst FROM Acred WHERE periodo = :periodo_actual) as acreditada_inst_ecas,
        (SELECT TOP 1 acre_inst_anio FROM Acred WHERE periodo = :periodo_anterior) as acreditacion_anterior_anio,
        (SELECT CAST(total_permanecen AS FLOAT) * 100 / NULLIF(total_base, 0) FROM Retencion) as tasa_retencion,
        (SELECT total_desertores FROM Desertores) as cant_desertores
    """

    df = pd.read_sql(text(sql_query), db_engine, params=params).iloc[0]

    return df

def get_detalle_instituciones_fuga(periodo_sel, categoria_sel, jornada="Todas"):
    params = {
        "periodo": periodo_sel,
        "categoria": categoria_sel
    }
    
    # Filtro opcional de jornada basado en permanencia
    f_jornada = "AND f.jornada_ecas = :jornada" if jornada != "Todas" else ""
    if jornada != "Todas": params["jornada"] = jornada

    sql_query = f"""
    WITH Acred_ECAS AS (
        SELECT DISTINCT periodo, acre_inst_anio AS acred_ecas_periodo
        FROM tabla_dashboard_permanencia WHERE cod_inst = 104
    ),
    PrimerIngresoPost AS (
        SELECT 
            mrun, inst_destino, acreditada_inst, acre_inst_anio,
            anio_matricula_post, anio_ultima_matricula_ecas, jornada_ecas,
            ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY anio_matricula_post ASC) as rn_ingreso
        FROM [DBMatriculas].[dbo].[tabla_fuga_detallada_desertores]
    ),
    MovilidadClasificada AS (
        SELECT 
            f.inst_destino,
            f.mrun,
            CASE 
                WHEN e.acred_ecas_periodo >= 99 
                     AND (f.acreditada_inst IN ('SÍ', 'ACREDITADA') OR (f.acre_inst_anio > 0 AND f.acre_inst_anio < 99))
                     THEN 'Más Acreditada'
                WHEN f.acreditada_inst IN ('NO', 'SIN ACREDITACIÓN') 
                     OR ISNULL(f.acre_inst_anio, 0) = 0 
                     OR f.acre_inst_anio >= 99 
                     THEN 'No Acreditada'
                WHEN f.acre_inst_anio > e.acred_ecas_periodo THEN 'Más Acreditada'
                WHEN f.acre_inst_anio = e.acred_ecas_periodo THEN 'Igual Acreditación'
                ELSE 'Menos Acreditada'
            END AS categoria_movilidad
        FROM PrimerIngresoPost f
        INNER JOIN Acred_ECAS e ON f.anio_ultima_matricula_ecas = e.periodo
        WHERE f.rn_ingreso = 1 
          AND f.anio_ultima_matricula_ecas = :periodo
          AND f.anio_matricula_post = (:periodo + 1)
          {f_jornada}
    )
    SELECT 
        inst_destino,
        COUNT(DISTINCT mrun) AS cantidad_alumnos
    FROM MovilidadClasificada
    WHERE categoria_movilidad = :categoria
    GROUP BY inst_destino
    ORDER BY cantidad_alumnos DESC
    """
    return pd.read_sql(text(sql_query), db_engine, params=params)
from conn_db import get_db_engine
from sqlalchemy import text
import pandas as pd
from typing import Optional, List

db_engine = get_db_engine()

def get_ingresos_competencia_parametrizado(top_n=10, anio_min=2007, anio_max=2025, jornada=None, genero="Todos"):
    
    params = {"top_n": top_n, "anio_min": anio_min, "anio_max": anio_max}
    
    filtro_jornada = "AND jornada = :jornada" if jornada and jornada != "Todas" else ""
    if filtro_jornada: params["jornada"] = jornada

    filtro_genero = "AND genero = :genero" if genero and genero != "Todos" else ""
    if filtro_genero: params["genero"] = genero

    sql_query = f"""
    WITH base AS (
        SELECT cohorte, cod_inst, nomb_inst, COUNT(DISTINCT mrun) AS total_ingresos
        FROM tabla_dashboard_permanencia
        WHERE cohorte BETWEEN :anio_min AND :anio_max
        {filtro_jornada}
        {filtro_genero}
        GROUP BY cohorte, cod_inst, nomb_inst
    ),
    ranking AS (
        -- El ranking se calcula sobre el promedio de ingresos en el periodo y filtros seleccionados
        SELECT TOP (:top_n) cod_inst
        FROM base
        WHERE cod_inst <> 104
        GROUP BY cod_inst
        ORDER BY AVG(CAST(total_ingresos AS FLOAT)) DESC
    )
    SELECT b.cohorte, b.cod_inst, b.nomb_inst, b.total_ingresos 
    FROM base b 
    LEFT JOIN ranking r ON b.cod_inst = r.cod_inst
    WHERE b.cod_inst = 104 OR r.cod_inst IS NOT NULL
    ORDER BY b.cohorte, b.total_ingresos DESC;
    """

    
    df = pd.read_sql(text(sql_query), db_engine, params=params)
    
    return df

#print(get_ingresos_competencia_parametrizado(top_n=10, anio_min=2007, anio_max=2025))

def get_permanencia_n_n1_competencia(anio_min: int, anio_max: int, jornada: None, genero:"Todos") -> pd.DataFrame:
    anio_max_ajustado = min(anio_max, 2024)
    
    params = {
        "anio_min": anio_min,
        "anio_max": anio_max_ajustado,
        "anio_max_ext": anio_max_ajustado + 1,
        "genero": genero
    }

    # El filtro de jornada SOLO debe aplicar al universo inicial (Cohorte)
    filtro_jornada_cohorte = "AND jornada = :jornada" if jornada and jornada != "Todas" else ""
    if filtro_jornada_cohorte: params["jornada"] = jornada

    filtro_genero = "AND genero = :genero" if genero and genero != "Todos" else ""
    if filtro_genero: params["genero"] = genero

    sql_query = f"""
    WITH universo_cohortes AS (
        -- Definimos quiénes entraron en la cohorte X con la jornada seleccionada
        SELECT DISTINCT mrun, cod_inst, nomb_inst, cohorte
        FROM tabla_dashboard_permanencia
        WHERE cohorte BETWEEN :anio_min AND :anio_max
        {filtro_jornada_cohorte}
        {filtro_genero}
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
    
   
    df = pd.read_sql(text(sql_query), db_engine, params=params)
    
    df['tasa_permanencia_pct'] = (df['retenidos_n1'] * 100.0 / df['base_n'].replace(0, pd.NA)).fillna(0).round(2)
    
    return df

#Cambios de jornada evaluados por cohorte
def get_distribucion_cambio_jornada_ecas(anio_min, anio_max, jornada_filtro=None, genero="Todos"):
    params = {
        "anio_min": anio_min, 
        "anio_max": min(anio_max, 2024),
    }
    
    # Filtro dinámico de Jornada
    filtro_jornada = ""
    if jornada_filtro and jornada_filtro != "Todas":
        filtro_jornada = "AND t1.jornada_origen = :jornada_filtro"
        params["jornada_filtro"] = jornada_filtro

    # Filtro dinámico de Género
    filtro_genero = ""
    if genero and genero != "Todos":
        filtro_genero = "AND t1.genero = :genero"
        params["genero"] = genero

    sql_query = f"""
    WITH cohorte_inicial AS (
        SELECT mrun, jornada AS jornada_origen, cohorte, genero
        FROM tabla_dashboard_permanencia
        WHERE cod_inst = 104
          AND cohorte BETWEEN :anio_min AND :anio_max
          AND cohorte = periodo
    ),
    seguimiento_n1 AS (
        SELECT mrun, jornada AS jornada_destino, periodo
        FROM tabla_dashboard_permanencia
        WHERE cod_inst = 104
          AND periodo BETWEEN :anio_min + 1 AND :anio_max + 1
    )
    SELECT 
        t1.jornada_origen,
        t1.cohorte,
        t1.genero,
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
    WHERE 1=1 
    {filtro_jornada}
    {filtro_genero}
    GROUP BY t1.jornada_origen, t1.cohorte, t1.genero,
             CASE 
                WHEN t2.jornada_destino IS NULL THEN 'Deserción'
                WHEN t1.jornada_origen = t2.jornada_destino THEN 'Mantiene Jornada'
                ELSE 'Cambio de Jornada'
             END
    """
    with db_engine.connect() as conn:
        df = pd.read_sql(text(sql_query), conn, params=params)

    return df

def get_supervivencia_vs_titulacion_data(anios_rango, instituciones=None, genero="Todos"):
    if not instituciones:
        instituciones = ["IP ESCUELA DE CONTADORES AUDITORES DE SANTIAGO"]
    elif isinstance(instituciones, str):
        instituciones = [instituciones]

    # 1. Parámetros de instituciones para la cláusula IN
    inst_params = {f"inst_{i}": nombre for i, nombre in enumerate(instituciones)}
    in_clause = ", ".join([f":{k}" for k in inst_params.keys()])

    # 2. Configuración de parámetros finales
    params = {
        "anio_min": anios_rango[0],
        "anio_max": anios_rango[1],
        **inst_params
    }

    # 3. Filtro dinámico de Género
    filtro_genero = ""
    if genero and genero != "Todos":
        filtro_genero = "AND genero = :genero"
        params["genero"] = genero

    # 4. Query SQL con soporte para género en todas las etapas
    sql_query = f"""
    WITH base_cohorte AS (
        SELECT nomb_inst, cohorte, COUNT(DISTINCT mrun) as total_inicial
        FROM tabla_dashboard_permanencia
        WHERE cohorte BETWEEN :anio_min AND :anio_max 
          AND nomb_inst IN ({in_clause})
          {filtro_genero}
        GROUP BY nomb_inst, cohorte
    ),
    matriculados_por_anio AS (
        SELECT 
            nomb_inst, cohorte, (periodo - cohorte) AS t_anios,
            COUNT(DISTINCT mrun) AS n_matriculados
        FROM tabla_dashboard_permanencia
        WHERE cohorte BETWEEN :anio_min AND :anio_max 
          AND nomb_inst IN ({in_clause})
          {filtro_genero}
        GROUP BY nomb_inst, cohorte, (periodo - cohorte)
    ),
    titulados_por_anio AS (
        -- Importante: Asegurar que tabla_dashboard_titulados también tenga columna genero
        SELECT 
            nomb_inst, cohorte, anios_para_titularse AS t_anios,
            COUNT(DISTINCT mrun) AS n_titulados
        FROM tabla_dashboard_titulados
        WHERE cohorte BETWEEN :anio_min AND :anio_max 
          AND nomb_inst IN ({in_clause})
          {filtro_genero}
        GROUP BY anios_para_titularse, nomb_inst, cohorte
    ),
    calculos_por_cohorte AS (
        SELECT 
            m.nomb_inst, m.cohorte, m.t_anios,
            (CAST(m.n_matriculados AS FLOAT) / NULLIF(b.total_inicial, 0)) * 100 AS pct_supervivencia,
            (CAST(SUM(COALESCE(t.n_titulados, 0)) OVER (PARTITION BY m.nomb_inst, m.cohorte ORDER BY m.t_anios) AS FLOAT) / NULLIF(b.total_inicial, 0)) * 100 AS pct_titulacion_acum
        FROM matriculados_por_anio m
        JOIN base_cohorte b ON m.nomb_inst = b.nomb_inst AND m.cohorte = b.cohorte
        LEFT JOIN titulados_por_anio t ON m.nomb_inst = t.nomb_inst AND m.cohorte = t.cohorte AND m.t_anios = t.t_anios
    )
    SELECT 
        nomb_inst, t_anios,
        AVG(pct_supervivencia) AS pct_supervivencia,
        AVG(pct_titulacion_acum) AS pct_titulacion_acum
    FROM calculos_por_cohorte
    GROUP BY nomb_inst, t_anios
    ORDER BY nomb_inst, t_anios
    """

    df = pd.read_sql(text(sql_query), db_engine, params=params)
    
    return df

def get_metrica_titulacion_externa(rango_anios, jornada="Todas", genero="Todos"):

    condiciones = [f"anio_cohorte_ecas BETWEEN {rango_anios[0]} AND {rango_anios[1]}"]
    
    if jornada != "Todas":
        condiciones.append(f"jornada_ecas = '{jornada}'")
    if genero != "Todos":
        condiciones.append(f"genero = '{genero}'")
        
    where_clause = " AND ".join(condiciones)

    query = f"""
    SELECT 
        (SELECT COUNT(DISTINCT mrun) FROM tabla_fuga_detallada_desertores WHERE {where_clause}) as total_desertores,
        (SELECT COUNT(DISTINCT mrun) FROM tabla_titulados_externos_desertores WHERE {where_clause}) as total_titulados_ext
    """
    
    df = pd.read_sql(query, db_engine)
    
    if not df.empty and df['total_desertores'][0] > 0:
        df['tasa_exito_externo'] = (df['total_titulados_ext'] / df['total_desertores']) * 100
    else:
        df['tasa_exito_externo'] = 0
        
    return df
from conn_db import get_db_engine
from sqlalchemy import text
import pandas as pd
from typing import Optional, List

db_engine = get_db_engine()

map_ensenianza = {
    310: "Enseñanza Media H-C Niños y Jóvenes",
    360: "Ed. Media H-C Adultos Vespertino y Nocturno (D. 190/1975)",
    361: "Ed. Media H-C Adultos (D. 12/1987)",
    362: "Escuelas Cárceles (Media Adultos)",
    363: "Ed. Media H-C Adultos (D. 1000/2009)",
    410: "Enseñanza Media T-P Comercial Niños y Jóvenes",
    460: "Ed. Media T-P Comercial Adultos (D. 152/1989)",
    461: "Ed. Media T-P Comercial Adultos (D. 152/1989)",
    463: "Ed. Media T-P Comercial Adultos (D. 1000/2009)",
    510: "Enseñanza Media T-P Industrial Niños y Jóvenes",
    560: "Ed. Media T-P Industrial Adultos (D. 152/1989)",
    561: "Ed. Media T-P Industrial Adultos (D. 152/1989)",
    563: "Ed. Media T-P Industrial Adultos (D. 1000/2009)",
    610: "Enseñanza Media T-P Técnica Niños y Jóvenes",
    660: "Ed. Media T-P Técnica Adultos (D. 152/1989)",
    661: "Ed. Media T-P Técnica Adultos (D. 152/1989)",
    663: "Ed. Media T-P Técnica Adultos (D. 1000/2009)",
    710: "Enseñanza Media T-P Agrícola Niños y Jóvenes",
    760: "Ed. Media T-P Agrícola Adultos (D. 152/1989)",
    761: "Ed. Media T-P Agrícola Adultos (D. 152/1989)",
    763: "Ed. Media T-P Agrícola Adultos (D. 1000/2009)",
    810: "Enseñanza Media T-P Marítima Niños y Jóvenes",
    860: "Ed. Media T-P Marítima Adultos (D. 152/1989)",
    863: "Ed. Media T-P Marítima Adultos (D. 1000/2009)",
    910: "Enseñanza Media Artística Niños y Jóvenes",
    963: "Enseñanza Media Artística Adultos"
}

map_provincias_rm = {
    131: "Provincia de Santiago",
    132: "Provincia de Cordillera",
    133: "Provincia de Chacabuco",
    134: "Provincia de Maipo",
    135: "Provincia de Melipilla",
    136: "Provincia de Talagante"
}

#Nota: Esta query ocupa un inner join que elimina a aquellos matriculados en ECAS que
#NO tienen un registro de egreso en la educación media.
def get_distribucion_dependencia_cohorte(cohorte_sel, cod_inst, genero="Todos", jornada="Todas"):
    params = {"cohorte": cohorte_sel,
              "cod_inst": cod_inst,}

    filtro_jornada = "AND jornada = :jornada" if jornada and jornada != "Todas" else ""
    if filtro_jornada: params["jornada"] = jornada

    filtro_genero = "AND genero = :genero" if genero and genero != "Todos" else ""
    if filtro_genero: params["genero"] = genero
    
    sql_query = f"""
    WITH cohorte_ingreso AS (
    SELECT 
        mrun,
        MIN(cohorte) AS anio_ingreso
    FROM tabla_matriculas_competencia_unificada
    WHERE cod_inst = :cod_inst
      {filtro_jornada}
      {filtro_genero}
    GROUP BY mrun
    ),
    egreso_ordenado AS (
        SELECT
            mrun,
            cod_dep_agrupado,
            periodo,
            ROW_NUMBER() OVER (
                PARTITION BY mrun
                ORDER BY periodo DESC
            ) AS rn
        FROM tabla_alumnos_egresados_unificada
    )
    SELECT 
        CASE 
            WHEN e.cod_dep_agrupado = 1 THEN 'Municipal'
            WHEN e.cod_dep_agrupado = 2 THEN 'Part. Subvencionado'
            WHEN e.cod_dep_agrupado = 3 THEN 'Part. Pagado'
            WHEN e.cod_dep_agrupado = 4 THEN 'Admin. Delegada'
            WHEN e.cod_dep_agrupado = 5 THEN 'SLEP'
            ELSE 'Otro / Sin información'
        END AS tipo_establecimiento,
        COUNT(*) AS cantidad
    FROM cohorte_ingreso c
    INNER JOIN egreso_ordenado e 
        ON c.mrun = e.mrun
    AND e.rn = 1
    WHERE c.anio_ingreso = :cohorte
    GROUP BY e.cod_dep_agrupado
    ORDER BY cantidad DESC;
    """
    
    df = pd.read_sql(text(sql_query), db_engine, params=params)

    return df

def get_distribucion_dependencia_rango(cohorte_range, cod_inst, genero="Todos", jornada="Todas"):
    """
    cohorte_range: Puede ser un entero (2009) o una lista [2007, 2010]
    """
    # Manejo de rango o valor único
    if isinstance(cohorte_range, list):
        c_inicio, c_fin = cohorte_range[0], cohorte_range[1]
        condicion_cohorte = "BETWEEN :c_inicio AND :c_fin"
        num_anios = (c_fin - c_inicio) + 1
    else:
        c_inicio, c_fin = cohorte_range, cohorte_range
        condicion_cohorte = "= :c_inicio"
        num_anios = 1

    params = {
        "c_inicio": c_inicio,
        "c_fin": c_fin,
        "cod_inst": cod_inst,
        "jornada": jornada,
        "genero": genero
    }

    filtro_jornada = "AND jornada = :jornada" if jornada != "Todas" else ""
    filtro_genero = "AND genero = :genero" if genero != "Todos" else ""

    sql_query = text(f"""
    WITH cohorte_ingreso AS (
        SELECT 
            mrun,
            MIN(cohorte) AS anio_ingreso
        FROM tabla_matriculas_competencia_unificada
        WHERE cod_inst = :cod_inst
          {filtro_jornada}
          {filtro_genero}
        GROUP BY mrun
    ),
    egreso_ordenado AS (
        SELECT
            mrun,
            cod_dep_agrupado,
            ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY periodo DESC) AS rn
        FROM tabla_alumnos_egresados_unificada
    )
    SELECT 
        CASE 
            WHEN e.cod_dep_agrupado = 1 THEN 'Municipal'
            WHEN e.cod_dep_agrupado = 2 THEN 'Part. Subvencionado'
            WHEN e.cod_dep_agrupado = 3 THEN 'Part. Pagado'
            WHEN e.cod_dep_agrupado = 4 THEN 'Admin. Delegada'
            WHEN e.cod_dep_agrupado = 5 THEN 'SLEP'
            ELSE 'Otro / Sin información'
        END AS tipo_establecimiento,
        COUNT(*) AS total_periodo
    FROM cohorte_ingreso c
    INNER JOIN egreso_ordenado e ON c.mrun = e.mrun AND e.rn = 1
    WHERE c.anio_ingreso {condicion_cohorte}
    GROUP BY e.cod_dep_agrupado
    ORDER BY total_periodo DESC;
    """)
    
    df = pd.read_sql(sql_query, db_engine, params=params)

    if not df.empty:
        # Calculamos el promedio anual basado en el rango
        df['promedio_anual'] = (df['total_periodo'] / num_anios).round(1)
        
        # Porcentaje respecto al total del rango
        total_absoluto = df['total_periodo'].sum()
        df['porcentaje'] = (df['total_periodo'] / total_absoluto * 100).round(1)
        
    return df

#print(get_distribucion_dependencia_rango(cohorte_range=[2007,2007], cod_inst=104))

def get_titulados_por_dependencia_rango(cohorte_range, cod_inst, genero="Todos", jornada="Todas", anio_titulacion_sel=None):
    """
    cohorte_range: puede ser int (2009) o list [2007, 2010]
    """
    # 1. Configuración de Rango
    if isinstance(cohorte_range, list):
        c_inicio, c_fin = cohorte_range[0], cohorte_range[1]
        condicion_cohorte = "BETWEEN :c_inicio AND :c_fin"
        num_anios = (c_fin - c_inicio) + 1
    else:
        c_inicio, c_fin = cohorte_range, cohorte_range
        condicion_cohorte = "= :c_inicio"
        num_anios = 1

    params = {
        "c_inicio": c_inicio,
        "c_fin": c_fin,
        "cod_inst": cod_inst,
        "genero": genero,
        "jornada": jornada
    }
    
    # Filtros dinámicos
    filtro_anio_tit = "AND anio_titulacion = :anio_tit" if anio_titulacion_sel else ""
    if anio_titulacion_sel: params["anio_tit"] = anio_titulacion_sel
    
    filtro_genero = "AND genero = :genero" if genero != "Todos" else ""
    filtro_jornada = "AND jornada = :jornada" if jornada != "Todas" else ""
    
    sql_query = text(f"""
    WITH CohorteEstudiantes AS (
        -- Identificamos el primer ingreso real para filtrar por rango de cohorte
        SELECT 
            mrun, 
            MIN(cohorte) as anio_ingreso
        FROM tabla_matriculas_competencia_unificada
        WHERE cod_inst = :cod_inst
        GROUP BY mrun
    ),
    UltimaInfoTitulado AS (
        -- Filtramos los titulados por los criterios del Dashboard
        SELECT * FROM (
            SELECT 
                mrun,
                ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY anio_titulacion DESC) as rn
            FROM tabla_dashboard_titulados
            WHERE cod_inst = :cod_inst
            {filtro_anio_tit}
            {filtro_genero}
            {filtro_jornada}
        ) t_sub WHERE rn = 1
    ),
    UltimoEgresoMedia AS (
        -- Datos de origen escolar únicos
        SELECT * FROM (
            SELECT 
                mrun,
                cod_dep_agrupado,
                ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY periodo DESC) as rn_media
            FROM tabla_alumnos_egresados_unificada
        ) e_sub WHERE rn_media = 1
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
        COUNT(DISTINCT t.mrun) AS total_titulados_periodo
    FROM UltimaInfoTitulado t
    INNER JOIN CohorteEstudiantes c ON t.mrun = c.mrun
    INNER JOIN UltimoEgresoMedia e ON t.mrun = e.mrun
    WHERE c.anio_ingreso {condicion_cohorte}
    GROUP BY e.cod_dep_agrupado
    ORDER BY total_titulados_periodo DESC
    """)
    
    df = pd.read_sql(sql_query, db_engine, params=params)

    if not df.empty:
        # 2. Cálculos Estadísticos para el Rango
        df['promedio_anual_titulados'] = (df['total_titulados_periodo'] / num_anios).round(1)
        
        total_total = df['total_titulados_periodo'].sum()
        df['porcentaje_del_periodo'] = (df['total_titulados_periodo'] / total_total * 100).round(1)
        
    return df

#print(get_titulados_por_dependencia_rango(cohorte_range=[2007,2025], cod_inst=104))

def get_demora_ingreso_total(cohorte_range, cod_inst, carrera="Todas", genero="Todos", jornada_filtro="Todas"):
    if isinstance(cohorte_range, list):
        c_inicio, c_fin = cohorte_range[0], cohorte_range[1]
        condicion_cohorte = "BETWEEN :c_inicio AND :c_fin"
    else:
        c_inicio, c_fin = cohorte_range, cohorte_range
        condicion_cohorte = "= :c_inicio"

    params = {
        "c_inicio": c_inicio,
        "c_fin": c_fin,
        "cod_inst": cod_inst,
        "carrera": carrera,
        "genero": genero
    }

    filtro_carrera = "AND p.nomb_carrera = :carrera" if carrera != "Todas" else ""
    filtro_genero = "AND p.genero = :genero" if genero != "Todos" else ""
    
    sql_query = text(f"""
    WITH PrimerIngresoGlobal AS (
        SELECT * FROM (
            SELECT 
                mrun, 
                cohorte as anio_ingreso,
                jornada,
                nomb_carrera,
                genero,
                ROW_NUMBER() OVER (
                    PARTITION BY mrun 
                    ORDER BY cohorte ASC, CASE WHEN jornada IS NULL THEN 1 ELSE 0 END ASC, jornada DESC
                ) as rn_ingreso
            FROM tabla_matriculas_competencia_unificada
            WHERE cod_inst = :cod_inst
        ) t WHERE rn_ingreso = 1
    ),
    UltimoEgresoMedia AS (
        SELECT * FROM (
            SELECT 
                mrun, periodo,
                ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY periodo DESC) as rn
            FROM tabla_alumnos_egresados_unificada
        ) e_sub WHERE rn = 1
    )
    SELECT 
        p.jornada,
        (p.anio_ingreso - CAST(e.periodo AS INT)) as anios_demora,
        p.mrun
    FROM PrimerIngresoGlobal p
    INNER JOIN UltimoEgresoMedia e ON p.mrun = e.mrun
    WHERE p.anio_ingreso {condicion_cohorte}
      {filtro_carrera}
      {filtro_genero}
    """)
    
    df_raw = pd.read_sql(sql_query, db_engine, params=params)

    df = df_raw.copy()

    if jornada_filtro != "Todas":
        df = df[df['jornada'] == jornada_filtro]

    df = df[df['anios_demora'] >= 1]
    
    # Agrupar y contar
    resumen = df.groupby('anios_demora').size().reset_index(name='total_alumnos_periodo')
    
    # Cálculos adicionales
    total = resumen['total_alumnos_periodo'].sum()
    resumen['porcentaje'] = (resumen['total_alumnos_periodo'] / total * 100).round(2)
    
    return resumen

#KPI para analizar si los alumnos con un buen rendimiento academico en su educación media
#son más o menos probables de desertar al primer año.
def get_correlacion_nem_persistencia(cohorte_sel, cod_inst, jornada="Todas", carrera="Todas", genero="Todos"):
    params = {
        "cohorte": cohorte_sel,
        "cod_inst": cod_inst,
        "prox_anio": cohorte_sel + 1
    }

    # Filtros Dinámicos
    filtros = ""
    if jornada != "Todas":
        filtros += " AND jornada = :jornada"
        params["jornada"] = jornada
    if carrera != "Todas":
        filtros += " AND nomb_carrera = :carrera"
        params["carrera"] = carrera
    if genero != "Todos":
        filtros += " AND genero = :genero"
        params["genero"] = genero

    sql_query = f"""
    WITH PromediosNEM AS (
        -- Calculamos el NEM promedio de la enseñanza media por alumno
        SELECT 
            mrun, 
            AVG(CAST(REPLACE(prom_notas_alu, ',', '.') AS FLOAT)) as nem_final
        FROM tabla_alumnos_egresados_unificada
        GROUP BY mrun
    ),
    UniversoCohorte AS (
        -- Alumnos que ingresaron en la cohorte y filtros seleccionados
        SELECT DISTINCT mrun
        FROM tabla_matriculas_competencia_unificada
        WHERE cod_inst = :cod_inst 
          AND cohorte = :cohorte
          {filtros}
    ),
    Persistencia AS (
        -- Verificamos si tienen matrícula en el año T+1
        SELECT 
            u.mrun,
            n.nem_final,
            CASE WHEN m.mrun IS NOT NULL THEN 1 ELSE 0 END as sigue_estudiando
        FROM UniversoCohorte u
        INNER JOIN PromediosNEM n ON u.mrun = n.mrun
        LEFT JOIN tabla_matriculas_competencia_unificada m ON u.mrun = m.mrun 
            AND m.periodo = :prox_anio 
            AND m.cod_inst = :cod_inst
    ),
    RangosNEM AS (
        -- Agrupamos por rangos de notas para el análisis
        SELECT 
            CASE 
                WHEN nem_final < 5.0 THEN '4.0 - 4.9'
                WHEN nem_final < 5.5 THEN '5.0 - 5.4'
                WHEN nem_final < 6.0 THEN '5.5 - 5.9'
                WHEN nem_final < 6.5 THEN '6.0 - 6.4'
                ELSE '6.5 - 7.0'
            END as rango_nem,
            sigue_estudiando
        FROM Persistencia
    )
    SELECT 
        rango_nem,
        COUNT(*) as total_alumnos,
        SUM(sigue_estudiando) as cantidad_persisten,
        ROUND(AVG(CAST(sigue_estudiando AS FLOAT)) * 100, 1) as tasa_persistencia
    FROM RangosNEM
    GROUP BY rango_nem
    ORDER BY rango_nem ASC
    """
    
    return pd.read_sql(text(sql_query), db_engine, params=params)

#print(get_correlacion_nem_persistencia(cohorte_sel=2007, cod_inst=104))

def get_correlacion_nem_titulacion(cohorte_sel, cod_inst, jornada="Todas", carrera="Todas", genero="Todos"):
    params = {
        "cohorte": cohorte_sel,
        "cod_inst": cod_inst
    }

    # Filtros dinámicos
    filtros = ""
    if jornada != "Todas":
        filtros += " AND jornada = :jornada"
        params["jornada"] = jornada
    if carrera != "Todas":
        filtros += " AND nomb_carrera = :carrera"
        params["carrera"] = carrera
    if genero != "Todos":
        filtros += " AND genero = :genero"
        params["genero"] = genero

    sql_query = f"""
    WITH PromediosNEM AS (
        SELECT 
            mrun, 
            AVG(CAST(REPLACE(prom_notas_alu, ',', '.') AS FLOAT)) as nem_final
        FROM tabla_alumnos_egresados_unificada
        GROUP BY mrun
    ),
    BaseIngreso AS (
        -- Obtenemos el ingreso, la carrera y su duración formal
        -- Usamos MAX para la duración formal por si hay pequeñas variaciones en registros
        SELECT 
            mrun, 
            MIN(cohorte) as anio_ingreso,
            MAX(CAST(dur_total_carr AS INT)) / 2.0 as duracion_formal_anios -- Asumiendo que viene en semestres
        FROM tabla_matriculas_competencia_unificada
        WHERE cod_inst = :cod_inst 
          AND cohorte = :cohorte
          {filtros}
        GROUP BY mrun
    ),
    DatosTitulacion AS (
        -- Cruzamos con la tabla de titulados
        SELECT 
            b.mrun,
            b.nem_final,
            b.duracion_formal_anios,
            t.anio_titulacion,
            (t.anio_titulacion - b.anio_ingreso ) as duracion_real_anios
        FROM (
            SELECT bi.*, pn.nem_final 
            FROM BaseIngreso bi 
            INNER JOIN PromediosNEM pn ON bi.mrun = pn.mrun
        ) b
        INNER JOIN tabla_dashboard_titulados t ON b.mrun = t.mrun AND t.cod_inst = :cod_inst
    ),
    Clasificacion AS (
        SELECT 
            CASE 
                WHEN nem_final < 5.0 THEN '4.0 - 4.9'
                WHEN nem_final < 5.5 THEN '5.0 - 5.4'
                WHEN nem_final < 6.0 THEN '5.5 - 5.9'
                WHEN nem_final < 6.5 THEN '6.0 - 6.4'
                ELSE '6.5 - 7.0'
            END as rango_nem,
            CASE 
                WHEN duracion_real_anios <= duracion_formal_anios THEN 1 
                ELSE 0 
            END as es_oportuna
        FROM DatosTitulacion
    )
    SELECT 
        rango_nem,
        COUNT(*) as total_titulados,
        SUM(es_oportuna) as titulados_a_tiempo,
        ROUND(AVG(CAST(es_oportuna AS FLOAT)) * 100, 1) as tasa_titulacion_oportuna
    FROM Clasificacion
    GROUP BY rango_nem
    ORDER BY rango_nem ASC
    """
    
    return pd.read_sql(text(sql_query), db_engine, params=params)

#print(get_correlacion_nem_titulacion(cohorte_sel=2007, cod_inst=104))

def get_tasas_articulacion_tipo_establecimiento(cohorte_sel, cod_inst, jornada="Todas", carrera="Todas", genero="Todos"):
    
    # Aseguramos que el código 0 sea visible
    map_ensenianza_full = map_ensenianza.copy()
    map_ensenianza_full[0] = "Media - Modalidad no registrada"

    # Diccionario de parámetros para SQLAlchemy
    params = {
        "cod_inst": cod_inst,
        "cohorte": cohorte_sel,
        "jornada": jornada,
        "genero": genero,
        "carrera": carrera
    }

    # Construcción de filtros dinámicos
    filtro_jornada = "AND jornada = :jornada" if jornada != "Todas" else ""
    filtro_genero = "AND genero = :genero" if genero != "Todos" else ""
    filtro_carrera = "AND nomb_carrera = :carrera" if carrera != "Todas" else ""

    sql_query = text(f"""
    WITH cohorte_ingreso AS (
    SELECT 
        mrun,
        MIN(cohorte) AS anio_ingreso
    FROM tabla_matriculas_competencia_unificada
    WHERE cod_inst = :cod_inst
      {filtro_jornada}
      {filtro_genero}
      {filtro_carrera}
    GROUP BY mrun
    ),
    universo_ies AS (
        SELECT mrun
        FROM cohorte_ingreso
        WHERE anio_ingreso = :cohorte
    ),
    egreso_ordenado AS (
        SELECT
            mrun,
            COALESCE(NULLIF(TRIM(CAST(cod_ensenianza AS VARCHAR(10))), ''), '0') AS cod_ense_clean,
            CAST(REPLACE(prom_notas_alu, ',', '.') AS FLOAT) AS prom_notas,
            periodo,
            ROW_NUMBER() OVER (
                PARTITION BY mrun
                ORDER BY periodo DESC
            ) AS rn
        FROM tabla_alumnos_egresados_unificada
    )
    SELECT
        u.mrun,
        e.cod_ense_clean,
        e.prom_notas AS prom_notas_media
    FROM universo_ies u
    INNER JOIN egreso_ordenado e
        ON u.mrun = e.mrun
    AND e.rn = 1;
    """)

    # IMPORTANTE: Pasar los parámetros dentro de read_sql
    df = pd.read_sql(sql_query, db_engine, params=params)

    df['cod_ense_clean'] = (
        df['cod_ense_clean']
        .fillna(0)
        .astype(int)
    )

    df['nomb_ensenianza'] = (
        df['cod_ense_clean']
        .map(map_ensenianza_full)
        .fillna("Media - Modalidad no registrada")
    )

    kpi = df.groupby('nomb_ensenianza').agg({
        'mrun': 'count',
        'prom_notas_media': 'mean'
    }).reset_index()

    kpi.columns = ['Tipo Enseñanza', 'Cant. Estudiantes', 'Promedio Notas']

    return kpi

#print(get_tasas_articulacion_tipo_establecimiento(cohorte_sel=2007, cod_inst=104))

def get_distribucion_regional_egreso(cohorte_sel, cod_inst, jornada="Todas"):
    
    params = {
        "cod_inst": cod_inst,
        "cohorte": cohorte_sel,
        "jornada": jornada
    }

    filtro_jornada = "AND m.jornada = :jornada" if jornada != "Todas" else ""

    sql_query = text(f"""
    WITH universo_ies AS (
        SELECT DISTINCT mrun
        FROM tabla_matriculas_competencia_unificada m
        WHERE m.cod_inst = :cod_inst
          AND m.cohorte = :cohorte
          {filtro_jornada}
    ),
    egresados_ranking AS (
        -- Rankeamos los registros de cada alumno por año (periodo) descendente
        SELECT 
            mrun,
            cod_region,
            nomb_region,
            ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY periodo DESC) as rn
        FROM tabla_alumnos_egresados_unificada
    ),
    ultimo_egreso AS (
        -- Nos quedamos solo con el registro más reciente (rn = 1)
        SELECT 
            mrun,
            cod_region,
            nomb_region
        FROM egresados_ranking
        WHERE rn = 1
    )
    SELECT 
        e.cod_region,
        e.nomb_region,
        COUNT(u.mrun) AS cantidad_estudiantes
    FROM universo_ies u
    INNER JOIN ultimo_egreso e ON u.mrun = e.mrun
    GROUP BY e.cod_region, e.nomb_region
    ORDER BY cantidad_estudiantes DESC
    """)

    df = pd.read_sql(sql_query, db_engine, params=params)

    if not df.empty:
        total = df['cantidad_estudiantes'].sum()
        df['porcentaje'] = (df['cantidad_estudiantes'] / total * 100).round(2)
    
    return df

def get_distribucion_provincial_egreso(cohorte_sel, cod_inst, cod_region_filtro, jornada="Todas"):
    
    params = {
        "cod_inst": cod_inst,
        "cohorte": cohorte_sel,
        "jornada": jornada,
        "cod_reg": cod_region_filtro
    }

    filtro_jornada = "AND m.jornada = :jornada" if jornada != "Todas" else ""

    sql_query = text(f"""
    WITH universo_ies AS (
        SELECT DISTINCT mrun
        FROM tabla_matriculas_competencia_unificada m
        WHERE m.cod_inst = :cod_inst
          AND m.cohorte = :cohorte
          {filtro_jornada}
    ),
    ultimo_egreso_geo AS (
        -- Seleccionamos el último registro de egreso para asegurar consistencia
        SELECT 
            mrun,
            cod_region,
            cod_provincia,
            ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY periodo DESC) as rn
        FROM tabla_alumnos_egresados_unificada
    )
    SELECT 
        e.cod_provincia,
        COUNT(u.mrun) AS cantidad_estudiantes
    FROM universo_ies u
    INNER JOIN ultimo_egreso_geo e ON u.mrun = e.mrun
    WHERE e.rn = 1 
      AND e.cod_region = :cod_reg -- Filtramos por la región solicitada
    GROUP BY e.cod_provincia
    ORDER BY cantidad_estudiantes DESC
    """)

    df = pd.read_sql(sql_query, db_engine, params=params)

    df['cod_provincia'] = df['cod_provincia'].astype(int)

    df['nomb_provincia'] = df['cod_provincia'].map(map_provincias_rm).fillna("Provincia No Mapeada")
        
    df = df[['cod_provincia', 'nomb_provincia', 'cantidad_estudiantes']]
    
    total_region = df['cantidad_estudiantes'].sum()
    df['porcentaje_reg'] = (df['cantidad_estudiantes'] / total_region * 100).round(2)

    return df

def get_distribucion_comuna_egreso(cohorte_sel, cod_inst, cod_region, jornada="Todas"):
    
    params = {
        "cod_inst": cod_inst,
        "cohorte": cohorte_sel,
        "jornada": jornada,
        "cod_reg": cod_region
    }

    # Filtro dinámico para jornada
    filtro_jornada = "AND m.jornada = :jornada" if jornada != "Todas" else ""

    sql_query = text(f"""
    WITH universo_ies AS (
        SELECT DISTINCT mrun
        FROM tabla_matriculas_competencia_unificada m
        WHERE m.cod_inst = :cod_inst
          AND m.cohorte = :cohorte
          {filtro_jornada}
    ),
    ultimo_egreso_geo AS (
        -- Obtenemos el registro más reciente para cada alumno
        SELECT 
            mrun,
            cod_region,
            cod_comuna,
            nomb_comuna,
            ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY periodo DESC) as rn
        FROM tabla_alumnos_egresados_unificada
    )
    SELECT 
        e.cod_comuna,
        e.nomb_comuna,
        COUNT(u.mrun) AS cantidad_estudiantes
    FROM universo_ies u
    INNER JOIN ultimo_egreso_geo e ON u.mrun = e.mrun
    WHERE e.rn = 1 
      AND e.cod_region = :cod_reg
    GROUP BY e.cod_comuna, e.nomb_comuna
    ORDER BY cantidad_estudiantes DESC
    """)

    df = pd.read_sql(sql_query, db_engine, params=params)

    if not df.empty:
        # Cálculo de porcentaje respecto al total de la región filtrada
        total_region = df['cantidad_estudiantes'].sum()
        df['porcentaje_reg'] = (df['cantidad_estudiantes'] / total_region * 100).round(2)
    
    return df

def get_data_geografica_unificada(cohorte_sel, cod_inst, jornada="Todas"):
    params = {
        "cod_inst": cod_inst,
        "cohorte": cohorte_sel,
        "jornada": jornada
    }

    filtro_jornada = "AND m.jornada = :jornada" if jornada != "Todas" else ""

    sql_query = text(f"""
    WITH universo_ies AS (
        SELECT DISTINCT mrun FROM tabla_matriculas_competencia_unificada m
        WHERE m.cod_inst = :cod_inst AND m.cohorte = :cohorte {filtro_jornada}
    ),
    ultimo_egreso AS (
        SELECT 
            mrun, cod_region, nomb_region, cod_provincia, cod_comuna, nomb_comuna,
            ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY periodo DESC) as rn
        FROM tabla_alumnos_egresados_unificada
    )
    SELECT 
        e.cod_region, e.nomb_region, e.cod_provincia, e.cod_comuna, e.nomb_comuna,
        COUNT(u.mrun) AS cantidad
    FROM universo_ies u
    INNER JOIN ultimo_egreso e ON u.mrun = e.mrun
    WHERE e.rn = 1
    GROUP BY e.cod_region, e.nomb_region, e.cod_provincia, e.cod_comuna, e.nomb_comuna
    """)

    return pd.read_sql(sql_query, db_engine, params=params)

def get_kpi_ruralidad_seguimiento(cohorte_sel, cod_inst, jornada="Todas", genero="Todos"):
    
    params = {
        "cohorte": cohorte_sel,
        "cohorte_next": cohorte_sel + 1,
        "cod_inst": cod_inst,
        "jornada": jornada,
        "genero": genero
    }

    # Filtros dinámicos
    filtro_jornada = "AND m.jornada = :jornada" if jornada != "Todas" else ""
    filtro_genero = "AND m.genero = :genero" if genero != "Todos" else ""

    sql_query = text(f"""
    WITH UniversoIngreso AS (
        -- Alumnos que entraron en la cohorte seleccionada
        SELECT DISTINCT mrun
        FROM tabla_matriculas_competencia_unificada m
        WHERE m.cod_inst = :cod_inst
          AND m.cohorte = :cohorte
          {filtro_jornada}
          {filtro_genero}
    ),
    CaracterizacionRural AS (
        -- Obtenemos el índice de ruralidad del último egreso
        SELECT * FROM (
            SELECT 
                mrun, 
                CAST(indice_rural AS INT) as cod_rural,
                ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY periodo DESC) as rn
            FROM tabla_alumnos_egresados_unificada
        ) e_sub WHERE rn = 1
    ),
    Retencion AS (
        -- Verificamos si aparecen matriculados al año siguiente
        SELECT DISTINCT mrun
        FROM tabla_matriculas_competencia_unificada
        WHERE cohorte = :cohorte_next
    ),
    Titulación AS (
        -- Verificamos si el alumno llegó a titularse en la institución
        SELECT DISTINCT mrun
        FROM tabla_dashboard_titulados
        WHERE cod_inst = :cod_inst
    )
    SELECT 
        c.cod_rural,
        COUNT(u.mrun) as total_ingreso,
        -- Alumnos que NO están en la tabla de retención del año siguiente
        SUM(CASE WHEN r.mrun IS NULL THEN 1 ELSE 0 END) as desertores_1er_anio,
        -- Alumnos que SÍ están en la tabla de titulados
        SUM(CASE WHEN t.mrun IS NOT NULL THEN 1 ELSE 0 END) as total_titulados
    FROM UniversoIngreso u
    INNER JOIN CaracterizacionRural c ON u.mrun = c.mrun
    LEFT JOIN Retencion r ON u.mrun = r.mrun
    LEFT JOIN Titulación t ON u.mrun = t.mrun
    GROUP BY c.cod_rural
    """)

    df = pd.read_sql(sql_query, db_engine, params=params)

    if not df.empty:
        # Mapeo de Ruralidad
        map_rural = {0: "Urbano", 1: "Rural"}
        df['Zona'] = df['cod_rural'].map(map_rural).fillna("Sin Información")
        
        # Cálculos de Tasas
        df['Tasa Deserción 1er Año (%)'] = (df['desertores_1er_anio'] / df['total_ingreso'] * 100).round(1)
        df['Tasa Titulación Final (%)'] = (df['total_titulados'] / df['total_ingreso'] * 100).round(1)
        
        # Reordenar y limpiar
        df = df[['Zona', 'total_ingreso', 'desertores_1er_anio', 'Tasa Deserción 1er Año (%)', 'total_titulados', 'Tasa Titulación Final (%)']]
    
    return df


#print(get_kpi_ruralidad_seguimiento(cohorte_sel=, cod_inst=104))
#print(get_data_geografica_unificada(2020, 104))
#print(get_distribucion_comuna_egreso(2020, 104, 13))
#print(get_distribucion_provincial_egreso(2020, 104, 13))
#print(get_distribucion_regional_egreso(2020, 104))
#print(get_distribucion_dependencia_cohorte(cohorte_sel=2020, cod_inst=103))
#print(get_tasas_articulacion_tipo_establecimiento(cohorte_sel=2020, cod_inst=103))
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

def get_distribucion_dependencia_rango(cohorte_range, cod_inst, genero="Todos", jornada="Todas"):
    if isinstance(cohorte_range, list):
        c_inicio, c_fin = cohorte_range[0], cohorte_range[1]
        condicion_cohorte = "BETWEEN :c_inicio AND :c_fin"
        num_anios = (c_fin - c_inicio) + 1
    else:
        c_inicio, c_fin = cohorte_range, cohorte_range
        condicion_cohorte = "= :c_inicio"
        num_anios = 1

    params = {"c_inicio": c_inicio, "c_fin": c_fin, "cod_inst": cod_inst, "genero": genero}
    filtro_genero = "AND m.genero = :genero" if genero != "Todos" else ""

    sql_query = text(f"""
    WITH PrimerRegistroHistorico AS (
        -- Paso 1: Buscamos la fila con el PERIODO más antiguo (primer año de matrícula)
        SELECT * FROM (
            SELECT 
                mrun, 
                cohorte AS anio_ingreso, 
                jornada, 
                genero,
                periodo,
                ROW_NUMBER() OVER (
                    PARTITION BY mrun 
                    ORDER BY 
                        periodo ASC
                ) AS rn
            FROM tabla_matriculas_competencia_unificada
            WHERE cod_inst = :cod_inst
            {filtro_genero}
        ) t WHERE rn = 1
        ),
        EgresoMedia AS (
            -- Paso 2: Buscamos su colegio de egreso estable
            SELECT * FROM (
                SELECT 
                    mrun, cod_dep_agrupado,
                    ROW_NUMBER() OVER (
                        PARTITION BY mrun 
                        ORDER BY periodo DESC, cod_dep_agrupado ASC
                    ) AS rn_e
                FROM tabla_alumnos_egresados_unificada
            ) e_sub WHERE rn_e = 1
        )
        -- Paso 3: El filtro de cohorte se aplica sobre el anio_ingreso del primer registro
        SELECT 
            p.jornada,
            p.anio_ingreso,
            e.cod_dep_agrupado
        FROM PrimerRegistroHistorico p
        INNER JOIN EgresoMedia e ON p.mrun = e.mrun
        WHERE p.anio_ingreso {condicion_cohorte}
    """)

    df_raw = pd.read_sql(sql_query, db_engine, params=params)

    if df_raw.empty: return pd.DataFrame()

    if jornada != "Todas":
        df_raw = df_raw[df_raw['jornada'] == jornada]

    # 5. MAPEO Y RESUMEN
    dep_map = {1: 'Municipal', 2: 'Part. Subvencionado', 3: 'Part. Pagado', 
               4: 'Admin. Delegada', 5: 'SLEP'}

    df_raw['cod_dep_agrupado'] = pd.to_numeric(df_raw['cod_dep_agrupado'], errors='coerce').astype('Int64')
    df_raw['tipo_establecimiento'] = df_raw['cod_dep_agrupado'].map(dep_map).fillna('Otro / Sin información')
    
    df = df_raw.groupby('tipo_establecimiento').size().reset_index(name='total_periodo')
    df = df.sort_values('total_periodo', ascending=False)

    # 6. CÁLCULOS
    df['promedio_anual'] = (df['total_periodo'] / num_anios).round(1)
    total_absoluto = df['total_periodo'].sum()
    df['porcentaje'] = (df['total_periodo'] / total_absoluto * 100).round(1) if total_absoluto > 0 else 0
        
    return df

# print(get_distribucion_dependencia_rango(cohorte_range=[2007,2007], cod_inst=104, jornada='Diurna'))
# print(get_distribucion_dependencia_rango(cohorte_range=[2007,2007], cod_inst=104, jornada='Vespertina'))
# print(get_distribucion_dependencia_rango(cohorte_range=[2007,2007], cod_inst=104))

def get_titulados_por_dependencia_rango(cohorte_range, cod_inst, genero="Todos", jornada="Todas", anio_titulacion_sel=None):
    # 1. Configuración de Rango (Cohorte)
    if isinstance(cohorte_range, list):
        c_inicio, c_fin = cohorte_range[0], cohorte_range[1]
        condicion_cohorte = "BETWEEN :c_inicio AND :c_fin"
        num_anios = (c_fin - c_inicio) + 1
    else:
        c_inicio, c_fin = cohorte_range, cohorte_range
        condicion_cohorte = "= :c_inicio"
        num_anios = 1

    params = {"c_inicio": c_inicio, "c_fin": c_fin, "cod_inst": cod_inst, "genero": genero}
    
    # Filtros dinámicos para SQL
    filtro_anio_tit = "AND anio_titulacion = :anio_tit" if anio_titulacion_sel else ""
    if anio_titulacion_sel: params["anio_tit"] = anio_titulacion_sel
    filtro_genero = "AND genero = :genero" if genero != "Todos" else ""

    sql_query = text(f"""
    WITH PrimerIngresoEstable AS (
        -- Identidad de cohorte: Primera vez en la institución (104)
        SELECT * FROM (
            SELECT 
                mrun, cohorte as anio_ingreso,
                ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY periodo ASC) as rn_i
            FROM tabla_matriculas_competencia_unificada
            WHERE cod_inst = :cod_inst
        ) t_ing WHERE rn_i = 1
    ),
    UltimaInfoTitulado AS (
        -- Información al momento de titularse (incluye la jornada de titulación)
        SELECT * FROM (
            SELECT 
                mrun, jornada, anio_titulacion, genero,
                ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY anio_titulacion DESC) as rn_t
            FROM tabla_dashboard_titulados
            WHERE cod_inst = :cod_inst
            {filtro_anio_tit}
            {filtro_genero}
        ) t_tit WHERE rn_t = 1
    ),
    UltimoEgresoMedia AS (
        -- Origen escolar estable
        SELECT * FROM (
            SELECT 
                mrun, cod_dep_agrupado,
                ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY periodo DESC, cod_dep_agrupado ASC) as rn_e
            FROM tabla_alumnos_egresados_unificada
        ) e_sub WHERE rn_e = 1
    )
    SELECT 
        t.jornada, 
        e.cod_dep_agrupado,
        c.anio_ingreso
    FROM UltimaInfoTitulado t
    INNER JOIN PrimerIngresoEstable c ON t.mrun = c.mrun
    INNER JOIN UltimoEgresoMedia e ON t.mrun = e.mrun
    WHERE c.anio_ingreso {condicion_cohorte}
    """)
    
    df_raw = pd.read_sql(sql_query, db_engine, params=params)

    if df_raw.empty:
        return pd.DataFrame()

    # 2. FILTRAR JORNADA EN PANDAS (Priorizando la jornada de titulación traída de 't')
    if jornada != "Todas":
        df_raw = df_raw[df_raw['jornada'] == jornada]

    # 3. MAPEO Y RESUMEN
    dep_map = {1: 'Municipal', 2: 'Part. Subvencionado', 3: 'Part. Pagado', 
               4: 'Admin. Delegada', 5: 'SLEP'}
    
    df_raw['cod_dep_agrupado'] = pd.to_numeric(df_raw['cod_dep_agrupado'], errors='coerce').astype('Int64')
    df_raw['tipo_establecimiento'] = df_raw['cod_dep_agrupado'].map(dep_map).fillna('Otro / Sin Información')
    
    df = df_raw.groupby('tipo_establecimiento').size().reset_index(name='total_titulados_periodo')
    df = df.sort_values('total_titulados_periodo', ascending=False)

    # 4. CÁLCULOS
    df['promedio_anual_titulados'] = (df['total_titulados_periodo'] / num_anios).round(1)
    total_total = df['total_titulados_periodo'].sum()
    df['porcentaje_del_periodo'] = (df['total_titulados_periodo'] / total_total * 100).round(1) if total_total > 0 else 0
        
    return df

#print(get_titulados_por_dependencia_rango(cohorte_range=[2007,2007], cod_inst=104))

def get_titulados_por_dependencia_rango_jornada_ingreso(cohorte_range, cod_inst, genero="Todos", jornada="Todas", anio_titulacion_sel=None):
    # 1. Configuración de Rango (Cohorte)
    if isinstance(cohorte_range, list):
        c_inicio, c_fin = cohorte_range[0], cohorte_range[1]
        condicion_cohorte = "BETWEEN :c_inicio AND :c_fin"
        num_anios = (c_fin - c_inicio) + 1
    else:
        c_inicio, c_fin = cohorte_range, cohorte_range
        condicion_cohorte = "= :c_inicio"
        num_anios = 1

    params = {"c_inicio": c_inicio, "c_fin": c_fin, "cod_inst": cod_inst, "genero": genero}
    
    # Filtros dinámicos para SQL
    filtro_anio_tit = "AND anio_titulacion = :anio_tit" if anio_titulacion_sel else ""
    if anio_titulacion_sel: params["anio_tit"] = anio_titulacion_sel
    filtro_genero = "AND genero = :genero" if genero != "Todos" else ""

    sql_query = text(f"""
    WITH PrimerIngresoEstable AS (
        -- Identidad de cohorte y jornada de ORIGEN
        SELECT * FROM (
            SELECT 
                mrun, 
                cohorte as anio_ingreso,
                jornada as jornada_ingreso,
                ROW_NUMBER() OVER (
                    PARTITION BY mrun 
                    ORDER BY periodo ASC, jornada ASC
                ) as rn_i
            FROM tabla_matriculas_competencia_unificada
            WHERE cod_inst = :cod_inst
        ) t_ing WHERE rn_i = 1
    ),
    UltimaInfoTitulado AS (
        -- Identificamos quiénes se titularon
        SELECT * FROM (
            SELECT 
                mrun, anio_titulacion, genero,
                ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY anio_titulacion DESC) as rn_t
            FROM tabla_dashboard_titulados
            WHERE cod_inst = :cod_inst
            {filtro_anio_tit}
            {filtro_genero}
        ) t_tit WHERE rn_t = 1
    ),
    UltimoEgresoMedia AS (
        -- Origen escolar estable
        SELECT * FROM (
            SELECT 
                mrun, cod_dep_agrupado,
                ROW_NUMBER() OVER (
                    PARTITION BY mrun 
                    ORDER BY periodo DESC, cod_dep_agrupado ASC
                ) as rn_e
            FROM tabla_alumnos_egresados_unificada
        ) e_sub WHERE rn_e = 1
    )
    SELECT 
        c.jornada_ingreso AS jornada, -- <--- CAMBIO CLAVE: Usamos la de ingreso
        e.cod_dep_agrupado,
        c.anio_ingreso
    FROM UltimaInfoTitulado t
    INNER JOIN PrimerIngresoEstable c ON t.mrun = c.mrun
    INNER JOIN UltimoEgresoMedia e ON t.mrun = e.mrun
    WHERE c.anio_ingreso {condicion_cohorte}
    """)
    
    df_raw = pd.read_sql(sql_query, db_engine, params=params)

    if df_raw.empty:
        return pd.DataFrame()

    # 2. FILTRAR JORNADA EN PANDAS
    # Ahora el filtro 'Vespertina' evaluará si el alumno ENTRÓ en Vespertina
    if jornada != "Todas":
        df_raw = df_raw[df_raw['jornada'] == jornada]

    # 3. MAPEO Y RESUMEN
    dep_map = {1: 'Municipal', 2: 'Part. Subvencionado', 3: 'Part. Pagado', 
               4: 'Admin. Delegada', 5: 'SLEP'}
    
    df_raw['cod_dep_agrupado'] = pd.to_numeric(df_raw['cod_dep_agrupado'], errors='coerce').astype('Int64')
    df_raw['tipo_establecimiento'] = df_raw['cod_dep_agrupado'].map(dep_map).fillna('Otro / Sin Información')
    
    df = df_raw.groupby('tipo_establecimiento').size().reset_index(name='total_titulados_periodo')
    df = df.sort_values('total_titulados_periodo', ascending=False)

    # 4. CÁLCULOS
    df['promedio_anual_titulados'] = (df['total_titulados_periodo'] / num_anios).round(1)
    total_total = df['total_titulados_periodo'].sum()
    df['porcentaje_del_periodo'] = (df['total_titulados_periodo'] / total_total * 100).round(1) if total_total > 0 else 0
        
    return df

#print(get_titulados_por_dependencia_rango_jornada_ingreso(cohorte_range=[2007,2007], cod_inst=104))

def get_demora_ingreso_total(cohorte_range, cod_inst, carrera="Todas", genero="Todos", jornada="Todas"):
    # 1. Configuración de Rango
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

    # Filtros dinámicos (se mantienen en SQL para optimizar, pero sobre la base estable)
    filtro_carrera = "AND p.nomb_carrera = :carrera" if carrera != "Todas" else ""
    filtro_genero = "AND p.genero = :genero" if genero != "Todos" else ""
    
    sql_query = text(f"""
    WITH PrimerIngresoInstitucion AS (
        -- Buscamos el primer registro histórico REAL en la institución 104
        SELECT * FROM (
            SELECT 
                mrun, 
                cohorte as anio_ingreso,
                jornada,
                nomb_carrera,
                genero,
                periodo,
                ROW_NUMBER() OVER (
                    PARTITION BY mrun 
                    ORDER BY 
                        periodo ASC,       -- El primer año que pisó la ECAS
                        jornada ASC        -- Desempate estable
                ) as rn_ingreso
            FROM tabla_matriculas_competencia_unificada
            WHERE cod_inst = :cod_inst
        ) t WHERE rn_ingreso = 1
    ),
    UltimoEgresoMedia AS (
        -- Registro de egreso de media más reciente (estabilidad total)
        SELECT * FROM (
            SELECT 
                mrun, periodo,
                ROW_NUMBER() OVER (
                    PARTITION BY mrun 
                    ORDER BY periodo DESC, cod_dep_agrupado ASC
                ) as rn
            FROM tabla_alumnos_egresados_unificada
        ) e_sub WHERE rn = 1
    )
    SELECT 
        p.jornada,
        p.anio_ingreso,
        e.periodo as anio_egreso_media,
        (p.anio_ingreso - CAST(e.periodo AS INT)) as anios_demora,
        p.mrun
    FROM PrimerIngresoInstitucion p
    INNER JOIN UltimoEgresoMedia e ON p.mrun = e.mrun
    WHERE p.anio_ingreso {condicion_cohorte}
      {filtro_carrera}
      {filtro_genero}
    """)
    
    df_raw = pd.read_sql(sql_query, db_engine, params=params)

    if df_raw.empty:
        return pd.DataFrame()

    # 2. FILTRAR JORNADA EN PANDAS
    # Usamos la jornada capturada en el primer periodo en la ECAS
    if jornada != "Todas":
        df_raw = df_raw[df_raw['jornada'] == jornada]

    # Limpieza de datos: solo demoras positivas (>= 0)
    # Nota: Usamos >= 0 porque algunos entran el mismo año que egresan
    df = df_raw[df_raw['anios_demora'] >= 0].copy()
    
    if df.empty:
        return pd.DataFrame()

    # 3. AGRUPAR Y CONTAR
    resumen = df.groupby('anios_demora').size().reset_index(name='total_alumnos_periodo')
    
    # 4. CÁLCULOS ESTADÍSTICOS
    total = resumen['total_alumnos_periodo'].sum()
    resumen['porcentaje'] = (resumen['total_alumnos_periodo'] / total * 100).round(2)
    
    # Ordenar por años de demora para el gráfico
    resumen = resumen.sort_values('anios_demora')
    
    return resumen

#print(get_demora_ingreso_total(cohorte_range=[2007,2007], cod_inst=104, jornada='Vespertina'))

#KPI para analizar si los alumnos con un buen rendimiento academico en su educación media
#son más o menos probables de desertar al primer año.
def get_correlacion_nem_persistencia_rango(cohorte_range, cod_inst, jornada="Todas", carrera="Todas", genero="Todos"):
    # 1. Manejo de Rango de Cohorte
    if isinstance(cohorte_range, list):
        c_inicio, c_fin = cohorte_range[0], cohorte_range[1]
        condicion_cohorte = "BETWEEN :c_inicio AND :c_fin"
    else:
        c_inicio, c_fin = cohorte_range, cohorte_range
        condicion_cohorte = "= :c_inicio"

    params = {
        "c_inicio": c_inicio,
        "c_fin": c_fin,
        "cod_inst": cod_inst
    }

    sql_query = text(f"""
    WITH PrimerIngresoInstitucion AS (
        -- Identidad de ingreso: Primera matrícula en la institución
        SELECT * FROM (
            SELECT 
                mrun, 
                cohorte as anio_ingreso,
                jornada,
                nomb_carrera,
                genero,
                periodo,
                ROW_NUMBER() OVER (
                    PARTITION BY mrun 
                    ORDER BY periodo ASC, jornada ASC
                ) as rn_ingreso
            FROM tabla_matriculas_competencia_unificada
            WHERE cod_inst = :cod_inst
        ) t WHERE rn_ingreso = 1
    ),
    UniversoValido AS (
        -- Alumnos que pertenecen al rango de cohortes seleccionado
        SELECT mrun, anio_ingreso, jornada, nomb_carrera, genero
        FROM PrimerIngresoInstitucion
        WHERE anio_ingreso {condicion_cohorte}
    ),
    PromediosNEM AS (
        -- Promedio histórico de notas de enseñanza media
        SELECT 
            mrun, 
            AVG(CAST(REPLACE(prom_notas_alu, ',', '.') AS FLOAT)) as nem_valor
        FROM tabla_alumnos_egresados_unificada
        GROUP BY mrun
    ),
    Persistencia AS (
        -- Cruce con T+1: Verificamos si existe matrícula en el periodo inmediatamente posterior al ingreso
        SELECT 
            u.mrun,
            u.jornada,
            u.nomb_carrera,
            u.genero,
            n.nem_valor,
            CASE WHEN m.mrun IS NOT NULL THEN 1 ELSE 0 END as sigue_estudiando
        FROM UniversoValido u
        INNER JOIN PromediosNEM n ON u.mrun = n.mrun
        LEFT JOIN tabla_matriculas_competencia_unificada m ON u.mrun = m.mrun 
            -- La persistencia es individual: el periodo debe ser el ingreso + 1
            AND m.periodo = (u.anio_ingreso + 1)
            AND m.cod_inst = :cod_inst
    )
    SELECT * FROM Persistencia
    """)
    
    df_raw = pd.read_sql(sql_query, db_engine, params=params)

    if df_raw.empty:
        return pd.DataFrame()

    # 2. FILTROS EN PANDAS
    df = df_raw.copy()
    if jornada != "Todas":
        df = df[df['jornada'] == jornada]
    if carrera != "Todas":
        df = df[df['nomb_carrera'] == carrera]
    if genero != "Todos":
        df = df[df['genero'] == genero]

    if df.empty:
        return pd.DataFrame()

    # 3. CATEGORIZACIÓN NEM
    def categorizar_nem(nota):
        if nota < 5.0: return '4.0 - 4.9'
        if nota < 5.5: return '5.0 - 5.4'
        if nota < 6.0: return '5.5 - 5.9'
        if nota < 6.5: return '6.0 - 6.4'
        return '6.5 - 7.0'

    df['rango_nem'] = df['nem_valor'].apply(categorizar_nem)

    # 4. RESUMEN FINAL
    resumen = df.groupby('rango_nem').agg(
        total_alumnos=('mrun', 'count'),
        cantidad_persisten=('sigue_estudiando', 'sum')
    ).reset_index()

    resumen['tasa_persistencia'] = (resumen['cantidad_persisten'] / resumen['total_alumnos'] * 100).round(1)
    resumen = resumen.sort_values('rango_nem')

    return resumen


#print(get_correlacion_nem_persistencia_rango(cohorte_range=[2007,2007], cod_inst=104, jornada='Vespertina'))

def get_correlacion_nem_titulacion_rango(cohorte_range, cod_inst, jornada="Todas", carrera="Todas", genero="Todos"):
    # 1. Configuración de Rango de Cohorte
    if isinstance(cohorte_range, list):
        c_inicio, c_fin = cohorte_range[0], cohorte_range[1]
        condicion_cohorte = "BETWEEN :c_inicio AND :c_fin"
    else:
        c_inicio, c_fin = cohorte_range, cohorte_range
        condicion_cohorte = "= :c_inicio"

    params = {
        "c_inicio": c_inicio,
        "c_fin": c_fin,
        "cod_inst": cod_inst
    }

    sql_query = text(f"""
    WITH PrimerIngresoInstitucion AS (
        -- Identidad de ingreso: Primera matrícula en la institución (104)
        SELECT * FROM (
            SELECT 
                mrun, 
                cohorte as anio_ingreso,
                jornada,
                nomb_carrera,
                genero,
                periodo,
                CAST(dur_total_carr AS INT) / 2.0 as duracion_formal_anios,
                ROW_NUMBER() OVER (
                    PARTITION BY mrun 
                    ORDER BY periodo ASC, jornada ASC
                ) as rn_ingreso
            FROM tabla_matriculas_competencia_unificada
            WHERE cod_inst = :cod_inst
        ) t WHERE rn_ingreso = 1
    ),
    UniversoValido AS (
        -- Filtramos por el rango de cohortes (Identidad fija)
        SELECT mrun, anio_ingreso, jornada, nomb_carrera, genero, duracion_formal_anios
        FROM PrimerIngresoInstitucion
        WHERE anio_ingreso {condicion_cohorte}
    ),
    PromediosNEM AS (
        -- NEM promedio histórico
        SELECT 
            mrun, 
            AVG(CAST(REPLACE(prom_notas_alu, ',', '.') AS FLOAT)) as nem_valor
        FROM tabla_alumnos_egresados_unificada
        GROUP BY mrun
    ),
    DatosTitulacion AS (
        -- Cruzamos Universo de Ingreso con la tabla de Titulados
        SELECT 
            u.mrun,
            u.jornada,
            u.nomb_carrera,
            u.genero,
            n.nem_valor,
            u.duracion_formal_anios,
            t.anio_titulacion,
            -- Calculamos duración real basándonos en el año de ingreso institucional
            (t.anio_titulacion - u.anio_ingreso) as duracion_real_anios
        FROM UniversoValido u
        INNER JOIN PromediosNEM n ON u.mrun = n.mrun
        INNER JOIN (
            -- Obtenemos el registro de titulación más reciente por si acaso
            SELECT mrun, anio_titulacion, 
                   ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY anio_titulacion DESC) as rn_t
            FROM tabla_dashboard_titulados
            WHERE cod_inst = :cod_inst
        ) t ON u.mrun = t.mrun AND t.rn_t = 1
    )
    SELECT * FROM DatosTitulacion
    """)
    
    df_raw = pd.read_sql(sql_query, db_engine, params=params)

    if df_raw.empty:
        return pd.DataFrame()

    # 2. FILTROS EN PANDAS (Sobre datos de INGRESO)
    df = df_raw.copy()
    if jornada != "Todas":
        df = df[df['jornada'] == jornada]
    if carrera != "Todas":
        df = df[df['nomb_carrera'] == carrera]
    if genero != "Todos":
        df = df[df['genero'] == genero]

    if df.empty:
        return pd.DataFrame()

    # 3. CLASIFICACIÓN Y CATEGORIZACIÓN
    def categorizar_nem(nota):
        if nota < 5.0: return '4.0 - 4.9'
        if nota < 5.5: return '5.0 - 5.4'
        if nota < 6.0: return '5.5 - 5.9'
        if nota < 6.5: return '6.0 - 6.4'
        return '6.5 - 7.0'

    df['rango_nem'] = df['nem_valor'].apply(categorizar_nem)
    
    # La titulación es oportuna si la duración real es menor o igual a la formal
    df['es_oportuna'] = (df['duracion_real_anios'] <= df['duracion_formal_anios']).astype(int)

    # 4. RESUMEN FINAL
    resumen = df.groupby('rango_nem').agg(
        total_titulados=('mrun', 'count'),
        titulados_a_tiempo=('es_oportuna', 'sum')
    ).reset_index()

    resumen['tasa_titulacion_oportuna'] = (resumen['titulados_a_tiempo'] / resumen['total_titulados'] * 100).round(1)
    resumen = resumen.sort_values('rango_nem')

    return resumen

#print(get_correlacion_nem_titulacion_rango(cohorte_range=[2007,2025], cod_inst=104))

def get_tasas_articulacion_tipo_establecimiento_rango(cohorte_range, cod_inst, jornada="Todas", carrera="Todas", genero="Todos"):
    # 1. Configuración de Rango de Cohorte
    if isinstance(cohorte_range, list):
        c_inicio, c_fin = cohorte_range[0], cohorte_range[1]
        condicion_cohorte = "BETWEEN :c_inicio AND :c_fin"
    else:
        c_inicio, c_fin = cohorte_range, cohorte_range
        condicion_cohorte = "= :c_inicio"

    # Diccionario de parámetros
    params = {
        "cod_inst": cod_inst,
        "c_inicio": c_inicio,
        "c_fin": c_fin
    }

    # Aseguramos que el código 0 sea visible en el mapeo
    map_ensenianza_full = map_ensenianza.copy()
    map_ensenianza_full[0] = "Media - Modalidad no registrada"

    sql_query = text(f"""
    WITH PrimerIngresoInstitucion AS (
        -- Identidad de ingreso: Primera matrícula en la institución (104)
        SELECT * FROM (
            SELECT 
                mrun, 
                cohorte as anio_ingreso,
                jornada,
                nomb_carrera,
                genero,
                periodo,
                ROW_NUMBER() OVER (
                    PARTITION BY mrun 
                    ORDER BY periodo ASC, jornada ASC
                ) as rn_ingreso
            FROM tabla_matriculas_competencia_unificada
            WHERE cod_inst = :cod_inst
        ) t WHERE rn_ingreso = 1
    ),
    UniversoValido AS (
        -- Filtramos por el rango de cohortes capturado en el ingreso
        SELECT mrun, anio_ingreso, jornada, nomb_carrera, genero
        FROM PrimerIngresoInstitucion
        WHERE anio_ingreso {condicion_cohorte}
    ),
    EgresoOrdenado AS (
        -- Información escolar estable (Último egreso de media registrado)
        SELECT * FROM (
            SELECT
                mrun,
                COALESCE(NULLIF(TRIM(CAST(cod_ensenianza AS VARCHAR(10))), ''), '0') AS cod_ense_clean,
                CAST(REPLACE(prom_notas_alu, ',', '.') AS FLOAT) AS prom_notas,
                ROW_NUMBER() OVER (
                    PARTITION BY mrun
                    ORDER BY periodo DESC
                ) AS rn_e
            FROM tabla_alumnos_egresados_unificada
        ) e_sub WHERE rn_e = 1
    )
    SELECT
        u.mrun,
        u.jornada,
        u.nomb_carrera,
        u.genero,
        e.cod_ense_clean,
        e.prom_notas AS prom_notas_media
    FROM UniversoValido u
    INNER JOIN EgresoOrdenado e ON u.mrun = e.mrun
    """)

    df_raw = pd.read_sql(sql_query, db_engine, params=params)

    if df_raw.empty:
        return pd.DataFrame()

    # 2. FILTROS EN PANDAS (Sobre datos de ingreso institucional)
    df = df_raw.copy()
    if jornada != "Todas":
        df = df[df['jornada'] == jornada]
    if carrera != "Todas":
        df = df[df['nomb_carrera'] == carrera]
    if genero != "Todos":
        df = df[df['genero'] == genero]

    if df.empty:
        return pd.DataFrame()

    # 3. PROCESAMIENTO Y MAPEO
    df['cod_ense_clean'] = pd.to_numeric(df['cod_ense_clean'], errors='coerce').fillna(0).astype(int)
    
    df['nomb_ensenianza'] = (
        df['cod_ense_clean']
        .map(map_ensenianza_full)
        .fillna("Media - Modalidad no registrada")
    )

    # 4. AGRUPACIÓN (KPI)
    kpi = df.groupby('nomb_ensenianza').agg({
        'mrun': 'count',
        'prom_notas_media': 'mean'
    }).reset_index()

    kpi.columns = ['Tipo Enseñanza', 'Cant. Estudiantes', 'Promedio Notas']
    kpi['Promedio Notas'] = kpi['Promedio Notas'].round(2)
    kpi = kpi.sort_values('Cant. Estudiantes', ascending=False)

    return kpi

#print(get_tasas_articulacion_tipo_establecimiento_rango(cohorte_range=[2007,2007], cod_inst=104))

def get_data_geografica_unificada_rango(cohorte_range, cod_inst, jornada="Todas", genero="Todos"):
    # 1. Manejo de Rango de Cohorte
    if isinstance(cohorte_range, list):
        c_inicio, c_fin = cohorte_range[0], cohorte_range[1]
        condicion_cohorte = "BETWEEN :c_inicio AND :c_fin"
    else:
        c_inicio, c_fin = cohorte_range, cohorte_range
        condicion_cohorte = "= :c_inicio"

    params = {
        "cod_inst": cod_inst,
        "c_inicio": c_inicio,
        "c_fin": c_fin
    }

    sql_query = text(f"""
    WITH PrimerIngresoInstitucion AS (
        -- Identidad de ingreso: Capturamos jornada y género de la primera matrícula
        SELECT * FROM (
            SELECT 
                mrun, 
                cohorte as anio_ingreso,
                jornada,
                genero,
                periodo,
                ROW_NUMBER() OVER (
                    PARTITION BY mrun 
                    ORDER BY periodo ASC, jornada ASC
                ) as rn_ingreso
            FROM tabla_matriculas_competencia_unificada
            WHERE cod_inst = :cod_inst
        ) t WHERE rn_ingreso = 1
    ),
    UniversoValido AS (
        -- Alumnos dentro del rango de cohortes
        SELECT mrun, jornada, genero
        FROM PrimerIngresoInstitucion
        WHERE anio_ingreso {condicion_cohorte}
    ),
    UltimoEgreso AS (
        -- Ubicación geográfica del último registro de enseñanza media
        SELECT * FROM (
            SELECT 
                mrun, cod_region, nomb_region, cod_provincia, cod_comuna, nomb_comuna,
                ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY periodo DESC) as rn_e
            FROM tabla_alumnos_egresados_unificada
        ) e_sub WHERE rn_e = 1
    )
    SELECT 
        e.cod_region, e.nomb_region, e.cod_provincia, e.cod_comuna, e.nomb_comuna,
        u.jornada,
        u.genero,
        COUNT(u.mrun) AS cantidad
    FROM UniversoValido u
    INNER JOIN UltimoEgreso e ON u.mrun = e.mrun
    GROUP BY e.cod_region, e.nomb_region, e.cod_provincia, e.cod_comuna, e.nomb_comuna, u.jornada, u.genero
    """)

    df_raw = pd.read_sql(sql_query, db_engine, params=params)

    if df_raw.empty:
        return pd.DataFrame()

    # 2. FILTROS EN PANDAS (Sobre la identidad de ingreso)
    df = df_raw.copy()
    if jornada != "Todas":
        df = df[df['jornada'] == jornada]
    
    if genero != "Todos":
        df = df[df['genero'] == genero]

    # 3. AGRUPACIÓN FINAL
    resumen = df.groupby(['cod_region', 'nomb_region', 'cod_provincia', 'cod_comuna', 'nomb_comuna'])['cantidad'].sum().reset_index()
    
    return resumen

#print(get_data_geografica_unificada_rango(cohorte_range=[2007,2025], cod_inst=104))

def get_kpi_ruralidad_seguimiento_rango(cohorte_range, cod_inst, jornada="Todas", genero="Todos"):
    # 1. Configuración de Rango de Cohorte
    if isinstance(cohorte_range, list):
        c_inicio, c_fin = cohorte_range[0], cohorte_range[1]
        condicion_cohorte = "BETWEEN :c_inicio AND :c_fin"
    else:
        c_inicio, c_fin = cohorte_range, cohorte_range
        condicion_cohorte = "= :c_inicio"

    params = {
        "cod_inst": cod_inst,
        "c_inicio": c_inicio,
        "c_fin": c_fin
    }

    sql_query = text(f"""
    WITH PrimerIngreso AS (
        -- Identidad de ingreso: capturamos datos de la primera matrícula en la institución
        SELECT * FROM (
            SELECT 
                mrun, 
                cohorte as anio_ingreso, 
                jornada, 
                genero, 
                periodo,
                ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY periodo ASC) as rn_i
            FROM tabla_matriculas_competencia_unificada
            WHERE cod_inst = :cod_inst
        ) t WHERE rn_i = 1
    ),
    UniversoValido AS (
        -- Filtramos por el rango de cohortes solicitado
        SELECT mrun, anio_ingreso, jornada, genero
        FROM PrimerIngreso
        WHERE anio_ingreso {condicion_cohorte}
    ),
    CaracterizacionRural AS (
        -- Índice de ruralidad del último egreso de enseñanza media
        SELECT * FROM (
            SELECT 
                mrun, 
                CAST(indice_rural AS INT) as cod_rural,
                ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY periodo DESC) as rn_e
            FROM tabla_alumnos_egresados_unificada
        ) e_sub WHERE rn_e = 1
    ),
    Persistencia AS (
        -- Verificamos si el alumno registra matrícula en el año T+1 (en la misma institución)
        SELECT DISTINCT m.mrun, m.periodo
        FROM tabla_matriculas_competencia_unificada m
        WHERE m.cod_inst = :cod_inst
    ),
    Titulacion AS (
        -- Verificamos si el alumno figura en la tabla maestra de titulados
        SELECT DISTINCT mrun FROM tabla_dashboard_titulados WHERE cod_inst = :cod_inst
    )
    SELECT 
        u.mrun, 
        u.jornada, 
        u.genero,
        c.cod_rural,
        -- Deserción: 1 si NO se encontró matrícula en ingreso + 1
        CASE WHEN p.mrun IS NULL THEN 1 ELSE 0 END as es_desertor_1er_anio,
        -- Titulación: 1 si existe en la tabla de titulados
        CASE WHEN t.mrun IS NOT NULL THEN 1 ELSE 0 END as es_titulado
    FROM UniversoValido u
    INNER JOIN CaracterizacionRural c ON u.mrun = c.mrun
    LEFT JOIN Persistencia p ON u.mrun = p.mrun AND p.periodo = (u.anio_ingreso + 1)
    LEFT JOIN Titulacion t ON u.mrun = t.mrun
    """)

    df_raw = pd.read_sql(sql_query, db_engine, params=params)

    if df_raw.empty:
        return pd.DataFrame()

    # 2. FILTROS EN PANDAS (Sobre la identidad de ingreso)
    df = df_raw.copy()
    if jornada != "Todas":
        df = df[df['jornada'] == jornada]
    if genero != "Todos":
        df = df[df['genero'] == genero]

    if df.empty:
        return pd.DataFrame()

    # 3. AGRUPACIÓN Y CÁLCULO DE TASAS
    resumen = df.groupby('cod_rural').agg(
        total_ingreso=('mrun', 'count'),
        desertores_1er_anio=('es_desertor_1er_anio', 'sum'),
        total_titulados=('es_titulado', 'sum')
    ).reset_index()

    # Mapeo de Zona
    map_rural = {0: "Urbano", 1: "Rural"}
    resumen['Zona'] = resumen['cod_rural'].map(map_rural).fillna("Sin Información")
    
    # Cálculos finales
    resumen['Tasa Deserción 1er Año (%)'] = (resumen['desertores_1er_anio'] / resumen['total_ingreso'] * 100).round(1)
    resumen['Tasa Titulación Final (%)'] = (resumen['total_titulados'] / resumen['total_ingreso'] * 100).round(1)
    
    # Ordenar columnas para el Dashboard
    columnas_finales = [
        'Zona', 'total_ingreso', 'desertores_1er_anio', 
        'Tasa Deserción 1er Año (%)', 'total_titulados', 'Tasa Titulación Final (%)'
    ]
    
    return resumen[columnas_finales].sort_values('total_ingreso', ascending=False)

#print(get_kpi_ruralidad_seguimiento_rango(cohorte_range=[2007,2007], cod_inst=104)){

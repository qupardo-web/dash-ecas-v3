from conn_db import get_db_engine
from sqlalchemy import text
import pandas as pd
from typing import Optional, List

db_engine = get_db_engine()

map_ensenianza = {
    310: "Cientifico Humanista",
    360: "Cientifico Humanista Vespertino",
    361: "Cientifico Humanista Adultos",
    362: "Escuelas Cárceles (Media Adultos)",
    363: "Cientifico Humanista Adultos D.1000",
    410: "Comercial",
    460: "Comercial Adultos D.152",
    461: "Comercial Adultos D.152",
    463: "Comercial Adultos D.1000",
    510: "Industrial",
    560: "Industrial Adultos D.152",
    561: "Industrial Adultos D.152",
    563: "Industrial Adultos D.1000",
    610: "Tecnica",
    660: "Tecnica Adultos D.152",
    661: "Tecnica Adultos D.152",
    663: "Tecnica Adultos D.1000",
    710: "Agricola",
    760: "Agricola Adultos D.152",
    761: "Agricola Adultos D.152",
    763: "Agricola Adultos D.1000",
    810: "Maritima",
    860: "Maritima Adultos D.152",
    863: "Maritima Adultos D.1000",
    910: "Artistica",
    963: "Artistica Adultos"
}

map_provincias_rm = {
    131: "Provincia de Santiago",
    132: "Provincia de Cordillera",
    133: "Provincia de Chacabuco",
    134: "Provincia de Maipo",
    135: "Provincia de Melipilla",
    136: "Provincia de Talagante"
}

def get_total_titulados_y_matriculados(cohorte_range, cod_inst, jornada="Todas", genero="Todos", region_id=None):
    params = {
        "cod_inst": cod_inst,
        "c_inicio": cohorte_range[0] if isinstance(cohorte_range, list) else cohorte_range,
        "c_fin": cohorte_range[1] if isinstance(cohorte_range, list) else cohorte_range,
        "jornada": jornada,
        "genero": genero,
        "region": region_id
    }

    # Filtros dinámicos consistentes
    filtro_jornada = "AND u.jornada = :jornada" if jornada != "Todas" else ""
    filtro_genero = "AND u.genero = :genero" if genero != "Todos" else ""
    filtro_region = "AND g.cod_region = :region" if region_id is not None else ""

    sql_query = text(f"""
    WITH UniversoMatricula AS (
        -- Identificamos el primer ingreso de cada alumno
        SELECT * FROM (
            SELECT mrun, cohorte as anio_ingreso, jornada, genero,
                   ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY periodo ASC) as rn
            FROM tabla_matriculas_competencia_unificada
            WHERE cod_inst = :cod_inst
        ) t WHERE rn = 1 AND anio_ingreso BETWEEN :c_inicio AND :c_fin
    ),
    Geolocalizacion AS (
        -- Obtenemos la última región conocida de egreso
        SELECT * FROM (
            SELECT mrun, cod_region,
                   ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY periodo DESC) as rn_geo
            FROM tabla_alumnos_egresados_unificada
        ) e WHERE rn_geo = 1
    )
    SELECT 
        COUNT(DISTINCT u.mrun) as total_m,
        COUNT(DISTINCT t.mrun) as total_t
    FROM UniversoMatricula u
    INNER JOIN Geolocalizacion g ON u.mrun = g.mrun
    LEFT JOIN tabla_dashboard_titulados t ON u.mrun = t.mrun AND t.cod_inst = :cod_inst
    WHERE 1=1 {filtro_jornada} {filtro_genero} {filtro_region}
    """)
    
    df = pd.read_sql(sql_query, db_engine, params=params)
    res = df.iloc[0] if not df.empty else {'total_m': 0, 'total_t': 0}
    return {"total_m": int(res['total_m']), "total_t": int(res['total_t'])}

def get_distribucion_dependencia_rango(cohorte_range, cod_inst, genero="Todos", jornada="Todas", region_id=None):
    
    if isinstance(cohorte_range, list):
        c_inicio, c_fin = cohorte_range[0], cohorte_range[1]
        condicion_cohorte = "BETWEEN :c_inicio AND :c_fin"
        num_anios = (c_fin - c_inicio) + 1
    else:
        c_inicio, c_fin = cohorte_range, cohorte_range
        condicion_cohorte = "= :c_inicio"
        num_anios = 1

    params = {"c_inicio": c_inicio, 
              "c_fin": c_fin, 
              "cod_inst": cod_inst, 
              "genero": genero,
              "region": region_id }

    filtro_genero = "AND genero = :genero" if genero != "Todos" else ""
    filtro_region = "AND e.cod_region = :region" if region_id != None else ""

    sql_query = text(f"""
    WITH PrimerRegistroHistorico AS (
        -- Paso 1: Buscamos el ingreso institucional validando existencia en egresados para geolocalización
        SELECT * FROM (
            SELECT 
                m.mrun, 
                m.cohorte AS anio_ingreso, 
                m.jornada, 
                m.genero,
                m.periodo,
                ROW_NUMBER() OVER (
                    PARTITION BY m.mrun 
                    ORDER BY m.periodo ASC
                ) AS rn
            FROM tabla_matriculas_competencia_unificada m
            INNER JOIN (
                SELECT mrun, cod_region,
                       ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY periodo DESC) as rn_geo
                FROM tabla_alumnos_egresados_unificada
            ) e ON m.mrun = e.mrun AND e.rn_geo = 1
            WHERE m.cod_inst = :cod_inst
            {filtro_genero}
            {filtro_region}
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
    -- Paso 3: Cruce final para obtener dependencia
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

#print(get_distribucion_dependencia_rango(cohorte_range=[2007,2007], cod_inst=104, jornada='Diurna'))
# print(get_distribucion_dependencia_rango(cohorte_range=[2007,2007], cod_inst=104, jornada='Vespertina'))
# print(get_distribucion_dependencia_rango(cohorte_range=[2007,2007], cod_inst=104))

def get_titulados_por_dependencia_rango(cohorte_range, cod_inst, genero="Todos", jornada="Todas", region_id=None, anio_titulacion_sel=None):
    # 1. Configuración de Rango (Cohorte)
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
        "region": region_id
    }
    
    # Filtros dinámicos
    filtro_anio_tit = "AND t.anio_titulacion = :anio_tit" if anio_titulacion_sel else ""
    if anio_titulacion_sel: params["anio_tit"] = anio_titulacion_sel
    
    filtro_genero = "AND m.genero = :genero" if genero != "Todos" else ""
    filtro_region = "AND geo.cod_region = :region" if region_id is not None else ""

    sql_query = text(f"""
    WITH GeolocalizacionEstable AS (
        -- Obtenemos la última región conocida de egreso para el filtrado geográfico
        SELECT * FROM (
            SELECT mrun, cod_region,
                   ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY periodo DESC) as rn_geo
            FROM tabla_alumnos_egresados_unificada
        ) e WHERE rn_geo = 1
    ),
    UniversoIngreso AS (
        -- Primera matrícula en la institución (cohorte real) cruzada con geolocalización
        SELECT * FROM (
            SELECT 
                m.mrun, m.cohorte as anio_ingreso,
                ROW_NUMBER() OVER (PARTITION BY m.mrun ORDER BY m.periodo ASC) as rn_i
            FROM tabla_matriculas_competencia_unificada m
            INNER JOIN GeolocalizacionEstable geo ON m.mrun = geo.mrun
            WHERE m.cod_inst = :cod_inst
              {filtro_genero}
              {filtro_region}
        ) t_ing WHERE rn_i = 1
    ),
    UltimaInfoTitulado AS (
        -- Identificamos a los titulados dentro del universo filtrado
        SELECT 
            t.mrun, t.jornada, t.anio_titulacion
        FROM tabla_dashboard_titulados t
        WHERE t.cod_inst = :cod_inst
          {filtro_anio_tit}
    ),
    OrigenEscolar AS (
        -- Dependencia administrativa del colegio de egreso
        SELECT * FROM (
            SELECT 
                mrun, cod_dep_agrupado,
                ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY periodo DESC, cod_dep_agrupado ASC) as rn_e
            FROM tabla_alumnos_egresados_unificada
        ) e_sub WHERE rn_e = 1
    )
    SELECT 
        tit.jornada, 
        esc.cod_dep_agrupado,
        uni.anio_ingreso
    FROM UltimaInfoTitulado tit
    INNER JOIN UniversoIngreso uni ON tit.mrun = uni.mrun
    INNER JOIN OrigenEscolar esc ON tit.mrun = esc.mrun
    WHERE uni.anio_ingreso {condicion_cohorte}
    """)
    
    df_raw = pd.read_sql(sql_query, db_engine, params=params)

    if df_raw.empty:
        return pd.DataFrame()

    # 2. Filtrar Jornada (Priorizando jornada de titulación)
    if jornada != "Todas":
        df_raw = df_raw[df_raw['jornada'] == jornada]

    if df_raw.empty:
        return pd.DataFrame()

    # 3. Mapeo de Dependencia
    dep_map = {1: 'Municipal', 2: 'Part. Subvencionado', 3: 'Part. Pagado', 
                4: 'Admin. Delegada', 5: 'SLEP'}
    
    df_raw['cod_dep_agrupado'] = pd.to_numeric(df_raw['cod_dep_agrupado'], errors='coerce').astype('Int64')
    df_raw['tipo_establecimiento'] = df_raw['cod_dep_agrupado'].map(dep_map).fillna('Otro / Sin Información')
    
    # 4. Agrupación y Cálculos
    df = df_raw.groupby('tipo_establecimiento').size().reset_index(name='total_titulados_periodo')
    df = df.sort_values('total_titulados_periodo', ascending=False)

    df['promedio_anual_titulados'] = (df['total_titulados_periodo'] / num_anios).round(1)
    total_total = df['total_titulados_periodo'].sum()
    df['porcentaje_del_periodo'] = (df['total_titulados_periodo'] / total_total * 100).round(1) if total_total > 0 else 0
        
    return df

print(get_titulados_por_dependencia_rango(cohorte_range=[2007,2025], cod_inst=104))

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

def get_demora_ingreso_total(cohorte_range, cod_inst, carrera="Todas", genero="Todos", jornada="Todas", region_id=None):
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
        "genero": genero,
        "region": region_id
    }

    # Filtros dinámicos SQL
    filtro_carrera = "AND p.nomb_carrera = :carrera" if carrera != "Todas" else ""
    filtro_genero = "AND p.genero = :genero" if genero != "Todos" else ""
    filtro_region = "AND e_geo.cod_region = :region" if region_id != None else ""

    sql_query = text(f"""
    WITH PrimerIngresoInstitucion AS (
        -- Buscamos el ingreso validando que el alumno exista en egresados para tener región
        SELECT * FROM (
            SELECT 
                m.mrun, 
                m.cohorte as anio_ingreso,
                m.jornada,
                m.nomb_carrera,
                m.genero,
                m.periodo,
                ROW_NUMBER() OVER (
                    PARTITION BY m.mrun 
                    ORDER BY m.periodo ASC, m.jornada ASC
                ) as rn_ingreso
            FROM tabla_matriculas_competencia_unificada m
            INNER JOIN (
                SELECT mrun, cod_region,
                       ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY periodo DESC) as rn_geo
                FROM tabla_alumnos_egresados_unificada
            ) e_geo ON m.mrun = e_geo.mrun AND e_geo.rn_geo = 1
            WHERE m.cod_inst = :cod_inst
            {filtro_region}
        ) t WHERE rn_ingreso = 1
    ),
    UltimoEgresoMedia AS (
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
        return pd.DataFrame(columns=['anios_demora', 'total_alumnos_periodo', 'porcentaje'])

    # 2. FILTRAR JORNADA EN PANDAS
    if jornada != "Todas":
        df_raw = df_raw[df_raw['jornada'] == jornada]

    # Limpieza: solo demoras >= 0
    df = df_raw[df_raw['anios_demora'] >= 0].copy()
    
    if df.empty:
        return pd.DataFrame(columns=['anios_demora', 'total_alumnos_periodo', 'porcentaje'])

    # 3. AGRUPAR Y CONTAR
    resumen = df.groupby('anios_demora').size().reset_index(name='total_alumnos_periodo')
    
    # 4. CÁLCULOS ESTADÍSTICOS
    total = resumen['total_alumnos_periodo'].sum()
    resumen['porcentaje'] = (resumen['total_alumnos_periodo'] / total * 100).round(2)
    resumen = resumen.sort_values('anios_demora')
    
    return resumen
#print(get_demora_ingreso_total(cohorte_range=[2007,2007], cod_inst=104, jornada='Vespertina'))

#KPI para analizar si los alumnos con un buen rendimiento academico en su educación media
#son más o menos probables de desertar al primer año.
def get_correlacion_nem_persistencia_rango(cohorte_range, cod_inst, jornada="Todas", carrera="Todas", genero="Todos", region_id=None):
    
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
        "region" : region_id
    }

    # Filtro de región
    filtro_region = "AND e_geo.cod_region = :region" if region_id != None else ""

    sql_query = text(f"""
    WITH PrimerIngresoInstitucion AS (
        -- Identidad de ingreso: Validamos existencia en egresados para tener región
        SELECT * FROM (
            SELECT 
                m.mrun, 
                m.cohorte as anio_ingreso,
                m.jornada,
                m.nomb_carrera,
                m.genero,
                m.periodo,
                ROW_NUMBER() OVER (
                    PARTITION BY m.mrun 
                    ORDER BY m.periodo ASC, m.jornada ASC
                ) as rn_ingreso
            FROM tabla_matriculas_competencia_unificada m
            INNER JOIN (
                SELECT mrun, cod_region,
                       ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY periodo DESC) as rn_geo
                FROM tabla_alumnos_egresados_unificada
            ) e_geo ON m.mrun = e_geo.mrun AND e_geo.rn_geo = 1
            WHERE m.cod_inst = :cod_inst
            {filtro_region}
        ) t WHERE rn_ingreso = 1
    ),
    UniversoValido AS (
        SELECT mrun, anio_ingreso, jornada, nomb_carrera, genero
        FROM PrimerIngresoInstitucion
        WHERE anio_ingreso {condicion_cohorte}
    ),
    PromediosNEM AS (
        SELECT 
            mrun, 
            AVG(CAST(REPLACE(prom_notas_alu, ',', '.') AS FLOAT)) as nem_valor
        FROM tabla_alumnos_egresados_unificada
        GROUP BY mrun
    ),
    Persistencia AS (
        SELECT 
            u.mrun, u.jornada, u.nomb_carrera, u.genero, n.nem_valor,
            CASE WHEN m.mrun IS NOT NULL THEN 1 ELSE 0 END as sigue_estudiando
        FROM UniversoValido u
        INNER JOIN PromediosNEM n ON u.mrun = n.mrun
        LEFT JOIN tabla_matriculas_competencia_unificada m ON u.mrun = m.mrun 
            AND m.periodo = (u.anio_ingreso + 1)
            AND m.cod_inst = :cod_inst
    )
    SELECT * FROM Persistencia
    """)
    
    df_raw = pd.read_sql(sql_query, db_engine, params=params)

    if df_raw.empty:
        return pd.DataFrame(columns=['rango_nem', 'total_alumnos', 'cantidad_persisten', 'tasa_persistencia'])

    # 2. FILTROS EN PANDAS
    df = df_raw.copy()
    if jornada != "Todas":
        df = df[df['jornada'] == jornada]
    if carrera != "Todas":
        df = df[df['nomb_carrera'] == carrera]
    if genero != "Todos":
        df = df[df['genero'] == genero]

    if df.empty:
        return pd.DataFrame(columns=['rango_nem', 'total_alumnos', 'cantidad_persisten', 'tasa_persistencia'])

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

def get_correlacion_nem_titulacion_rango(cohorte_range, cod_inst, jornada="Todas", carrera="Todas", genero="Todos", region_id=None):
    
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
        "region": region_id
    }

    # Filtro de región dinámico
    filtro_region = "AND e_geo.cod_region = :region" if region_id != None else ""

    sql_query = text(f"""
    WITH PrimerIngresoInstitucion AS (
        -- Identidad de ingreso: Validamos existencia en egresados para filtro regional
        SELECT * FROM (
            SELECT 
                m.mrun, 
                m.cohorte as anio_ingreso,
                m.jornada,
                m.nomb_carrera,
                m.genero,
                m.periodo,
                CAST(m.dur_total_carr AS INT) / 2.0 as duracion_formal_anios,
                ROW_NUMBER() OVER (
                    PARTITION BY m.mrun 
                    ORDER BY m.periodo ASC, m.jornada ASC
                ) as rn_ingreso
            FROM tabla_matriculas_competencia_unificada m
            -- Aseguramos que el alumno tenga registro geográfico
            INNER JOIN (
                SELECT mrun, cod_region,
                       ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY periodo DESC) as rn_geo
                FROM tabla_alumnos_egresados_unificada
            ) e_geo ON m.mrun = e_geo.mrun AND e_geo.rn_geo = 1
            WHERE m.cod_inst = :cod_inst
            {filtro_region}
        ) t WHERE rn_ingreso = 1
    ),
    UniversoValido AS (
        SELECT mrun, anio_ingreso, jornada, nomb_carrera, genero, duracion_formal_anios
        FROM PrimerIngresoInstitucion
        WHERE anio_ingreso {condicion_cohorte}
    ),
    PromediosNEM AS (
        SELECT 
            mrun, 
            AVG(CAST(REPLACE(prom_notas_alu, ',', '.') AS FLOAT)) as nem_valor
        FROM tabla_alumnos_egresados_unificada
        GROUP BY mrun
    ),
    DatosTitulacion AS (
        SELECT 
            u.mrun, u.jornada, u.nomb_carrera, u.genero, n.nem_valor,
            u.duracion_formal_anios, t.anio_titulacion,
            (t.anio_titulacion - u.anio_ingreso) as duracion_real_anios
        FROM UniversoValido u
        INNER JOIN PromediosNEM n ON u.mrun = n.mrun
        INNER JOIN (
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
        return pd.DataFrame(columns=['rango_nem', 'total_titulados', 'titulados_a_tiempo', 'tasa_titulacion_oportuna'])

    # 2. FILTROS EN PANDAS
    df = df_raw.copy()
    if jornada != "Todas":
        df = df[df['jornada'] == jornada]
    if carrera != "Todas":
        df = df[df['nomb_carrera'] == carrera]
    if genero != "Todos":
        df = df[df['genero'] == genero]

    if df.empty:
        return pd.DataFrame(columns=['rango_nem', 'total_titulados', 'titulados_a_tiempo', 'tasa_titulacion_oportuna'])

    # 3. CATEGORIZACIÓN NEM
    def categorizar_nem(nota):
        if nota < 5.0: return '4.0 - 4.9'
        if nota < 5.5: return '5.0 - 5.4'
        if nota < 6.0: return '5.5 - 5.9'
        if nota < 6.5: return '6.0 - 6.4'
        return '6.5 - 7.0'

    df['rango_nem'] = df['nem_valor'].apply(categorizar_nem)
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

def get_tasas_articulacion_tipo_establecimiento_rango(cohorte_range, cod_inst, jornada="Todas", carrera="Todas", genero="Todos", region_id=None):
    
    if isinstance(cohorte_range, list):
        c_inicio, c_fin = cohorte_range[0], cohorte_range[1]
        condicion_cohorte = "BETWEEN :c_inicio AND :c_fin"
    else:
        c_inicio, c_fin = cohorte_range, cohorte_range
        condicion_cohorte = "= :c_inicio"

    params = {
        "cod_inst": cod_inst,
        "c_inicio": c_inicio,
        "c_fin": c_fin,
        "region": region_id
    }

    # Filtro de región dinámico
    filtro_region = "AND e_geo.cod_region = :region" if region_id != None else ""

    # Mapeo local (aseguramos el código 0)
    map_ensenianza_full = map_ensenianza.copy()
    map_ensenianza_full[0] = "Media - Modalidad no registrada"

    sql_query = text(f"""
    WITH PrimerIngresoInstitucion AS (
        -- Identidad de ingreso: Validamos existencia en egresados para filtro regional
        SELECT * FROM (
            SELECT 
                m.mrun, 
                m.cohorte as anio_ingreso,
                m.jornada,
                m.nomb_carrera,
                m.genero,
                m.periodo,
                ROW_NUMBER() OVER (
                    PARTITION BY m.mrun 
                    ORDER BY m.periodo ASC, m.jornada ASC
                ) as rn_ingreso
            FROM tabla_matriculas_competencia_unificada m
            -- Forzamos vínculo geográfico
            INNER JOIN (
                SELECT mrun, cod_region,
                       ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY periodo DESC) as rn_geo
                FROM tabla_alumnos_egresados_unificada
            ) e_geo ON m.mrun = e_geo.mrun AND e_geo.rn_geo = 1
            WHERE m.cod_inst = :cod_inst
            {filtro_region}
        ) t WHERE rn_ingreso = 1
    ),
    UniversoValido AS (
        SELECT mrun, anio_ingreso, jornada, nomb_carrera, genero
        FROM PrimerIngresoInstitucion
        WHERE anio_ingreso {condicion_cohorte}
    ),
    EgresoOrdenado AS (
        -- Obtenemos el tipo de enseñanza del egreso estable
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
        u.mrun, u.jornada, u.nomb_carrera, u.genero,
        e.cod_ense_clean, e.prom_notas AS prom_notas_media
    FROM UniversoValido u
    INNER JOIN EgresoOrdenado e ON u.mrun = e.mrun
    """)

    df_raw = pd.read_sql(sql_query, db_engine, params=params)

    if df_raw.empty:
        return pd.DataFrame(columns=['Tipo Enseñanza', 'Cant. Estudiantes', 'Promedio Notas'])

    # 2. FILTROS EN PANDAS
    df = df_raw.copy()
    if jornada != "Todas":
        df = df[df['jornada'] == jornada]
    if carrera != "Todas":
        df = df[df['nomb_carrera'] == carrera]
    if genero != "Todos":
        df = df[df['genero'] == genero]

    if df.empty:
        return pd.DataFrame(columns=['Tipo Enseñanza', 'Cant. Estudiantes', 'Promedio Notas'])

    # 3. PROCESAMIENTO Y MAPEO
    df['cod_ense_clean'] = pd.to_numeric(df['cod_ense_clean'], errors='coerce').fillna(0).astype(int)
    df['nomb_ensenianza'] = df['cod_ense_clean'].map(map_ensenianza_full).fillna("Media - Modalidad no registrada")

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

def get_kpi_ruralidad_seguimiento_rango(cohorte_range, cod_inst, jornada="Todas", genero="Todos", region_id=None):
    params = {
        "cod_inst": cod_inst,
        "c_inicio": cohorte_range[0] if isinstance(cohorte_range, list) else cohorte_range,
        "c_fin": cohorte_range[1] if isinstance(cohorte_range, list) else cohorte_range,
        "jornada": jornada,
        "genero": genero,
        "region": region_id
    }

    filtro_jornada = "AND u.jornada = :jornada" if jornada != "Todas" else ""
    filtro_genero = "AND u.genero = :genero" if genero != "Todos" else ""
    filtro_region = "AND g.cod_region = :region" if region_id is not None else ""

    sql_query = text(f"""
    WITH UniversoMatricula AS (
        SELECT * FROM (
            SELECT mrun, cohorte as anio_ingreso, jornada, genero,
                   ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY periodo ASC) as rn
            FROM tabla_matriculas_competencia_unificada
            WHERE cod_inst = :cod_inst
        ) t WHERE rn = 1 AND anio_ingreso BETWEEN :c_inicio AND :c_fin
    ),
    Geolocalizacion AS (
        -- Agregamos el índice de ruralidad a la geolocalización
        SELECT * FROM (
            SELECT mrun, cod_region, CAST(indice_rural AS INT) as cod_rural,
                   ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY periodo DESC) as rn_geo
            FROM tabla_alumnos_egresados_unificada
        ) e WHERE rn_geo = 1
    )
    SELECT 
        g.cod_rural,
        COUNT(DISTINCT u.mrun) as total_ingreso,
        COUNT(DISTINCT t.mrun) as total_titulados
    FROM UniversoMatricula u
    INNER JOIN Geolocalizacion g ON u.mrun = g.mrun
    LEFT JOIN tabla_dashboard_titulados t ON u.mrun = t.mrun AND t.cod_inst = :cod_inst
    WHERE 1=1 {filtro_jornada} {filtro_genero} {filtro_region}
    GROUP BY g.cod_rural
    """)

    df = pd.read_sql(sql_query, db_engine, params=params)
    
    if df.empty:
        return pd.DataFrame(columns=['Zona', 'total_ingreso', 'total_titulados'])

    map_rural = {0: "Urbano", 1: "Rural"}
    df['Zona'] = df['cod_rural'].map(map_rural).fillna("Sin Información")
    
    return df[['Zona', 'total_ingreso', 'total_titulados']].sort_values('total_ingreso', ascending=False)

#print(get_kpi_ruralidad_seguimiento_rango(cohorte_range=[2007,2025], cod_inst=104))

def get_info_competencia():
    sql = text("""
        WITH CarrerasUnicas AS (
            SELECT DISTINCT cod_inst, nomb_inst, nomb_carrera
            FROM tabla_matriculas_competencia_unificada
        )
        SELECT 
            cod_inst,
            MAX(nomb_inst) as nomb_inst, 
            STRING_AGG(nomb_carrera, ', ') WITHIN GROUP (ORDER BY nomb_carrera ASC) as carreras
        FROM CarrerasUnicas
        GROUP BY cod_inst
        ORDER BY nomb_inst ASC
    """)
    
    df = pd.read_sql(sql, db_engine)
    return df

def get_jornadas_disponibles():
    """
    Obtiene las jornadas únicas presentes en la base de datos.
    """
    sql = text("SELECT DISTINCT jornada FROM tabla_matriculas_competencia_unificada WHERE jornada IS NOT NULL")
    df = pd.read_sql(sql, db_engine)
    return df['jornada'].tolist()
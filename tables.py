from conn_db import get_db_engine
from sqlalchemy import text
import pandas as pd
import numpy as np
from collections import defaultdict
from typing import List, Optional, Tuple

db_engine = get_db_engine()

def get_fuga_multianual_trayectoria(db_conn, anio_n: Optional[int] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    
    filtro_cohorte = f"AND anio_ing_carr_ori = {anio_n}" if isinstance(anio_n, int) else ""

    # 1. Identificación de estudiantes en ECAS
    sql_base_ecas = f"""
    SELECT 
    mrun,
    gen_alu,
    rango_edad,
    cat_periodo,
    anio_ing_carr_ori AS cohorte,
    cod_inst,
    jornada, 
    nomb_carrera 
    FROM vista_matricula_unificada
    WHERE mrun IS NOT NULL 
    AND cod_inst = 104
    AND anio_ing_carr_ori BETWEEN 2007 AND 2025
    {filtro_cohorte}
    ORDER BY mrun, cat_periodo;
    """
    
    df_ecas_cohortes = pd.read_sql(sql_base_ecas, db_conn)
    
    if df_ecas_cohortes.empty:
        print("No se encontraron datos de matrículas para la cohorte especificada en ECAS.")
        return pd.DataFrame(), pd.DataFrame()

    cohortes_iniciales = (
        df_ecas_cohortes
        .sort_values('cat_periodo')
        .groupby('mrun', as_index=False)
        .agg(
            cohorte=('cohorte', 'min'),
            rango_edad_ingreso=('rango_edad', 'first') # Edad al entrar a ECAS
        )
    )
    cohortes_iniciales.dropna(subset=['cohorte'], inplace=True)
    
    if cohortes_iniciales.empty:
        print("Advertencia: No quedan cohortes válidas después de limpiar los valores nulos.")
        return pd.DataFrame(), pd.DataFrame()
        
    max_anio_registro = df_ecas_cohortes['cat_periodo'].max()
    if pd.isna(max_anio_registro):
        print("Advertencia: max_anio_registro es NaN. Saliendo.")
        return pd.DataFrame(), pd.DataFrame() 
    max_anio_registro = int(max_anio_registro)
    
    
    matrículas_ecas = set(df_ecas_cohortes[['mrun', 'cat_periodo']].apply(tuple, axis=1))
    fugas_detectadas_supuestas = []

    # 2. Detección de Fugas Supuestas (basado en ausencia de matrícula y no retorno)
    for index, row in cohortes_iniciales.iterrows():
        mrun = row['mrun']
        cohorte = row['cohorte']

        cohorte = int(cohorte)

        matriculas_mrun = df_ecas_cohortes[df_ecas_cohortes['mrun'] == mrun]
    
        if matriculas_mrun.empty:
            continue 
            
        max_anio_en_ecas = int(matriculas_mrun['cat_periodo'].max())
        
        if max_anio_en_ecas == max_anio_registro:
            continue
        
        anio_primer_fuga = max_anio_en_ecas + 1
        
        retorno_detectado = False
        for anio_posterior in range(anio_primer_fuga + 1, max_anio_registro + 1):
            if (mrun, anio_posterior) in matrículas_ecas:
                retorno_detectado = True
                break
        if retorno_detectado:
            continue
        
        fugas_detectadas_supuestas.append({
            'mrun': mrun, 
            'cohorte': cohorte, 
            'anio_fuga': anio_primer_fuga
        })
    
    df_fugas_supuestas = pd.DataFrame(fugas_detectadas_supuestas)

    if df_fugas_supuestas.empty:
        print("No se detectaron fugas o todos se mantuvieron hasta el final del período registrado.")
        return pd.DataFrame(), pd.DataFrame()
        
    
    # 3. IDENTIFICAR TITULADOS (EGRESADOS) REALES USANDO VISTA UNIFICADA
    
    sql_titulados = """
    SELECT 
        DISTINCT mrun
    FROM vista_titulados_unificada_limpia
    WHERE mrun IS NOT NULL
      AND cod_inst = 104; -- Opcional: Filtrar solo titulados de ECAS si es relevante.
    """
    df_mruns_titulados = pd.read_sql(sql_titulados, db_conn)
    
    mruns_titulados = df_mruns_titulados['mrun'].tolist()
    
    # 4. CLASIFICACIÓN DE EGRESADOS/TITULADOS (Criterio simple y exacto)
    
    # Los egresados son todas las 'fugas supuestas' que tienen un registro de titulación.
    df_egresados = df_fugas_supuestas[
        df_fugas_supuestas['mrun'].isin(mruns_titulados)
    ].copy()
    
    mruns_egresados = df_egresados['mrun'].tolist()
    
    # Los Desertores son las fugas supuestas que NO son titulados.
    df_fugas_final_meta = df_fugas_supuestas[~df_fugas_supuestas['mrun'].isin(mruns_egresados)].copy()
    mruns_solo_desertores = df_fugas_final_meta['mrun'].tolist()

    if df_fugas_final_meta.empty:
        print("Todos los estudiantes que dejaron la institución fueron clasificados como Egresados/Titulados.")
        return pd.DataFrame(), pd.DataFrame() 
    
    df_fugas_final_meta = pd.merge(
        df_fugas_final_meta, # Este df viene de la clasificación anterior
        cohortes_iniciales[['mrun', 'rango_edad_ingreso']], 
        on='mrun', 
        how='left'
    )

    # 6. Complementamos con la jornada y última matrícula
    df_info_salida = (
        df_ecas_cohortes
        .sort_values(["mrun", "cat_periodo"])
        .groupby("mrun", as_index=False)
        .last()[["mrun", "jornada", "gen_alu", "cat_periodo"]]
    )

    df_fugas_final_meta = pd.merge(
        df_fugas_final_meta, 
        df_info_salida, 
        on='mrun', 
        how='left'
    ).rename(columns={"cat_periodo": "anio_ultima_matricula_ecas"})
    
    # 6. CONSULTA DE TRAYECTORIA Y CREACIÓN DE TABLA TEMPORAL (Solo para los desertores)
    
    df_mruns_temp = pd.DataFrame(mruns_solo_desertores, columns=['mrun_fuga'])
    df_mruns_temp.to_sql('#TempMrunsFuga', db_conn, if_exists='replace', index=False, chunksize=1000)

    sql_trayectoria = f"""
    SELECT 
        t1.mrun,
        t1.cat_periodo AS anio_matricula_destino,
        t1.nomb_inst AS institucion_destino,
        t1.nomb_carrera AS carrera_destino,
        t1.area_conocimiento AS area_conocimiento_destino,
        t1.cod_inst,
        t1.rango_edad,
        t1.dur_total_carr as duracion_total_carrera,
        t1.nivel_global,
        t1.nivel_carrera_1,
        t1.nivel_carrera_2,
        t1.tipo_inst_1,
        t1.tipo_inst_2,
        t1.tipo_inst_3,
        t1.requisito_ingreso,
        t1.acreditada_carr,
        t1.acreditada_inst,
        t1.acre_inst_anio
    FROM vista_matricula_unificada t1
    INNER JOIN #TempMrunsFuga tm ON t1.mrun = tm.mrun_fuga
    ORDER BY t1.mrun, t1.cat_periodo;
    """
    df_trayectoria = pd.read_sql(sql_trayectoria, db_conn)
    
    # 7. Unir las trayectorias con la metadata de fuga
    df_fugas_matriculas = df_trayectoria[df_trayectoria['mrun'].isin(mruns_solo_desertores)].copy()
    
    df_fugas_final = pd.merge(
        df_fugas_matriculas, 
        df_fugas_final_meta[['mrun', 'cohorte', 'anio_fuga', 'jornada']], 
        on='mrun', 
        how='left'
    )
    
    # 8. Clasificación Fuga a Destino vs Abandono Total
    
    df_destino_filtrado = df_fugas_final[
        (df_fugas_final['anio_matricula_destino'] >= df_fugas_final['anio_fuga']) &
        (df_fugas_final['cod_inst'] != 104)
    ].copy()

    # Eliminamos duplicados de trayectoria para no inflar conteos
    df_destino_filtrado.drop_duplicates(
        subset=['mrun', 'anio_matricula_destino', 'institucion_destino', 'carrera_destino'], 
        inplace=True
    )

    # UNIMOS LA METADATA DE INGRESO (Rango edad ingreso y Género)
    # Usamos df_destino_filtrado para asegurar que solo vemos trayectoria POST-FUGA
    df_destino_final = pd.merge(
        df_destino_filtrado, 
        df_fugas_final_meta[['mrun', 'rango_edad_ingreso', 'gen_alu']], 
        on='mrun', 
        how='left'
    )

    # 9. Clasificar Abandono Total (Sin destino posterior)
    mruns_con_destino = df_destino_final['mrun'].unique()
    mruns_desertores_base = df_fugas_final_meta['mrun'].unique()
    mruns_abandono_total = [m for m in mruns_desertores_base if m not in mruns_con_destino]
    
    df_abandono_total = df_fugas_final_meta[df_fugas_final_meta['mrun'].isin(mruns_abandono_total)].copy()
    
    # Estandarización de nombres para el Dashboard
    df_destino_final.rename(columns={'rango_edad_ingreso': 'rango_edad'}, inplace=True)
    df_fugas_final_meta.rename(columns={'rango_edad_ingreso': 'rango_edad'}, inplace=True)

    return df_destino_final, df_fugas_final_meta, df_abandono_total

def poblar_tabla_fuga_fisica(db_conn, df_destino, df_fugas_final_meta):
    """
    Estandariza los nombres de columnas para que coincidan con la lógica de 
    trayectorias de titulados y desertores, incluyendo el rango de edad de ingreso.
    """
    # 1. Preparar Metadata de ECAS (Aseguramos que rango_edad esté presente)
    # df_fugas_final_meta ya trae el rango de edad de ingreso renombrado o capturado
    df_meta = df_fugas_final_meta[[
        'mrun', 'gen_alu', 'rango_edad', 'jornada', 
        'cohorte', 'anio_ultima_matricula_ecas', 'anio_fuga'
    ]].copy()

    mapa_genero = {1: "Hombre", 2: "Mujer"}
    df_meta["gen_alu"] = df_meta["gen_alu"].map(mapa_genero).fillna("Sin información")

    # 2. Preparar Datos de Destino (Trayectoria externa)
    df_destino_clean = df_destino[[
        'mrun', 'anio_matricula_destino', 'institucion_destino', 
        'carrera_destino', 'area_conocimiento_destino', 
        'tipo_inst_1', 'duracion_total_carrera', 'nivel_global',
        'acreditada_carr', 'acreditada_inst', 'acre_inst_anio'
    ]].copy()

    # 3. Merge para tener la tabla plana
    df_final = pd.merge(df_meta, df_destino_clean, on='mrun', how='inner')

    # --- MAPEO DE COLUMNAS ESTANDARIZADO ---
    # Es vital que 'jornada_titulacion' sea el nombre para AMBAS tablas (titulados y desertores)
    # para que los filtros del dashboard funcionen con la misma query.
    df_final = df_final.rename(columns={
        'gen_alu': 'genero',
        'jornada': 'jornada_ecas', 
        'cohorte': 'anio_ingreso_ecas',
        'anio_matricula_destino': 'anio_matricula_post',
        'institucion_destino': 'inst_destino',
        'nivel_global': 'nivel_estudio_post',
        'anio_fuga': 'anio_fuga_ecas' # Lo renombramos a anio_titulacion para estandarizar con la otra tabla
    })

    # 4. Cálculo de tiempo de espera (Demora)
    # Ahora usamos 'anio_titulacion' que representa el año de fuga en desertores
    df_final['tiempo_espera_post'] = df_final['anio_matricula_post'] - (df_final['anio_fuga_ecas'] - 1)

    # 5. Carga a SQL
    # 'rango_edad' se guarda automáticamente ya que está en el DataFrame final
    df_final.to_sql('tabla_fuga_detallada_desertores', db_conn, if_exists='replace', index=False)
    print("Tabla física de desertores actualizada y estandarizada con Rango de Edad.")

def poblar_tabla_abandono_fisica(db_conn, df_abandono_total):
    """
    Toma el segundo DataFrame devuelto por get_fuga_multianual_trayectoria
    y lo inserta en la tabla física de abandono total.
    """
    if df_abandono_total.empty:
        print("No hay datos de abandono total para insertar.")
        return

    df_final = df_abandono_total.copy()
    
    # 1. Mapeo exacto basado en tus columnas reales:
    # 'mrun', 'cohorte', 'anio_fuga', 'rango_edad_ingreso', 'jornada', 'gen_alu', 'anio_ultima_matricula_ecas'
    df_final = df_final.rename(columns={
        'cohorte': 'anio_ingreso_ecas',
        'anio_fuga': 'anio_fuga_ecas',
        'gen_alu': 'genero',
        'rango_edad_ingreso': 'rango_edad',
        'jornada': 'jornada_ecas',
        'anio_ultima_matricula_ecas': 'anio_ultima_mat_ecas'
    })

    # 2. Verificación de cálculo (Opcional)
    # Si 'anio_ultima_matricula_ecas' ya viene calculado, no necesitas restarle 1 a mano
    # a menos que quieras sobreescribirlo por seguridad:
    # df_final['anio_ultima_mat_ecas'] = df_final['anio_fuga_ecas'] - 1

    # 3. Carga a SQL
    df_final.to_sql('tabla_abandono_total_desertores', db_conn, if_exists='replace', index=False)
    print(f"Tabla de abandono total actualizada con {len(df_final)} registros.")

def actualizar_tabla_matriculas():

    query_insert = text("""
    IF OBJECT_ID('tabla_matriculas_competencia_unificada', 'U') IS NOT NULL
        DROP TABLE tabla_matriculas_competencia_unificada;

    WITH EdadIngreso AS (
        SELECT 
            mrun, 
            rango_edad AS rango_edad_ingreso,
            ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY cat_periodo ASC) as rn
        FROM vista_matricula_unificada
        WHERE mrun IS NOT NULL
    )
    SELECT
        V.mrun,
        V.nomb_carrera,
        V.nomb_inst, 
        V.cod_inst,
        V.jornada,
        V.region_sede,
        V.dur_total_carr,
        V.dur_estudio_carr,
        V.acreditada_carr,
        V.acreditada_inst,
        V.acre_inst_anio,
        CASE 
            WHEN V.gen_alu = 1 THEN 'Hombre'
            WHEN V.gen_alu = 2 THEN 'Mujer'
            ELSE 'Sin Información'
        END AS genero,
        -- Rango de edad estático de ingreso
        COALESCE(E.rango_edad_ingreso, V.rango_edad) AS rango_edad,
        CAST(V.anio_ing_carr_ori AS INT) AS cohorte, 
        CAST(V.cat_periodo AS INT) AS periodo
    INTO tabla_matriculas_competencia_unificada
    FROM vista_matricula_unificada V
    LEFT JOIN EdadIngreso E ON V.mrun = E.mrun AND E.rn = 1
    WHERE V.anio_ing_carr_ori BETWEEN 2007 AND 2025
    AND V.region_sede = 'Metropolitana'
    AND (V.nomb_carrera LIKE 'AUDITOR%' OR V.nomb_carrera LIKE 'CONTA%')
    AND (V.cod_inst = 104 OR V.tipo_inst_1 IN ('Institutos Profesionales', 'Centros de Formación Técnica') OR v.nomb_inst = 'UNIVERSIDAD SANTO TOMAS')
    AND V.dur_total_carr BETWEEN 8 AND 10;

    -- 3. Recreación de índices para optimizar el Dashboard
    CREATE INDEX idx_matriculas_cohorte ON tabla_matriculas_competencia_unificada(cohorte, cod_inst);
    CREATE INDEX idx_matriculas_mrun ON tabla_matriculas_competencia_unificada(mrun, cod_inst);
    """)

    try:
        with db_engine.connect() as conn:
            conn.execute(query_insert)
            conn.commit()
            print("Tabla actualizada con las matriculas de ECAS y competidores.")
    except Exception as e:
        print(f"Error al actualizar la tabla: {e}")

def actualizar_tabla_titulados():

    query_insert = text("""
    IF OBJECT_ID('tabla_dashboard_titulados', 'U') IS NOT NULL
        DROP TABLE tabla_dashboard_titulados;

    WITH EdadIngreso AS (
    SELECT 
        mrun, 
        rango_edad AS rango_edad_ingreso,
        ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY cat_periodo ASC) as rn
    FROM dbo.vista_matricula_unificada
    WHERE cod_inst = 104 -- Filtramos por su ingreso original en ECAS
    )
    -- 2. Construimos la tabla final de titulados usando la edad capturada arriba
    SELECT 
        CAST(T.cat_periodo AS INT) AS anio_titulacion,
        T.mrun,
        CAST(T.anio_ing_carr_ori AS INT) AS cohorte,
        CASE
            WHEN T.nombre_titulo_obtenido IN (
                'TECNICO DE NIVEL SUPERIOR EN CONTABILIDAD',
                'CONTADOR TECNICO DE NIVEL SUPERIOR'
            ) THEN 'CONTADOR TECNICO DE NIVEL SUPERIOR'
            WHEN T.nombre_titulo_obtenido IS NULL AND T.cod_inst = 104 THEN 'CONTADOR AUDITOR'
            ELSE T.nombre_titulo_obtenido
        END AS nomb_titulo,
        T.fecha_obtencion_titulo,
        T.cod_inst,
        T.nomb_inst,
        T.nomb_carrera,
        T.dur_total_carr,
        T.jornada,
        -- CAMBIO CLAVE: Usamos la edad de ingreso estática en lugar de la edad de titulación
        COALESCE(E.rango_edad_ingreso, T.rango_edad) AS rango_edad,
        T.region_sede,
        T.tipo_inst_1,
        T.nombre_grado_obtenido,
        CASE 
            WHEN T.gen_alu = 1 THEN 'Hombre'
            WHEN T.gen_alu = 2 THEN 'Mujer'
            ELSE 'Sin Información'
        END AS genero,
        (CAST(T.cat_periodo AS INT) - CAST(T.anio_ing_carr_ori AS INT)) AS anios_para_titularse
    INTO tabla_dashboard_titulados
    FROM dbo.vista_titulados_unificada T
    LEFT JOIN EdadIngreso E ON T.mrun = E.mrun AND E.rn = 1
    WHERE T.fecha_obtencion_titulo IS NOT NULL
    AND T.anio_ing_carr_ori BETWEEN 2007 AND 2025
    AND T.region_sede = 'Metropolitana'
    AND (T.nomb_carrera LIKE 'AUDITOR%' OR T.nomb_carrera LIKE 'CONTA%')
    AND (T.cod_inst = 104 OR T.tipo_inst_1 IN ('Institutos Profesionales', 'Centros de Formación Técnica') OR T.nomb_inst LIKE 'UNIVERSIDAD SANTO TOMAS')
    AND T.anio_ing_carr_ori IS NOT NULL
    AND T.dur_total_carr BETWEEN 8 AND 10;

    -- PASO CRUCIAL: Índices para velocidad de análisis longitudinal
    CREATE INDEX idx_titulados_cohorte ON tabla_dashboard_titulados(cohorte, cod_inst);
    CREATE INDEX idx_titulados_mrun ON tabla_dashboard_titulados(mrun);
    CREATE INDEX idx_titulados_anios ON tabla_dashboard_titulados(anios_para_titularse);
    """)

    try:
        with db_engine.connect() as conn:
            conn.execute(query_insert)
            conn.commit()
            print("Tabla actualizada con los titulados de ECAS y competencia.")
    except Exception as e:
        print(f"Error al actualizar la tabla: {e}")


def actualizar_tabla_egresados():

    query_insert = text("""
    -- 1. Eliminar la tabla si ya existe para recrearla
    IF OBJECT_ID('tabla_alumnos_egresados_unificada', 'U') IS NOT NULL
        DROP TABLE tabla_alumnos_egresados_unificada;

    -- 2. Insertar todos los registros de egreso para alumnos que existen en la tabla de competencia
    SELECT 
        e.*
    INTO tabla_alumnos_egresados_unificada
    FROM vista_egresados_unificada e
    WHERE EXISTS (
        SELECT 1 
        FROM tabla_matriculas_competencia_unificada p 
        WHERE p.mrun = e.mrun
    );

    -- 3. Opcional: Crear un índice para mejorar el rendimiento de los JOINs en los KPIs
    CREATE INDEX idx_mrun_egresados_full ON tabla_alumnos_egresados_unificada (mrun);
    """)

    try:
        with db_engine.connect() as conn:
            conn.execute(query_insert)
            conn.commit()
            print("Tabla actualizada con éxito. Se han importado todos los registros históricos por MRUN.")
    except Exception as e:
        print(f"Error al actualizar la tabla: {e}")

#Tabla que reune las titulaciones de los desertores de ECAS
def actualizar_tabla_titulados_desertores():

    query_insert = text("""
    IF OBJECT_ID('tabla_titulados_externos_desertores', 'U') IS NOT NULL
        DROP TABLE tabla_titulados_externos_desertores;

    SELECT 
        f.mrun,
        f.genero,
        f.rango_edad,
        f.jornada_ecas,
        f.anio_ingreso_ecas,
        t.cat_periodo as anio_titulacion,
        t.nomb_inst AS inst_titulacion,
        t.nomb_carrera AS carrera_titulacion,
        t.tipo_inst_1 AS tipo_inst_titulacion
    INTO tabla_titulados_externos_desertores
    FROM (SELECT DISTINCT mrun, genero, rango_edad, jornada_ecas, anio_ingreso_ecas 
        FROM tabla_fuga_detallada_desertores) f
    INNER JOIN vista_titulados_unificada_limpia t ON f.mrun = t.mrun
    WHERE t.cod_inst <> 104; -- Excluimos ECAS porque buscamos titulación externa

    -- Índice para filtros rápidos
    CREATE INDEX idx_tit_ext_filtros ON tabla_titulados_externos_desertores(anio_ingreso_ecas);
    """)

    try:
        with db_engine.connect() as conn:
            conn.execute(query_insert)
            conn.commit()
            print("Tabla actualizada con los registros de titulación de desertores")
    except Exception as e:
        print(f"Error al actualizar la tabla: {e}")

#Tabla para buscar estudiantes que provenian desde otra institución antes de llegar a ECAS
def actualizar_tabla_origenes_totales():

    query_insert = text("""
    IF OBJECT_ID('tabla_origenes_estudiantes_ecas', 'U') IS NOT NULL
        DROP TABLE tabla_origenes_estudiantes_ecas;

    SELECT 
    v.mrun,
    v.nomb_inst AS inst_origen,
    v.nomb_carrera AS carrera_origen,
    v.cat_periodo AS anio_matricula_origen,
    CASE 
        WHEN v.gen_alu = 1 THEN 'Hombre'
        WHEN v.gen_alu = 2 THEN 'Mujer'
        ELSE 'Sin Información'
    END AS genero,
    v.jornada
    INTO tabla_origenes_estudiantes_ecas
    FROM vista_matricula_unificada v
    WHERE v.mrun IN (SELECT DISTINCT mrun FROM tabla_matriculas_competencia_unificada WHERE cod_inst = 104)
    AND v.cod_inst <> 104; -- Todo lo que NO fue ECAS

    CREATE INDEX idx_origen_mrun ON tabla_origenes_estudiantes_ecas(mrun);
    """)

    try:
        with db_engine.connect() as conn:
            conn.execute(query_insert)
            conn.commit()
            print("Tabla actualizada con los origenes de estudiantes de otras instituciones que se movieron a ecas.")
    except Exception as e:
        print(f"Error al actualizar la tabla: {e}")

def actualizar_tabla_trayectoria_titulados():

    query_insert = text("""
    IF OBJECT_ID('tabla_trayectoria_post_titulado', 'U') IS NOT NULL
        DROP TABLE tabla_trayectoria_post_titulado;

    SELECT 
        t.mrun,
        t.genero,
        t.jornada AS jornada_ecas,
        t.cohorte AS anio_ingreso_ecas,
        t.anio_titulacion,
        t.rango_edad,
        m.cat_periodo AS anio_matricula_post,
        m.nomb_inst AS inst_destino,
        m.nomb_carrera AS carrera_destino,
        m.nivel_global AS nivel_estudio_post,
        m.tipo_inst_1,
        m.area_conocimiento AS area_conocimiento_destino,
        (m.cat_periodo - t.anio_titulacion) AS tiempo_espera_post
    INTO tabla_trayectoria_post_titulado
    FROM tabla_dashboard_titulados t
    INNER JOIN vista_matricula_unificada m ON t.mrun = m.mrun
    WHERE t.cod_inst = 104
    AND m.cat_periodo > t.anio_titulacion; -- Solo registros posteriores al título

    -- Índices para optimizar el Dashboard de Titulados
    CREATE INDEX idx_post_tit_mrun ON tabla_trayectoria_post_titulado(mrun);
    CREATE INDEX idx_post_tit_filtros ON tabla_trayectoria_post_titulado(anio_ingreso_ecas, genero);
    """)

    try:
        with db_engine.connect() as conn:
            conn.execute(query_insert)
            conn.commit()
            print("Tabla actualizada con la trayectoria de los titulados en ECAS.")
    except Exception as e:
        print(f"Error al actualizar la tabla: {e}")


#Ejecutar creación de trayectoria fugas y abandono
#df_destino, df_fugas_final_meta, df_abandono_total = get_fuga_multianual_trayectoria(db_engine)
#poblar_tabla_fuga_fisica(db_engine, df_destino, df_fugas_final_meta)
#poblar_tabla_abandono_fisica(db_engine, df_abandono_total)

# Ejecutar la actualización de tablas fisicas
actualizar_tabla_matriculas()
#actualizar_tabla_egresados()
#actualizar_tabla_titulados()
#actualizar_tabla_trayectoria_titulados()
#actualizar_tabla_origenes_totales()
#actualizar_tabla_titulados_desertores()
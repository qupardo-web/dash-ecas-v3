from conn_db import *
from sqlalchemy import text
import pandas as pd
import numpy as np
from collections import defaultdict
from typing import List, Optional, Tuple

db_engine = get_db_engine()

anio_max_cohorte = 2025

def actualizar_tabla_matriculas():

    query_insert = f"""
    IF OBJECT_ID('tabla_matriculas_competencia_unificada', 'U') IS NOT NULL
        DROP TABLE tabla_matriculas_competencia_unificada;

    WITH EdadIngreso AS (
        SELECT 
            mrun, 
            rango_edad AS rango_edad_ingreso,
            ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY cat_periodo ASC) as rn
        FROM matriculas_mrun
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
        COALESCE(E.rango_edad_ingreso, V.rango_edad) AS rango_edad,
        CAST(V.anio_ing_carr_ori AS INT) AS cohorte, 
        CAST(V.cat_periodo AS INT) AS periodo
    INTO tabla_matriculas_competencia_unificada
    FROM matriculas_mrun V
    LEFT JOIN EdadIngreso E ON V.mrun = E.mrun AND E.rn = 1
    WHERE V.anio_ing_carr_ori BETWEEN 2007 AND {anio_max_cohorte}
    AND (V.nomb_carrera LIKE 'AUDITOR%' OR V.nomb_carrera LIKE 'CONTA%')
    AND (V.cod_inst = 104 OR V.tipo_inst_1 IN ('Institutos Profesionales', 'Centros de Formación Técnica') OR v.nomb_inst = 'UNIVERSIDAD SANTO TOMAS')
    AND V.dur_total_carr BETWEEN 8 AND 10;

    -- 3. Recreación de índices para optimizar el Dashboard
    CREATE INDEX idx_matriculas_cohorte ON tabla_matriculas_competencia_unificada(cohorte, cod_inst);
    CREATE INDEX idx_matriculas_mrun ON tabla_matriculas_competencia_unificada(mrun, cod_inst);
    """

    try:
        with db_engine.connect() as conn:
            conn.execute(text(query_insert))
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
    FROM matriculas_mrun
    WHERE cod_inst = 104 
    )
    SELECT 
        CAST(T.cat_periodo AS INT) AS anio_titulacion,
        T.mrun,
        CAST(T.anio_ing_carr_ori AS INT) AS cohorte,
        T.nombre_titulo_obtenido as nomb_titulo,
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
    FROM titulados_mrun T
    LEFT JOIN EdadIngreso E ON T.mrun = E.mrun AND E.rn = 1
    WHERE T.fecha_obtencion_titulo IS NOT NULL
    AND T.anio_ing_carr_ori BETWEEN 2007 AND 2025
    AND (
        (T.cod_inst = 104) 
        OR 
        (
            (T.nomb_carrera LIKE '%AUDITOR%' OR T.nomb_carrera LIKE '%CONTA%')
            AND (T.tipo_inst_1 IN ('Institutos Profesionales', 'Centros de Formación Técnica') 
                 OR T.nomb_inst LIKE 'UNIVERSIDAD SANTO TOMAS')
            AND T.dur_total_carr BETWEEN 8 AND 10
        )
    );

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
    IF OBJECT_ID('tabla_alumnos_egresados_unificada', 'U') IS NOT NULL
        DROP TABLE tabla_alumnos_egresados_unificada;

    SELECT 
        e.*
    INTO tabla_alumnos_egresados_unificada
    FROM egresados_mrun e
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

def actualizar_tabla_abandono_total_ecas():
    query_insert_abandono = text("""
    IF OBJECT_ID('tabla_abandono_total_ecas', 'U') IS NOT NULL
        DROP TABLE tabla_abandono_total_ecas;

    DECLARE @MaxPeriodo INT = (SELECT MAX(periodo) FROM tabla_matriculas_competencia_unificada);

    WITH UltimaMatriculaECAS AS (
        SELECT * FROM (
            SELECT 
                mrun, 
                periodo as ultimo_periodo_ecas, 
                genero, 
                rango_edad,
                jornada as jornada_ecas, 
                cohorte as anio_ingreso_ecas,
                ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY periodo DESC) as rn
            FROM tabla_matriculas_competencia_unificada
            WHERE cod_inst = 104
        ) t WHERE rn = 1
    ),
    DesertoresPotenciales AS (
        SELECT u.*
        FROM UltimaMatriculaECAS u
        LEFT JOIN tabla_dashboard_titulados t ON u.mrun = t.mrun AND t.cod_inst = 104
        WHERE t.mrun IS NULL
          AND u.ultimo_periodo_ecas < @MaxPeriodo 
    ),
    TrayectoriaPosterior AS (
        SELECT DISTINCT V.mrun
        FROM matriculas_mrun V
        INNER JOIN DesertoresPotenciales D ON V.mrun = D.mrun
        WHERE V.cat_periodo > D.ultimo_periodo_ecas
    )
    SELECT 
        D.mrun, 
        D.genero, 
        D.rango_edad, 
        D.jornada_ecas, 
        D.anio_ingreso_ecas, 
        D.ultimo_periodo_ecas as anio_ultima_mat_ecas,
        (D.ultimo_periodo_ecas + 1) AS anio_fuga_ecas
    INTO tabla_abandono_total_ecas
    FROM DesertoresPotenciales D
    LEFT JOIN TrayectoriaPosterior TP ON D.mrun = TP.mrun
    WHERE TP.mrun IS NULL;

    CREATE INDEX idx_abandono_mrun ON tabla_abandono_total_ecas(mrun);
    CREATE INDEX idx_abandono_cohorte ON tabla_abandono_total_ecas(anio_ingreso_ecas);
    """)

    try:
        with db_engine.connect() as conn:
            conn.execute(query_insert_abandono)
            conn.commit()
            result = conn.execute(text("SELECT COUNT(*) FROM tabla_abandono_total_ecas")).scalar()
            print(f"Tabla de abandono total actualizada. Desertores confirmados (sin rastro post-salida): {result}")
    except Exception as e:
        print(f"Error al actualizar la tabla de abandono: {e}")

def actualizar_tabla_desertores_ecas():
   
    query_insert_fuga = text("""
    IF OBJECT_ID('tabla_fuga_detallada_ecas', 'U') IS NOT NULL
        DROP TABLE tabla_fuga_detallada_ecas;

    WITH UltimaMatriculaECAS AS (
        SELECT * FROM (
            SELECT 
                mrun, periodo as ultimo_periodo_ecas, genero, rango_edad,
                jornada as jornada_ecas, cohorte as anio_ingreso_ecas,
                ROW_NUMBER() OVER (PARTITION BY mrun ORDER BY periodo DESC) as rn
            FROM tabla_matriculas_competencia_unificada
            WHERE cod_inst = 104
        ) t WHERE rn = 1
    ),
    DesertoresValidos AS (
        SELECT u.*
        FROM UltimaMatriculaECAS u
        LEFT JOIN tabla_dashboard_titulados t ON u.mrun = t.mrun AND t.cod_inst = 104
        WHERE t.mrun IS NULL
    )
    SELECT 
        D.mrun, D.genero, D.rango_edad, D.jornada_ecas, D.anio_ingreso_ecas, D.ultimo_periodo_ecas,
        V.cat_periodo AS anio_matricula_post,
        V.cod_inst AS inst_destino_id,
        V.nomb_inst AS inst_destino,
        V.nomb_carrera AS carrera_destino,
        V.nivel_global AS nivel_estudio_post,
        V.tipo_inst_1,
        V.area_conocimiento AS area_conocimiento_destino,
        V.dur_total_carr AS duracion_total_carrera,
        V.acreditada_carr AS acreditada_carr,
        V.acreditada_inst AS acreditada_inst,
        V.acre_inst_anio AS acre_inst_anio,
        (D.ultimo_periodo_ecas + 1) AS anio_fuga_ecas,
        (V.cat_periodo - (D.ultimo_periodo_ecas + 1)) AS tiempo_espera_post

    INTO tabla_fuga_detallada_ecas
    FROM DesertoresValidos D
    INNER JOIN matriculas_mrun V ON D.mrun = V.mrun 
        AND V.cod_inst <> 104 
        AND V.cat_periodo > D.ultimo_periodo_ecas;

    CREATE INDEX idx_fuga_mrun ON tabla_fuga_detallada_ecas(mrun);
    CREATE INDEX idx_fuga_cohorte ON tabla_fuga_detallada_ecas(anio_ingreso_ecas);
    """)

    try:
        with db_engine.connect() as conn:
            conn.execute(query_insert_fuga)
            conn.commit()
            
            # Verificación inmediata de conteo
            result = conn.execute(text("SELECT COUNT(*) FROM tabla_fuga_detallada_ecas")).scalar()
            print(f"Tabla 'tabla_fuga_detallada_ecas' actualizada. Registros totales: {result}")
            
    except Exception as e:
        print(f"Error al actualizar la tabla de fuga: {e}")


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
        FROM tabla_fuga_detallada_ecas) f
    INNER JOIN titulados_mrun t ON f.mrun = t.mrun
    WHERE t.cod_inst <> 104; 

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
    FROM matriculas_mrun v
    WHERE v.mrun IN (SELECT DISTINCT mrun FROM tabla_matriculas_competencia_unificada  WHERE cod_inst = 104)
    AND v.cod_inst <> 104; 

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
    
    query_tabla = text("""
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
        m.cod_inst AS cod_inst_post,
        m.nomb_inst AS inst_destino,
        m.nomb_carrera AS carrera_destino,
        m.nivel_global AS nivel_estudio_post,
        m.tipo_inst_1,
        m.area_conocimiento AS area_conocimiento_destino,
        (m.cat_periodo - t.anio_titulacion) AS tiempo_espera_post
    INTO tabla_trayectoria_post_titulado
    FROM tabla_dashboard_titulados t
    INNER JOIN matriculas_mrun m ON t.mrun = m.mrun
    WHERE t.cod_inst = 104
      AND m.cod_inst <> 104
      AND m.cat_periodo > t.anio_titulacion;
    """)

    query_idx1 = text("CREATE INDEX idx_post_tit_mrun ON tabla_trayectoria_post_titulado(mrun);")
    query_idx2 = text("CREATE INDEX idx_post_tit_filtros ON tabla_trayectoria_post_titulado(anio_ingreso_ecas);")

    try:
        with db_engine.begin() as conn:
            # Ejecutar creación de tabla
            conn.execute(query_tabla)
            print("Tabla 'tabla_trayectoria_post_titulado' creada exitosamente.")
            
            # Ejecutar índices
            conn.execute(query_idx1)
            conn.execute(query_idx2)
            print("Índices creados exitosamente.")
            
    except Exception as e:
        print(f"Error al actualizar la tabla: {e}")

# actualizar_tabla_matriculas()
# actualizar_tabla_egresados()
# actualizar_tabla_titulados()
# actualizar_tabla_trayectoria_titulados()
# actualizar_tabla_origenes_totales()
# actualizar_tabla_desertores_ecas()
# actualizar_tabla_abandono_total_ecas()
actualizar_tabla_titulados_desertores()

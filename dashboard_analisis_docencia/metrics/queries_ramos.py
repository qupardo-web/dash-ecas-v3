from conn_db import *
import pandas as pd

db_engine = get_db_engine_umasnet()

limite_anio = 2015

def query_matriculas_totales():
    
    sql_query = f"""
        WITH FEC AS (SELECT  [FECHA]
        ,[añomat]
        ,[AntDiurnos_tot]
        ,[AntVesp_tot]
        ,[NueDiurnos_tot]
        ,[NueVesp_tot]
        ,[Total_tot],
        ROW_NUMBER() OVER (
                PARTITION BY añomat
                ORDER BY FECHA DESC
            ) AS RANK_SITUACION
    FROM [umasnet].[dbo].[RC_Contador]
    )


    SELECT TOP(7)
            [añomat] AS COHORTE,
            [Total_tot] AS cantidad,
            NueDiurnos_tot + NueVesp_tot AS nuevos

            ,[AntDiurnos_tot]
        ,[AntVesp_tot]
        ,[NueDiurnos_tot]
        ,[NueVesp_tot]
        
        
            
        FROM
            FEC
        WHERE
            RANK_SITUACION = 1 
        ORDER BY añomat DESC
    """

    df = pd.read_sql(sql_query, db_engine)

    return df

#print(query_matriculas_totales())

def query_alumnos_nuevos(jornada="Todas", genero="Todos"):
    
    filtro_j = f"AND t1.JORNADA = '{jornada}'" if jornada != "Todas" else ""
    filtro_g = f"AND t2.SEXO = '{genero}'" if genero != "Todos" else ""

    sql_query = f"""
    WITH COHORTES_VALIDAS AS (
        SELECT DISTINCT t1.CODCLI
        FROM [umasnet].[dbo].[RA_NOTA] t1
        JOIN [umasnet].[dbo].[MT_ALUMNO] t2 ON t1.CODCLI = t2.CODCLI
        WHERE t1.PERIODO = 1 
          AND t1.ANO = t2.ANO 
          AND t2.ANO >= {limite_anio}
    ) 
    SELECT 
        t1.[ANO] AS COHORTE,
        t1.[JORNADA],
        t2.[SEXO] AS GENERO,
        COUNT(1) AS CANTIDAD
    FROM [umasnet].[dbo].[MT_ALUMNO] t1
    JOIN [umasnet].[dbo].[MT_CLIENT] t2 ON t2.[CODCLI] = t1.[RUT]
    JOIN COHORTES_VALIDAS t3 ON t1.CODCLI = t3.CODCLI
    WHERE 1=1
      {filtro_j}
      {filtro_g}
    GROUP BY 
        t1.ANO, 
        t1.JORNADA, 
        t2.SEXO
    ORDER BY 
        t1.ANO DESC, 
        t1.JORNADA, 
        t2.SEXO
    """

    df = pd.read_sql(sql_query, db_engine)
        
    return df

#print(query_alumnos_nuevos())

def query_distribucion_demora_titulacion(jornada="Todas", genero="Todos"):
    
    filtro_j = f"AND t1.JORNADA = '{jornada}'" if jornada != "Todas" else ""
    filtro_g = f"AND t2.SEXO = '{genero}'" if genero != "Todos" else ""

    sql_query = f"""
    WITH COHORTES_VALIDAS AS (
        SELECT DISTINCT t1.CODCLI
        FROM [umasnet].[dbo].[RA_NOTA] t1
        JOIN [umasnet].[dbo].[MT_ALUMNO] t2 ON t1.CODCLI = t2.CODCLI
        WHERE t1.ANO = t2.ANO
          AND t2.PERIODO = 1
          AND t2.ANO >= {limite_anio}
    ) 
    SELECT 
        t1.[ANO] AS COHORTE,
        t1.[JORNADA],
        t2.[SEXO] AS GENERO,
        -- Calculamos la demora: Año Titulación menos Año Ingreso
        (t1.ANOTIT - t1.ANO) AS ANIOS_DEMORA,
        COUNT(1) AS CANTIDAD_TITULADOS
    FROM [umasnet].[dbo].[MT_ALUMNO] t1
    JOIN [umasnet].[dbo].[MT_CLIENT] t2 ON t2.[CODCLI] = t1.[RUT]
    JOIN COHORTES_VALIDAS t3 ON t1.CODCLI = t3.CODCLI
    WHERE t1.ESTACAD = 'TITULADO' 
      AND t1.ANOTIT IS NOT NULL
      AND t1.ANOTIT >= t1.ANO  -- Filtro de seguridad
      {filtro_j}
      {filtro_g}
    GROUP BY 
        t1.ANO, 
        t1.JORNADA, 
        t2.SEXO,
        (t1.ANOTIT - t1.ANO)
    ORDER BY 
        t1.ANO DESC, 
        ANIOS_DEMORA ASC
    """

    df = pd.read_sql(sql_query, db_engine)
    
    return df

#print(query_distribucion_demora_titulacion())

def obtener_metricas_vias_admision_vacantes(limite_anio=2019):
    """
    Calcula la cantidad de alumnos y el porcentaje de ocupación de vacantes
    desglosado por Vía de Admisión y Año.
    """
    
    sql_query = f"""
    WITH vacantes_ano_j AS (
        SELECT 
            ANO, 
            SUM(VACANTES) AS Total_Vacantes
        FROM [umasnet].[dbo].[MT_VACANTES]
        GROUP BY ANO
    ),
    COHORTES AS (
        SELECT DISTINCT t1.CODCLI
        FROM [umasnet].[dbo].[RA_NOTA] t1
        JOIN [umasnet].[dbo].[MT_ALUMNO] t2 ON t1.CODCLI = t2.CODCLI
        WHERE t1.PERIODO = 1 
          AND t1.ANO = t2.ANO 
          AND t2.ANO >= {limite_anio}
    ) 
    SELECT 
        t1.ANO AS COHORTE,
        COALESCE(t3.DESCRIPCION, 'OTRA / NO DEFINIDA') AS VIA_ADMISION,
        t1.ANO,
        j.Total_Vacantes,
        COUNT(1) AS CANTIDAD_MATRICULADOS
    FROM [umasnet].[dbo].[MT_ALUMNO] t1
    JOIN [umasnet].[dbo].[MT_CLIENT] t2 ON t2.[CODCLI] = t1.[RUT]
    LEFT JOIN [umasnet].[dbo].[MT_VIADMISION] t3 ON t3.COD_VIA = t2.[VIADMISION]
    JOIN COHORTES t4 ON t1.CODCLI = t4.CODCLI
    LEFT JOIN vacantes_ano_j j ON t1.[ANO] = j.[ANO]
    GROUP BY 
        t1.ANO, 
        t3.DESCRIPCION, 
        j.Total_Vacantes
    ORDER BY 
        t1.ANO DESC, 
        CANTIDAD_MATRICULADOS DESC
    """

    df = pd.read_sql(sql_query, db_engine)
        
    return df

#print(obtener_metricas_vias_admision_vacantes())

def obtener_persistencia_retencion_historica(jornada="Todas", genero="Todos"):
    """
    Calcula la persistencia año a año incluyendo la CANTIDAD_INICIAL de la cohorte.
    """
    
    filtro_j = f"AND t1.JORNADA = '{jornada}'" if jornada != "Todas" else ""
    filtro_g = f"AND t4.SEXO = '{genero}'" if genero != "Todos" else ""

    columnas_seguimiento = ", ".join([
        f"COUNT(DISTINCT CASE WHEN t2.ano_mat = t1.ANO + {i} "
        f"OR (t1.ESTACAD = 'TITULADO' AND t1.ANOTIT <= t1.ANO + {i}) THEN t1.CODCLI END) "
        f"* 100.0 / NULLIF(COUNT(DISTINCT CASE WHEN t2.ano_mat = t1.ANO THEN t1.CODCLI END), 0) AS [{i}]" 
        for i in range(1, 8)
    ])

    sql_query = f"""
    WITH ES AS (
        SELECT DISTINCT 
            t1.[CODCLI], 
            t1.ANO AS ano_mat,
            ROW_NUMBER() OVER (
                PARTITION BY t1.[CODCLI]
                ORDER BY t1.ANO DESC
            ) AS RANK_SITUACION
        FROM [umasnet].[dbo].[RA_NOTA] t1
        LEFT JOIN [umasnet].[dbo].[MT_ALUMNO] t2 ON t2.CODCLI = t1.CODCLI
        WHERE t2.PERIODO = 1 AND t1.PERIODO = 1 AND t2.ANO >= {limite_anio}
        GROUP BY t1.CODCLI, t1.ANO
    )
    SELECT 
        t1.ANO AS COHORTE,
        t1.JORNADA,
        t4.SEXO AS GENERO,
        -- Traemos la cantidad inicial (Alumnos en el año T+0)
        COUNT(DISTINCT CASE WHEN t2.ano_mat = t1.ANO THEN t1.CODCLI END) AS CANTIDAD_INICIAL,
        {columnas_seguimiento}
    FROM [umasnet].[dbo].[MT_ALUMNO] t1
    LEFT JOIN ES t2 ON t1.[CODCLI] = t2.[CODCLI]
    LEFT JOIN [umasnet].[dbo].[MT_CLIENT] t4 ON t4.[CODCLI] = t1.[RUT]
    WHERE t1.PERIODO = 1
      {filtro_j}
      {filtro_g}
    GROUP BY 
        t1.ANO,
        t1.JORNADA,
        t4.SEXO
    HAVING COUNT(DISTINCT CASE WHEN t2.ano_mat = t1.ANO THEN t1.CODCLI END) > 0
    ORDER BY t1.ANO DESC
    """

    df = pd.read_sql(sql_query, db_engine)

    if not df.empty:
        # Al hacer el melt, incluimos CANTIDAD_INICIAL en id_vars para que no se pierda
        df = df.melt(
            id_vars=['COHORTE', 'JORNADA', 'GENERO', 'CANTIDAD_INICIAL'],
            value_vars=['1', '2', '3', '4', '5', '6', '7'],
            var_name='ANIO_SEGUIMIENTO',
            value_name='PORCENTAJE_PERSISTENCIA'
        )
        df['PORCENTAJE_PERSISTENCIA'] = df['PORCENTAJE_PERSISTENCIA'].round(2)
        
        # Opcional: Calcular la cantidad de alumnos que persisten actualmente en números enteros
        df['CANTIDAD_PERSISTENTE'] = (df['CANTIDAD_INICIAL'] * df['PORCENTAJE_PERSISTENCIA'] / 100).round(0)
        
    return df

print(obtener_persistencia_retencion_historica(jornada="Todas", genero="Todos"))

def query_docentes_area_formacion():

    sql_query = f"""
        SELECT TOP(8) [ano] AS AÑO,COUNT(DISTINCT t1.[codprof]) AS cantidad,
            COUNT(DISTINCT CASE WHEN t3.DESCRIPCION  IS NOT NULL AND  t3.DESCRIPCION = 'PROFESIONAL' THEN t1.[codprof] END) AS PROFESIONAL,
            COUNT(DISTINCT CASE WHEN t3.DESCRIPCION  IS NOT NULL AND  t3.DESCRIPCION = 'UNIVERSITARIO' THEN t1.[codprof] END) AS UNIVERSITARIO,
            COUNT(DISTINCT CASE WHEN t5.DESCRIPCION  IS NOT NULL AND  t5.DESCRIPCION = 'DOCTORADOS' THEN t1.[codprof] END) AS DOCTORADO,
            COUNT(DISTINCT CASE WHEN t5.DESCRIPCION  IS NOT NULL AND  t5.DESCRIPCION = 'MAGISTER' THEN t1.[codprof] END) AS MAGISTER,
            COUNT(DISTINCT CASE WHEN t5.DESCRIPCION  IS NOT NULL AND  t5.DESCRIPCION = 'TITULO O LICENCIATURA' THEN t1.[codprof] END) AS LICENCIADO
            

    FROM [umasnet].[dbo].[RA_HORASCONT] t1
    JOIN [umasnet].[dbo].[RA_PROFES] t2 ON t2.CODPROF = t1.codprof
    LEFT JOIN  [umasnet].[dbo].[RA_TITULODOC] t3 ON t2.CODTITULO = t3.CODTITULO
    LEFT JOIN  [umasnet].[dbo].[RA_JORNADADOC] t4 ON t4 .CODJORNADA = t2.CODJORNADA 
    LEFT JOIN  [umasnet].[dbo].[RA_GRADODOC] t5 ON t2.CODGRADO = t5.CODGRADO 
    GROUP BY t1.[ano]
    ORDER BY t1.[ano] DESC
    """

    df = pd.read_sql(sql_query, db_engine)

    return df

def query_docentes_tipo_contrato():

    sql_query = f"""
    SELECT TOP(10) [ano] AS AÑO,COUNT(DISTINCT t1.[codprof]) AS cantidad,
		COUNT(DISTINCT CASE WHEN   t2.Categoria = 'HONORARIO' THEN t1.[codprof] END) AS HONORARIO,
		COUNT(DISTINCT CASE WHEN  t2.Categoria  = 'CONTRATO' THEN t1.[codprof] END) AS CONTRATO,
		COUNT(DISTINCT CASE WHEN   t2.Categoria  IS NULL THEN t1.[codprof] END) AS OTROS
		

    FROM [umasnet].[dbo].[RA_HORASCONT] t1
    JOIN [umasnet].[dbo].[RA_PROFES] t2 ON t2.CODPROF = t1.codprof
    LEFT JOIN  [umasnet].[dbo].[RA_TITULODOC] t3 ON t2.CODTITULO = t3.CODTITULO
    LEFT JOIN  [umasnet].[dbo].[RA_JORNADADOC] t4 ON t4 .CODJORNADA = t2.CODJORNADA 
    LEFT JOIN  [umasnet].[dbo].[RA_GRADODOC] t5 ON t2.CODGRADO = t5.CODGRADO 
    GROUP BY t1.[ano]
    ORDER BY t1.[ano] DESC
    """

    df = pd.read_sql(sql_query, db_engine)

    return df

#print(query_docentes_tipo_contrato())

def query_docentes_tasa_rotacion():

    sql_query = f"""
    WITH academicos_por_ano AS (
    SELECT 
        [ANO],
        [CODPROF]
    FROM 
        [umasnet].[dbo].[RA_CTLPRF]
    GROUP BY 
         [ANO], [CODPROF]
    ), 

    continuos AS (
        SELECT 
            a1.[ANO] AS ano_actual,
            a2.[ANO] AS ano_siguiente,
            a1.[CODPROF]
        FROM 
            academicos_por_ano a1
        JOIN 
            academicos_por_ano a2 
            ON a1.[CODPROF] = a2.[CODPROF] AND a2.[ANO]= a1.[ANO] + 1
    ),tasa_rotacion AS (
        SELECT 
            a.[ANO] AS ano_actual,
            COUNT(DISTINCT a.[CODPROF] ) AS total_ano_actual,
            COUNT(DISTINCT c.[CODPROF] ) AS continuos_ano_siguiente,
            (1 - CAST(COUNT(DISTINCT c.[CODPROF] ) AS FLOAT) / COUNT(DISTINCT a.[CODPROF] )) * 100 AS tasa_rotacion
        FROM 
            academicos_por_ano a
        LEFT JOIN 
            continuos c ON a.[ANO] = c.ano_actual
        GROUP BY 
            a.[ANO]
    )SELECT TOP(7)
        ano_actual AS AÑO,
        total_ano_actual AS Total_Academicos,
        continuos_ano_siguiente AS Permanecen_Siguiente_Año,
        tasa_rotacion AS Tasa_Rotacion_Porcentaje
    FROM 
        tasa_rotacion
    ORDER BY 
        ano_actual DESC;
    """

    df = pd.read_sql(sql_query, db_engine)

    return df

def query_docentes_horario():

    sql_query = f"""
    SELECT TOP(10) [ano] AS AÑO,COUNT(DISTINCT t1.[codprof]) AS cantidad,
		COUNT(DISTINCT CASE WHEN t4.DESCRIPCION  IS NOT NULL AND  t4.DESCRIPCION = 'COMPLETA' THEN t1.[codprof] END) AS COMPLETA,
		COUNT(DISTINCT CASE WHEN t4.DESCRIPCION  IS NOT NULL AND  t4.DESCRIPCION = 'MEDIA' THEN t1.[codprof] END) AS MEDIA,
		COUNT(DISTINCT CASE WHEN t4.DESCRIPCION  IS NOT NULL AND  t4.DESCRIPCION = 'HORAS' THEN t1.[codprof] END) AS HORAS
		

    FROM [umasnet].[dbo].[RA_HORASCONT] t1
    JOIN [umasnet].[dbo].[RA_PROFES] t2 ON t2.CODPROF = t1.codprof
    LEFT JOIN  [umasnet].[dbo].[RA_TITULODOC] t3 ON t2.CODTITULO = t3.CODTITULO
    LEFT JOIN  [umasnet].[dbo].[RA_JORNADADOC] t4 ON t4 .CODJORNADA = t2.CODJORNADA 
    LEFT JOIN  [umasnet].[dbo].[RA_GRADODOC] t5 ON t2.CODGRADO = t5.CODGRADO 
    GROUP BY t1.[ano]
    ORDER BY t1.[ano] DESC"""

    df = pd.read_sql(sql_query, db_engine)

    return df

def query_reprobados_primer_anio_filtrada(jornada="Todas", genero="Todos"):
    
    filtro_j = f"AND t2.JORNADA = '{jornada}'" if jornada != "Todas" else ""
    filtro_g = f"AND t3.SEXO = '{genero}'" if genero != "Todos" else ""

    sql_query = f"""
    WITH Equivalencias AS (
    -- 1. Normalización de códigos de ramos
    SELECT 
        E.CODRAMO AS Original,
        COALESCE(E.RAMOEQUIV, E.CODRAMO) AS Equivalente
    FROM [umasnet].[dbo].[RA_EQUIV] E
    ),
    Universo_Activo_P1 AS (
        SELECT 
            t2.ANO AS COHORTE,
            t2.JORNADA,
            t3.SEXO,
            COUNT(DISTINCT t2.CODCLI) AS TOTAL_ALUMNOS_CON_NOTAS
        FROM [umasnet].[dbo].[MT_ALUMNO] t2
        JOIN [umasnet].[dbo].[MT_CLIENT] t3 ON t2.RUT = t3.CODCLI
        JOIN [umasnet].[dbo].[RA_NOTA] t1 ON t1.CODCLI = t2.CODCLI AND t1.ANO = t2.ANO
        WHERE t2.ANO = (2000 + CAST(LEFT(t2.CODCLI, 2) AS INT)) 
        AND t1.PERIODO = 1 
        GROUP BY t2.ANO, t2.JORNADA, t3.SEXO
    ),
    Reprobados_Detalle AS (
        -- 3. Conteo de todas las reprobaciones por cada ramo en el P1 del primer año
        SELECT
            t2.ANO AS COHORTE,
            t2.JORNADA,
            t3.SEXO,
            COALESCE(EQ.Equivalente, t1.CODRAMO) AS CODRAMO,
            COUNT(t1.CODCLI) AS CANTIDAD_REPROBACIONES -- Aquí se cuentan las 5 si reprueba 5
        FROM [umasnet].[dbo].[RA_NOTA] t1
        JOIN [umasnet].[dbo].[MT_ALUMNO] t2 ON t1.CODCLI = t2.CODCLI
        JOIN [umasnet].[dbo].[MT_CLIENT] t3 ON t2.RUT = t3.CODCLI
        LEFT JOIN Equivalencias EQ ON t1.CODRAMO = EQ.Original
        WHERE t1.ESTADO = 'R' 
        AND t1.ANO = t2.ANO
        AND t1.PERIODO = 1
        AND t2.ANO = (2000 + CAST(LEFT(t2.CODCLI, 2) AS INT))
        {filtro_j} 
        {filtro_g}
        GROUP BY t2.ANO, t2.JORNADA, t3.SEXO, COALESCE(EQ.Equivalente, t1.CODRAMO)
    )
    SELECT 
        R.COHORTE,
        R.CODRAMO,
        R.JORNADA,
        R.SEXO AS GENERO,
        R.CANTIDAD_REPROBACIONES,
        U.TOTAL_ALUMNOS_CON_NOTAS AS UNIVERSO_P1,
        ROUND((CAST(R.CANTIDAD_REPROBACIONES AS FLOAT) / U.TOTAL_ALUMNOS_CON_NOTAS) * 100, 2) AS TASA_REPROBACION_P1
    FROM Reprobados_Detalle R
    JOIN Universo_Activo_P1 U 
        ON R.COHORTE = U.COHORTE 
        AND R.JORNADA = U.JORNADA 
        AND R.SEXO = U.SEXO
    ORDER BY R.COHORTE ASC, R.CODRAMO;
    """

    df = pd.read_sql(sql_query, db_engine)

    return df

#print(query_reprobados_primer_anio_filtrada(jornada="V", genero="F"))

def query_reprobados_historico_simple(jornada="Todas", genero="Todos"):
    
    filtro_j = f"AND T2.JORNADA = '{jornada}'" if jornada != "Todas" else ""
    filtro_g = f"AND T4.SEXO = '{genero}'" if genero != "Todos" else ""

    sql_query = f"""
    WITH Equivalencias AS (
        SELECT E.CODRAMO AS Original, COALESCE(E.RAMOEQUIV, E.CODRAMO) AS Equivalente
        FROM [umasnet].[dbo].[RA_EQUIV] E
    )
    SELECT 
        T2.ANO AS ANIO,
        COALESCE(E.Equivalente, T1.CODRAMO) AS CODRAMO,
        T4.SEXO AS GENERO,
        T2.JORNADA, 
        COUNT(T1.CODCLI) AS CANTIDAD_REPROBACIONES
    FROM [umasnet].[dbo].[RA_NOTA] T1
    LEFT JOIN [umasnet].[dbo].[MT_ALUMNO] T2 ON T1.CODCLI = T2.CODCLI
    LEFT JOIN [umasnet].[dbo].[MT_CLIENT] T4 ON T2.RUT = T4.CODCLI
    LEFT JOIN [umasnet].[dbo].[RA_RAMO] T3 ON T3.CODRAMO = T1.CODRAMO
    LEFT JOIN Equivalencias E ON T1.CODRAMO = E.Original
    WHERE T1.ESTADO = 'R' 
        AND T2.ANO >= 2000 
        AND T3.ESTADO = 'VIGENTE'
        {filtro_j} 
        {filtro_g}
    GROUP BY 
        T2.ANO, 
        COALESCE(E.Equivalente, T1.CODRAMO),
        T4.SEXO, 
        T2.JORNADA
    ORDER BY T2.ANO ASC;
    """
    return pd.read_sql(sql_query, db_engine)

#print(query_reprobados_historico_simple(jornada="D", genero="F"))
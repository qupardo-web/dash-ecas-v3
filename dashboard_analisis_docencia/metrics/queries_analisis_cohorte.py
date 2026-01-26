from conn_db import *
import pandas as pd

db_engine = get_db_engine_umasnet()

limite_año= 2019

def obtener_distribucion_historica_ingreso(jornada="Todas", genero="Todos"):
    
    filtro_j = f"AND t1.JORNADA = '{jornada}'" if jornada != "Todas" else ""
    filtro_g = f"AND t2.SEXO = '{genero}'" if genero != "Todos" else ""

    sql_query = f"""
    WITH COHORTES_VALIDAS AS (
        SELECT DISTINCT t1.CODCLI
        FROM [umasnet].[dbo].[RA_NOTA] t1
        JOIN [umasnet].[dbo].[MT_ALUMNO] t2 ON t1.CODCLI = t2.CODCLI
        WHERE t1.ANO = t2.ANO
        AND t2.PERIODO = 1
    ) 
    SELECT 
        t1.ANO AS COHORTE,
        t1.JORNADA,
        t2.SEXO AS GENERO,
        COUNT(1) AS CANTIDAD
    FROM [umasnet].[dbo].[MT_ALUMNO] t1
    JOIN [umasnet].[dbo].[MT_CLIENT] t2 ON t2.CODCLI = t1.RUT
    JOIN COHORTES_VALIDAS t3 ON t1.CODCLI = t3.CODCLI
    WHERE t1.ANO >= {limite_año} 
      {filtro_j}
      {filtro_g}
    GROUP BY t1.ANO, t1.JORNADA, t2.SEXO
    ORDER BY t1.ANO DESC, t1.JORNADA, t2.SEXO
    """

    df = pd.read_sql(sql_query, db_engine)

    return df

#print(obtener_distribucion_historica_ingreso())

def obtener_distribucion_nacionalidad_ingreso(jornada="Todas", genero="Todos"):

    filtro_j = f"AND t1.JORNADA = '{jornada}'" if jornada != "Todas" else ""
    filtro_g = f"AND t2.SEXO = '{genero}'" if genero != "Todos" else ""

    sql_query = f"""
    WITH COHORTES_VALIDAS AS (
        SELECT DISTINCT t1.CODCLI
        FROM [umasnet].[dbo].[RA_NOTA] t1
        JOIN [umasnet].[dbo].[MT_ALUMNO] t2 ON t1.CODCLI = t2.CODCLI
        WHERE t1.ANO = t2.ANO 
          AND t2.PERIODO = 1
          AND t2.ANO >= {limite_año} 
    ) 
    SELECT 
        t1.ANO AS COHORTE,
        t2.NACIONALIDAD,
        t1.JORNADA,
        t2.SEXO AS GENERO,
        COUNT(t1.CODCLI) AS CANTIDAD
    FROM [umasnet].[dbo].[MT_ALUMNO] t1
    JOIN [umasnet].[dbo].[MT_CLIENT] t2 ON t2.CODCLI = t1.RUT
    JOIN COHORTES_VALIDAS t3 ON t1.CODCLI = t3.CODCLI
    WHERE 1=1
      {filtro_j}
      {filtro_g}
    GROUP BY t1.ANO, t2.NACIONALIDAD, t1.JORNADA, t2.SEXO
    ORDER BY t1.ANO DESC, t2.NACIONALIDAD ASC
    """

    df = pd.read_sql(sql_query, db_engine)

    return df 

#print(obtener_distribucion_nacionalidad_ingreso())

def obtener_distribucion_comuna_historica(jornada="Todas", genero="Todos"):
    
    filtro_j = f"AND t1.JORNADA = '{jornada}'" if jornada != "Todas" else ""
    filtro_g = f"AND t2.SEXO = '{genero}'" if genero != "Todos" else ""

    sql_query = f"""
    WITH COHORTES_VALIDAS AS (
        -- Identificación de novatos en su primer semestre real
        SELECT DISTINCT t1.CODCLI
        FROM [umasnet].[dbo].[RA_NOTA] t1
        JOIN [umasnet].[dbo].[MT_ALUMNO] t2 ON t1.CODCLI = t2.CODCLI
        WHERE t1.ANO = t2.ANO 
          AND t2.PERIODO = 1
          AND t2.ANO >= {limite_año} 
    ) 
    SELECT 
        t1.ANO AS COHORTE,
        t2.COMUNA,
        t1.JORNADA,
        t2.SEXO AS GENERO,
        COUNT(t1.CODCLI) AS CANTIDAD
    FROM [umasnet].[dbo].[MT_ALUMNO] t1
    JOIN [umasnet].[dbo].[MT_CLIENT] t2 ON t2.CODCLI = t1.RUT
    JOIN COHORTES_VALIDAS t3 ON t1.CODCLI = t3.CODCLI
    WHERE 1=1
      {filtro_j}
      {filtro_g}
    GROUP BY t1.ANO, t2.COMUNA, t1.JORNADA, t2.SEXO
    ORDER BY t1.ANO DESC, t2.COMUNA ASC
    """
    df = pd.read_sql(sql_query, db_engine)

    return df

# print(obtener_distribucion_comuna_historica())

# def obtener_distribucion_edad_historica(jornada="Todas", genero="Todos"):
    
#     filtro_j = f"AND t1.JORNADA = '{jornada}'" if jornada != "Todas" else ""
#     filtro_g = f"AND t2.SEXO = '{genero}'" if genero != "Todos" else ""

#     sql_query = f"""
#     WITH COHORTES_VALIDAS AS (
#         -- Identificación de novatos en su primer semestre real
#         SELECT DISTINCT t1.CODCLI
#         FROM [umasnet].[dbo].[RA_NOTA] t1
#         JOIN [umasnet].[dbo].[MT_ALUMNO] t2 ON t1.CODCLI = t2.CODCLI
#         WHERE t1.ANO = t2.ANO 
#           AND t2.PERIODO = 1
#           AND t2.ANO >= 2000 
#     ) 
#     SELECT 
#         t1.ANO AS COHORTE,
#         DATEDIFF(YEAR, t2.FECNAC, GETDATE()) -
#             CASE 
#                 WHEN MONTH(t2.FECNAC) > MONTH(GETDATE()) OR 
#                     (MONTH(t2.FECNAC) = MONTH(GETDATE()) AND DAY(t2.FECNAC) > DAY(GETDATE())) 
#                 THEN 1 ELSE 0 
#             END AS EDAD,
#         t1.JORNADA,
#         t2.SEXO AS GENERO,
#         COUNT(t1.CODCLI) AS CANTIDAD
#     FROM [umasnet].[dbo].[MT_ALUMNO] t1
#     JOIN [umasnet].[dbo].[MT_CLIENT] t2 ON t2.CODCLI = t1.RUT
#     JOIN COHORTES_VALIDAS t3 ON t1.CODCLI = t3.CODCLI
#     WHERE (DATEDIFF(YEAR, t2.FECNAC, GETDATE()) -
#             CASE 
#                 WHEN MONTH(t2.FECNAC) > MONTH(GETDATE()) OR 
#                     (MONTH(t2.FECNAC) = MONTH(GETDATE()) AND DAY(t2.FECNAC) > DAY(GETDATE())) 
#                 THEN 1 ELSE 0 
#             END) > 16 -- Filtro de edad mínima solicitado
#       {filtro_j}
#       {filtro_g}
#     GROUP BY 
#         t1.ANO, 
#         t1.JORNADA, 
#         t2.SEXO,
#         DATEDIFF(YEAR, t2.FECNAC, GETDATE()) -
#             CASE 
#                 WHEN MONTH(t2.FECNAC) > MONTH(GETDATE()) OR 
#                     (MONTH(t2.FECNAC) = MONTH(GETDATE()) AND DAY(t2.FECNAC) > DAY(GETDATE())) 
#                 THEN 1 ELSE 0 
#             END
#     ORDER BY t1.ANO DESC, EDAD ASC
#     """

#     df = pd.read_sql(sql_query, db_engine)

#     return df

#print(obtener_distribucion_edad_historica())

#La versión incluida en el dashboard anterior calculaba edades actuales, no de ingreso.
def obtener_distribucion_edad_historica(jornada="Todas", genero="Todos"):
    
    filtro_j = f"AND t1.JORNADA = '{jornada}'" if jornada != "Todas" else ""
    filtro_g = f"AND t2.SEXO = '{genero}'" if genero != "Todos" else ""

    sql_query = f"""
    WITH COHORTES_VALIDAS AS (
        SELECT DISTINCT t1.CODCLI
        FROM [umasnet].[dbo].[RA_NOTA] t1
        JOIN [umasnet].[dbo].[MT_ALUMNO] t2 ON t1.CODCLI = t2.CODCLI
        WHERE t1.ANO = t2.ANO 
          AND t2.PERIODO = 1
          AND t2.ANO >= {limite_año}
    ) 
    SELECT 
        t1.ANO AS COHORTE,
        -- Calculamos la edad al momento de ingresar (COHORTE - Año Nacimiento)
        (t1.ANO - YEAR(t2.FECNAC)) AS EDAD,
        t1.JORNADA,
        t2.SEXO AS GENERO,
        COUNT(t1.CODCLI) AS CANTIDAD
    FROM [umasnet].[dbo].[MT_ALUMNO] t1
    JOIN [umasnet].[dbo].[MT_CLIENT] t2 ON t2.CODCLI = t1.RUT
    JOIN COHORTES_VALIDAS t3 ON t1.CODCLI = t3.CODCLI
    WHERE 1=1
      -- Filtro de edad de ingreso mínima
      AND (t1.ANO - YEAR(t2.FECNAC)) > 16 
      {filtro_j}
      {filtro_g}
    GROUP BY 
        t1.ANO, 
        t1.JORNADA, 
        t2.SEXO,
        (t1.ANO - YEAR(t2.FECNAC))
    ORDER BY t1.ANO DESC, EDAD ASC
    """

    df = pd.read_sql(sql_query, db_engine)
    return df

def obtener_distribucion_via_admision_historica(jornada="Todas", genero="Todos"):

    filtro_j = f"AND t1.JORNADA = '{jornada}'" if jornada != "Todas" else ""
    filtro_g = f"AND t2.SEXO = '{genero}'" if genero != "Todos" else ""

    sql_query = f"""
    WITH COHORTES_VALIDAS AS (
        -- Identificación de novatos en su primer semestre real
        SELECT DISTINCT t1.CODCLI
        FROM [umasnet].[dbo].[RA_NOTA] t1
        JOIN [umasnet].[dbo].[MT_ALUMNO] t2 ON t1.CODCLI = t2.CODCLI
        WHERE t1.ANO = t2.ANO 
          AND t2.PERIODO = 1
          AND t2.ANO >= {limite_año}
    ) 
    SELECT 
        t1.ANO AS COHORTE,
        COALESCE(t4.DESCRIPCION, 'SIN ESPECIFICAR') AS VIA_ADMISION,
        t1.JORNADA,
        t2.SEXO AS GENERO,
        COUNT(t1.CODCLI) AS CANTIDAD
    FROM [umasnet].[dbo].[MT_ALUMNO] t1
    JOIN [umasnet].[dbo].[MT_CLIENT] t2 ON t2.CODCLI = t1.RUT
    LEFT JOIN [umasnet].[dbo].[MT_VIADMISION] t4 ON t2.VIADMISION = t4.COD_VIA
    JOIN COHORTES_VALIDAS t3 ON t1.CODCLI = t3.CODCLI
    WHERE 1=1
      {filtro_j}
      {filtro_g}
    GROUP BY 
        t1.ANO, 
        t4.DESCRIPCION,
        t1.JORNADA, 
        t2.SEXO
    ORDER BY t1.ANO DESC, CANTIDAD DESC
    """

    df = pd.read_sql(sql_query, db_engine)

    return df

def obtener_distribucion_modalidad_historica(jornada="Todas", genero="Todos"):
    
    filtro_j = f"AND t1.JORNADA = '{jornada}'" if jornada != "Todas" else ""
    filtro_g = f"AND t2.SEXO = '{genero}'" if genero != "Todos" else ""

    sql_query = f"""
    WITH COHORTES_VALIDAS AS (
        -- Identificación de novatos en su primer semestre real
        SELECT DISTINCT t1.CODCLI
        FROM [umasnet].[dbo].[RA_NOTA] t1
        JOIN [umasnet].[dbo].[MT_ALUMNO] t2 ON t1.CODCLI = t2.CODCLI
        WHERE t1.ANO = t2.ANO 
          AND t2.PERIODO = 1
          AND t2.ANO >= {limite_año}
    ) 
    SELECT 
        t1.ANO AS COHORTE,
        COALESCE(t4.DESCRIPCION, 'NO DEFINIDA') AS MODALIDAD,
        t1.JORNADA,
        t2.SEXO AS GENERO,
        COUNT(t1.CODCLI) AS CANTIDAD
    FROM [umasnet].[dbo].[MT_ALUMNO] t1
    JOIN [umasnet].[dbo].[MT_CLIENT] t2 ON t2.CODCLI = t1.RUT
    LEFT JOIN [umasnet].[dbo].[MT_MODALIDAD] t4 ON t4.CODMODALIDAD = t2.CodModalidad
    JOIN COHORTES_VALIDAS t3 ON t1.CODCLI = t3.CODCLI
    WHERE 1=1
      {filtro_j}
      {filtro_g}
    GROUP BY 
        t1.ANO, 
        t4.DESCRIPCION,
        t1.JORNADA, 
        t2.SEXO
    ORDER BY t1.ANO DESC, CANTIDAD DESC
    """

    df = pd.read_sql(sql_query, db_engine)
    
    return df

def obtener_metricas_titulacion_seguimiento(jornada="Todas", genero="Todos", anios_seguimiento=4):
    """
    Calcula la tasa de titulación para una cohorte X tras N años de seguimiento.
    Ejemplo: Para cohorte 2010 con anios_seguimiento=4, cuenta titulados hasta 2014 inclusive.
    """
    
    filtro_j = f"AND t1.JORNADA = '{jornada}'" if jornada != "Todas" else ""
    filtro_g = f"AND t2.SEXO = '{genero}'" if genero != "Todos" else ""

    sql_query = f"""
    WITH COHORTES_VALIDAS AS (
        SELECT DISTINCT t1.CODCLI
        FROM [umasnet].[dbo].[RA_NOTA] t1
        JOIN [umasnet].[dbo].[MT_ALUMNO] t2 ON t1.CODCLI = t2.CODCLI
        WHERE t1.ANO = t2.ANO
          AND t2.PERIODO = 1
          AND t2.ANO >= {limite_año}
    ) 
    SELECT 
        t1.[ANO] AS COHORTE,
        t1.[JORNADA],
        t2.[SEXO] AS GENERO,
        COUNT(1) AS CANTIDAD,
        COUNT(CASE 
            WHEN t1.ESTACAD = 'TITULADO' 
            AND t1.ANOTIT <= (t1.ANO + {anios_seguimiento}) THEN 1 
        END) AS TITULADOS_PLAZO,
        COUNT(1) - COUNT(CASE 
            WHEN t1.ESTACAD = 'TITULADO' 
            AND t1.ANOTIT <= (t1.ANO + {anios_seguimiento}) THEN 1 
        END) AS RESTO_COHORTE
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


#print(obtener_metricas_titulacion_seguimiento(anios_seguimiento=6))
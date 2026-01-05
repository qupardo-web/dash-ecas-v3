from conn_db import get_db_engine
from sqlalchemy import text

db_engine = get_db_engine()

def actualizar_tabla_egresados_ecas():
    # Definimos la query de inserción
    query_insert = text("""
    IF OBJECT_ID('[DBMatriculas].[dbo].[alumnos_ecas_egresados_unificada]', 'U') IS NOT NULL
        DROP TABLE [DBMatriculas].[dbo].[alumnos_ecas_egresados_unificada];

    SELECT DISTINCT e.*
    INTO [DBMatriculas].[dbo].[alumnos_ecas_egresados_unificada]
    FROM [DBMatriculas].[dbo].[vista_egresados_unificada] e
    WHERE EXISTS (
        SELECT 1 
        FROM [DBMatriculas].[dbo].[tabla_dashboard_permanencia] p 
        WHERE p.mrun = e.mrun AND p.cod_inst = 104
    );
    """)

    try:
        with db_engine.connect() as conn:
            conn.execute(query_insert)
            conn.commit()
            print("Tabla de egresados vinculados a ECAS actualizada con éxito.")
    except Exception as e:
        print(f"Error al actualizar la tabla: {e}")

# Ejecutar la actualización
actualizar_tabla_egresados_ecas()
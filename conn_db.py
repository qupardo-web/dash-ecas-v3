from sqlalchemy import create_engine
import urllib

SERVER = '192.168.1.194'
SERVER_PERSONAL = 'QUPARDO'
USERNAME = 'jraby'
PASSWORD = '123'
DATABASE_UMAS = 'umasnet'
DATABASE_MRUN = 'DATOSACADEMICOS'
DATABASE = 'DATOSACADEMICOS'
DRIVER_NAME = 'ODBC Driver 17 for SQL Server' 

def get_db_engine_personal():
    """Establece y devuelve el motor de conexión (Engine) a SQL Server usando Autenticación de Windows."""
    try:
        
        DRIVER = urllib.parse.quote_plus(DRIVER_NAME)
        
        DB_URL = f"mssql+pyodbc://{SERVER_PERSONAL}/{DATABASE}?driver={DRIVER}&trusted_connection=yes"
        
        engine = create_engine(DB_URL, fast_executemany=True)
        
        # Probar la conexión
        with engine.connect():
            return engine
            
    except Exception as e:
        print("="*50)
        print(f"ERROR DE CONEXIÓN A SQL SERVER: {e}")
        print(f"Revisa el nombre del servidor ({SERVER}) y el driver ({DRIVER_NAME}).")
        print("="*50)
        return None

def get_db_engine():
        connection_string = (
            f"mssql+pyodbc://{USERNAME}:{PASSWORD}@{SERVER}/{DATABASE_MRUN}"
            "?driver=ODBC+Driver+17+for+SQL+Server"
            "&MultipleActiveResultSets=True"
                )
        engine = create_engine(connection_string)
        
        with engine.connect():
            return engine

def get_db_engine_umasnet():
        connection_string = (
            f"mssql+pyodbc://{USERNAME}:{PASSWORD}@{SERVER}/{DATABASE_UMAS}"
            "?driver=ODBC+Driver+17+for+SQL+Server"
            "&MultipleActiveResultSets=True"
                )
        engine = create_engine(connection_string)
        
        with engine.connect():
            return engine

# def get_db_engine_umasnet_2():
#         connection_string = (
#             f"mssql+pyodbc://{USERNAME2}:{PASSWORD2}@{SERVER_MRUN}/{DATABASE_MRUN}"
#             "?driver=ODBC+Driver+17+for+SQL+Server"
#             "&MultipleActiveResultSets=True"
#                 )
#         engine = create_engine(connection_string)
        
#         with engine.connect():
#             return engine
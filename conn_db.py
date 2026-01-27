from sqlalchemy import create_engine
import urllib

SERVER = 'QUPARDO'
DATABASE1 = 'DBMatriculas'
DATABASE2 = 'DATOSACADEMICOS'
DRIVER_NAME = 'ODBC Driver 17 for SQL Server' 

SERVER2 = '192.168.1.194'
USERNAME2 = 'jraby'
DATABASE3 = 'umasnet'
PASSWORD2 = '123'

def get_db_engine():
    """Establece y devuelve el motor de conexión (Engine) a SQL Server usando Autenticación de Windows."""
    try:
        
        DRIVER = urllib.parse.quote_plus(DRIVER_NAME)
        
        DB_URL = f"mssql+pyodbc://{SERVER}/{DATABASE2}?driver={DRIVER}&trusted_connection=yes"
        
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

def get_db_engine_umasnet():
        connection_string = (
            f"mssql+pyodbc://{USERNAME2}:{PASSWORD2}@{SERVER2}/{DATABASE3}"
            "?driver=ODBC+Driver+17+for+SQL+Server"
            "&MultipleActiveResultSets=True"
                )
        engine = create_engine(connection_string)
        
        with engine.connect():
            return engine
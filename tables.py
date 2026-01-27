import pandas as pd
import os
from conn_db import *
from sqlalchemy import create_engine, Integer, String, Float, BigInteger
from sqlalchemy import text

# Conexión a la base de datos
engine = get_db_engine()

DTYPE_MAP = {
    'cat_periodo': Integer(),
    'codigo_unico': String(50),
    'mrun': String(50),
    'gen_alu': Integer(),
    'rango_edad' : String(50),
    'fec_nac_alu': Integer(),
    'anio_ing_carr_ori': Integer(),
    'sem_ing_carr_ori' : String(10),
    'anio_ing_carr_act' : Integer(),
    'sem_ing_carr_act' : String(10),
    'tipo_inst_1' : String(255),
    'tipo_inst_2' : String(255),
    'tipo_inst_3' : String(255),
    'cod_inst': Integer(),
    'nomb_inst' : String(255),
    'cod_sede': Integer(),
    'nomb_sede': String(255),
    'cod_carrera': Integer(),
    'nomb_carrera': String(255),
    'modalidad': String(50),
    'jornada': String(50),
    'version': String(50),
    'tipo_plan_carr': String(50),
    'dur_estudio_carr': Integer(),
    'dur_proceso_tit': Integer(),
    'dur_total_carr': Integer(),
    'region_sede': String(100),
    'provincia_sede': String(100),
    'comuna_sede': String(100),
    'nivel_global': String(100),
    'nivel_carrera_1': String(100),
    'nivel_carrera_2': String(100),
    'requisito_ingreso': String(255),
    'vigencia_carrera': String(50),
    'valor_matricula': String(50), 
    'valor_arancel': String(50),
    'codigo_demre': String(50),
    'area_conocimiento': String(255),
    'cine_f_97_area': String(255),
    'cine_f_97_subarea': String(255),
    'area_carrera_generica': String(255),
    'cine_f_13_area': String(255),
    'cine_f_13_subarea': String(255),
    'acreditada_carr': String(50),
    'acreditada_inst': String(50),
    'acre_inst_desde_hasta': String(50),
    'acre_inst_anio': Integer(),
    'costo_proceso_titulacion': String(255),
    'costo_obtencion_titulo_diploma': String(255),
    'costo_obtencion_titulo_diploma': String(255),
    'forma_de_ingreso': String(255)
}

# Mapeo basado fielmente en tu descripción
DTYPE_TITULADOS = {
    'cat_periodo': String(50),
    'codigo_unico': String(100),
    'mrun': BigInteger(),
    'gen_alu': Integer(),
    'fec_nac_alu': Integer(),
    'rango_edad': String(100),
    'año_ing_carr_ori': Integer(),
    'sem_ing_carr_ori': Integer(),
    'año_ing_carr_act': Integer(),
    'sem_ing_carr_act': Integer(),
    'nomb_titulo_obtenido': String(500),
    'nomb_grado_obtenido': String(500),
    'fecha_obtencion_titulo': Integer(),
    'tipo_inst_1': String(100),
    'tipo_inst_2': String(100),
    'tipo_inst_3': String(100),
    'cod_inst': Integer(),
    'nomb_inst': String(255),
    'cod_sede': Integer(),
    'nomb_sede': String(255),
    'cod_carrera': Integer(),
    'nomb_carrera': String(255),
    'nivel_global': String(100),
    'nivel_carrera_1': String(100),
    'nivel_carrera_2': String(100),
    'dur_estudio_carr': Integer(),
    'dur_proceso_tit': Integer(),
    'dur_total_carr': Integer(),
    'region_sede': String(150),
    'provincia_sede': String(150),
    'comuna_sede': String(150),
    'jornada': String(100),
    'modalidad': String(100),
    'version': Integer(),
    'tipo_plan_carr': String(100),
    'area_conocimiento': String(150),
    'cine_f_97_area': String(255),
    'cine_f_97_subarea': String(255),
    'area_generica': String(255),
    'cine_f_13_area': String(255),
    'cine_f_13_subarea': String(255)
}

DTYPE_EGRESADOS = {
    'periodo': Integer(),
    'mrun': BigInteger(),
    'mascara_provisoria': BigInteger(),
    'rbd': Integer(),
    'cod_region': Integer(),
    'nomb_region': String(50),
    'cod_provincia': Integer(),
    'cod_comuna': Integer(),
    'nomb_comuna': String(150),
    'cod_departamento': Integer(),
    'nomb_departamento': String(255),
    'cod_ensenianza': Integer(),
    'cod_grado': Integer(),
    'cod_dependencia': Integer(),
    'cod_dep_agrupado': Integer(),
    'indice_rural': Integer(),
    'prom_notas_alu': Float(),
    'origen_dato': String(100),
    'ense_completa': Integer(),
    'marca_egreso': Integer()
}

def cargar_matriculas_con_mapeo():
    path = 'datos'
    archivos = [f for f in os.listdir(path) if f.endswith('.csv')]

    columnas_maestras = list(DTYPE_MAP.keys())

    primera_carga = True
    
    for archivo in archivos:
        print(f"Procesando: {archivo}")
        
        df = pd.read_csv(os.path.join(path, archivo), sep=';', encoding='utf-8', dtype=str)
        
        df.columns = [c.strip().lower().replace('ï»¿', '') for c in df.columns]
        
        df = df.reindex(columns=columnas_maestras)
        
        df = df.where(pd.notnull(df), None)

        cols_con_datos = df.columns[df.notnull().any()].tolist()
        print(f"Columnas con datos detectadas: {len(cols_con_datos)} de {len(columnas_maestras)}")

        modo = 'replace' if primera_carga else 'append'

        try:
            df.to_sql(
                'matriculas_mrun', 
                con=engine, 
                if_exists=modo, 
                index=False,
                chunksize=50000, 
                dtype=DTYPE_MAP
            )
            print(f"--- Éxito: {archivo} cargado ({len(df)} filas) ---")
        except Exception as e:
            print(f"!!! Error al insertar {archivo}: {e}")

def cargar_titulados_con_mapeo():
    path = 'titulados'
    archivos = [f for f in os.listdir(path) if f.endswith('.csv')]

    primera_carga = True
    
    for archivo in archivos:
        print(f"Procesando: {archivo}")
        
        df = pd.read_csv(os.path.join(path, archivo), sep=';', encoding='utf-8', dtype=str)
        
        df = df.where(pd.notnull(df), None)

        modo = 'replace' if primera_carga else 'append'

        try:
            df.to_sql(
                'titulados_mrun', 
                con=engine, 
                if_exists=modo, 
                index=False,
                chunksize=50000, 
                dtype=DTYPE_MAP
            )
            print(f"--- Éxito: {archivo} cargado ({len(df)} filas) ---")

            primera_carga = False

        except Exception as e:
            print(f"!!! Error al insertar {archivo}: {e}")

def actualizar_campos_titulados():

    query_update = text("""
    UPDATE titulados_mrun
    SET nombre_titulo_obtenido = CASE 
        WHEN nombre_titulo_obtenido IN (
            'TECNICO DE NIVEL SUPERIOR EN CONTABILIDAD', 
            'CONTADOR TECNICO DE NIVEL SUPERIOR'
        ) THEN 'CONTADOR TECNICO DE NIVEL SUPERIOR'
        
        WHEN nombre_titulo_obtenido IS NULL AND cod_inst = 104 
        THEN 'CONTADOR AUDITOR'
        
        ELSE nombre_titulo_obtenido 
    END
    WHERE cod_inst = 104 OR nombre_titulo_obtenido IS NULL OR nombre_titulo_obtenido LIKE '%TECNICO%';
    """)

    with engine.connect() as conn:
        conn.execute(query_update)
        conn.commit()

def cargar_egresados():
    path = 'egresados'
    tabla_destino = 'egresados_mrun' # Ahora será tu tabla física maestra
    
    # 1. Definir el mapeo de nombres (Origen CSV -> Destino SQL)
    MAPA_COLUMNAS = {
        'AGNO': 'periodo',
        'MRUN': 'mrun',
        'MRUN_IPE': 'mascara_provisoria',
        'RBD': 'rbd',
        'COD_REG_RBD': 'cod_region',
        'NOM_REG_RBD_A': 'nomb_region',
        'COD_PRO_RBD': 'cod_provincia',
        'COD_COM_RBD': 'cod_comuna',
        'NOM_COM_RBD': 'nomb_comuna',
        'COD_DEPROV_RBD': 'cod_departamento',
        'NOM_DEPROV_RBD': 'nomb_departamento',
        'COD_ENSE': 'cod_ensenianza',
        'COD_GRADO': 'cod_grado',
        'COD_DEPE': 'cod_dependencia',
        'COD_DEPE2': 'cod_dep_agrupado',
        'RURAL_RBD': 'indice_rural',
        'PROM_NOTAS_ALU': 'prom_notas_alu',
        'ORIGEN': 'origen_dato',
        'ENSE_COMPLETA': 'ense_completa',
        'MARCA_EGRESO': 'marca_egreso'
    }

    archivos = [f for f in os.listdir(path) if f.endswith('.csv')]

    primera_carga = True
    
    for archivo in archivos:
        print(f"Procesando: {archivo}")
        
        df = pd.read_csv(os.path.join(path, archivo), sep=';', encoding='utf-8-sig', dtype=str)

        df.columns = [c.strip().replace('ï»¿', '') for c in df.columns]

        if 'PROM_NOTAS_ALU' in df.columns:
            df['PROM_NOTAS_ALU'] = df['PROM_NOTAS_ALU'].str.replace(',', '.')

        df = df.rename(columns=MAPA_COLUMNAS)

        df = df.replace(r'^\s*$', None, regex=True)
        df = df.where(pd.notnull(df), None)
        
        columnas_finales = [c for c in MAPA_COLUMNAS.values() if c in df.columns]
        df = df[columnas_finales]

        modo = 'replace' if primera_carga else 'append'

        try:
            df.to_sql(
                tabla_destino, 
                con=engine, 
                if_exists=modo, # <-- Aquí ocurre la magia
                index=False, 
                dtype=DTYPE_EGRESADOS, 
                chunksize=50000
            )
            print(f"Archivo {archivo} cargado exitosamente (Modo: {modo}).")
            
            # Después del primer archivo, cambiamos a modo append
            primera_carga = False

        except Exception as e:
            print(f"Error crítico en archivo {archivo}: {e}")

#cargar_matriculas_con_mapeo()
#cargar_titulados_con_mapeo()
#actualizar_campos_titulados()
cargar_egresados()
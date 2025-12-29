import os
import pandas as pd
from typing import Optional, List
from utilities.aux_funcs import *
import numpy as np


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILE_DESTINO = os.path.join(BASE_DIR, 'utilities', 'files', 'fuga_a_destino_todas_cohortes.xlsx')
FILE_ABANDONO = os.path.join(BASE_DIR, 'utilities', 'files', 'abandono_total_todas_cohortes.xlsx')

def get_fuga_por_rango(columna: str, orden: int = 1, rango_anios: list = None, top_n: int = 5):
    if not os.path.exists(FILE_DESTINO):
        return pd.DataFrame()

    df = pd.read_excel(FILE_DESTINO)

    # Filtro por RANGO de cohortes
    if rango_anios:
        df["año_cohorte_ecas"] = pd.to_numeric(df["año_cohorte_ecas"], errors="coerce")
        df = df[(df["año_cohorte_ecas"] >= rango_anios[0]) & 
                (df["año_cohorte_ecas"] <= rango_anios[1])]

    columnas_pipe = ["institucion_destino", "carrera_destino", "area_conocimiento_destino", "anio_ingreso_destino"]
    
    # Limpieza y Explode
    for col in columnas_pipe:
        df[col] = df[col].astype(str).apply(split_pipe_column)
    
    df = df.explode(columnas_pipe)
    df["anio_ingreso_destino"] = pd.to_numeric(df["anio_ingreso_destino"], errors="coerce")
    df = df.dropna(subset=["anio_ingreso_destino", columna])

    # Identificar destino N (1ero, 2do, 3ero) cronológicamente
    df_orden = (
        df.sort_values(["mrun", "anio_ingreso_destino"])
        .groupby("mrun")
        .nth(orden - 1)
        .reset_index()
    )

    if df_orden.empty:
        return pd.DataFrame()

    # Conteo de estudiantes únicos por destino
    df_conteo = (
        df_orden.groupby(columna)["mrun"]
        .nunique()
        .reset_index(name="cant")
        .sort_values("cant", ascending=False)
        .head(top_n)
    )
    return df_conteo

def get_tiempo_de_descanso_procesado(rango_anios: List[int], jornada: Optional[str] = None) -> pd.DataFrame:
    if not os.path.exists(FILE_DESTINO):
        return pd.DataFrame()

    df = pd.read_excel(FILE_DESTINO)

    # ---------- Parseo y Limpieza ----------
    df['anio_ingreso_destino'] = df['anio_ingreso_destino'].apply(
        lambda x: [int(i.strip()) for i in x.split('|')]
        if isinstance(x, str) else []
    )

    df['año_cohorte_ecas'] = pd.to_numeric(df['año_cohorte_ecas'], errors='coerce')
    df['año_primer_fuga'] = pd.to_numeric(df['año_primer_fuga'], errors='coerce')

    # ---------- Filtros Reactivos ----------
    # Filtro de Rango
    df = df[
        (df['año_cohorte_ecas'] >= rango_anios[0]) &
        (df['año_cohorte_ecas'] <= rango_anios[1])
    ]

    # Filtro de Jornada (basado en la jornada de origen en ECAS)
    if jornada and jornada != "Ambas":
        # Asegúrate de que la columna en tu Excel se llame 'jornada_ecas' o similar
        if 'jornada_ecas' in df.columns:
            df = df[df['jornada_ecas'] == jornada]

    if df.empty:
        return pd.DataFrame()

    # ---------- Cálculo de Tiempo de Descanso ----------
    df['primer_ingreso_destino'] = df['anio_ingreso_destino'].apply(
        lambda x: min(x) if x else np.nan
    )

    df = df.dropna(subset=['primer_ingreso_destino', 'año_primer_fuga'])
    df['tiempo_de_descanso'] = df['primer_ingreso_destino'] - df['año_primer_fuga']

    # ---------- Categorización ----------
    bins = [-np.inf, 0, 1, 2, 5, 10, np.inf]
    labels = ['Inmediato (<=0)', '1 año', '2 años', '3 a 5 años', '6 a 10 años', '+10 años']

    df['Rango_de_Descanso'] = pd.cut(df['tiempo_de_descanso'], bins=bins, labels=labels)

    # ---------- Cálculo de Porcentajes Totales (Promedio del Rango) ----------
    # Al seleccionar un rango, calculamos sobre el universo total de ese periodo
    total_estudiantes = df['mrun'].nunique()
    
    df_resumen = (
        df.groupby('Rango_de_Descanso', observed=False)['mrun']
        .nunique()
        .reset_index(name='conteo')
    )
    
    df_resumen['porcentaje'] = (df_resumen['conteo'] / total_estudiantes) * 100
    
    return df_resumen
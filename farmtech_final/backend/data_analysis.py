"""data_analysis.py
Funções para análise estatística, plotagem, simulação e correlação
dos dados coletados pela FarmTech.
"""
from __future__ import annotations
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Tuple

# --- Estatísticas Descritivas ---
def descriptive_stats(df: pd.DataFrame) -> pd.DataFrame:
    return df.describe().T

# --- Detecção de Anomalias ---
def detect_anomalies(df: pd.DataFrame, col: str, z_thresh: float = 3.0) -> pd.DataFrame:
    if df.empty: return df.assign(anomalia=False)
    z_scores = (df[col] - df[col].mean()) / df[col].std(ddof=0)
    return df.assign(anomalia=np.abs(z_scores) > z_thresh)

# --- Funções de Plotagem ---
def plot_correlations(df: pd.DataFrame):
    corr_df = df.select_dtypes(include=np.number).corr()
    fig = px.imshow(corr_df, text_auto=True, aspect="auto", color_continuous_scale='viridis', title="Matriz de Correlação")
    fig.update_layout(height=600)
    return fig

def plot_distribution(df: pd.DataFrame, column: str):
    fig = px.histogram(df, x=column, marginal="box", title=f"Distribuição de {column.replace('_', ' ').capitalize()}")
    fig.update_layout(bargap=0.1)
    return fig

# --- Simulação da Lógica do ESP32 ---
def simular_logica_irrigacao(umidade: float, ph: float, cfg_logica: dict):
    params = cfg_logica
    decisao, justificativa = "Manter bomba desligada", "Condições normais."
    emergencia = False

    if umidade < params['UMIDADE_CRITICA_BAIXA'] or not (params['PH_CRITICO_MINIMO'] < ph < params['PH_CRITICO_MAXIMO']):
        decisao, emergencia = "Ligar bomba (EMERGÊNCIA)", True
        justificativa = f"EMERGÊNCIA: Umidade ({umidade}%) abaixo do crítico." if umidade < params['UMIDADE_CRITICA_BAIXA'] else f"EMERGÊNCIA: pH ({ph}) fora da faixa crítica."
        return {'decisao': decisao, 'justificativa': justificativa, 'emergencia': emergencia}

    if umidade < params['UMIDADE_MINIMA_PARA_IRRIGAR']:
        if not (params['PH_IDEAL_MINIMO'] < ph < params['PH_IDEAL_MAXIMO']):
            justificativa = f"Umidade baixa ({umidade}%), mas pH ({ph}) fora do ideal."
        else:
            decisao, justificativa = "Ligar bomba", f"Umidade ({umidade}%) ideal para irrigar."
    elif umidade > params['UMIDADE_ALTA_PARAR_IRRIGACAO']:
        justificativa = f"Umidade ({umidade}%) acima do necessário."

    return {'decisao': decisao, 'justificativa': justificativa, 'emergencia': emergencia}

# --- Análise do Histórico de Decisões ---
def analisar_historico_decisoes(df: pd.DataFrame) -> dict:
    if df.empty or 'decisao_logica_esp32' not in df.columns:
        return {'total_emergencias': 0, 'ph_criticos': 0, 'decisao_mais_comum': None}
    
    decisoes = df['decisao_logica_esp32'].fillna('').astype(str)
    total_emergencias = int(decisoes.str.contains('EMERGENCIA', case=False).sum())
    ph_criticos = int(decisoes.str.contains('pH critico', case=False).sum())
    mais_comum = decisoes.value_counts().idxmax() if not decisoes.empty else None
    
    return {'total_emergencias': total_emergencias, 'ph_criticos': ph_criticos, 'decisao_mais_comum': mais_comum}

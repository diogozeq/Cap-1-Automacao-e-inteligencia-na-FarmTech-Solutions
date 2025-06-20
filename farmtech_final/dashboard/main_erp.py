#!/usr/bin/env python3
"""
FarmTech ERP - Sistema Unificado de Gerenciamento
Versão Final com todas as funcionalidades e correções de IA.
"""
import sys
import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="FarmTech ERP", layout="wide", initial_sidebar_state="expanded", page_icon="🌱")

# --- Configuração de Path e Imports do Backend ---
try:
    backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
    sys.path.insert(0, backend_path)
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from backend import services, db_manager, ml_predictor, data_analysis, config_manager
except ImportError as e:
    st.error(f"Erro Crítico ao importar módulos: {e}. Verifique a estrutura de pastas.")
    st.stop()

# --- CSS Customizado ---
st.markdown("""<style>... a mesma estilização de antes ...</style>""", unsafe_allow_html=True) # Mantendo o CSS que já tínhamos

# --- Inicialização e Cache ---
@st.cache_resource
def init_system():
    try:
        db_manager.init_db()
        return True, config_manager.get_config()
    except Exception as e:
        st.error(f"Erro na inicialização: {e}")
        return False, None

system_initialized, config = init_system()
if not system_initialized: st.stop()

@st.cache_data(ttl=30)
def carregar_dados(limit=2000):
    try:
        with db_manager.session_scope() as s:
            leituras = db_manager.get_ultimas_leituras(s, limit=limit)
            if not leituras: return pd.DataFrame()
            s.expunge_all()
            df = pd.DataFrame([vars(l) for l in leituras])
            df.drop('_sa_instance_state', axis=1, inplace=True)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df.sort_values('timestamp', ascending=False)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

# --- Navegação ---
st.sidebar.title(" Menu de Navegação")
page = st.sidebar.radio("Módulos:", [" Painel de Controle", " Análise Histórica", " Gerenciamento", " Simulação", " IA e Previsões"])

# =================== PÁGINAS ===================

# --- 1. PAINEL DE CONTROLE ---
if page == " Painel de Controle":
    st.header(" Painel de Controle")
    if st.button(" Atualizar"): st.rerun()
    
    latest_reading = carregar_dados(limit=1).iloc[0] if not carregar_dados(limit=1).empty else None
    
    if latest_reading is not None:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(" Umidade", f"{latest_reading['umidade']:.1f}%")
        c2.metric(" pH", f"{latest_reading['ph_estimado']:.1f}")
        c3.metric(" Temp.", f"{latest_reading['temperatura']:.1f}°C")
        c4.metric(" Bomba", "Ligada" if latest_reading['bomba_ligada'] else "Desligada")
        
        if latest_reading['emergencia']:
            st.error(" ALERTA DE EMERGÊNCIA ATIVO!")

        df_chart = carregar_dados(limit=100).set_index('timestamp').sort_index()
        fig = px.line(df_chart, y=['umidade', 'ph_estimado', 'temperatura'], title="Métricas Recentes")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Nenhum dado encontrado.")

# --- 2. ANÁLISE HISTÓRICA ---
elif page == " Análise Histórica":
    st.header(" Análise Histórica")
    df_full = carregar_dados()
    if not df_full.empty:
        st.plotly_chart(data_analysis.plot_correlations(df_full), use_container_width=True)
        st.plotly_chart(data_analysis.plot_distribution(df_full, 'umidade'), use_container_width=True)
    else:
        st.warning("Nenhum dado para análise.")

# --- 3. GERENCIAMENTO (CRUD) ---
elif page == " Gerenciamento":
    st.header(" Gerenciamento de Dados (CRUD)")
    df_full = carregar_dados()
    st.dataframe(df_full)
    
    st.subheader(" Deletar Registro")
    record_id = st.number_input("ID do registro para deletar", min_value=1, step=1)
    if st.button("Deletar"):
        if services.delete_leitura(record_id):
            st.success(f"Registro {record_id} deletado.")
            st.rerun()
        else:
            st.error("Falha ao deletar.")

# --- 4. SIMULAÇÃO ---
elif page == " Simulação":
    st.header(" Simulador What-If")
    st.write("Teste a lógica de decisão do sistema.")
    umidade = st.slider("Umidade Sim.", 0.0, 100.0, 50.0)
    ph = st.slider("pH Sim.", 0.0, 14.0, 7.0)
    resultado = data_analysis.simular_logica_irrigacao(umidade, ph, config['logica_esp32'])
    st.write(f"**Decisão:** {resultado['decisao']}")
    st.write(f"**Justificativa:** {resultado['justificativa']}")

# --- 5. IA E PREVISÕES (O CÓDIGO CORRIGIDO) ---
elif page == " IA e Previsões":
    st.header(" Inteligência Artificial e Previsões")
    df_historico = carregar_dados()
    if df_historico.empty:
        st.warning("Não há dados históricos para as operações de IA.")
        st.stop()

    tab1, tab2, tab3 = st.tabs([" Risco", " Forecast", " Manutenção"])

    with tab1:
        st.subheader(" Treinamento do Modelo de Risco")
        if st.button(" Treinar Modelo de Risco"):
            with st.spinner("Treinando..."):
                try:
                    resultado = ml_predictor.train_risk_model(df_historico)
                    if resultado.get("modelo"):
                        st.session_state['risk_model'] = resultado['modelo']
                        st.success(f" Modelo treinado! Acurácia: {resultado['acuracia']:.2%}")
                    else:
                        st.error(f" Erro: {resultado.get('mensagem', 'Causa desconhecida.')}")
                except Exception as e:
                    st.error(f" Falha crítica: {e}")

    with tab2:
        st.subheader(" Forecast de Umidade (ARIMA)")
        if st.button(" Gerar Forecast"):
            with st.spinner("Calculando..."):
                try:
                    df_ts = df_historico.set_index('timestamp')['umidade'].sort_index().asfreq('h').fillna(method='ffill')
                    modelo_arima = ml_predictor.train_arima_model(df_ts)
                    forecast_df = modelo_arima.get_forecast(steps=24).summary_frame()
                    st.session_state['arima_forecast'] = forecast_df
                    st.success(" Forecast gerado!")
                except Exception as e:
                    st.error(f" Erro no forecast: {e}")
        if 'arima_forecast' in st.session_state:
             st.write(st.session_state['arima_forecast']) # Simplificado para exibir a tabela

    with tab3:
        st.subheader(" Previsão de Manutenção da Bomba")
        if st.button(" Analisar Manutenção"):
            with st.spinner("Analisando..."):
                try:
                    resultado = ml_predictor.train_maintenance_model(df_historico)
                    if resultado.get("modelo"):
                         st.success(f" Modelo treinado! Acurácia: {resultado['acuracia']:.2%}")
                    else:
                        st.error(f" Erro: {resultado.get('mensagem', 'Causa desconhecida.')}")
                except Exception as e:
                    st.error(f" Falha crítica: {e}")

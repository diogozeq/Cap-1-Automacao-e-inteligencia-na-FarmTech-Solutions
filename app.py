#!/usr/bin/env python3
"""
FarmTech ERP - Sistema Unificado Simplificado
Aplicação única com todas as funcionalidades
Autor: Diogo Zequini + Claude AI
Data: 2025-06-20
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import os
import time
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
import threading
import random

# Configuração da página
st.set_page_config(
    page_title="FarmTech ERP", 
    layout="wide", 
    initial_sidebar_state="expanded", 
    page_icon="🌱"
)

# CSS customizado
st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #4CAF50, #45a049);
        color: white;
        padding: 2rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .alert-critical {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
    .alert-warning {
        background-color: #fff8e1;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
    .alert-success {
        background-color: #e8f5e8;
        border-left: 4px solid #4caf50;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
    </style>
""", unsafe_allow_html=True)

# Configurações do banco de dados
DB_PATH = "farmtech_data.db"

# Configurações do sistema
CONFIG = {
    'UMIDADE_CRITICA_BAIXA': 15.0,
    'UMIDADE_MINIMA_PARA_IRRIGAR': 20.0,
    'UMIDADE_ALTA_PARAR_IRRIGACAO': 60.0,
    'PH_IDEAL_MINIMO': 5.5,
    'PH_IDEAL_MAXIMO': 6.5,
    'PH_CRITICO_MINIMO': 4.5,
    'PH_CRITICO_MAXIMO': 7.5,
}

# Funções do banco de dados
@contextmanager
def get_db_connection():
    """Context manager para conexão com banco de dados"""
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    """Inicializa o banco de dados"""
    try:
        with get_db_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS leituras_sensores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    umidade REAL NOT NULL,
                    ph_estimado REAL NOT NULL,
                    fosforo_presente BOOLEAN NOT NULL,
                    potassio_presente BOOLEAN NOT NULL,
                    temperatura REAL,
                    bomba_ligada BOOLEAN NOT NULL,
                    decisao_logica_esp32 TEXT,
                    emergencia BOOLEAN NOT NULL DEFAULT 0
                )
            """)
            conn.commit()
        return True
    except Exception as e:
        st.error(f"Erro ao inicializar banco: {e}")
        return False

def add_leitura(timestamp, umidade, ph_estimado, fosforo_presente, potassio_presente, 
               temperatura, bomba_ligada, emergencia, decisao_logica_esp32="Manual"):
    """Adiciona uma nova leitura ao banco"""
    try:
        with get_db_connection() as conn:
            conn.execute("""
                INSERT INTO leituras_sensores 
                (timestamp, umidade, ph_estimado, fosforo_presente, potassio_presente, 
                 temperatura, bomba_ligada, emergencia, decisao_logica_esp32)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (timestamp, umidade, ph_estimado, fosforo_presente, potassio_presente,
                  temperatura, bomba_ligada, emergencia, decisao_logica_esp32))
            conn.commit()
            return conn.lastrowid
    except Exception as e:
        st.error(f"Erro ao adicionar leitura: {e}")
        return None

def get_leituras(limit=100):
    """Obtém leituras do banco de dados"""
    try:
        with get_db_connection() as conn:
            df = pd.read_sql_query("""
                SELECT * FROM leituras_sensores 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, conn, params=(limit,))
            
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                return df.sort_index()
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

def get_latest_reading():
    """Obtém a última leitura"""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM leituras_sensores 
                ORDER BY timestamp DESC 
                LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None
    except Exception as e:
        st.error(f"Erro ao obter última leitura: {e}")
        return None

def update_leitura(leitura_id, campo, valor):
    """Atualiza uma leitura"""
    try:
        with get_db_connection() as conn:
            conn.execute(f"""
                UPDATE leituras_sensores 
                SET {campo} = ? 
                WHERE id = ?
            """, (valor, leitura_id))
            conn.commit()
            return conn.rowcount > 0
    except Exception as e:
        st.error(f"Erro ao atualizar leitura: {e}")
        return False

def delete_leitura(leitura_id):
    """Deleta uma leitura"""
    try:
        with get_db_connection() as conn:
            conn.execute("DELETE FROM leituras_sensores WHERE id = ?", (leitura_id,))
            conn.commit()
            return conn.rowcount > 0
    except Exception as e:
        st.error(f"Erro ao deletar leitura: {e}")
        return False

# Funções de simulação
def simulate_sensor_data():
    """Simula dados de sensores"""
    umidade = random.uniform(10, 70)
    ph = random.uniform(4.0, 8.0)
    temperatura = random.uniform(15, 35)
    fosforo = random.choice([True, False])
    potassio = random.choice([True, False])
    
    # Lógica de irrigação
    bomba_ligada = False
    emergencia = False
    
    if umidade < CONFIG['UMIDADE_CRITICA_BAIXA']:
        bomba_ligada = True
        emergencia = True
    elif umidade < CONFIG['UMIDADE_MINIMA_PARA_IRRIGAR']:
        bomba_ligada = True
    elif umidade > CONFIG['UMIDADE_ALTA_PARAR_IRRIGACAO']:
        bomba_ligada = False
    
    if ph < CONFIG['PH_CRITICO_MINIMO'] or ph > CONFIG['PH_CRITICO_MAXIMO']:
        emergencia = True
    
    return {
        'umidade': umidade,
        'ph_estimado': ph,
        'temperatura': temperatura,
        'fosforo_presente': fosforo,
        'potassio_presente': potassio,
        'bomba_ligada': bomba_ligada,
        'emergencia': emergencia
    }

def run_what_if_simulation(umidade, ph, temperatura, fosforo, potassio):
    """Executa simulação what-if"""
    bomba_ligada = False
    justificativa = []
    
    if umidade < CONFIG['UMIDADE_CRITICA_BAIXA']:
        bomba_ligada = True
        justificativa.append("Umidade crítica - irrigação emergencial")
    elif umidade < CONFIG['UMIDADE_MINIMA_PARA_IRRIGAR']:
        bomba_ligada = True
        justificativa.append("Umidade baixa - irrigação necessária")
    elif umidade > CONFIG['UMIDADE_ALTA_PARAR_IRRIGACAO']:
        bomba_ligada = False
        justificativa.append("Umidade alta - não irrigar")
    else:
        justificativa.append("Umidade adequada")
    
    if ph < CONFIG['PH_CRITICO_MINIMO'] or ph > CONFIG['PH_CRITICO_MAXIMO']:
        justificativa.append("pH crítico - atenção necessária")
    
    if not fosforo or not potassio:
        justificativa.append("Deficiência nutricional detectada")
    
    return bomba_ligada, "; ".join(justificativa)

# Inicialização
if not init_database():
    st.error("Falha na inicialização do banco de dados")
    st.stop()

# Interface principal
st.markdown("""
    <div class="main-header">
        <h1>🌱 FarmTech ERP</h1>
        <p>Sistema Unificado de Gerenciamento de Irrigação Inteligente</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("📋 Menu de Navegação")
page = st.sidebar.selectbox(
    "Escolha o módulo:",
    [
        "🏠 Painel de Controle",
        "📊 Análise Histórica", 
        "⚙️ Gerenciamento de Dados",
        "🧪 Simulação",
        "🤖 Inteligência Artificial"
    ]
)

# PAINEL DE CONTROLE
if page == "🏠 Painel de Controle":
    st.header("🏠 Painel de Controle")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("📊 Métricas Atuais")
        
        if st.button("🔄 Atualizar Dados"):
            st.rerun()
        
        ultima_leitura = get_latest_reading()
        
        if ultima_leitura:
            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
            
            with metric_col1:
                st.metric("💧 Umidade", f"{ultima_leitura['umidade']:.1f}%")
            
            with metric_col2:
                st.metric("🧪 pH", f"{ultima_leitura['ph_estimado']:.1f}")
            
            with metric_col3:
                temp_val = ultima_leitura['temperatura']
                st.metric("🌡️ Temperatura", f"{temp_val:.1f}°C" if temp_val else "N/A")
            
            with metric_col4:
                status = "🟢 Ligada" if ultima_leitura['bomba_ligada'] else "🔴 Desligada"
                st.metric("💦 Bomba", status)
            
            # Alertas
            st.subheader("🚨 Alertas")
            alertas = []
            
            if ultima_leitura['emergencia']:
                alertas.append("🔴 EMERGÊNCIA: Condições críticas!")
            
            if ultima_leitura['umidade'] < 15:
                alertas.append("⚠️ Umidade criticamente baixa!")
            
            if ultima_leitura['ph_estimado'] < 4.5 or ultima_leitura['ph_estimado'] > 7.5:
                alertas.append("⚠️ pH fora da faixa segura!")
            
            if alertas:
                for alerta in alertas:
                    st.markdown(f'<div class="alert-critical">{alerta}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="alert-success">✅ Sistema normal</div>', unsafe_allow_html=True)
        else:
            st.warning("Nenhuma leitura disponível")
    
    with col2:
        st.subheader("ℹ️ Informações")
        st.info(f"Última atualização: {datetime.now().strftime('%H:%M:%S')}")
        
        if ultima_leitura:
            st.write(f"**Última leitura:** {ultima_leitura['timestamp']}")
            st.write("**Nutrientes:**")
            st.write(f"- Fósforo: {'✅' if ultima_leitura['fosforo_presente'] else '❌'}")
            st.write(f"- Potássio: {'✅' if ultima_leitura['potassio_presente'] else '❌'}")
    
    # Gráfico de tendência
    st.subheader("📈 Tendência Recente")
    df_hist = get_leituras(limit=24)
    
    if not df_hist.empty:
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df_hist.index,
            y=df_hist['umidade'],
            mode='lines+markers',
            name='Umidade (%)',
            line=dict(color='#2196F3')
        ))
        
        fig.add_trace(go.Scatter(
            x=df_hist.index,
            y=df_hist['ph_estimado'] * 10,
            mode='lines+markers',
            name='pH (x10)',
            line=dict(color='#FF9800'),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title="Tendência de Umidade e pH",
            xaxis_title="Data/Hora",
            yaxis_title="Umidade (%)",
            yaxis2=dict(title="pH (x10)", overlaying='y', side='right'),
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Nenhum dado histórico disponível")

# ANÁLISE HISTÓRICA
elif page == "📊 Análise Histórica":
    st.header("📊 Análise Histórica")
    
    df_hist = get_leituras(limit=1000)
    
    if not df_hist.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            data_inicio = st.date_input(
                "Data Inicial",
                value=(datetime.now() - timedelta(days=7)).date()
            )
        
        with col2:
            data_fim = st.date_input(
                "Data Final",
                value=datetime.now().date()
            )
        
        # Filtrar dados
        mask = (df_hist.index.date >= data_inicio) & (df_hist.index.date <= data_fim)
        df_periodo = df_hist.loc[mask]
        
        if not df_periodo.empty:
            st.subheader("📈 Estatísticas do Período")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Umidade Média", f"{df_periodo['umidade'].mean():.1f}%")
            
            with col2:
                st.metric("pH Médio", f"{df_periodo['ph_estimado'].mean():.1f}")
            
            with col3:
                st.metric("Temp. Média", f"{df_periodo['temperatura'].mean():.1f}°C")
            
            with col4:
                st.metric("Irrigações", int(df_periodo['bomba_ligada'].sum()))
            
            # Gráficos
            fig_hist = px.histogram(df_periodo.reset_index(), x='umidade', 
                                   title="Distribuição de Umidade")
            st.plotly_chart(fig_hist, use_container_width=True)
            
            fig_scatter = px.scatter(df_periodo.reset_index(), 
                                   x='umidade', y='ph_estimado',
                                   title="Relação Umidade vs pH")
            st.plotly_chart(fig_scatter, use_container_width=True)
            
            # Sugestões
            st.subheader("💡 Sugestões")
            umidade_media = df_periodo['umidade'].mean()
            ph_medio = df_periodo['ph_estimado'].mean()
            
            if umidade_media < 20:
                st.info("💡 Umidade média baixa. Considere aumentar irrigação.")
            
            if ph_medio < 5.5 or ph_medio > 6.5:
                st.info("💡 pH fora da faixa ideal. Considere correção do solo.")
            
            eventos_criticos = len(df_periodo[df_periodo['emergencia'] == True])
            if eventos_criticos > 0:
                st.warning(f"⚠️ {eventos_criticos} eventos críticos no período.")
        else:
            st.warning("Nenhum dado no período selecionado")
    else:
        st.warning("Nenhum dado histórico disponível")

# GERENCIAMENTO DE DADOS
elif page == "⚙️ Gerenciamento de Dados":
    st.header("⚙️ Gerenciamento de Dados")
    
    tab1, tab2, tab3 = st.tabs(["➕ Adicionar", "✏️ Atualizar", "🗑️ Deletar"])
    
    with tab1:
        st.subheader("➕ Adicionar Nova Leitura")
        
        with st.form("form_adicionar"):
            col1, col2 = st.columns(2)
            
            with col1:
                data = st.date_input("Data", value=datetime.now().date())
                hora = st.time_input("Hora", value=datetime.now().time())
                umidade = st.number_input("Umidade (%)", min_value=0.0, max_value=100.0, value=30.0)
                ph = st.number_input("pH", min_value=0.0, max_value=14.0, value=6.5)
                temperatura = st.number_input("Temperatura (°C)", min_value=-10.0, max_value=50.0, value=25.0)
            
            with col2:
                fosforo = st.checkbox("Fósforo Presente", value=True)
                potassio = st.checkbox("Potássio Presente", value=True)
                bomba_ligada = st.checkbox("Bomba Ligada", value=False)
                emergencia = st.checkbox("Emergência", value=False)
            
            if st.form_submit_button("➕ Adicionar"):
                timestamp = datetime.combine(data, hora)
                leitura_id = add_leitura(
                    timestamp, umidade, ph, fosforo, potassio,
                    temperatura, bomba_ligada, emergencia
                )
                if leitura_id:
                    st.success(f"✅ Leitura {leitura_id} adicionada!")
    
    with tab2:
        st.subheader("✏️ Atualizar Leitura")
        
        with st.form("form_atualizar"):
            leitura_id = st.number_input("ID da Leitura", min_value=1, value=1)
            campo = st.selectbox("Campo", ["umidade", "ph_estimado", "temperatura", 
                                         "fosforo_presente", "potassio_presente", 
                                         "bomba_ligada", "emergencia"])
            
            if campo in ["fosforo_presente", "potassio_presente", "bomba_ligada", "emergencia"]:
                novo_valor = st.checkbox("Novo Valor", value=False)
            else:
                novo_valor = st.number_input("Novo Valor", value=0.0)
            
            if st.form_submit_button("✏️ Atualizar"):
                if update_leitura(leitura_id, campo, novo_valor):
                    st.success("✅ Leitura atualizada!")
                else:
                    st.error("❌ Leitura não encontrada")
    
    with tab3:
        st.subheader("🗑️ Deletar Leitura")
        
        with st.form("form_deletar"):
            leitura_id = st.number_input("ID da Leitura", min_value=1, value=1)
            confirmar = st.checkbox("✅ Confirmar exclusão")
            
            if st.form_submit_button("🗑️ Deletar"):
                if confirmar:
                    if delete_leitura(leitura_id):
                        st.success("✅ Leitura deletada!")
                    else:
                        st.error("❌ Leitura não encontrada")
                else:
                    st.warning("⚠️ Confirme a exclusão")

# SIMULAÇÃO
elif page == "🧪 Simulação":
    st.header("🧪 Simulação e Testes")
    
    tab1, tab2 = st.tabs(["📊 Gerador de Dados", "💡 Simulador What-If"])
    
    with tab1:
        st.subheader("📊 Gerador de Dados Simulados")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🎲 Gerar Dados Simulados"):
                dados = simulate_sensor_data()
                timestamp = datetime.now()
                
                leitura_id = add_leitura(
                    timestamp,
                    dados['umidade'],
                    dados['ph_estimado'],
                    dados['fosforo_presente'],
                    dados['potassio_presente'],
                    dados['temperatura'],
                    dados['bomba_ligada'],
                    dados['emergencia'],
                    "Simulação"
                )
                
                if leitura_id:
                    st.success(f"✅ Dados simulados gerados! ID: {leitura_id}")
                    st.json(dados)
        
        with col2:
            if st.button("📈 Gerar Múltiplos Dados"):
                for i in range(10):
                    dados = simulate_sensor_data()
                    timestamp = datetime.now() - timedelta(minutes=i*5)
                    
                    add_leitura(
                        timestamp,
                        dados['umidade'],
                        dados['ph_estimado'],
                        dados['fosforo_presente'],
                        dados['potassio_presente'],
                        dados['temperatura'],
                        dados['bomba_ligada'],
                        dados['emergencia'],
                        "Simulação Múltipla"
                    )
                
                st.success("✅ 10 registros simulados gerados!")
    
    with tab2:
        st.subheader("💡 Simulador What-If")
        
        col1, col2 = st.columns(2)
        
        with col1:
            sim_umidade = st.slider("Umidade (%)", 0.0, 100.0, 30.0)
            sim_ph = st.slider("pH", 0.0, 14.0, 6.5)
            sim_temperatura = st.slider("Temperatura (°C)", 0.0, 40.0, 25.0)
        
        with col2:
            sim_fosforo = st.checkbox("Fósforo Presente", value=True)
            sim_potassio = st.checkbox("Potássio Presente", value=True)
        
        if st.button("🔄 Simular Cenário"):
            resultado = run_what_if_simulation(
                sim_umidade, sim_ph, sim_temperatura, sim_fosforo, sim_potassio
            )
            
            if resultado[0]:
                st.success("✅ **DECISÃO: LIGAR BOMBA**")
            else:
                st.error("❌ **DECISÃO: NÃO LIGAR BOMBA**")
            
            st.info(f"**Justificativa:** {resultado[1]}")
            
            # Análise visual
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if sim_umidade < 15:
                    st.error("🚨 Umidade Crítica")
                elif sim_umidade < 20:
                    st.warning("⚠️ Umidade Baixa")
                else:
                    st.success("✅ Umidade OK")
            
            with col2:
                if sim_ph < 4.5 or sim_ph > 7.5:
                    st.error("🚨 pH Crítico")
                elif sim_ph < 5.5 or sim_ph > 6.5:
                    st.warning("⚠️ pH Subótimo")
                else:
                    st.success("✅ pH Ideal")
            
            with col3:
                if sim_fosforo and sim_potassio:
                    st.success("✅ Nutrientes OK")
                elif sim_fosforo or sim_potassio:
                    st.warning("⚠️ Nutriente Parcial")
                else:
                    st.error("🚨 Sem Nutrientes")

# INTELIGÊNCIA ARTIFICIAL
elif page == "🤖 Inteligência Artificial":
    st.header("🤖 Inteligência Artificial")
    
    df_hist = get_leituras(limit=1000)
    
    if not df_hist.empty and len(df_hist) > 10:
        tab1, tab2 = st.tabs(["📊 Análise Preditiva", "🔮 Forecast"])
        
        with tab1:
            st.subheader("📊 Análise Preditiva")
            
            # Estatísticas descritivas
            st.write("**Estatísticas dos Dados:**")
            st.dataframe(df_hist.describe())
            
            # Correlações
            st.subheader("🔗 Correlações")
            numeric_cols = ['umidade', 'ph_estimado', 'temperatura']
            corr_matrix = df_hist[numeric_cols].corr()
            
            fig_corr = px.imshow(corr_matrix, text_auto=True, 
                               title="Matriz de Correlação")
            st.plotly_chart(fig_corr, use_container_width=True)
            
            # Padrões
            st.subheader("📈 Padrões Identificados")
            
            # Análise de umidade vs irrigação
            irrigacao_media = df_hist.groupby('bomba_ligada')['umidade'].mean()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Umidade Média (Bomba OFF)", f"{irrigacao_media[False]:.1f}%")
            with col2:
                st.metric("Umidade Média (Bomba ON)", f"{irrigacao_media[True]:.1f}%")
        
        with tab2:
            st.subheader("🔮 Previsão de Umidade")
            
            if st.button("📊 Gerar Previsão"):
                # Previsão simples baseada em média móvel
                df_recent = df_hist.tail(10)
                media_umidade = df_recent['umidade'].mean()
                std_umidade = df_recent['umidade'].std()
                
                # Gerar previsão para próximas 6 horas
                future_times = [datetime.now() + timedelta(hours=i) for i in range(1, 7)]
                forecast_values = []
                
                for i in range(6):
                    # Previsão com tendência e ruído
                    trend = -0.5 if media_umidade > 50 else 0.5  # Tendência baseada na umidade atual
                    noise = np.random.normal(0, std_umidade * 0.5)
                    forecast = media_umidade + (trend * i) + noise
                    forecast_values.append(max(0, min(100, forecast)))  # Manter entre 0-100%
                
                # Gráfico de previsão
                fig_forecast = go.Figure()
                
                # Dados históricos
                fig_forecast.add_trace(go.Scatter(
                    x=df_recent.index,
                    y=df_recent['umidade'],
                    mode='lines+markers',
                    name='Histórico',
                    line=dict(color='#2196F3')
                ))
                
                # Previsão
                fig_forecast.add_trace(go.Scatter(
                    x=future_times,
                    y=forecast_values,
                    mode='lines+markers',
                    name='Previsão',
                    line=dict(color='#FF9800', dash='dash')
                ))
                
                fig_forecast.update_layout(
                    title="Previsão de Umidade - Próximas 6 Horas",
                    xaxis_title="Data/Hora",
                    yaxis_title="Umidade (%)",
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig_forecast, use_container_width=True)
                
                # Alertas de previsão
                st.subheader("⚠️ Alertas de Previsão")
                min_forecast = min(forecast_values)
                max_forecast = max(forecast_values)
                
                if min_forecast < 20:
                    st.warning(f"🚨 Umidade pode cair para {min_forecast:.1f}% - preparar irrigação!")
                
                if max_forecast > 80:
                    st.info(f"💧 Umidade pode subir para {max_forecast:.1f}% - suspender irrigação!")
                
                if not any(v < 20 for v in forecast_values):
                    st.success("✅ Níveis de umidade estáveis previstos")
    else:
        st.warning("Dados insuficientes para análise de IA. Adicione mais registros.")

# Rodapé
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <small>
            🌱 FarmTech ERP v2.0 Simplificado | Desenvolvido por Diogo Zequini + Claude AI | 
            © 2025 | Sistema Único de Irrigação Inteligente
        </small>
    </div>
""", unsafe_allow_html=True)
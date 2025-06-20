"""
🌱 FarmTech Solutions - Suite Unificada PhD
Interface completa com Dashboard + App integrados
Design com vieses cognitivos para UX perfeita
"""
import os
import sys
import datetime as dt
import pathlib
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configuração de página PRIMEIRA
st.set_page_config(
    page_title="🌱 FarmTech Solutions PhD",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Path setup
_pkg_root = pathlib.Path(__file__).resolve().parent
if str(_pkg_root) not in sys.path:
    sys.path.insert(0, str(_pkg_root))

# CSS customizado para vieses cognitivos
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #00b894, #00cec9);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #00b894;
    }
    .alert-critical {
        background: linear-gradient(90deg, #ff6b6b, #ee5a52);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .alert-warning {
        background: linear-gradient(90deg, #fdcb6e, #f39c12);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .alert-success {
        background: linear-gradient(90deg, #00b894, #00cec9);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #2d3436, #636e72);
    }
    .stSelectbox > div > div {
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

# Imports do backend
try:
    from farmtech_final.backend.app import (
        LeituraSensor, SessionLocal, carregar_dados_para_pandas,
        executar_forecast_umidade_phd, RichConsole
    )
    from farmtech_final.backend.config_manager import get_config
    from farmtech_final.backend import services
    config = get_config()
except ImportError as e:
    st.error(f"❌ Erro ao importar módulos backend: {e}")
    st.stop()

# Header principal
st.markdown("""
<div class="main-header">
    <h1>🌱 FarmTech Solutions PhD Suite</h1>
    <p>Sistema Inteligente de Irrigação com IA e IoT</p>
</div>
""", unsafe_allow_html=True)

# Sidebar com navegação
st.sidebar.image("https://img.icons8.com/color/96/000000/agriculture.png", width=80)
st.sidebar.title("🎛️ Painel de Controle")

# Auto-refresh
refresh_rate = st.sidebar.selectbox(
    "🔄 Auto-refresh",
    [0, 10, 30, 60],
    index=2,
    format_func=lambda x: "Desabilitado" if x == 0 else f"{x}s"
)

if refresh_rate > 0:
    import time
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = time.time()
    
    if time.time() - st.session_state.last_refresh > refresh_rate:
        st.session_state.last_refresh = time.time()
        st.rerun()

# Navegação principal
page = st.sidebar.radio(
    "📍 Navegação",
    ["🏠 Dashboard Principal", "📊 Analytics Avançado", "⚙️ Gerenciamento", "🔮 Previsões IA", "🚨 Alertas & Logs"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("**🔧 Status do Sistema**")

# Função para carregar dados com cache
@st.cache_data(ttl=30)
def load_data():
    try:
        return carregar_dados_para_pandas()
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

# Função para métricas com viés cognitivo
def display_metrics(df):
    if df.empty:
        st.warning("⚠️ Nenhum dado disponível")
        return
    
    latest = df.iloc[-1]
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Umidade com cores psicológicas
    umidade = latest['umidade']
    umidade_color = "#e74c3c" if umidade < 30 else "#f39c12" if umidade < 50 else "#27ae60"
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: {umidade_color};">💧 Umidade</h3>
            <h2 style="color: {umidade_color};">{umidade:.1f}%</h2>
            <p>{'🚨 Crítico' if umidade < 30 else '⚠️ Baixo' if umidade < 50 else '✅ Normal'}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # pH com indicador visual
    ph = latest['ph_estimado']
    ph_color = "#e74c3c" if ph < 6.0 or ph > 8.0 else "#f39c12" if ph < 6.5 or ph > 7.5 else "#27ae60"
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: {ph_color};">🧪 pH</h3>
            <h2 style="color: {ph_color};">{ph:.2f}</h2>
            <p>{'🚨 Crítico' if ph < 6.0 or ph > 8.0 else '⚠️ Atenção' if ph < 6.5 or ph > 7.5 else '✅ Ideal'}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Temperatura
    temp = latest['temperatura']
    temp_color = "#e74c3c" if temp < 15 or temp > 35 else "#f39c12" if temp < 20 or temp > 30 else "#27ae60"
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: {temp_color};">🌡️ Temperatura</h3>
            <h2 style="color: {temp_color};">{temp:.1f}°C</h2>
            <p>{'🚨 Extremo' if temp < 15 or temp > 35 else '⚠️ Subótimo' if temp < 20 or temp > 30 else '✅ Perfeito'}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Status da Bomba
    bomba = latest['bomba_ligada']
    bomba_color = "#27ae60" if bomba else "#95a5a6"
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: {bomba_color};">💦 Bomba</h3>
            <h2 style="color: {bomba_color};">{'🟢 LIGADA' if bomba else '🔴 DESLIGADA'}</h2>
            <p>{'Irrigando' if bomba else 'Standby'}</p>
        </div>
        """, unsafe_allow_html=True)

# Dashboard Principal
if page == "🏠 Dashboard Principal":
    df = load_data()
    
    # Métricas principais
    display_metrics(df)
    
    st.markdown("---")
    
    # Gráficos em tempo real
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Tendências (24h)")
        if not df.empty:
            # Últimas 24 horas
            df_24h = df.tail(24)
            
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Umidade (%)', 'pH'),
                vertical_spacing=0.1
            )
            
            # Umidade
            fig.add_trace(
                go.Scatter(
                    x=df_24h.index,
                    y=df_24h['umidade'],
                    mode='lines+markers',
                    name='Umidade',
                    line=dict(color='#3498db', width=3),
                    marker=dict(size=6)
                ),
                row=1, col=1
            )
            
            # pH
            fig.add_trace(
                go.Scatter(
                    x=df_24h.index,
                    y=df_24h['ph_estimado'],
                    mode='lines+markers',
                    name='pH',
                    line=dict(color='#e74c3c', width=3),
                    marker=dict(size=6)
                ),
                row=2, col=1
            )
            
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Status Atual")
        if not df.empty:
            latest = df.iloc[-1]
            
            # Gauge de umidade
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = latest['umidade'],
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Umidade (%)"},
                delta = {'reference': 50},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 30], 'color': "lightgray"},
                        {'range': [30, 70], 'color': "gray"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            fig_gauge.update_layout(height=300)
            st.plotly_chart(fig_gauge, use_container_width=True)
    
    # Tabela de últimas leituras
    st.subheader("📋 Últimas Leituras")
    if not df.empty:
        df_display = df.tail(10).copy()
        df_display['bomba_ligada'] = df_display['bomba_ligada'].map({True: '🟢', False: '🔴'})
        df_display['emergencia'] = df_display['emergencia'].map({True: '🚨', False: '✅'})
        st.dataframe(df_display, use_container_width=True)

# Analytics Avançado
elif page == "📊 Analytics Avançado":
    st.header("📊 Analytics Avançado")
    df = load_data()
    
    if df.empty:
        st.warning("⚠️ Nenhum dado disponível para análise")
    else:
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            days = st.selectbox("📅 Período", [7, 15, 30, 60], index=1)
        with col2:
            metric = st.selectbox("📈 Métrica", ['umidade', 'ph_estimado', 'temperatura'])
        
        df_filtered = df.tail(days * 24)  # Assumindo leituras horárias
        
        # Gráfico principal
        fig = px.line(df_filtered, y=metric, title=f"Evolução de {metric.title()}")
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Estatísticas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Média", f"{df_filtered[metric].mean():.2f}")
        with col2:
            st.metric("Máximo", f"{df_filtered[metric].max():.2f}")
        with col3:
            st.metric("Mínimo", f"{df_filtered[metric].min():.2f}")
        with col4:
            st.metric("Desvio", f"{df_filtered[metric].std():.2f}")

# Gerenciamento
elif page == "⚙️ Gerenciamento":
    st.header("⚙️ Gerenciamento de Dados")
    
    tab1, tab2, tab3 = st.tabs(["➕ Adicionar", "✏️ Editar", "🗑️ Deletar"])
    
    with tab1:
        st.subheader("➕ Nova Leitura")
        with st.form("add_form"):
            col1, col2 = st.columns(2)
            with col1:
                data = st.date_input("📅 Data", value=dt.datetime.now().date())
                hora = st.time_input("🕐 Hora", value=dt.datetime.now().time())
                umidade = st.number_input("💧 Umidade (%)", 0.0, 100.0, 45.0, 0.1)
                ph = st.number_input("🧪 pH", 0.0, 14.0, 6.8, 0.1)
            
            with col2:
                temperatura = st.number_input("🌡️ Temperatura (°C)", -10.0, 60.0, 25.0, 0.1)
                fosforo = st.checkbox("🟡 Fósforo presente")
                potassio = st.checkbox("🔵 Potássio presente")
                bomba = st.checkbox("💦 Bomba ligada")
            
            submitted = st.form_submit_button("💾 Salvar", use_container_width=True)
            
            if submitted:
                timestamp = dt.datetime.combine(data, hora)
                try:
                    # Lógica de emergência
                    cfg = config['logica_esp32']
                    emergencia = (umidade < cfg['UMIDADE_CRITICA_BAIXA']) or \
                               (ph < cfg['PH_CRITICO_MINIMO']) or \
                               (ph > cfg['PH_CRITICO_MAXIMO'])
                    
                    id_novo = services.add_leitura(
                        timestamp=timestamp,
                        umidade=umidade,
                        ph_estimado=ph,
                        fosforo_presente=fosforo,
                        potassio_presente=potassio,
                        temperatura=temperatura,
                        bomba_ligada=bomba,
                        decisao_logica_esp32="Manual",
                        emergencia=emergencia
                    )
                    
                    st.success(f"✅ Leitura adicionada com ID: {id_novo}")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Erro: {e}")
    
    with tab2:
        st.subheader("✏️ Editar Leitura")
        df = load_data()
        if not df.empty:
            ids = df.index.tolist()
            selected_id = st.selectbox("🔍 Selecionar ID", ids)
            
            if selected_id:
                row = df.loc[selected_id]
                st.write("**Dados atuais:**")
                st.json(row.to_dict())
                
                # Formulário de edição seria implementado aqui
                st.info("🚧 Funcionalidade de edição em desenvolvimento")
    
    with tab3:
        st.subheader("🗑️ Deletar Leitura")
        with st.form("delete_form"):
            id_delete = st.number_input("🔍 ID para deletar", min_value=1, step=1)
            confirma = st.checkbox("⚠️ Confirmo que quero deletar")
            
            submitted = st.form_submit_button("🗑️ Deletar", use_container_width=True)
            
            if submitted and confirma:
                try:
                    sucesso = services.delete_leitura(int(id_delete))
                    if sucesso:
                        st.success("✅ Registro deletado!")
                    else:
                        st.warning("⚠️ ID não encontrado")
                except Exception as e:
                    st.error(f"❌ Erro: {e}")

# Previsões IA
elif page == "🔮 Previsões IA":
    st.header("🔮 Previsões com Inteligência Artificial")
    
    df = load_data()
    if df.empty:
        st.warning("⚠️ Dados insuficientes para previsões")
    else:
        st.info("🤖 Gerando previsões com modelo ARIMA...")
        
        try:
            console_fake = RichConsole(file=open(os.devnull, 'w'))
            fc_cfg = config['forecast_settings']
            umid_crit = config['logica_esp32']['UMIDADE_CRITICA_BAIXA']
            
            forecast, alerts = executar_forecast_umidade_phd(df, console_fake, fc_cfg, umid_crit)
            
            if forecast is not None:
                st.subheader("📈 Previsão de Umidade")
                st.line_chart(forecast)
                
                if alerts:
                    st.markdown('<div class="alert-critical">🚨 ALERTAS CRÍTICOS</div>', unsafe_allow_html=True)
                    for alert in alerts:
                        st.error(alert)
                else:
                    st.markdown('<div class="alert-success">✅ Sem alertas críticos</div>', unsafe_allow_html=True)
            else:
                st.error("❌ Não foi possível gerar previsões")
                
        except Exception as e:
            st.error(f"❌ Erro na previsão: {e}")

# Alertas & Logs
elif page == "🚨 Alertas & Logs":
    st.header("🚨 Sistema de Alertas e Logs")
    
    df = load_data()
    if not df.empty:
        # Alertas críticos
        emergencias = df[df['emergencia'] == True]
        
        if not emergencias.empty:
            st.markdown('<div class="alert-critical">🚨 SITUAÇÕES DE EMERGÊNCIA DETECTADAS</div>', unsafe_allow_html=True)
            st.dataframe(emergencias.tail(10), use_container_width=True)
        else:
            st.markdown('<div class="alert-success">✅ Nenhuma emergência detectada</div>', unsafe_allow_html=True)
        
        # Logs de bomba
        st.subheader("💦 Histórico da Bomba")
        bomba_logs = df[df['bomba_ligada'] == True]
        if not bomba_logs.empty:
            st.dataframe(bomba_logs.tail(20), use_container_width=True)
        else:
            st.info("ℹ️ Nenhuma ativação da bomba registrada")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**🔧 Build Info**")
st.sidebar.caption("FarmTech Solutions PhD v2.0")
st.sidebar.caption("🚀 Powered by Streamlit + IA")

# Status de conexão
try:
    df_test = load_data()
    status = "🟢 Online" if not df_test.empty else "🟡 Sem dados"
except:
    status = "🔴 Offline"

st.sidebar.markdown(f"**Status:** {status}") 
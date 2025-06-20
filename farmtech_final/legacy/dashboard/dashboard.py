#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FarmTech Solutions - Dashboard Avançado com Integração API para Irrigação Inteligente
Autor: Diogo Zequini
Data: 2025-05-20

Descrição:
Dashboard interativo com Streamlit para visualização de dados históricos de irrigação,
integração com dados meteorológicos em tempo real, simulação de lógica de decisão,
alertas proativos, análise de custos e diagnóstico do sistema.
"""

# Bloco 1: Imports Padrão e Configuração Inicial de Logging
import sys
import subprocess
import importlib
import logging
import os
import datetime
import warnings

LOGGING_LEVEL = logging.INFO
logging.basicConfig(
    level=LOGGING_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("FarmTechDashboardApp")

# Bloco 2: Gerenciamento de Dependências
PIP_MODULE_MAP_DASH = {
    'streamlit': 'streamlit', 'pandas': 'pandas', 'numpy': 'numpy',
    'requests': 'requests', 'sqlalchemy': 'SQLAlchemy',
    'plotly': 'plotly', 'yaml': 'PyYAML'
}
INSTALLED_PACKAGES_CACHE_DASH = {}

def ensure_package_dash(module_name, critical=True):
    if module_name in INSTALLED_PACKAGES_CACHE_DASH:
        return INSTALLED_PACKAGES_CACHE_DASH[module_name]
    try:
        pkg = importlib.import_module(module_name)
        version = getattr(pkg, '__version__', getattr(pkg, 'VERSION', 'não especificada'))
        if module_name == 'reportlab' and hasattr(pkg, 'Version'): version = pkg.Version
        logger.debug(f"Pacote '{module_name}' já instalado (versão: {version}).")
        INSTALLED_PACKAGES_CACHE_DASH[module_name] = pkg
        return pkg
    except ImportError:
        pip_name = PIP_MODULE_MAP_DASH.get(module_name, module_name)
        logger.warning(f"Pacote '{module_name}' (pip: '{pip_name}') não encontrado. Tentando instalar...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name, "--user", "--quiet", "--disable-pip-version-check"])
            logger.info(f"Pacote '{pip_name}' instalado com sucesso.")
            importlib.invalidate_caches()
            pkg = importlib.import_module(module_name)
            version_after_install = getattr(pkg, '__version__', getattr(pkg, 'VERSION', 'não especificada'))
            if module_name == 'reportlab' and hasattr(pkg, 'Version'): version_after_install = pkg.Version
            logger.info(f"Pacote '{module_name}' importado (versão: {version_after_install}).")
            INSTALLED_PACKAGES_CACHE_DASH[module_name] = pkg
            return pkg
        except Exception as e:
            logger.error(f"Falha ao instalar/importar '{pip_name}'. Erro: {e}", exc_info=True)
            if critical:
                print(f"ERRO CRÍTICO: Dependência '{pip_name}' não instalada. Instale manualmente.", file=sys.stderr)
                sys.exit(1)
            INSTALLED_PACKAGES_CACHE_DASH[module_name] = None
            return None

logger.info("Dashboard: Verificando dependências...")
yaml_module = ensure_package_dash('yaml', critical=True)
st_module = ensure_package_dash('streamlit', critical=True)
pd_module = ensure_package_dash('pandas', critical=True)
np_module = ensure_package_dash('numpy', critical=True)
requests_module = ensure_package_dash('requests', critical=True)
sqlalchemy_module = ensure_package_dash('sqlalchemy', critical=True)
plotly_module = ensure_package_dash('plotly', critical=True)
logger.info("Dashboard: Dependências verificadas.")

if not st_module:
    logger.critical("Streamlit não pôde ser carregado.")
    sys.exit("ERRO CRÍTICO: Streamlit não está disponível.")

import streamlit as st
try:
    from streamlit_autorefresh import st_autorefresh  # Pacote leve para auto-refresh
except ImportError:
    st_autorefresh = None

# CONFIGURAÇÃO DA PÁGINA (PRIMEIRO COMANDO STREAMLIT)
st.set_page_config(page_title="FarmTech PhD Dashboard", layout="wide", initial_sidebar_state="expanded", page_icon="💧")

# Auto-refresh a cada 30s (configurável via barra lateral)
if st_autorefresh:
    REFRESH_INTERVAL_SEC = st.sidebar.number_input("Intervalo de refresh (s)", min_value=10, max_value=300, value=30, step=5)
    st_autorefresh(interval=REFRESH_INTERVAL_SEC * 1000, key="autorefresh")

# Injetar CSS customizado para melhoria de UI e UX
def load_custom_css():
    st.markdown(
        """
        <style>
        /* Tipografia e Cores Base */
        :root {
            --primary-color: #4CAF50;
            --secondary-color: #2196F3;
            --warning-color: #FFC107;
            --danger-color: #F44336;
            --success-color: #4CAF50;
            --text-color: #333333;
            --bg-color: #FFFFFF;
            --sidebar-bg: #f8f9fa;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            color: var(--text-color);
            background-color: var(--bg-color);
            line-height: 1.6;
        }

        /* Layout e Containers */
        .stApp {
            background: var(--bg-color);
            max-width: 1400px;
            margin: 0 auto;
            padding: 1rem;
        }

        /* Header e Navigation */
        .top-banner {
            background: linear-gradient(135deg, var(--primary-color), #45a049);
            color: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
            position: relative;
            overflow: hidden;
        }

        .top-banner::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="40" fill="rgba(255,255,255,0.1)"/></svg>');
            opacity: 0.1;
        }

        .top-banner h1 {
            font-size: 2.5rem;
            font-weight: 700;
            margin: 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }

        /* Sidebar Improvements */
        [data-testid="stSidebar"] {
            background-color: var(--sidebar-bg);
            border-right: 1px solid rgba(0,0,0,0.1);
            padding: 2rem 1rem;
        }

        [data-testid="stSidebar"] [data-testid="stMarkdown"] {
            font-size: 0.9rem;
        }

        /* Cards e Containers */
        div.element-container {
            background: white;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: transform 0.2s, box-shadow 0.2s;
        }

        div.element-container:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }

        /* Buttons e Inputs */
        .stButton > button {
            border-radius: 50px;
            padding: 0.5rem 2rem;
            font-weight: 600;
            transition: all 0.3s ease;
            border: none;
            background: var(--primary-color);
            color: white;
        }

        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(76, 175, 80, 0.2);
        }

        /* Metrics e KPIs */
        [data-testid="stMetric"] {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid var(--primary-color);
        }

        [data-testid="stMetricLabel"] {
            font-weight: 600;
            color: #666;
        }

        /* Tables */
        .dataframe {
            border-collapse: collapse;
            width: 100%;
            border: none;
            background: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .dataframe th {
            background: #f8f9fa;
            padding: 12px;
            font-weight: 600;
            text-align: left;
            border-bottom: 2px solid #dee2e6;
        }

        .dataframe td {
            padding: 12px;
            border-bottom: 1px solid #dee2e6;
        }

        /* Alerts e Notificações */
        .alert {
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
            border-left: 4px solid;
        }

        .alert-success {
            background-color: #f0fff4;
            border-color: var(--success-color);
        }

        .alert-warning {
            background-color: #fff9e6;
            border-color: var(--warning-color);
        }

        .alert-danger {
            background-color: #fff5f5;
            border-color: var(--danger-color);
        }

        /* Tooltips e Popovers */
        .tooltip {
            position: relative;
            display: inline-block;
        }

        .tooltip .tooltiptext {
            visibility: hidden;
            background-color: #333;
            color: white;
            text-align: center;
            padding: 5px;
            border-radius: 6px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            transform: translateX(-50%);
            opacity: 0;
            transition: opacity 0.3s;
        }

        .tooltip:hover .tooltiptext {
            visibility: visible;
            opacity: 1;
        }

        /* Animações */
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        .fade-in {
            animation: fadeIn 0.5s ease-in;
        }

        /* Acessibilidade */
        @media (prefers-reduced-motion: reduce) {
            * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
                scroll-behavior: auto !important;
            }
        }

        /* Dark Mode Support */
        @media (prefers-color-scheme: dark) {
            :root {
                --text-color: #e0e0e0;
                --bg-color: #1a1a1a;
                --sidebar-bg: #2d2d2d;
            }

            .dataframe {
                background: #2d2d2d;
            }

            .dataframe th {
                background: #333;
            }

            [data-testid="stMetric"] {
                background: #2d2d2d;
            }
        }

        /* Responsividade */
        @media screen and (max-width: 768px) {
            .top-banner {
                padding: 1rem;
            }

            .top-banner h1 {
                font-size: 1.8rem;
            }

            [data-testid="stSidebar"] {
                padding: 1rem 0.5rem;
            }
        }
        </style>
        """, unsafe_allow_html=True
    )

load_custom_css()

# Função para criar cabeçalhos animados
def animated_header(text, icon="💧", animation_key=None):
    st.markdown(f"""
        <div class="fade-in" {'key="' + animation_key + '"' if animation_key else ''}>
            <h1 style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="font-size: 2rem;">{icon}</span>
                <span>{text}</span>
            </h1>
        </div>
    """, unsafe_allow_html=True)

# Função para criar cards interativos
def interactive_card(title, content, icon=None):
    st.markdown(f"""
        <div class="element-container" style="cursor: pointer;">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                {f'<span style="font-size: 1.5rem;">{icon}</span>' if icon else ''}
                <h3>{title}</h3>
            </div>
            <div>{content}</div>
        </div>
    """, unsafe_allow_html=True)

# Função para criar métricas estilizadas
def styled_metric(label, value, delta=None, delta_color="normal"):
    st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            {f'<div class="metric-delta" style="color: {delta_color}">{delta}</div>' if delta else ''}
        </div>
    """, unsafe_allow_html=True)

# Exibir Top Banner personalizado
st.markdown('<div class="top-banner fade-in">', unsafe_allow_html=True)
animated_header("FarmTech Solutions - Dashboard Avançado PhD", "🌱")
st.markdown('</div>', unsafe_allow_html=True)

import pandas as pd
import numpy as np
import requests
import yaml
from sqlalchemy import create_engine, Column, Integer, Float, Boolean, DateTime, String
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# # (O Bloco 4: st.set_page_config(...) deve estar ANTES desta seção)

# --- Constantes Padrão Globais para Configuração (DEFINIDAS ANTES DE USAR) ---
DB_NAME_DEFAULT_GLOBAL_DASH = 'farmtech_phd_data_final_v2.db'
TABLE_NAME_DEFAULT_GLOBAL_DASH = 'leituras_sensores_phd_v2'

LOGICA_ESP32_PARAMS_DEFAULT_GLOBAL_DASH = {
    'UMIDADE_CRITICA_BAIXA': 15.0, 
    'UMIDADE_MINIMA_PARA_IRRIGAR': 20.0,
    'UMIDADE_ALTA_PARAR_IRRIGACAO': 60.0, 
    'PH_IDEAL_MINIMO': 5.5,
    'PH_IDEAL_MAXIMO': 6.5, 
    'PH_CRITICO_MINIMO': 4.5, 
    'PH_CRITICO_MAXIMO': 7.5,
}

FORECAST_SETTINGS_DEFAULT_GLOBAL_DASH = {
    'num_leituras_futuras': 6, 
    'intervalo_leitura_minutos': 5,
    'alerta_forecast_ativo': True, 
    'arima_p': 1, 
    'arima_d': 1, 
    'arima_q': 1
}

CUSTO_SETTINGS_DEFAULT_GLOBAL_DASH = {
    'custo_agua_reais_por_m3': 5.00, 
    'vazao_bomba_litros_por_hora': 1000.0,
    'tempo_irrigacao_padrao_minutos': 15.0, 
    'custo_energia_kwh': 0.75,
    'potencia_bomba_kw': 0.75
}

ML_CLASSIFIER_DEFAULT_GLOBAL_DASH = {
    'test_size': 0.3, 
    'random_state': 42, 
    'n_estimators': 100,
    'min_samples_leaf': 3
}

REPORT_SETTINGS_DEFAULT_GLOBAL_DASH = {
    'max_anomalias_no_relatorio': 5, 
    'max_leituras_recentes_tabela_pdf': 15,
    'autor_relatorio': "Diogo Zequini" # Seu nome aqui
}

CLI_SETTINGS_DEFAULT_GLOBAL_DASH = { 
    'max_leituras_tabela_console': 10 
}

CONFIG_FILE_PATH_GLOBAL_DASH = 'farmtech_config_phd.yaml'
# OPT: chave de API lida de variável de ambiente para evitar hard-code
METEOBLUE_API_KEY = os.getenv("METEOBLUE_API_KEY") or "DEMO"

# (A função @st.cache_resource def carregar_configuracoes_dashboard_corrigido(): continua DEPOIS deste bloco)


@st.cache_resource
def carregar_configuracoes_dashboard_final():
    default_cfg_interno = {
        'db_name': DB_NAME_DEFAULT_GLOBAL_DASH,
        'table_name': TABLE_NAME_DEFAULT_GLOBAL_DASH,
        'logica_esp32': LOGICA_ESP32_PARAMS_DEFAULT_GLOBAL_DASH.copy(),
        'custo_settings': CUSTO_SETTINGS_DEFAULT_GLOBAL_DASH.copy(), # Adicionada ao default
        # Adicione outras seções de config default que seu YAML cobre
        'forecast_settings': {'num_leituras_futuras': 6, 'intervalo_leitura_minutos': 5, 'alerta_forecast_ativo': True, 'arima_p': 1, 'arima_d': 1, 'arima_q': 1},
        'ml_classifier': {'test_size': 0.3, 'random_state': 42, 'n_estimators': 100, 'min_samples_leaf': 3},
        'report_settings': {'max_anomalias_no_relatorio': 5, 'max_leituras_recentes_tabela_pdf': 15, 'autor_relatorio': "Diogo Zequini"},
        'cli_settings': {'max_leituras_tabela_console': 10}
    }
    config_final_para_uso = default_cfg_interno.copy()
    if yaml_module and os.path.exists(CONFIG_FILE_PATH_GLOBAL_DASH):
        try:
            with open(CONFIG_FILE_PATH_GLOBAL_DASH, 'r', encoding='utf-8') as f:
                config_do_arquivo = yaml_module.safe_load(f)
            if config_do_arquivo:
                logger.info(f"Configurações carregadas de '{CONFIG_FILE_PATH_GLOBAL_DASH}'.")
                for chave_principal, valor_default_secao in default_cfg_interno.items():
                    if chave_principal in config_do_arquivo:
                        if isinstance(valor_default_secao, dict) and isinstance(config_do_arquivo.get(chave_principal), dict):
                            secao_mesclada = valor_default_secao.copy()
                            secao_mesclada.update(config_do_arquivo[chave_principal])
                            config_final_para_uso[chave_principal] = secao_mesclada
                        else:
                            config_final_para_uso[chave_principal] = config_do_arquivo[chave_principal]
                
                # Tratar arima_order se p,d,q separados existem
                if 'forecast_settings' in config_final_para_uso and \
                   all(k in config_final_para_uso['forecast_settings'] for k in ['arima_p', 'arima_d', 'arima_q']):
                     cfg_fc = config_final_para_uso['forecast_settings']
                     config_final_para_uso['forecast_settings']['arima_order'] = (cfg_fc['arima_p'], cfg_fc['arima_d'], cfg_fc['arima_q'])
                
                # Reescrever o YAML se a estrutura carregada for diferente da final esperada
                config_para_salvar_yaml = config_final_para_uso.copy()
                if 'forecast_settings' in config_para_salvar_yaml and \
                   isinstance(config_para_salvar_yaml['forecast_settings'].get('arima_order'), tuple):
                    p,d,q = config_para_salvar_yaml['forecast_settings']['arima_order']
                    config_para_salvar_yaml['forecast_settings']['arima_p'] = p
                    config_para_salvar_yaml['forecast_settings']['arima_d'] = d
                    config_para_salvar_yaml['forecast_settings']['arima_q'] = q
                    if 'arima_order' in config_para_salvar_yaml['forecast_settings']:
                        del config_para_salvar_yaml['forecast_settings']['arima_order'] 
                
                # Verifica se precisa reescrever
                precisa_reescrever_yaml = False
                if not all(k in config_do_arquivo for k in default_cfg_interno): # Se faltam chaves default no arquivo
                    precisa_reescrever_yaml = True
                else: # Checa se os sub-dicionários também estão completos
                    for k_default, v_default_section in default_cfg_interno.items():
                        if isinstance(v_default_section, dict):
                            if not all(sub_k in config_do_arquivo.get(k_default,{}) for sub_k in v_default_section):
                                precisa_reescrever_yaml = True; break
                if config_para_salvar_yaml != config_do_arquivo and any(k not in config_do_arquivo.get('forecast_settings', {}) for k in ['arima_p','arima_d','arima_q']): # Se arima p,d,q não estavam no arquivo
                    precisa_reescrever_yaml = True

                if precisa_reescrever_yaml:
                    try:
                        with open(CONFIG_FILE_PATH_GLOBAL_DASH, 'w', encoding='utf-8') as f_save:
                            yaml_module.dump(config_para_salvar_yaml, f_save, sort_keys=False, allow_unicode=True, indent=4)
                        logger.info(f"'{CONFIG_FILE_PATH_GLOBAL_DASH}' (re)escrito com estrutura completa/padronizada.")
                    except IOError as e_write:
                        logger.error(f"Não reescreveu '{CONFIG_FILE_PATH_GLOBAL_DASH}': {e_write}")
            else:
                 logger.warning(f"'{CONFIG_FILE_PATH_GLOBAL_DASH}' vazio/malformado. Usando defaults e recriando.")
                 # Recria com p,d,q separados
                 with open(CONFIG_FILE_PATH_GLOBAL_DASH, 'w', encoding='utf-8') as f_create_empty:
                    yaml_module.dump(default_cfg_interno, f_create_empty, sort_keys=False, allow_unicode=True, indent=4)
            return config_final_para_uso
        except yaml.YAMLError as e:
            logger.error(f"Sintaxe YAML em '{CONFIG_FILE_PATH_GLOBAL_DASH}': {e}. Usando padrões.")
            return default_cfg_interno
        except Exception as e_gen:
            logger.error(f"Erro geral ao carregar '{CONFIG_FILE_PATH_GLOBAL_DASH}': {e_gen}. Usando padrões.")
            return default_cfg_interno
    else:
        logger.warning(f"'{CONFIG_FILE_PATH_GLOBAL_DASH}' não encontrado. Usando padrões e criando.")
        try:
            with open(CONFIG_FILE_PATH_GLOBAL_DASH, 'w', encoding='utf-8') as f:
                yaml_module.dump(default_cfg_interno, f, sort_keys=False, allow_unicode=True, indent=4)
            logger.info(f"'{CONFIG_FILE_PATH_GLOBAL_DASH}' criado com defaults.")
        except IOError as e_io_create:
            logger.error(f"Não criou '{CONFIG_FILE_PATH_GLOBAL_DASH}': {e_io_create}")
        return default_cfg_interno

config_app = carregar_configuracoes_dashboard_final()

# Usa as configurações carregadas ou os defaults globais
DB_NAME_APP = config_app.get('db_name', DB_NAME_DEFAULT_GLOBAL_DASH)
TABLE_NAME_APP = config_app.get('table_name', TABLE_NAME_DEFAULT_GLOBAL_DASH)
LOGICA_ESP32_PARAMS_APP_CONFIG = config_app.get('logica_esp32', LOGICA_ESP32_PARAMS_DEFAULT_GLOBAL_DASH.copy())
CUSTO_CFG_APP_CONFIG = config_app.get('custo_settings', CUSTO_SETTINGS_DEFAULT_GLOBAL_DASH.copy())


# --- Sidebar ---
st.sidebar.header("Configurações da Simulação")
st.sidebar.subheader("Localização para Dados Climáticos")
default_lat_app, default_lon_app = -22.9083, -43.1964
sim_lat_app = st.sidebar.number_input("Latitude", value=default_lat_app, format="%.4f", key="app_lat_v3")
sim_lon_app = st.sidebar.number_input("Longitude", value=default_lon_app, format="%.4f", key="app_lon_v3")
st.sidebar.info(f"Meteoblue API: {'DEMO' if METEOBLUE_API_KEY=='DEMO' else 'OK'} | Lat/Lon: {sim_lat_app:.2f}, {sim_lon_app:.2f}")


# --- Conexão com Banco de Dados e Definição da Tabela ---
BaseDB_App = declarative_base()
engine_app_conn = None
SessionLocal_App = None
try:
    engine_app_conn = create_engine(f"sqlite:///{DB_NAME_APP}?check_same_thread=False")
    SessionLocal_App = sessionmaker(autocommit=False, autoflush=False, bind=engine_app_conn)
    class LeituraSensorApp(BaseDB_App):
        __tablename__ = TABLE_NAME_APP
        __table_args__ = {'extend_existing': True}
        id = Column(Integer, primary_key=True)
        timestamp = Column(DateTime, unique=True, nullable=False)
        umidade = Column(Float, nullable=False)
        ph_estimado = Column(Float, nullable=False)
        fosforo_presente = Column(Boolean, nullable=False)
        potassio_presente = Column(Boolean, nullable=False)
        temperatura = Column(Float)
        bomba_ligada = Column(Boolean, nullable=False)
        decisao_logica_esp32 = Column(String, nullable=True)
        emergencia = Column(Boolean, nullable=False)
    BaseDB_App.metadata.create_all(bind=engine_app_conn)
except Exception as e_db_app_setup:
    logger.error(f"Erro DB dashboard: {e_db_app_setup}", exc_info=True)
    st.error(f"Erro crítico DB: {e_db_app_setup}. Verifique '{DB_NAME_APP}'.")

# --- Funções de Apoio (carregar dados, buscar clima, simular lógica) ---
@st.cache_data(ttl=300)
def carregar_dados_historicos_app():
    if not engine_app_conn or not SessionLocal_App: return pd.DataFrame()
    try:
        with SessionLocal_App() as db:
            query = db.query(LeituraSensorApp).order_by(LeituraSensorApp.timestamp.desc())
            df = pd.read_sql(query.statement, db.bind, index_col='timestamp', parse_dates=['timestamp'])
        if not df.empty:
            if df.index.tz is None: df.index = df.index.tz_localize('UTC')
            else: df.index = df.index.tz_convert('UTC')
        return df
    except Exception as e:
        logger.error(f"Erro ao carregar dados histórico para App: {e}", exc_info=True)
        st.warning(f"Não foi possível carregar dados históricos (Tabela '{TABLE_NAME_APP}' existe?).")
        return pd.DataFrame()

@st.cache_data(ttl=1800)
def buscar_dados_meteoblue_app(lat, lon, tipo_pacote="basic-1h"):
    api_key_interna_mb = METEOBLUE_API_KEY
    if not api_key_interna_mb: return None, "Chave API Meteoblue não configurada no código."
    # ... (resto da função buscar_dados_meteoblue_cached_app, usando api_key_interna_mb)
    base_url = f"https://my.meteoblue.com/packages/{tipo_pacote}"
    params = {
        "apikey": api_key_interna_mb, "lat": lat, "lon": lon, "format": "json",
        "temperature": "C", "windspeed": "kmh", "precipitationamount": "mm",
        "timeformat": "iso8601", "forecast_days": 3
    }
    try:
        response = requests.get(base_url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        if "metadata" not in data or (tipo_pacote == "basic-day" and "data_day" not in data) or \
           (tipo_pacote == "basic-1h" and "data_1h" not in data) :
            logger.error(f"Estrutura API Meteoblue inesperada ({tipo_pacote}): {data}")
            return None, "Resposta API Meteoblue com estrutura inesperada."
        return data, None
    except requests.exceptions.Timeout:
        logger.error(f"Timeout Meteoblue ({tipo_pacote}).")
        return None, f"Timeout API Meteoblue ({tipo_pacote})."
    except requests.exceptions.HTTPError as http_err:
        err_msg_http = f"Erro HTTP {response.status_code} API Meteoblue ({tipo_pacote}): {http_err}."
        if response and hasattr(response, 'text') and response.text: err_msg_http += f" Detalhe: {response.text[:200]}"
        logger.error(err_msg_http)
        return None, err_msg_http
    except Exception as e_meteo:
        logger.error(f"Erro API Meteoblue ({tipo_pacote}): {e_meteo}", exc_info=True)
        return None, f"Erro ao buscar dados Meteoblue ({tipo_pacote})."


def simular_logica_irrigacao_app(umidade, ph, p, k, cfg_logica: dict, chuva_mm=0.0):
    # (Lógica do ESP32 - replicada e usando cfg_logica)
    ligar_bomba, motivo = False, "Condições padrão, bomba desligada."
    if umidade < cfg_logica['UMIDADE_CRITICA_BAIXA']:
        ligar_bomba, motivo = True, f"EMERGÊNCIA: Umidade crítica ({umidade:.1f}%)"
    elif ph < cfg_logica['PH_CRITICO_MINIMO'] or ph > cfg_logica['PH_CRITICO_MAXIMO']:
        ligar_bomba, motivo = False, f"pH crítico ({ph:.1f}%)"
    elif umidade < cfg_logica['UMIDADE_MINIMA_PARA_IRRIGAR']:
        if cfg_logica['PH_IDEAL_MINIMO'] <= ph <= cfg_logica['PH_IDEAL_MAXIMO']:
            ligar_bomba = True
            if p and k: motivo = f"Umid. baixa ({umidade:.1f}%), pH ideal ({ph:.1f}), P&K OK"
            elif p or k: motivo = f"Umid. baixa ({umidade:.1f}%), pH ideal ({ph:.1f}), P ou K OK"
            else: motivo = f"Umid. baixa ({umidade:.1f}%), pH ideal ({ph:.1f}), Nutrientes Ausentes"
        else: motivo = f"Umid. baixa ({umidade:.1f}%), mas pH ({ph:.1f}) não ideal"
    elif umidade > cfg_logica['UMIDADE_ALTA_PARAR_IRRIGACAO']:
        ligar_bomba, motivo = False, f"Umidade alta ({umidade:.1f}%)"
    
    if ligar_bomba and chuva_mm > 1.0: # Limiar de chuva significativa
        return False, f"DECISÃO BASE: Ligar ({motivo}). AJUSTE CLIMA: DESLIGAR (Chuva: {chuva_mm:.1f}mm)."
    
    final_motivo = motivo
    if chuva_mm > 0: final_motivo += f" (Chuva: {chuva_mm:.1f}mm)"
    else: final_motivo += " (Sem chuva prevista)"
    return ligar_bomba, final_motivo

# --- Funções para Novas Melhorias ---
def analisar_alertas_recentes_app(df_periodo, cfg_logica, console=st):
    """Analisa os dados mais recentes do período e exibe alertas."""
    if df_periodo.empty: return
    alertas = []
    # Analisar os últimos 5 registros do período selecionado, por exemplo
    df_recente = df_periodo.tail(5) 
    for idx, row in df_recente.iterrows():
        if row['umidade'] < cfg_logica['UMIDADE_CRITICA_BAIXA']:
            alertas.append(f"🔴 Umidade Crítica ({row['umidade']:.1f}%) em {idx.strftime('%d/%m %H:%M')}")
        if not (cfg_logica['PH_CRITICO_MINIMO'] <= row['ph_estimado'] <= cfg_logica['PH_CRITICO_MAXIMO']):
            alertas.append(f"🟡 pH Fora da Faixa Segura ({row['ph_estimado']:.1f}) em {idx.strftime('%d/%m %H:%M')}")
    
    if alertas:
        console.warning("🚨 Painel de Alertas Rápidos (Dados Recentes):")
        for alerta in alertas:
            console.markdown(f"- {alerta}")
    else:
        console.info("✅ Sem alertas críticos nos dados recentes do período selecionado.")

def calcular_custos_operacionais_app(df_periodo, cfg_custos, cfg_geral, console=st):
    if df_periodo.empty or 'bomba_ligada' not in df_periodo.columns:
        console.info("Custos: Dados insuficientes para cálculo.")
        return 0.0, 0.0, 0
    
    intervalo_registros_min = cfg_geral.get('forecast_settings', {}).get('intervalo_leitura_minutos', 5)
    tempo_bomba_ligada_min = df_periodo['bomba_ligada'].sum() * intervalo_registros_min
    
    if tempo_bomba_ligada_min == 0:
        console.info("Custos: Bomba não foi acionada no período. Custo zero.")
        return 0.0, 0.0, 0
    
    tempo_bomba_ligada_h = tempo_bomba_ligada_min / 60.0
    volume_agua_usado_m3 = (cfg_custos['vazao_bomba_litros_por_hora'] / 1000.0) * tempo_bomba_ligada_h
    custo_total_agua = volume_agua_usado_m3 * cfg_custos['custo_agua_reais_por_m3']
    
    consumo_energia_kwh = cfg_custos['potencia_bomba_kw'] * tempo_bomba_ligada_h
    custo_total_energia = consumo_energia_kwh * cfg_custos['custo_energia_kwh']
    
    custo_operacional_total = custo_total_agua + custo_total_energia
    num_ciclos_estimados = df_periodo['bomba_ligada'].astype(int).diff().fillna(0).eq(1).sum()


    console.metric("Ciclos de Irrigação Estimados", num_ciclos_estimados)
    col1, col2, col3 = console.columns(3)
    col1.metric("Custo Água Estimado", f"R$ {custo_total_agua:.2f}")
    col2.metric("Custo Energia Estimado", f"R$ {custo_total_energia:.2f}")
    col3.metric("CUSTO OPERACIONAL TOTAL", f"R$ {custo_operacional_total:.2f}")
    return custo_total_agua, custo_total_energia, num_ciclos_estimados


def gerar_diagnostico_sugestoes_app(df_periodo, cfg_logica, console=st):
    if df_periodo.empty or len(df_periodo) < 5: # Precisa de alguns dados para diagnóstico
        console.info("Diagnóstico: Dados insuficientes para um diagnóstico detalhado.")
        return

    with console.expander("🔬 Diagnóstico do Sistema e Sugestões (Beta)"):
        st.markdown("**Análise de Comportamento:**")
        # Umidade média no acionamento
        df_bomba_on = df_periodo[df_periodo['bomba_ligada'] == True]
        if not df_bomba_on.empty:
            umid_media_acionamento = df_bomba_on['umidade'].mean()
            st.write(f"- Umidade média no momento do acionamento da bomba: **{umid_media_acionamento:.1f}%**.")
            if umid_media_acionamento < cfg_logica['UMIDADE_MINIMA_PARA_IRRIGAR'] - 5: # Se aciona muito abaixo
                st.caption("  Sugestão: A bomba está sendo acionada com umidade já consideravelmente baixa. Verifique se o limiar de irrigação está adequado ou se há atrasos na resposta do sistema.")
            elif umid_media_acionamento > cfg_logica['UMIDADE_MINIMA_PARA_IRRIGAR'] + 5:
                 st.caption("  Sugestão: A bomba parece ser acionada com umidade ainda relativamente alta. Considere revisar o limiar MÍNIMO para irrigar para otimizar o uso da água.")
        else:
            st.write("- Bomba não foi acionada no período para análise de umidade de acionamento.")

        # pH médio
        ph_medio_periodo = df_periodo['ph_estimado'].mean()
        st.write(f"- pH médio no período: **{ph_medio_periodo:.1f}**.")
        if not (cfg_logica['PH_IDEAL_MINIMO'] <= ph_medio_periodo <= cfg_logica['PH_IDEAL_MAXIMO']):
            st.caption(f"  Atenção: O pH médio está fora da faixa ideal ({cfg_logica['PH_IDEAL_MINIMO']}-{cfg_logica['PH_IDEAL_MAXIMO']}). Isso pode afetar a absorção de nutrientes. Considere análise e correção do solo.")

        # Frequência de condições críticas
        umidade_critica_ocorrencias = df_periodo[df_periodo['umidade'] < cfg_logica['UMIDADE_CRITICA_BAIXA']].shape[0]
        ph_critico_ocorrencias = df_periodo[(df_periodo['ph_estimado'] < cfg_logica['PH_CRITICO_MINIMO']) | (df_periodo['ph_estimado'] > cfg_logica['PH_CRITICO_MAXIMO'])].shape[0]
        
        st.write(f"- Ocorrências de umidade crítica (<{cfg_logica['UMIDADE_CRITICA_BAIXA']}%): **{umidade_critica_ocorrencias}**.")
        if umidade_critica_ocorrencias > len(df_periodo) * 0.1: # Se mais de 10% das leituras foram críticas
            st.caption("  Sugestão: Alta frequência de umidade crítica. Revise a frequência de irrigação ou os limiares de emergência.")
        
        st.write(f"- Ocorrências de pH crítico (<{cfg_logica['PH_CRITICO_MINIMO']} ou >{cfg_logica['PH_CRITICO_MAXIMO']}): **{ph_critico_ocorrencias}**.")
        if ph_critico_ocorrencias > len(df_periodo) * 0.1:
            st.caption("  Sugestão: Alta frequência de pH crítico. Priorize a correção do pH do solo.")

# --- Funções avançadas de análise de dados
def calculate_advanced_metrics(df):
    """Calcula métricas avançadas para análise do sistema"""
    if df.empty:
        return None
    
    metrics = {
        "irrigation_cycles": df['bomba_ligada'].astype(int).diff().fillna(0).eq(1).sum(),
        "avg_humidity": df['umidade'].mean(),
        "humidity_std": df['umidade'].std(),
        "ph_stability": df['ph_estimado'].std(),
        "critical_events": len(df[df['umidade'] < LOGICA_ESP32_PARAMS_DEFAULT_GLOBAL_DASH['UMIDADE_CRITICA_BAIXA']]),
        "system_efficiency": calculate_system_efficiency(df)
    }
    return metrics

def calculate_system_efficiency(df):
    """Calcula a eficiência do sistema baseada em múltiplos fatores"""
    if df.empty:
        return 0
    
    # Fatores de peso para cada componente
    weights = {
        'humidity_control': 0.4,
        'ph_stability': 0.3,
        'response_time': 0.3
    }
    
    # Cálculo do controle de umidade
    humidity_ideal = (LOGICA_ESP32_PARAMS_DEFAULT_GLOBAL_DASH['UMIDADE_MINIMA_PARA_IRRIGAR'] + 
                     LOGICA_ESP32_PARAMS_DEFAULT_GLOBAL_DASH['UMIDADE_ALTA_PARAR_IRRIGACAO']) / 2
    humidity_dev = abs(df['umidade'] - humidity_ideal).mean()
    humidity_score = max(0, 100 - (humidity_dev * 2))
    
    # Cálculo da estabilidade do pH
    ph_ideal = (LOGICA_ESP32_PARAMS_DEFAULT_GLOBAL_DASH['PH_IDEAL_MINIMO'] + 
                LOGICA_ESP32_PARAMS_DEFAULT_GLOBAL_DASH['PH_IDEAL_MAXIMO']) / 2
    ph_dev = abs(df['ph_estimado'] - ph_ideal).mean()
    ph_score = max(0, 100 - (ph_dev * 10))
    
    # Cálculo do tempo de resposta
    response_score = 100
    if 'bomba_ligada' in df.columns:
        critical_points = df[df['umidade'] < LOGICA_ESP32_PARAMS_DEFAULT_GLOBAL_DASH['UMIDADE_MINIMA_PARA_IRRIGAR']]
        if not critical_points.empty:
            response_delays = []
            for idx in critical_points.index:
                future_window = df.loc[idx:].head(12)  # Próximas 12 leituras
                if not future_window.empty and 'bomba_ligada' in future_window:
                    response_time = future_window['bomba_ligada'].values.argmax()
                    response_delays.append(response_time)
            if response_delays:
                avg_response = sum(response_delays) / len(response_delays)
                response_score = max(0, 100 - (avg_response * 10))
    
    # Cálculo da eficiência total
    efficiency = (
        weights['humidity_control'] * humidity_score +
        weights['ph_stability'] * ph_score +
        weights['response_time'] * response_score
    )
    
    return round(efficiency, 2)

# Função para criar gráficos avançados com Plotly
def create_advanced_plotly_chart(df, y_column, title, color_scheme='viridis'):
    """Cria um gráfico Plotly avançado com análises estatísticas"""
    if df.empty or y_column not in df.columns:
        return None
    
    # Calcula médias móveis e bandas de confiança
    df['MA7'] = df[y_column].rolling(window=7).mean()
    df['MA21'] = df[y_column].rolling(window=21).mean()
    df['std'] = df[y_column].rolling(window=7).std()
    df['upper_band'] = df['MA7'] + (df['std'] * 2)
    df['lower_band'] = df['MA7'] - (df['std'] * 2)
    
    # Cria o gráfico base
    fig = go.Figure()
    
    # Adiciona as bandas de confiança
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['upper_band'],
        fill=None,
        mode='lines',
        line_color='rgba(0,100,80,0.2)',
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['lower_band'],
        fill='tonexty',
        mode='lines',
        line_color='rgba(0,100,80,0.2)',
        name='Banda de Confiança (95%)'
    ))
    
    # Adiciona os dados principais
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df[y_column],
        mode='lines',
        name=y_column,
        line=dict(color='#2196F3')
    ))
    
    # Adiciona as médias móveis
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['MA7'],
        mode='lines',
        name='Média Móvel (7 períodos)',
        line=dict(color='#FF9800', dash='dash')
    ))
    
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['MA21'],
        mode='lines',
        name='Média Móvel (21 períodos)',
        line=dict(color='#4CAF50', dash='dash')
    ))
    
    # Configuração do layout
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor='center'
        ),
        xaxis_title="Data/Hora",
        yaxis_title=y_column,
        template="plotly_white",
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

# Função para criar um relatório executivo
def create_executive_summary(df, metrics):
    """Cria um relatório executivo com insights principais"""
    if df.empty or not metrics:
        return "Dados insuficientes para gerar relatório executivo."
    
    summary = f"""
    ### 📊 Relatório Executivo

    #### Indicadores Chave (KPIs)
    - **Eficiência do Sistema**: {metrics['system_efficiency']}%
    - **Ciclos de Irrigação**: {metrics['irrigation_cycles']}
    - **Eventos Críticos**: {metrics['critical_events']}

    #### Análise de Estabilidade
    - Desvio Padrão Umidade: {metrics['humidity_std']:.2f}%
    - Desvio Padrão pH: {metrics['ph_stability']:.2f}

    #### Recomendações
    {generate_recommendations(df, metrics)}
    """
    return summary

def generate_recommendations(df, metrics):
    """Gera recomendações baseadas nos dados e métricas"""
    recommendations = []
    
    # Análise de eficiência
    if metrics['system_efficiency'] < 70:
        recommendations.append("⚠️ Necessária otimização do sistema - eficiência abaixo do ideal.")
    
    # Análise de estabilidade
    if metrics['humidity_std'] > 10:
        recommendations.append("📈 Alta variação na umidade - considerar ajuste nos parâmetros de controle.")
    
    if metrics['ph_stability'] > 0.5:
        recommendations.append("🧪 Instabilidade no pH - recomendada análise do solo.")
    
    # Análise de eventos críticos
    if metrics['critical_events'] > 0:
        recommendations.append(f"🚨 {metrics['critical_events']} eventos críticos detectados - revisar limiares de alerta.")
    
    return "\n".join(f"- {r}" for r in recommendations)

# Funções auxiliares para simulação avançada
def calculate_irrigation_cost(minutes, flow_rate, water_cost, power, energy_cost):
    """Calcula o custo de irrigação baseado nos parâmetros fornecidos"""
    hours = minutes / 60
    water_volume = (flow_rate * hours) / 1000  # Conversão para m³
    water_total = water_volume * water_cost
    energy_total = power * hours * energy_cost
    return water_total + energy_total

def evaluate_soil_conditions(humidity, ph, phosphorus, potassium, params):
    """Avalia as condições do solo e retorna recomendações"""
    recommendations = []
    risk_level = 'baixo'
    efficiency_impact = 0
    
    # Avaliação de umidade
    if humidity < params['UMIDADE_CRITICA_BAIXA']:
        risk_level = 'alto'
        efficiency_impact -= 30
        recommendations.append({
            'type': 'critical',
            'message': '⚠️ Umidade criticamente baixa',
            'action': 'Irrigação emergencial necessária'
        })
    elif humidity < params['UMIDADE_MINIMA_PARA_IRRIGAR']:
        risk_level = max(risk_level, 'médio')
        efficiency_impact -= 15
        recommendations.append({
            'type': 'warning',
            'message': '⚡ Umidade abaixo do ideal',
            'action': 'Considerar irrigação preventiva'
        })
    
    # Avaliação de pH
    if ph < params['PH_CRITICO_MINIMO']:
        risk_level = 'alto'
        efficiency_impact -= 20
        recommendations.append({
            'type': 'critical',
            'message': '🧪 pH criticamente baixo',
            'action': 'Correção de acidez necessária'
        })
    elif ph > params['PH_CRITICO_MAXIMO']:
        risk_level = 'alto'
        efficiency_impact -= 20
        recommendations.append({
            'type': 'critical',
            'message': '🧪 pH criticamente alto',
            'action': 'Correção de alcalinidade necessária'
        })
    elif not (params['PH_IDEAL_MINIMO'] <= ph <= params['PH_IDEAL_MAXIMO']):
        risk_level = max(risk_level, 'médio')
        efficiency_impact -= 10
        recommendations.append({
            'type': 'warning',
            'message': '🧪 pH fora da faixa ideal',
            'action': 'Monitorar e planejar correção'
        })
    
    # Avaliação de nutrientes
    if not (phosphorus and potassium):
        risk_level = max(risk_level, 'médio')
        efficiency_impact -= 15
        recommendations.append({
            'type': 'warning',
            'message': '🌱 Deficiência de nutrientes',
            'action': 'Considerar fertilização'
        })
    
    return risk_level, efficiency_impact, recommendations

def generate_intelligent_insights(params, historical_data):
    """Gera insights inteligentes baseados nos parâmetros e dados históricos"""
    insights = []
    
    if historical_data is not None and not historical_data.empty:
        # Análise de tendências
        recent_data = historical_data.tail(24)  # Últimas 24 leituras
        avg_humidity = recent_data['umidade'].mean()
        
        if abs(params['umidade'] - avg_humidity) > 15:
            insights.append({
                'type': 'trend',
                'message': f'📈 Variação significativa da umidade em relação à média recente ({avg_humidity:.1f}%)',
                'details': 'Considerar investigação de causas'
            })
        
        # Análise de padrões
        if len(recent_data) >= 24:
            irrigation_count = recent_data['bomba_ligada'].sum()
            if irrigation_count > 12:  # Mais de 50% do tempo
                insights.append({
                    'type': 'pattern',
                    'message': '⚠️ Alta frequência de irrigação nas últimas 24 leituras',
                    'details': 'Verificar eficiência do sistema'
                })
    
    return insights

def simulate_advanced_scenario(params, historical_data=None):
    """Simula um cenário avançado com base nos parâmetros fornecidos"""
    # Inicialização dos resultados
    results = {
        'decision': False,
        'explanation': '',
        'risk_level': 'baixo',
        'efficiency_impact': 0,
        'cost_impact': 0,
        'recommendations': [],
        'insights': []
    }
    
    # Simulação básica de decisão
    results['decision'], base_explanation = simular_logica_irrigacao_app(
        params['umidade'],
        params['ph'],
        params['fosforo'],
        params['potassio'],
        LOGICA_ESP32_PARAMS_DEFAULT_GLOBAL_DASH,
        params.get('precipitation', 0)
    )
    results['explanation'] = base_explanation
    
    # Avaliação avançada das condições
    risk_level, efficiency_impact, recommendations = evaluate_soil_conditions(
        params['umidade'],
        params['ph'],
        params['fosforo'],
        params['potassio'],
        LOGICA_ESP32_PARAMS_DEFAULT_GLOBAL_DASH
    )
    
    results['risk_level'] = risk_level
    results['efficiency_impact'] = efficiency_impact
    results['recommendations'].extend(recommendations)
    
    # Cálculo de custos se decidir irrigar
    if results['decision']:
        results['cost_impact'] = calculate_irrigation_cost(
            CUSTO_SETTINGS_DEFAULT_GLOBAL_DASH['tempo_irrigacao_padrao_minutos'],
            CUSTO_SETTINGS_DEFAULT_GLOBAL_DASH['vazao_bomba_litros_por_hora'],
            CUSTO_SETTINGS_DEFAULT_GLOBAL_DASH['custo_agua_reais_por_m3'],
            CUSTO_SETTINGS_DEFAULT_GLOBAL_DASH['potencia_bomba_kw'],
            CUSTO_SETTINGS_DEFAULT_GLOBAL_DASH['custo_energia_kwh']
        )
    
    # Geração de insights baseados em dados históricos
    if historical_data is not None:
        results['insights'] = generate_intelligent_insights(params, historical_data)
    
    return results

# --- Layout Principal do Dashboard ---
# (Adaptações para usar as novas funções)
# ... (Logo e Título como antes) ...
if os.path.exists("logo_farmtech.png"): # Assumindo que você tem um logo.png
    st.image("logo_farmtech.png", width=80)

# Banner principal animado
st.markdown('<div class="top-banner fade-in">', unsafe_allow_html=True)
animated_header("FarmTech Solutions - Dashboard Avançado PhD", "🌱")
st.markdown('</div>', unsafe_allow_html=True)

# Tabs principais
tab_historico, tab_sistema, tab_clima, tab_whatif, tab_sobre = st.tabs([
    "📈 Histórico e Diagnóstico", 
    "🔧 Sistema",
    "🌦️ Clima (Meteoblue)", 
    "💡 Simulador What-If",
    "ℹ️ Sobre"
])

# Tab Histórico
with tab_historico:
    df_hist_app_main = carregar_dados_historicos_app()
    if not df_hist_app_main.empty:
        animated_header("Análise Histórica e Diagnóstico", "📊")
        
        # Filtros avançados
        with st.container():
            st.markdown("""
                <div class="filter-container fade-in">
                    <h3>Filtros de Análise</h3>
                </div>
            """, unsafe_allow_html=True)
            
            # Seletor de período
            col1, col2 = st.columns(2)
            with col1:
                datas_disponiveis = sorted(list(set(df_hist_app_main.index.date)))
                if datas_disponiveis:
                    data_inicial = st.date_input(
                        "Data Inicial",
                        value=datas_disponiveis[0],
                        min_value=datas_disponiveis[0],
                        max_value=datas_disponiveis[-1]
                    )
            with col2:
                if datas_disponiveis:
                    data_final = st.date_input(
                        "Data Final",
                        value=datas_disponiveis[-1],
                        min_value=datas_disponiveis[0],
                        max_value=datas_disponiveis[-1]
                    )
            
            # Filtra os dados pelo período selecionado
            mask = (df_hist_app_main.index.date >= data_inicial) & (df_hist_app_main.index.date <= data_final)
            df_periodo = df_hist_app_main.loc[mask]
            
            # Métricas avançadas
            metrics = calculate_advanced_metrics(df_periodo)
            if metrics:
                st.markdown("### 📊 Métricas do Sistema")
                col1, col2, col3, col4 = st.columns(4)
                
                col1.metric(
                    "Eficiência do Sistema",
                    f"{metrics['system_efficiency']}%",
                    delta="referência: 70%"
                )
                
                col2.metric(
                    "Ciclos de Irrigação",
                    metrics['irrigation_cycles'],
                    delta=f"{metrics['critical_events']} críticos"
                )
                
                col3.metric(
                    "Umidade Média",
                    f"{metrics['avg_humidity']:.1f}%",
                    delta=f"±{metrics['humidity_std']:.1f}%"
                )
                
                col4.metric(
                    "Estabilidade pH",
                    f"{metrics['ph_stability']:.2f}",
                    delta="referência: <0.5"
                )

                # --- Comparativo de Eficiência entre Períodos ---
                st.markdown("---")
                st.subheader("📊 Comparativo de Eficiência entre Períodos")
                comp_col1, comp_col2 = st.columns(2)
                with comp_col1:
                    periodo1 = st.date_input("Período 1", key="periodo1")
                with comp_col2:
                    periodo2 = st.date_input("Período 2", key="periodo2")
                if st.button("Comparar Eficiência", key="btn_comp_eff"):
                    def _calc_eff(date_sel):
                        mask_p = df_hist_app_main.index.date == date_sel
                        return calculate_system_efficiency(df_hist_app_main.loc[mask_p])
                    eff1 = _calc_eff(periodo1)
                    eff2 = _calc_eff(periodo2)
                    delta_eff = eff2 - eff1
                    st.metric("Melhoria de Eficiência", f"{eff2:.1f}%", f"{delta_eff:+.1f}%")
            
            # Gráficos avançados
            st.markdown("### 📈 Análise Visual Avançada")
            chart_type = st.radio(
                "Tipo de Visualização",
                ["Série Temporal Avançada", "Análise de Correlação", "Distribuição"]
            )
            
            if chart_type == "Série Temporal Avançada":
                variable = st.selectbox(
                    "Variável para Análise",
                    ["umidade", "ph_estimado", "temperatura"]
                )
                fig = create_advanced_plotly_chart(df_periodo, variable, f"Análise Avançada - {variable}")
                st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Análise de Correlação":
                fig = px.scatter(df_periodo, x="umidade", y="ph_estimado",
                               color="temperatura", size="temperatura",
                               title="Correlação entre Variáveis")
                st.plotly_chart(fig, use_container_width=True)
            
            else:  # Distribuição
                fig = px.histogram(df_periodo, x="umidade",
                                 marginal="box",
                                 title="Distribuição da Umidade")
                st.plotly_chart(fig, use_container_width=True)
            
            # Relatório Executivo
            with st.expander("📋 Relatório Executivo", expanded=True):
                st.markdown(create_executive_summary(df_periodo, metrics))
    
    else:
        st.info("Nenhum dado histórico disponível. Execute o gerenciador_dados.py para popular o banco.")

# --- Adição no Histórico: Comparativo de Eficiência ---
# BLOCO DUPLICADO REMOVIDO PARA CORREÇÃO DE INDENTAÇÃO

# --- Nova Aba: Sistema ---
with tab_sistema:
    st.header("🩺 Relatório de Saúde do Sistema")
    df_hist_full = carregar_dados_historicos_app()
    if df_hist_full.empty:
        st.warning("Sem dados coletados para calcular métricas de saúde do sistema.")
    else:
        tempo_total_horas = (df_hist_full.index.max() - df_hist_full.index.min()).total_seconds() / 3600.0
        uptime_sistema = 0.0
        if tempo_total_horas > 0:
            uptime_sistema = min(100.0, (len(df_hist_full) * (3/60)) / tempo_total_horas * 100)
        eficiencia_irrigacao = calculate_system_efficiency(df_hist_full)
        economia_calculada = round((100 - eficiencia_irrigacao) * 0.05, 2)

        col1, col2, col3 = st.columns(3)
        col1.metric("Uptime Sistema", f"{uptime_sistema:.1f}%")
        col2.metric("Eficiência Irrigação", f"{eficiencia_irrigacao:.1f}%")
        col3.metric("Economia de Água (estim.)", f"R$ {economia_calculada:.2f}")

        from backend import data_analysis as da
        hist_stats = da.analisar_historico_decisoes(df_hist_full)
        st.subheader("📚 Estatísticas das Decisões")
        st.write(f"Emergências registradas: **{hist_stats['total_emergencias']}**")
        st.write(f"pH críticos detectados: **{hist_stats['ph_criticos']}**")
        st.write(f"Decisão mais comum: **{hist_stats['decisao_mais_comum']}**")

    st.markdown("---")
    if not df_hist_full.empty:
        csv_exp = df_hist_full.to_csv(index=True).encode('utf-8')
        st.download_button(
            label="📥 Exportar Dados CSV",
            data=csv_exp,
            file_name=f"farmtech_dados_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key="download_csv_sistema"
        )

# --- Aba: Clima (Meteoblue) ---
with tab_clima:
    # (Como antes, usando METEOBLUE_API_KEY_FIXA e sim_lat_app, sim_lon_app)
    st.header("Condições Meteorológicas (API Meteoblue)")
    if not METEOBLUE_API_KEY or METEOBLUE_API_KEY == "DEMO":
        st.error("Chave da API Meteoblue não configurada no código do dashboard.")
    else:
        if st.button("Buscar Dados Climáticos Agora (Meteoblue)", key="btn_fetch_mb_main_v3"):
            with st.spinner(f"Buscando dados Meteoblue para Lat:{sim_lat_app:.2f}, Lon:{sim_lon_app:.2f}..."):
                dados_diarios_mb_main, erro_d_mb_main = buscar_dados_meteoblue_app(sim_lat_app, sim_lon_app, "basic-day")
                dados_horarios_mb_main, erro_h_mb_main = buscar_dados_meteoblue_app(sim_lat_app, sim_lon_app, "basic-1h")
            
            if erro_d_mb_main: st.error(f"Erro (diário Meteoblue): {erro_d_mb_main}")
            if erro_h_mb_main: st.error(f"Erro (horário Meteoblue): {erro_h_mb_main}")

            if dados_diarios_mb_main and "metadata" in dados_diarios_mb_main:
                st.subheader(f"Previsão Diária - {dados_diarios_mb_main['metadata'].get('name', 'Local')}")
                # ... (código para exibir dados diários da Meteoblue)
                try:
                    df_d_mb_main = pd.DataFrame({
                        'Data': pd.to_datetime(dados_diarios_mb_main['data_day']['time'][:3]),
                        'TMax(°C)': dados_diarios_mb_main['data_day']['temperature_max'][:3],
                        # ... (outras colunas diárias)
                        'Chuva(mm)': dados_diarios_mb_main['data_day']['precipitation'][:3]
                    }).set_index('Data')
                    st.dataframe(df_d_mb_main.style.format("{:.1f}", subset=['TMax(°C)', 'Chuva(mm)'])) # Ajuste subset
                except Exception as e_d_proc_mb_main: st.error(f"Processar dados diários Meteoblue: {e_d_proc_mb_main}")


            if dados_horarios_mb_main and "metadata" in dados_horarios_mb_main:
                st.subheader(f"Previsão Horária - {dados_horarios_mb_main['metadata'].get('name', 'Local')} (Próximas 12h)")
                # ... (código para exibir dados horários da Meteoblue)
                try:
                    df_h_mb_main = pd.DataFrame({
                        'Hora': pd.to_datetime(dados_horarios_mb_main['data_1h']['time'][:12]),
                        'Temp(°C)': dados_horarios_mb_main['data_1h']['temperature'][:12],
                        'Chuva(mm)': dados_horarios_mb_main['data_1h']['precipitation'][:12]
                        # ... (outras colunas horárias)
                    }).set_index('Hora')
                    st.dataframe(df_h_mb_main.style.format("{:.1f}", subset=['Temp(°C)', 'Chuva(mm)']))
                    
                    chuva_prox_val_mb_main = df_h_mb_main["Chuva (mm)"][:3].sum() if not df_h_mb_main.empty else 0.0
                    st.session_state.chuva_mm_meteoblue_proximas_horas_val_main = chuva_prox_val_mb_main
                    st.info(f"Chuva prevista (Meteoblue) para as próximas ~3h: {chuva_prox_val_mb_main:.1f} mm")
                    if plotly_module and not df_h_mb_main.empty:
                        fig_ch_mb_main = px.bar(df_h_mb_main, y="Chuva (mm)", title="Precipitação Horária Prevista (Meteoblue)")
                        st.plotly_chart(fig_ch_mb_main, use_container_width=True)
                except Exception as e_h_proc_mb_main: st.error(f"Processar dados horários Meteoblue: {e_h_proc_mb_main}")


# --- Funções Avançadas para Clima ---
def create_weather_forecast_chart(data_1h, hours=24):
    """Cria um gráfico avançado de previsão do tempo"""
    if not data_1h or "data_1h" not in data_1h:
        return None
    
    df_weather = pd.DataFrame({
        'time': pd.to_datetime(data_1h['data_1h']['time'][:hours]),
        'temperature': data_1h['data_1h']['temperature'][:hours],
        'precipitation': data_1h['data_1h']['precipitation'][:hours],
        'humidity': data_1h['data_1h']['relativehumidity'][:hours],
    })
    
    fig = go.Figure()
    
    # Temperatura
    fig.add_trace(go.Scatter(
        x=df_weather['time'],
        y=df_weather['temperature'],
        name='Temperatura (°C)',
        line=dict(color='#FF9800', width=2),
        yaxis='y'
    ))
    
    # Precipitação
    fig.add_trace(go.Bar(
        x=df_weather['time'],
        y=df_weather['precipitation'],
        name='Precipitação (mm)',
        marker_color='#2196F3',
        yaxis='y2'
    ))
    
    # Umidade Relativa
    fig.add_trace(go.Scatter(
        x=df_weather['time'],
        y=df_weather['humidity'],
        name='Umidade Relativa (%)',
        line=dict(color='#4CAF50', width=2, dash='dot'),
        yaxis='y3'
    ))
    
    # Layout
    fig.update_layout(
        title='Previsão Meteorológica Detalhada',
        hovermode='x unified',
        height=600,
        yaxis=dict(
            title='Temperatura (°C)',
            titlefont=dict(color='#FF9800'),
            tickfont=dict(color='#FF9800')
        ),
        yaxis2=dict(
            title='Precipitação (mm)',
            titlefont=dict(color='#2196F3'),
            tickfont=dict(color='#2196F3'),
            overlaying='y',
            side='right'
        ),
        yaxis3=dict(
            title='Umidade Relativa (%)',
            titlefont=dict(color='#4CAF50'),
            tickfont=dict(color='#4CAF50'),
            overlaying='y',
            side='right',
            position=0.85
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

# Função para análise avançada de risco climático
def analyze_weather_risk(data_1h, hours=24):
    """Analisa riscos baseados na previsão do tempo"""
    if not data_1h or "data_1h" not in data_1h:
        return []
    
    risks = []
    data = data_1h['data_1h']
    
    # Análise das próximas 24 horas
    precipitation_sum = sum(data['precipitation'][:hours])
    temp_max = max(data['temperature'][:hours])
    temp_min = min(data['temperature'][:hours])
    humidity_avg = sum(data['relativehumidity'][:hours]) / hours
    
    # Avaliação de riscos
    if precipitation_sum > 20:
        risks.append({
            'level': 'alto',
            'type': 'precipitação',
            'message': f'🌧️ Alta precipitação prevista ({precipitation_sum:.1f}mm em {hours}h)',
            'recommendation': 'Considerar redução na irrigação'
        })
    elif precipitation_sum > 10:
        risks.append({
            'level': 'médio',
            'type': 'precipitação',
            'message': f'🌦️ Precipitação moderada ({precipitation_sum:.1f}mm em {hours}h)',
            'recommendation': 'Monitorar níveis de umidade'
        })
    
    if temp_max > 30:
        risks.append({
            'level': 'alto',
            'type': 'temperatura',
            'message': f'🌡️ Temperatura elevada prevista (máx: {temp_max:.1f}°C)',
            'recommendation': 'Aumentar frequência de irrigação'
        })
    
    if humidity_avg < 40:
        risks.append({
            'level': 'médio',
            'type': 'umidade',
            'message': f'💧 Baixa umidade relativa (média: {humidity_avg:.1f}%)',
            'recommendation': 'Monitorar necessidade de irrigação'
        })
    
    return risks

# Na aba de clima
with tab_clima:
    st.header("🌦️ Análise Meteorológica Avançada")
    
    # Configurações de localização
    with st.container():
        st.markdown("""
            <div class="element-container">
                <h3>📍 Configuração de Localização</h3>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            sim_lat_app = st.number_input(
                "Latitude",
                value=default_lat_app,
                format="%.4f",
                help="Latitude da localização para previsão do tempo"
            )
        with col2:
            sim_lon_app = st.number_input(
                "Longitude",
                value=default_lon_app,
                format="%.4f",
                help="Longitude da localização para previsão do tempo"
            )
    
    if st.button("🔄 Atualizar Dados Meteorológicos", key="btn_fetch_mb_main_v3"):
        with st.spinner("Buscando dados meteorológicos..."):
            dados_1h, erro_h = buscar_dados_meteoblue_app(sim_lat_app, sim_lon_app, "basic-1h")
            if erro_h:
                st.error(f"Erro ao buscar dados horários: {erro_h}")
            else:
                # Gráfico de previsão
                fig_weather = create_weather_forecast_chart(dados_1h)
                if fig_weather:
                    st.plotly_chart(fig_weather, use_container_width=True)
                
                # Análise de riscos
                risks = analyze_weather_risk(dados_1h)
                if risks:
                    st.markdown("### ⚠️ Análise de Riscos")
                    for risk in risks:
                        color = "red" if risk['level'] == 'alto' else "orange"
                        st.markdown(f"""
                            <div style="padding: 1rem; border-left: 4px solid {color}; background-color: rgba({255 if color == 'red' else 255}, {0 if color == 'red' else 165}, 0, 0.1); margin: 0.5rem 0;">
                                <p style="margin: 0;"><strong>{risk['message']}</strong></p>
                                <p style="margin: 0.5rem 0 0 0; font-size: 0.9em;">Recomendação: {risk['recommendation']}</p>
                            </div>
                        """, unsafe_allow_html=True)

# --- Simulador What-If ---
# (Novo código para a aba What-If)
with tab_whatif:
    st.header("💡 Simulador Avançado de Cenários")
    
    # Container para inputs
    with st.container():
        st.markdown("""
            <div class="element-container">
                <h3>🎯 Parâmetros de Simulação</h3>
                <p>Configure os parâmetros para simular diferentes cenários de irrigação</p>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            sim_umidade = st.slider(
                "Umidade do Solo (%)",
                0.0, 100.0,
                value=30.0,
                help="Porcentagem de umidade do solo"
            )
            
            sim_ph = st.slider(
                "pH do Solo",
                0.0, 14.0,
                value=6.0,
                help="Nível de pH do solo"
            )
        
        with col2:
            sim_fosforo = st.checkbox(
                "Fósforo Presente",
                value=True,
                help="Indica presença de fósforo no solo"
            )
            
            sim_potassio = st.checkbox(
                "Potássio Presente",
                value=True,
                help="Indica presença de potássio no solo"
            )
            
            sim_precipitation = st.number_input(
                "Precipitação Prevista (mm)",
                0.0, 100.0,
                value=0.0,
                help="Quantidade de chuva prevista em milímetros"
            )
    
    # Botão de simulação
    if st.button("🔄 Simular Cenário", key="btn_simulate_v3"):
        with st.spinner("Processando simulação..."):
            # Prepara parâmetros
            simulation_params = {
                'umidade': sim_umidade,
                'ph': sim_ph,
                'fosforo': sim_fosforo,
                'potassio': sim_potassio,
                'precipitation': sim_precipitation
            }
            
            # Executa simulação
            results = simulate_advanced_scenario(simulation_params, df_hist_app_main)
            
            # Exibe resultados
            st.markdown("### 📊 Resultados da Simulação")
            
            # Decisão principal
            decision_color = "#4CAF50" if results['decision'] else "#F44336"
            st.markdown(f"""
                <div style="padding: 1rem; border-radius: 8px; background-color: {decision_color}; color: white; margin: 1rem 0;">
                    <h3 style="margin: 0;">Decisão: {'IRRIGAR' if results['decision'] else 'NÃO IRRIGAR'}</h3>
                    <p style="margin: 0.5rem 0 0 0;">{results['explanation']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Métricas
            col1, col2, col3 = st.columns(3)
            
            col1.metric(
                "Nível de Risco",
                results['risk_level'].upper(),
                delta=None,
                delta_color="off"
            )
            
            col2.metric(
                "Impacto na Eficiência",
                f"{results['efficiency_impact']:+d}%",
                delta=None,
                delta_color="inverse"
            )
            
            col3.metric(
                "Custo Estimado",
                f"R$ {results['cost_impact']:.2f}",
                delta=None,
                delta_color="off"
            )
            
            # Recomendações
            if results['recommendations']:
                st.markdown("### 📋 Recomendações")
                for rec in results['recommendations']:
                    color = "red" if rec['type'] == 'critical' else "orange"
                    st.markdown(f"""
                        <div style="padding: 1rem; border-left: 4px solid {color}; background-color: rgba({255 if color == 'red' else 255}, {0 if color == 'red' else 165}, 0, 0.1); margin: 0.5rem 0;">
                            <p style="margin: 0;"><strong>{rec['message']}</strong></p>
                            <p style="margin: 0.5rem 0 0 0; font-size: 0.9em;">Ação Recomendada: {rec['action']}</p>
                        </div>
                    """, unsafe_allow_html=True)

# --- Sobre ---
with tab_sobre:
    st.header("ℹ️ Sobre este Dashboard")
    st.markdown("""
        Este é um dashboard avançado para monitoramento e análise de sistemas de irrigação, desenvolvido como parte do projeto de PhD em Irrigação Inteligente.
        
        ### Funcionalidades:
        - Visualização de dados históricos de irrigação
        - Integração com dados meteorológicos em tempo real (Meteoblue)
        - Simulação de lógica de decisão para irrigação
        - Alertas proativos baseados em condições de umidade e pH
        - Análise de custos operacionais de irrigação
        - Diagnóstico avançado do sistema com sugestões de melhoria
        
        ### Tecnologias Usadas:
        - **Frontend:** Streamlit, Plotly
        - **Backend:** Python, SQLAlchemy, SQLite
        - **APIs:** Meteoblue, OpenWeatherMap (futuras)
        
        ### Como Usar:
        1. Configure as credenciais da API Meteoblue no código fonte.
        2. Utilize o gerenciador de dados para popular o banco de dados com dados históricos.
        3. Explore as abas do dashboard para visualizar dados, simular cenários e analisar o clima.
        
        ### Contato:
        - **Autor:** Diogo Zequini
        - **E-mail:** diogo.zequini@exemplo.com
        - **GitHub:** [diogozequini](https://github.com/diogozequini)
    """)
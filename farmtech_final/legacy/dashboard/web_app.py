"""web_app.py - Interface Streamlit unificada FarmTech
Refatora o antigo dashboard para UX simplificada em uma única aplicação.
"""
from __future__ import annotations
import os
import datetime as _dt
import importlib
import numpy as np
import pandas as pd
import streamlit as st
import pathlib, sys

# Garante que o pacote raiz esteja no sys.path quando executado diretamente
_pkg_root = pathlib.Path(__file__).resolve().parent.parent
if str(_pkg_root.parent) not in sys.path:
    sys.path.insert(0, str(_pkg_root.parent))

# Auto-refresh (opcional)
try:
    from streamlit_autorefresh import st_autorefresh  # type: ignore
except ImportError:
    st_autorefresh = None

# --- Backend Imports Dinâmicos ---
backend_app = importlib.import_module("farmtech_final.backend.app")
LeituraSensor = getattr(backend_app, "LeituraSensor")
SessionLocal = getattr(backend_app, "SessionLocal")
carregar_dados_para_pandas = getattr(backend_app, "carregar_dados_para_pandas")
executar_forecast_umidade_phd = getattr(backend_app, "executar_forecast_umidade_phd")

# Importa módulos backend (após garantir path)
from farmtech_final.backend.config_manager import get_config
from farmtech_final.backend import services
from typing import Any

# Config global (após import)
config = get_config()

st.set_page_config(page_title="FarmTech PhD Suite", page_icon="💧", layout="wide")

# Auto-refresh intervalo
if st_autorefresh:
    REFRESH_MS = st.sidebar.number_input("Atualizar a cada (seg)", 10, 300, 30, 5) * 1000
    st_autorefresh(interval=REFRESH_MS, key="auto_refresh")

st.sidebar.title("☘️ FarmTech Suite")
page = st.sidebar.radio("Navegação", (
    "Visão Geral",
    "Histórico",
    "Gerenciamento",
    "Previsões",
))


def _format_bool(val: bool) -> str:
    return "✅" if val else "❌"


def pagina_visao_geral():
    st.header("📊 Visão Geral")
    df = carregar_dados_para_pandas()
    if df.empty:
        st.info("Sem dados disponíveis.")
        return
    df_sorted = df.sort_values("timestamp")
    ultima = df_sorted.iloc[-1]
    col1, col2, col3 = st.columns(3)
    col1.metric("Umidade (%)", f"{ultima['umidade']:.1f}")
    col2.metric("pH", f"{ultima['ph_estimado']:.2f}")
    col3.metric("Temp (°C)", f"{ultima['temperatura']:.1f}")

    st.subheader("Últimas Leituras")
    st.dataframe(df_sorted.tail(20).reset_index(drop=True), use_container_width=True)


def pagina_historico():
    st.header("🗄️ Histórico de Leituras")
    df = carregar_dados_para_pandas()
    if df.empty:
        st.info("Nenhum dado encontrado.")
        return
    st.dataframe(df.sort_values("timestamp", ascending=False).reset_index(drop=True), height=600, use_container_width=True)


def pagina_gerenciamento():
    st.header("🛠️ Gerenciamento de Leituras")

    aba_add, aba_update, aba_delete = st.tabs(["Adicionar", "Atualizar", "Deletar"])

    with aba_add:
        st.subheader("➕ Adicionar")
        with st.form("form_add"):
            ts = st.date_input("Data", value=_dt.datetime.now().date())
            hora = st.time_input("Hora", value=_dt.datetime.now().time())
            ts = _dt.datetime.combine(ts, hora)
            umid = st.number_input("Umidade (%)", 0.0, 100.0, 30.0, 0.1)
            ph = st.number_input("pH", 0.0, 14.0, 6.5, 0.1)
            temperatura = st.number_input("Temperatura (°C)", -10.0, 60.0, 25.0, 0.1)
            fosforo = st.checkbox("Fósforo presente (P)")
            potassio = st.checkbox("Potássio presente (K)")
            submitted = st.form_submit_button("Salvar")
        if submitted:
            cfg = config['logica_esp32']
            emergencia = (umid < cfg['UMIDADE_CRITICA_BAIXA']) or (ph < cfg['PH_CRITICO_MINIMO']) or (ph > cfg['PH_CRITICO_MAXIMO'])
            try:
                id_l = services.add_leitura(
                    timestamp=ts,
                    umidade=umid,
                    ph_estimado=ph,
                    fosforo_presente=fosforo,
                    potassio_presente=potassio,
                    temperatura=temperatura,
                    bomba_ligada=False,
                    decisao_logica_esp32="Inserção Manual",
                    emergencia=emergencia,
                )
                st.success(f"Leitura adicionada (ID {id_l})")
            except Exception as e:
                st.error(f"Erro: {e}")

    with aba_update:
        st.subheader("✏️ Atualizar")
        with st.form("form_update"):
            id_upd = st.number_input("ID da leitura", min_value=1, step=1)
            campo = st.selectbox("Campo", options=["umidade", "ph_estimado", "temperatura", "fosforo_presente", "potassio_presente", "bomba_ligada", "decisao_logica_esp32", "emergencia"])
            valor = st.text_input("Novo Valor")
            submitted_u = st.form_submit_button("Atualizar")
        if submitted_u:
            try:
                # Converter tipos básicos
                val_conv: Any
                if campo in {"umidade", "ph_estimado", "temperatura"}:
                    val_conv = float(valor)
                elif campo in {"fosforo_presente", "potassio_presente", "bomba_ligada", "emergencia"}:
                    val_conv = valor.lower() in {"1", "true", "t", "sim", "yes", "y"}
                else:
                    val_conv = valor
                sucesso = services.update_leitura(int(id_upd), {campo: val_conv})
                if sucesso:
                    st.success("Atualizado!")
                else:
                    st.warning("ID não encontrado.")
            except Exception as e:
                st.error(f"Erro: {e}")

    with aba_delete:
        st.subheader("🗑️ Deletar")
        with st.form("form_delete"):
            id_del = st.number_input("ID da leitura para deletar", min_value=1, step=1)
            submitted_d = st.form_submit_button("Deletar")
        if submitted_d:
            try:
                sucesso = services.delete_leitura(int(id_del))
                if sucesso:
                    st.success("Registro deletado!")
                else:
                    st.warning("ID não encontrado.")
            except Exception as e:
                st.error(f"Erro: {e}")


def pagina_previsoes():
    st.header("🔮 Previsões de Umidade (ARIMA)")
    df = carregar_dados_para_pandas()
    console_fake = backend_app.RichConsole(file=open(os.devnull, 'w'))
    fc_cfg = config['forecast_settings']
    umid_crit = config['logica_esp32']['UMIDADE_CRITICA_BAIXA']
    forecast, alerts = executar_forecast_umidade_phd(df, console_fake, fc_cfg, umid_crit)
    if forecast is None:
        st.info("Não foi possível gerar forecast. Verifique se há dados suficientes.")
        return
    st.line_chart(forecast)
    if alerts:
        st.error("\n".join(alerts))


if page == "Visão Geral":
    pagina_visao_geral()
elif page == "Histórico":
    pagina_historico()
elif page == "Gerenciamento":
    pagina_gerenciamento()
elif page == "Previsões":
    pagina_previsoes()

st.sidebar.caption("Build: PhD ✨") 
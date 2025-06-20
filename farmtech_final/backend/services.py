"""services.py
Camada de serviços da FarmTech Suite.
Agrupa funções de orquestração de análises e CRUD de leituras, evitando duplicação
entre CLI e interface web.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional
from . import db_manager, config_manager, ml_predictor
from rich.console import Console

# Importa as dependências diretamente dos módulos corretos
LeituraSensor = db_manager.LeituraSensor

# ---------------------------- CRUD BÁSICO -----------------------------

def add_leitura(**kwargs) -> int:
    """Adiciona leitura e devolve ID gerado."""
    with db_manager.session_scope() as sess:
        leitura = LeituraSensor(**kwargs)
        sess.add(leitura)
        sess.commit()
        sess.refresh(leitura)
        return leitura.id

def update_leitura(leitura_id: int, campos: Dict[str, Any]) -> bool:
    with db_manager.session_scope() as sess:
        leitura = sess.get(LeituraSensor, leitura_id)
        if not leitura:
            return False
        for k, v in campos.items():
            if hasattr(leitura, k):
                setattr(leitura, k, v)
        sess.commit()
        return True

def delete_leitura(leitura_id: int) -> bool:
    with db_manager.session_scope() as sess:
        leitura = sess.get(LeituraSensor, leitura_id)
        if not leitura:
            return False
        sess.delete(leitura)
        sess.commit()
        return True

# --------------------- FUNÇÕES DE ANÁLISE ORQUESTRADA -----------------

def get_full_analysis(df):
    """Executa pipeline completo de análises e devolve dict com resultados."""
    resultados: Dict[str, Any] = {}
    if not df.empty:
        resultados['stats'] = df.describe()
        resultados['corr'] = df.corr(numeric_only=True)
        # Adicione outras análises se necessário
    return resultados


def run_what_if_simulation(umidade: float, ph: float, temperatura: float = 25.0,
                            fosforo: bool = True, potassio: bool = True):
    """Wrapper de simulação de lógica de irrigação (what-if)."""
    cfg = config_manager.get_config()['logica_esp32']
    
    if umidade < cfg['UMIDADE_MINIMA_PARA_IRRIGAR']:
        return True, f"Ligar: Umidade ({umidade}%) abaixo do mínimo ({cfg['UMIDADE_MINIMA_PARA_IRRIGAR']}%)"
        
    if umidade > cfg['UMIDADE_ALTA_PARAR_IRRIGACAO']:
        return False, f"Desligar: Umidade ({umidade}%) acima do ideal ({cfg['UMIDADE_ALTA_PARAR_IRRIGACAO']}%)"

    return False, f"Manter desligada: Umidade ({umidade}%) está dentro da faixa ideal." 
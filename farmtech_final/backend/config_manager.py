"""config_manager.py
Centraliza a leitura de configurações YAML para o FarmTech ERP.
Carrega configurações do arquivo erp_config.yaml na raiz do projeto.
"""
import os
import yaml
from pathlib import Path

def get_config():
    """Retorna objeto de configuração carregado do erp_config.yaml."""
    
    # Encontrar o arquivo de configuração na raiz do projeto
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    config_path = project_root / "erp_config.yaml"
    
    # Configuração padrão caso o arquivo não exista
    default_config = {
        'db_name': 'backend/data/farmtech.db',
        'table_name': 'leituras_sensores_phd_v2',
        'logica_esp32': {
            'UMIDADE_CRITICA_BAIXA': 15.0,
            'UMIDADE_MINIMA_PARA_IRRIGAR': 20.0,
            'UMIDADE_ALTA_PARAR_IRRIGACAO': 60.0,
            'PH_IDEAL_MINIMO': 5.5,
            'PH_IDEAL_MAXIMO': 6.5,
            'PH_CRITICO_MINIMO': 4.5,
            'PH_CRITICO_MAXIMO': 7.5,
        },
        'forecast_settings': {
            'num_leituras_futuras': 6,
            'intervalo_leitura_minutos': 5,
            'alerta_forecast_ativo': True,
            'arima_p': 1,
            'arima_d': 1,
            'arima_q': 1
        },
        'custo_settings': {
            'custo_agua_reais_por_m3': 5.00,
            'vazao_bomba_litros_por_hora': 1000.0,
            'tempo_irrigacao_padrao_minutos': 15.0,
            'custo_energia_kwh': 0.75,
            'potencia_bomba_kw': 0.75
        }
    }
    
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config if config else default_config
        else:
            # Criar arquivo de configuração se não existir
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, default_flow_style=False)
            return default_config
    except Exception as e:
        print(f"Erro ao carregar configuração: {e}")
        return default_config 
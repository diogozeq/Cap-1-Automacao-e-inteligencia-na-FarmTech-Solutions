from backend.app import simular_logica_irrigacao_esp32_py, config
from backend.app import RichConsole
import os

console = RichConsole(file=open(os.devnull, 'w'))
cfg = config['logica_esp32']


def test_emergencia_umidade():
    ligar, motivo = simular_logica_irrigacao_esp32_py(umidade=10.0, ph=6.0, p_presente=True, k_presente=True, console_rich=console, cfg_logica=cfg)
    assert ligar is True
    assert "EMERGENCIA" in motivo


def test_ph_critico():
    ligar, motivo = simular_logica_irrigacao_esp32_py(umidade=40.0, ph=8.0, p_presente=True, k_presente=True, console_rich=console, cfg_logica=cfg)
    assert ligar is False
    assert "pH critico" in motivo


def test_umidade_baixa_com_nutrientes():
    ligar, motivo = simular_logica_irrigacao_esp32_py(umidade=18.0, ph=6.0, p_presente=True, k_presente=True, console_rich=console, cfg_logica=cfg)
    assert ligar is True 
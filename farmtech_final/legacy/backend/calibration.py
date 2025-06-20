"""calibration.py
Funções de calibração para sensores analógicos.
Atualmente fornece conversão LDR→pH usando curva polinomial obtida em bancada.
"""
from __future__ import annotations

from typing import Sequence
import numpy as np
import os

# Coeficientes da curva de calibração pH = a + b*x + c*x^2 + d*x^3
# x = leitura ADC normalizada (0–1). Ajuste esses valores conforme laboratório
DEFAULT_PH_COEFFS: tuple[float, float, float, float] = (
    1.5,    # a (Intercepto - ajustado para subir a curva)
    10.5,   # b (Linear - ajustado)
    -5.0,   # c (Quadrático - ajustado)
    2.5,    # d (Cúbico - ajustado)
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_COEFFS_FILE = os.path.join(BASE_DIR, "calib_coeffs.txt")


def _load_coeffs_from_file(path: str = _COEFFS_FILE):
    """Tenta ler 4 coeficientes (a,b,c,d) de um arquivo texto.
    Retorna tuple ou None.
    """
    if not os.path.exists(path):
        return None
    try:
        line = open(path, "r", encoding="utf-8").readline()
        vals = [float(v) for v in line.replace(",", " ").split() if v]
        if len(vals) == 4:
            return tuple(vals)
    except Exception:
        pass
    return None


def adc_to_ph(raw: int | float, coeffs: Sequence[float] | None = None, adc_max: int = 4095) -> float:
    """Converte valor *raw* do ADC (0–adc_max) para pH usando curva polinomial.

    Parameters
    ----------
    raw: int | float
        Valor lido do ADC.
    coeffs: sequência de 4 coeficientes (a,b,c,d) para o polinômio.
    adc_max: valor máximo que o ADC pode ler (e.g., 4095 para 12-bit).

    Returns
    -------
    float
        Valor de pH calculado, restrito entre 0.0 e 14.0.
    """
    # Garante que leituras fora do range não causem erros
    if raw < 0:
        return 0.0
    if raw > adc_max:
        return 14.0

    if coeffs is None:
        coeffs = _load_coeffs_from_file() or DEFAULT_PH_COEFFS
    if len(coeffs) != 4:
        raise ValueError("São necessários 4 coeficientes (a,b,c,d)")
    a, b, c, d = coeffs
    x = max(0.0, min(float(raw) / adc_max, 1.0))  # normaliza 0–1
    ph = a + b * x + c * x ** 2 + d * x ** 3
    # Limita resultado à faixa 0–14
    return max(0.0, min(ph, 14.0)) 
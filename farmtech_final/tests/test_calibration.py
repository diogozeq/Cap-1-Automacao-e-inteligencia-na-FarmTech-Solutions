import pytest
from backend.calibration import adc_to_ph

def test_adc_to_ph_bounds():
    assert adc_to_ph(-100) == 0.0  # abaixo do mínimo
    assert adc_to_ph(5000) == 14.0  # acima do máximo

def test_adc_to_ph_midpoint():
    ph_mid = adc_to_ph(2047)
    assert 5.0 <= ph_mid <= 9.0  # faixa razoável para sensor 

def test_adc_to_ph_accuracy():
    # Dados de calibração fictícios (adc_norm, ph_real)
    samples = [
        (0, 1.5),
        (1023, 4.0),
        (2047, 6.8),
        (3071, 9.5),
        (4095, 14.0)
    ]
    for adc, ph_real in samples:
        ph_calc = adc_to_ph(adc)
        assert abs(ph_calc - ph_real) <= 0.2 
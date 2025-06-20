import os
from backend.app import treinar_ou_carregar_classificador_phd, MODEL_PATH, carregar_dados_para_pandas, config, RichConsole

console = RichConsole(file=open(os.devnull, 'w'))

def test_model_persistence(tmp_path):
    # Usa banco existente
    df = carregar_dados_para_pandas()
    cfg_ml = config['ml_classifier']
    # Treina / carrega
    model1, acc1, *_ = treinar_ou_carregar_classificador_phd(df, console, cfg_ml)
    assert model1 is not None
    # Garante que arquivo gerado
    assert os.path.exists(MODEL_PATH)
    # Carrega novamente
    model2, acc2, *_ = treinar_ou_carregar_classificador_phd(df, console, cfg_ml)
    assert model2 is not None
    # Deve ser mesma classe
    assert type(model1) == type(model2) 
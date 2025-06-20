import pytest
from backend.db_manager import init_db, add_leitura, get_ultimas_leituras, LeituraSensor
from sqlalchemy.orm import sessionmaker

def test_insert_and_fetch(tmp_path):
    """Testa a inicialização, inserção e busca no banco de dados."""
    # Cria um db temporário para o teste
    db_file = tmp_path / "test.db"
    db_url = f"sqlite:///{db_file}"

    # 1. Inicializa o DB com o caminho temporário
    engine = init_db(db_url)
    assert engine is not None

    # Cria uma sessão para o teste
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = TestingSessionLocal()

    leitura = LeituraSensor(
        umidade=65.5,
        temperatura=28.2,
        ph_estimado=6.8,
        fosforo_presente=True,
        potassio_presente=True,
        bomba_ligada=True,
        decisao_logica_esp32="EMERGENCIA: Umidade Baixa",
        emergencia=True
    )
    
    # 2. Adiciona a leitura
    added = add_leitura(leitura, db_session)
    assert added.id is not None
    assert added.umidade == 65.5

    # 3. Busca a leitura
    leituras = get_ultimas_leituras(db_session, 1)
    assert len(leituras) == 1
    assert leituras[0].ph_estimado == 6.8

    db_session.close() 
from __future__ import annotations
"""db_manager.py
Camada de persistência e acesso ao banco de dados SQLite utilizado pelo
sistema FarmTech. Esse módulo é responsável por:

1. Definir o modelo ORM principal (LeituraSensor).
2. Disponibilizar funções utilitárias de CRUD.
3. Expor um contexto de sessão seguro via context manager.

Ele foi extraído do script monolítico `gerenciador_dados.py` para melhorar a
organização, permitir reuso em outros módulos (ex.: dashboard, testes
unitários) e facilitar a manutenção.
"""

import datetime as _dt
from contextlib import contextmanager
from typing import List, Optional, Iterable

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    Float,
    Boolean,
    DateTime,
    String,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# ---------------------------------------------------------------------------
# Configurações básicas
# ---------------------------------------------------------------------------
import os

# Garantir que o diretório data existe
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_FILENAME: str = os.path.join(DATA_DIR, "farmtech.db")
DATABASE_URL = f"sqlite:///{DB_FILENAME}"

# Permite que o engine seja acessado globalmente após a inicialização
_ENGINE = None
_SessionLocal = None

Base = declarative_base()


# ---------------------------------------------------------------------------
# Modelos ORM
# ---------------------------------------------------------------------------
class LeituraSensor(Base):
    """Tabela com leituras de sensores da fazenda."""

    __tablename__ = "leituras_sensores_phd_v2"

    id: int = Column(Integer, primary_key=True, index=True)
    timestamp: _dt.datetime = Column(
        DateTime, default=_dt.datetime.utcnow, index=True, unique=True, nullable=False
    )
    umidade: float = Column(Float, nullable=False)
    ph_estimado: float = Column(Float, nullable=False)
    fosforo_presente: bool = Column(Boolean, nullable=False)
    potassio_presente: bool = Column(Boolean, nullable=False)
    temperatura: float = Column(Float, nullable=True)
    bomba_ligada: bool = Column(Boolean, nullable=False)
    decisao_logica_esp32: Optional[str] = Column(String, nullable=True)
    emergencia: bool = Column(Boolean, nullable=False)

    # ---------------------------------------------------------------------
    # Métodos utilitários
    # ---------------------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "umidade": self.umidade,
            "ph_estimado": self.ph_estimado,
            "fosforo_presente": self.fosforo_presente,
            "potassio_presente": self.potassio_presente,
            "temperatura": self.temperatura,
            "bomba_ligada": self.bomba_ligada,
            "decisao_logica_esp32": self.decisao_logica_esp32,
            "emergencia": self.emergencia,
        }


# ---------------------------------------------------------------------------
# Funções de controle de sessão
# ---------------------------------------------------------------------------
@contextmanager
def session_scope() -> Iterable[Session]:
    """Context manager para uma sessão do SQLAlchemy com commit/rollback
    automáticos.
    """
    if _SessionLocal is None:
        raise RuntimeError(
            "O banco de dados não foi inicializado. Chame init_db() primeiro."
        )
    session: Session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:  # pragma: no cover
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# CRUD simples
# ---------------------------------------------------------------------------

def init_db(db_url: str | None = None):
    """Inicializa a conexão com o banco e cria as tabelas, se não existirem."""
    global _ENGINE, _SessionLocal

    # Se uma URL for fornecida (tipicamente para testes), use-a.
    # Senão, use a URL global.
    url_to_use = db_url if db_url else DATABASE_URL

    # Usa connect_args para ser compatível com SQLite em ambiente multithread
    _ENGINE = create_engine(url_to_use, connect_args={"check_same_thread": False})
    
    # Inicializa o SessionLocal com o engine configurado
    _SessionLocal = sessionmaker(bind=_ENGINE, autocommit=False, autoflush=False)
    
    # Cria as tabelas que não existem
    Base.metadata.create_all(bind=_ENGINE)
    
    return _ENGINE

def get_engine():
    """Retorna a instância global do engine. Garante que init_db foi chamado."""
    if _ENGINE is None:
        raise RuntimeError(
            "O banco de dados não foi inicializado. Chame init_db() primeiro."
        )
    return _ENGINE

def add_leitura(leitura: LeituraSensor, db_session) -> LeituraSensor:
    """Adiciona um novo registro de leitura ao banco."""
    db_session.add(leitura)
    db_session.commit()
    db_session.refresh(leitura)
    return leitura


def get_ultimas_leituras(db_session, limit: int = 100) -> list[LeituraSensor]:
    """Retorna as `limit` últimas leituras, ordenadas da mais recente."""
    return (
        db_session.query(LeituraSensor)
        .order_by(LeituraSensor.timestamp.desc())
        .limit(limit)
        .all()
    )


def delete_leitura_por_id(leitura_id: int) -> bool:
    """Remove uma leitura pelo ID. Retorna True se algo foi apagado."""
    with session_scope() as s:
        deleted = s.query(LeituraSensor).filter_by(id=leitura_id).delete()
        return bool(deleted)


# ---------------------------------------------------------------------------
# Execução direta (debug)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    init_db()
    print("Tabelas garantidas.") 
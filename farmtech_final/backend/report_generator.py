"""report_generator.py
Geração de relatórios em PDF sobre o estado do sistema.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from rich.console import Console as RichConsole

try:
    from gerenciador_dados import gerar_relatorio_farmtech_pdf_phd as _legacy_pdf
except ImportError:
    _legacy_pdf = None


STYLE = getSampleStyleSheet()["BodyText"]


def gerar_relatorio_pdf(resumo_info: Dict[str, str], destino: str | Path = "relatorio_farmtech.pdf") -> Path:
    """Cria um PDF simples contendo as chaves/valores de *resumo_info*."""

    doc = SimpleDocTemplate(str(destino), pagesize=A4)
    story = []

    for k, v in resumo_info.items():
        story.append(Paragraph(f"<b>{k}:</b> {v}", STYLE))
        story.append(Spacer(1, 12))

    doc.build(story)
    return Path(destino)


def gerar_relatorio_farmtech_pdf_detalhado(df_historico, cache_analises: dict, modelo_ml=None):
    """Envia para a função legado se disponível, garantindo compatibilidade."""
    if _legacy_pdf is None:
        raise RuntimeError("Função PDF detalhada não disponível (módulo gerenciador_dados não encontrado).")

    return _legacy_pdf(
        df_historico,
        cache_analises.get("stats"),
        cache_analises.get("correl"),
        cache_analises.get("forecast"),
        cache_analises.get("alertas_fc"),
        cache_analises.get("ciclos_irr", 0),
        cache_analises.get("custo_total", 0.0),
        modelo_ml,
        cache_analises.get("anomalias"),
        console_rich=RichConsole(),
    ) 
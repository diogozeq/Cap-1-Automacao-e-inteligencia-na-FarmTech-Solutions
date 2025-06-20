#!/usr/bin/env python3
"""
run_erp.py
Script para iniciar o FarmTech ERP
Launcher principal para o sistema unificado
"""

import os
import sys
import subprocess
from pathlib import Path

# Adicionar o diretório do projeto ao Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Função principal para iniciar o ERP"""
    print("🌱 Iniciando FarmTech ERP...")
    print("=" * 50)
    
    # Verificar se o Streamlit está instalado
    try:
        import streamlit
        print("✅ Streamlit encontrado")
    except ImportError:
        print("❌ Streamlit não encontrado. Instalando...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])
        import streamlit
    
    # Verificar dependências do backend
    try:
        from backend import db_manager, services
        print("✅ Módulos do backend carregados")
    except ImportError as e:
        print(f"❌ Erro ao carregar módulos do backend: {e}")
        print("Verifique se você está no diretório correto")
        return
    
    # Inicializar banco de dados
    try:
        db_manager.init_db()
        print("✅ Banco de dados inicializado")
    except Exception as e:
        print(f"❌ Erro ao inicializar banco de dados: {e}")
        return
    
    # Caminho para o dashboard principal
    dashboard_path = project_root / "dashboard" / "main_erp.py"
    
    if not dashboard_path.exists():
        print(f"❌ Dashboard não encontrado: {dashboard_path}")
        return
    
    print(f"✅ Iniciando dashboard: {dashboard_path}")
    print("\n🚀 O FarmTech ERP será aberto no seu navegador!")
    print("💡 Pressione Ctrl+C para parar o servidor")
    print("=" * 50)
    
    # Executar o Streamlit
    try:
        # Usar python3 explicitamente no WSL
        python_cmd = "python3" if sys.executable == "/usr/bin/python3" else sys.executable
        subprocess.run([
            python_cmd, "-m", "streamlit", "run", 
            str(dashboard_path),
            "--server.address", "localhost",
            "--server.port", "8501",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 FarmTech ERP encerrado. Até logo!")
    except Exception as e:
        print(f"❌ Erro ao executar o dashboard: {e}")

if __name__ == "__main__":
    main()
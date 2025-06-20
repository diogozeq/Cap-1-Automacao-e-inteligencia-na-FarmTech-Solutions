#!/usr/bin/env python3
"""
Launcher para o FarmTech ERP
Executa o sistema usando streamlit run para abrir automaticamente no navegador
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    # Caminho para o arquivo main_erp.py
    erp_file = Path(__file__).parent / "farmtech_final" / "dashboard" / "main_erp.py"
    
    if not erp_file.exists():
        print(f"❌ Arquivo não encontrado: {erp_file}")
        return
    
    print("🚀 Iniciando FarmTech ERP...")
    print("🌐 O navegador será aberto automaticamente...")
    
    # Comando para executar via streamlit
    cmd = [sys.executable, "-m", "streamlit", "run", str(erp_file), "--browser.serverAddress=localhost"]
    
    try:
        # Executa o streamlit
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar: {e}")
    except KeyboardInterrupt:
        print("\n👋 FarmTech ERP encerrado pelo usuário")

if __name__ == "__main__":
    main() 
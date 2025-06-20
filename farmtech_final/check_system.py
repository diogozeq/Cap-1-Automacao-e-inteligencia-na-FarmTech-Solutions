#!/usr/bin/env python3
"""
check_system.py
Script para verificar se o sistema FarmTech ERP está pronto para execução
"""

import sys
import os
from pathlib import Path

def check_python():
    """Verifica a versão do Python"""
    print("🐍 Verificando Python...")
    print(f"   Versão: {sys.version}")
    print(f"   Executável: {sys.executable}")
    
    if sys.version_info < (3, 8):
        print("   ❌ Python 3.8 ou superior é necessário")
        return False
    else:
        print("   ✅ Versão do Python OK")
        return True

def check_dependencies():
    """Verifica se as dependências estão instaladas"""
    print("\n📦 Verificando dependências...")
    
    dependencies = [
        'streamlit',
        'pandas', 
        'numpy',
        'plotly',
        'sqlalchemy'
    ]
    
    missing = []
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"   ✅ {dep}")
        except ImportError:
            print(f"   ❌ {dep} - NÃO INSTALADO")
            missing.append(dep)
    
    if missing:
        print(f"\n❌ Dependências ausentes: {', '.join(missing)}")
        print("💡 Para instalar: pip install " + " ".join(missing))
        return False
    else:
        print("\n✅ Todas as dependências estão instaladas")
        return True

def check_project_structure():
    """Verifica a estrutura do projeto"""
    print("\n📁 Verificando estrutura do projeto...")
    
    required_files = [
        'backend/db_manager.py',
        'backend/services.py',
        'backend/ml_predictor.py',
        'backend/wokwi_listener.py',
        'dashboard/main_erp.py',
        'run_erp.py'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - NÃO ENCONTRADO")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ Arquivos ausentes: {', '.join(missing_files)}")
        return False
    else:
        print("\n✅ Estrutura do projeto OK")
        return True

def check_backend_modules():
    """Verifica se os módulos do backend funcionam"""
    print("\n🔧 Verificando módulos do backend...")
    
    try:
        sys.path.insert(0, 'backend')
        
        # Testar imports
        from backend import db_manager, services
        print("   ✅ Imports do backend OK")
        
        # Testar inicialização do banco
        db_manager.init_db()
        print("   ✅ Banco de dados inicializado")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro nos módulos do backend: {e}")
        return False

def main():
    """Função principal"""
    print("🌱 FarmTech ERP - Verificação do Sistema")
    print("=" * 50)
    
    checks = [
        check_python(),
        check_dependencies(),
        check_project_structure(),
        check_backend_modules()
    ]
    
    print("\n" + "=" * 50)
    
    if all(checks):
        print("🎉 SISTEMA PRONTO PARA EXECUÇÃO!")
        print("💡 Execute: python run_erp.py")
    else:
        print("❌ SISTEMA NÃO ESTÁ PRONTO")
        print("💡 Corrija os problemas acima antes de executar")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
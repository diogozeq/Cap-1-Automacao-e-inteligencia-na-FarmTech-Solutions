#!/usr/bin/env python3
"""
setup_erp.py
Script de configuração inicial do FarmTech ERP
Instala dependências, cria banco de dados e verifica sistema
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header(text):
    """Imprime cabeçalho formatado"""
    print("\n" + "=" * 60)
    print(f"🌱 {text}")
    print("=" * 60)

def print_step(step, text):
    """Imprime passo da configuração"""
    print(f"\n[{step}] {text}")

def run_command(cmd, description):
    """Executa comando e trata erros"""
    print(f"   Executando: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ {description} - OK")
            return True
        else:
            print(f"   ❌ {description} - ERRO")
            print(f"   Saída: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ {description} - EXCEÇÃO: {e}")
        return False

def check_python():
    """Verifica versão do Python"""
    print_step(1, "Verificando Python")
    print(f"   Versão: {sys.version}")
    
    if sys.version_info < (3, 8):
        print("   ❌ Python 3.8+ é necessário")
        return False
    
    print("   ✅ Versão do Python OK")
    return True

def install_dependencies():
    """Instala dependências"""
    print_step(2, "Instalando dependências")
    
    # Verificar se pip está disponível
    pip_cmd = "pip3" if sys.executable.endswith("python3") else "pip"
    
    try:
        subprocess.run([pip_cmd, "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("   ❌ pip não encontrado")
        print("   💡 Instale pip primeiro: sudo apt install python3-pip")
        return False
    
    # Instalar dependências
    requirements_file = Path("requirements.txt")
    if requirements_file.exists():
        return run_command(
            [pip_cmd, "install", "-r", "requirements.txt", "--user"],
            "Instalação de dependências"
        )
    else:
        # Instalar dependências básicas manualmente
        basic_deps = [
            "streamlit>=1.33.0",
            "pandas>=2.0.0", 
            "numpy>=1.24.0",
            "sqlalchemy>=2.0.0",
            "plotly>=5.0.0",
            "pyyaml>=6.0.0",
            "scikit-learn>=1.4.0",
            "requests>=2.31.0"
        ]
        
        success = True
        for dep in basic_deps:
            if not run_command([pip_cmd, "install", dep, "--user"], f"Instalação {dep}"):
                success = False
        
        return success

def setup_directories():
    """Cria diretórios necessários"""
    print_step(3, "Criando diretórios")
    
    directories = [
        "backend/data",
        "logs",
        "reports"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"   ✅ Diretório: {directory}")
    
    return True

def initialize_database():
    """Inicializa banco de dados"""
    print_step(4, "Inicializando banco de dados")
    
    try:
        # Adicionar backend ao path
        sys.path.insert(0, "backend")
        
        from backend import db_manager
        db_manager.init_db()
        
        print("   ✅ Banco de dados inicializado")
        return True
        
    except Exception as e:
        print(f"   ❌ Erro ao inicializar banco: {e}")
        return False

def populate_sample_data():
    """Popula banco com dados de exemplo"""
    print_step(5, "Adicionando dados de exemplo")
    
    try:
        from backend import initial_data
        
        # Verificar se já existem dados
        from backend import db_manager
        with db_manager.session_scope() as session:
            existing_count = session.query(db_manager.LeituraSensor).count()
            
        if existing_count == 0:
            initial_data.main()
            print("   ✅ Dados de exemplo adicionados")
        else:
            print(f"   ℹ️  Banco já contém {existing_count} registros")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro ao popular dados: {e}")
        return False

def verify_system():
    """Verifica se o sistema está funcionando"""
    print_step(6, "Verificando sistema")
    
    try:
        # Testar imports principais
        from backend import services, db_manager
        print("   ✅ Módulos backend OK")
        
        # Testar Streamlit
        import streamlit
        print("   ✅ Streamlit OK")
        
        # Testar banco de dados
        with db_manager.session_scope() as session:
            count = session.query(db_manager.LeituraSensor).count()
            print(f"   ✅ Banco de dados OK ({count} registros)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro na verificação: {e}")
        return False

def main():
    """Função principal"""
    print_header("FarmTech ERP - Configuração Inicial")
    
    # Verificar se estamos no diretório correto
    if not Path("run_erp.py").exists():
        print("❌ Execute este script a partir do diretório farmtech_final/")
        sys.exit(1)
    
    steps = [
        check_python,
        install_dependencies,
        setup_directories,
        initialize_database,
        populate_sample_data,
        verify_system
    ]
    
    results = []
    for step_func in steps:
        try:
            result = step_func()
            results.append(result)
        except KeyboardInterrupt:
            print("\n\n❌ Setup interrompido pelo usuário")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Erro inesperado: {e}")
            results.append(False)
    
    # Relatório final
    print_header("Relatório Final")
    
    if all(results):
        print("🎉 CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!")
        print("\n💡 Para executar o FarmTech ERP:")
        print("   python3 run_erp.py")
        print("\n💡 Para verificar o sistema:")
        print("   python3 check_system.py")
    else:
        print("❌ CONFIGURAÇÃO INCOMPLETA")
        failed_steps = [i+1 for i, result in enumerate(results) if not result]
        print(f"   Passos com falha: {failed_steps}")
        print("   Corrija os erros e execute novamente")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
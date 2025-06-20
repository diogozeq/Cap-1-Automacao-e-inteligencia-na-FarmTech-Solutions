# 🌱 FarmTech ERP - Sistema Simplificado

Sistema unificado de gerenciamento de irrigação inteligente em um único arquivo.

## 🚀 Como Executar

### Opção 1: Executar com Batch (Windows)
```
Clique duas vezes no arquivo: RUN_APP.bat
```

### Opção 2: Executar Manual
```bash
# Instalar dependências
pip install -r requirements.txt

# Executar aplicação
streamlit run app.py
```

## 📁 Estrutura Simplificada

```
├── app.py              # Aplicação principal (ÚNICO arquivo necessário)
├── requirements.txt    # Dependências
├── RUN_APP.bat        # Script para executar no Windows
├── README.md          # Este arquivo
└── farmtech_data.db   # Banco de dados (criado automaticamente)
```

## 🔧 Funcionalidades

- **🏠 Painel de Controle**: Dashboard com métricas em tempo real
- **📊 Análise Histórica**: Análise estatística dos dados
- **⚙️ Gerenciamento de Dados**: CRUD completo (Create, Read, Update, Delete)
- **🧪 Simulação**: Gerador de dados simulados e simulador What-If
- **🤖 Inteligência Artificial**: Análise preditiva e forecast

## 💡 Principais Melhorias

✅ **UM ÚNICO ARQUIVO** - Toda funcionalidade em `app.py`
✅ **SEM DEPENDÊNCIAS COMPLEXAS** - Apenas SQLite (nativo do Python)
✅ **FÁCIL DE EXECUTAR** - Apenas `streamlit run app.py`
✅ **INTERFACE LIMPA** - Design moderno com CSS customizado
✅ **FUNCIONALIDADE COMPLETA** - Todos os recursos do sistema original

## 🛠️ Tecnologias

- **Streamlit**: Interface web
- **SQLite**: Banco de dados
- **Pandas**: Manipulação de dados
- **Plotly**: Gráficos interativos
- **NumPy**: Cálculos científicos

## 📝 Observações

- O banco de dados `farmtech_data.db` é criado automaticamente
- Use o gerador de dados simulados para popular o sistema
- Todas as configurações estão no próprio código (variável CONFIG)
# Arquivos Legacy - FarmTech ERP

Com a implementação do FarmTech ERP unificado, alguns arquivos se tornaram obsoletos ou redundantes. Este documento lista os arquivos que podem ser removidos ou arquivados após a confirmação de que o novo sistema está funcionando perfeitamente.

## 📁 Arquivos que podem ser removidos/arquivados:

### Dashboard Legacy
- `dashboard/dashboard.py` - Dashboard original substituído pelo ERP
- `dashboard/web_app.py` - Protótipo de UI substituído pelo ERP

### CLI Legacy  
- `backend/app.py` - CLI principal substituída pelo ERP (manter apenas para debug/desenvolvimento)

## 📁 Arquivos mantidos mas com uso modificado:

### Backend Core (MANTIDOS)
- `backend/services.py` - Usado pelo ERP
- `backend/db_manager.py` - Usado pelo ERP  
- `backend/ml_predictor.py` - Usado pelo ERP
- `backend/data_analysis.py` - Usado pelo ERP
- `backend/config_manager.py` - Usado pelo ERP
- `backend/wokwi_listener.py` - Usado pelo ERP

### Novos Arquivos do ERP
- `dashboard/main_erp.py` - **NOVO: Interface principal unificada**
- `run_erp.py` - **NOVO: Launcher simplificado**
- `check_system.py` - **NOVO: Verificação do sistema**

## 🔄 Migração recomendada:

1. **Teste completo do ERP** - Verifique todas as funcionalidades
2. **Backup dos arquivos legacy** - Mova para uma pasta `legacy/`
3. **Atualização da documentação** - Foque no ERP como interface principal
4. **Simplificação do CLI** - `backend/app.py` pode ser mantido apenas para desenvolvimento

## 📋 Comandos para limpeza (EXECUTE APENAS APÓS TESTES COMPLETOS):

```bash
# Criar pasta de backup
mkdir legacy

# Mover arquivos obsoletos
mv dashboard/dashboard.py legacy/
mv dashboard/web_app.py legacy/

# Opcional: simplificar app.py para desenvolvedores apenas
# mv backend/app.py legacy/app_cli.py
```

## ⚠️ ATENÇÃO:

**NÃO execute a limpeza antes de:**
- Testar completamente o FarmTech ERP
- Verificar que todas as funcionalidades estão funcionando
- Confirmar que não há dependências ocultas nos arquivos legacy
- Fazer backup completo do projeto

---

*Esta limpeza é recomendada apenas após validação completa do sistema ERP.*
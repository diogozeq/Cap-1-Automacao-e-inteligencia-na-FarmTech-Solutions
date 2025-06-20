@echo off
echo 🌱 Iniciando FarmTech ERP...
echo 🌐 O navegador sera aberto automaticamente...
echo.

cd /d "%~dp0"
streamlit run "farmtech_final\dashboard\main_erp.py" --browser.serverAddress=localhost --server.port=8501

pause 
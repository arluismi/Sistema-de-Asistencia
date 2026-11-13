@echo off
rem Atajo para Windows: ejecuta configurar-entorno.ps1 sin cambiar la politica de
rem ejecucion de la sesion. Los argumentos recibidos se pasan al script de PowerShell.
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0configurar-entorno.ps1" %*
endlocal
exit /b %ERRORLEVEL%

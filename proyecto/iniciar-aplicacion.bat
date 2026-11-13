@echo off
rem Atajo para Windows: inicia backend y frontend y abre el navegador.
rem Los argumentos recibidos se pasan al script de PowerShell.
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0iniciar-aplicacion.ps1" %*
endlocal
exit /b %ERRORLEVEL%

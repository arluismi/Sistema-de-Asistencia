@echo off
rem Atajo para Windows: carga datos de prueba con volumen en la base de datos.
rem Los argumentos recibidos se pasan al script de PowerShell.
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0cargar-datos-prueba.ps1" %*
endlocal
exit /b %ERRORLEVEL%

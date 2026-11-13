<#
.SYNOPSIS
    Carga datos de prueba con volumen en la base de datos del proyecto.

.DESCRIPTION
    Ejecuta el comando `generar-datos-prueba`, que crea cursos, docentes,
    materias, matrículas, bloques horarios, asistencias estudiantiles y firmas
    docentes para recorrer la aplicación con datos representativos.

    Si el entorno virtual no existe, se crea antes de continuar. La carga es
    idempotente: si ya se ejecutó sobre la misma base, no duplica registros.

    Al terminar, la consola queda abierta hasta presionar Enter para poder leer
    el resumen y las credenciales generadas.

.PARAMETER SinPausa
    Cierra la consola al terminar sin esperar a que se presione Enter.

.EXAMPLE
    .\scripts\cargar-datos-prueba.ps1
#>
[CmdletBinding()]
param(
    [switch]$SinPausa
)

$ErrorActionPreference = 'Stop'

# El script vive en `scripts/`; la raíz del proyecto es la carpeta superior.
$carpetaScripts = Split-Path -Parent $MyInvocation.MyCommand.Path
$raizProyecto = Split-Path -Parent $carpetaScripts
Set-Location -LiteralPath $raizProyecto

$rutaPython = Join-Path $raizProyecto '.venv\Scripts\python.exe'
$rutaScriptEntorno = Join-Path $carpetaScripts 'configurar-entorno.ps1'

function Escribir-Paso {
    param([string]$Mensaje)

    Write-Host ''
    Write-Host "==> $Mensaje" -ForegroundColor Cyan
}

$codigoSalida = 0
try {
    if (-not (Test-Path -LiteralPath $rutaPython)) {
        if (-not (Test-Path -LiteralPath $rutaScriptEntorno)) {
            throw "No existe el entorno virtual ni '$rutaScriptEntorno'. Creá el entorno manualmente."
        }
        Escribir-Paso 'No existe el entorno virtual; se ejecuta configurar-entorno.ps1.'
        & $rutaScriptEntorno
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $rutaPython)) {
            throw 'No se pudo preparar el entorno virtual.'
        }
    }

    Escribir-Paso 'Generando datos de prueba con volumen.'
    & $rutaPython run.py generar-datos-prueba
    if ($LASTEXITCODE -ne 0) {
        throw "Falló la generación de datos de prueba (código de salida $LASTEXITCODE)."
    }

    Write-Host ''
    Write-Host 'Credenciales de prueba:'
    Write-Host '  Docente: docente.prueba.1 / Docente123!'
    Write-Host '  Alumno:  alumno.prueba.1 / Alumno123!'
    Write-Host 'La carga no se repite: si ya se generó, el comando no duplica datos.' -ForegroundColor DarkGray
}
catch {
    $codigoSalida = 1
    Write-Host ''
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
}

if (-not $SinPausa) {
    Write-Host ''
    Read-Host 'Presioná Enter para cerrar esta ventana' | Out-Null
}

exit $codigoSalida

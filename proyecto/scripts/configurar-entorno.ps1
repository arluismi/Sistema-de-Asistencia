<#
.SYNOPSIS
    Prepara el entorno virtual de Python del proyecto.

.DESCRIPTION
    Crea el entorno virtual `.venv` si todavía no existe e instala las dependencias
    declaradas en `requirements.txt`. Si el entorno ya existe y `requirements.txt`
    no cambió desde la última instalación, no vuelve a instalar nada.

.PARAMETER EjecutablePython
    Ejecutable usado para crear el entorno virtual (por ejemplo `py` o una ruta a
    `python.exe`). Si se omite, se busca `py` y luego `python`.

.PARAMETER ForzarInstalacion
    Reinstala las dependencias aunque `requirements.txt` no haya cambiado.

.EXAMPLE
    .\scripts\configurar-entorno.ps1

.EXAMPLE
    .\scripts\configurar-entorno.ps1 -ForzarInstalacion
#>
[CmdletBinding()]
param(
    [string]$EjecutablePython = '',

    [switch]$ForzarInstalacion
)

$ErrorActionPreference = 'Stop'

# El script vive en `scripts/`; la raíz del proyecto es la carpeta superior.
$carpetaScripts = Split-Path -Parent $MyInvocation.MyCommand.Path
$raizProyecto = Split-Path -Parent $carpetaScripts
Set-Location -LiteralPath $raizProyecto

$rutaEntorno = Join-Path $raizProyecto '.venv'
$rutaPython = Join-Path $rutaEntorno 'Scripts\python.exe'
$rutaRequirements = Join-Path $raizProyecto 'requirements.txt'
# Sello dentro de `.venv` con el hash de requirements.txt ya instalado.
$rutaSelloDependencias = Join-Path $rutaEntorno '.dependencias-instaladas'

function Escribir-Paso {
    param([string]$Mensaje)

    Write-Host ''
    Write-Host "==> $Mensaje" -ForegroundColor Cyan
}

function Obtener-EjecutablePython {
    if ($EjecutablePython) {
        if (Get-Command $EjecutablePython -ErrorAction SilentlyContinue) {
            return $EjecutablePython
        }
        throw "No se encontró el ejecutable de Python indicado: $EjecutablePython"
    }

    if (Get-Command py -ErrorAction SilentlyContinue) {
        return 'py'
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return 'python'
    }

    throw 'No se encontró Python. Instalá Python 3.11 o superior y volvé a ejecutar el script.'
}

function New-EntornoVirtual {
    $ejecutable = Obtener-EjecutablePython

    Escribir-Paso "No existe '$rutaEntorno'; se crea el entorno virtual con '$ejecutable'."

    # `-m venv` crea la carpeta del entorno con su propio intérprete y pip.
    if ($ejecutable -eq 'py') {
        & py -3 -m venv $rutaEntorno
    }
    else {
        & $ejecutable -m venv $rutaEntorno
    }

    if ($LASTEXITCODE -ne 0) {
        throw "Falló la creación del entorno virtual (código de salida $LASTEXITCODE)."
    }
}

function Comprobar-VersionPython {
    $textoVersion = & $rutaPython -c "import sys; print('%d.%d' % sys.version_info[:2])"
    if ($LASTEXITCODE -ne 0) {
        throw 'No se pudo determinar la versión de Python del entorno virtual.'
    }

    $version = [version]$textoVersion.Trim()
    if ($version -lt [version]'3.11') {
        throw "El entorno virtual usa Python $version, pero el proyecto requiere 3.11 o superior."
    }

    return $version
}

function Install-Dependencias {
    param([switch]$Obligatorio)

    $hashActual = (Get-FileHash -LiteralPath $rutaRequirements -Algorithm SHA256).Hash
    $hashAnterior = ''
    if (Test-Path -LiteralPath $rutaSelloDependencias) {
        $hashAnterior = (Get-Content -LiteralPath $rutaSelloDependencias -Raw).Trim()
    }

    if (-not $Obligatorio -and -not $ForzarInstalacion -and $hashAnterior -eq $hashActual) {
        Write-Host 'Las dependencias ya están instaladas y requirements.txt no cambió.' -ForegroundColor DarkGray
        return
    }

    Escribir-Paso 'Actualizando pip dentro del entorno virtual.'
    & $rutaPython -m pip install --upgrade pip --disable-pip-version-check
    if ($LASTEXITCODE -ne 0) {
        throw "Falló la actualización de pip (código de salida $LASTEXITCODE)."
    }

    Escribir-Paso "Instalando dependencias desde '$rutaRequirements'."
    & $rutaPython -m pip install -r $rutaRequirements --disable-pip-version-check
    if ($LASTEXITCODE -ne 0) {
        throw "Falló la instalación de dependencias (código de salida $LASTEXITCODE)."
    }

    Set-Content -LiteralPath $rutaSelloDependencias -Value $hashActual -Encoding ASCII
}

if (-not (Test-Path -LiteralPath $rutaRequirements)) {
    throw "No se encontró requirements.txt en '$raizProyecto'."
}

$seCreoEntorno = $false
if (-not (Test-Path -LiteralPath $rutaPython)) {
    New-EntornoVirtual
    $seCreoEntorno = $true
}
else {
    Escribir-Paso "Se reutiliza el entorno virtual existente en '$rutaEntorno'."
}

$versionPython = Comprobar-VersionPython
Write-Host "Python $versionPython detectado en el entorno virtual." -ForegroundColor DarkGray

Install-Dependencias -Obligatorio:$seCreoEntorno

Escribir-Paso 'Entorno listo.'
Write-Host "Intérprete del proyecto: $rutaPython"
Write-Host 'Siguientes pasos opcionales:'
Write-Host '  .\.venv\Scripts\python.exe run.py inicializar-base-de-datos'
Write-Host '  .\.venv\Scripts\python.exe run.py sembrar-datos-demostracion'

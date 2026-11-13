<#
.SYNOPSIS
    Inicia el backend y el frontend del proyecto y abre el navegador.

.DESCRIPTION
    Levanta el servidor de desarrollo de Flask (puerto 5000) y el servidor
    estático del frontend (puerto 5173), espera a que ambos respondan y abre
    `http://localhost:5173` en el navegador predeterminado. Al presionar
    Ctrl+C se detienen los dos servidores iniciados por este script.

    Si el entorno virtual no existe, se crea antes de continuar. Si la base de
    datos SQLite todavía no existe, se inicializa y se cargan los datos de
    demostración.

.PARAMETER SinNavegador
    Inicia los servidores pero no abre el navegador.

.PARAMETER SinDatosDemostracion
    Sólo crea las tablas cuando la base de datos no existe; no carga los datos
    de demostración.

.EXAMPLE
    .\iniciar-aplicacion.ps1

.EXAMPLE
    .\iniciar-aplicacion.ps1 -SinNavegador
#>
[CmdletBinding()]
param(
    [switch]$SinNavegador,

    [switch]$SinDatosDemostracion
)

$ErrorActionPreference = 'Stop'

$raizProyecto = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $raizProyecto

$puertoBackend = 5000
$puertoFrontend = 5173
$urlFrontend = "http://localhost:$puertoFrontend"

$rutaPython = Join-Path $raizProyecto '.venv\Scripts\python.exe'
$rutaScriptEntorno = Join-Path $raizProyecto 'configurar-entorno.ps1'

$script:procesosIniciados = @()

function Escribir-Paso {
    param([string]$Mensaje)

    Write-Host ''
    Write-Host "==> $Mensaje" -ForegroundColor Cyan
}

function Test-PuertoOcupado {
    param([int]$Puerto)

    $cliente = New-Object System.Net.Sockets.TcpClient
    try {
        # `ConnectAsync` evita bloquearse cuando no hay nadie escuchando.
        $conexion = $cliente.ConnectAsync('127.0.0.1', $Puerto)
        return $conexion.Wait(300) -and $cliente.Connected
    }
    catch {
        return $false
    }
    finally {
        $cliente.Close()
    }
}

function Wait-PuertoDisponible {
    param(
        [int]$Puerto,
        [string]$Descripcion,
        [System.Diagnostics.Process]$Proceso,
        [int]$SegundosMaximos = 40
    )

    $limite = (Get-Date).AddSeconds($SegundosMaximos)
    while ((Get-Date) -lt $limite) {
        if (Test-PuertoOcupado -Puerto $Puerto) {
            return
        }
        if ($Proceso -and $Proceso.HasExited) {
            throw "El $Descripcion terminó antes de responder en el puerto $Puerto."
        }
        Start-Sleep -Milliseconds 300
    }

    throw "El $Descripcion no respondió en el puerto $Puerto después de $SegundosMaximos segundos."
}

function Get-RutaBaseDeDatosSqlite {
    # Se consulta la configuración real de la aplicación para respetar `.env`.
    $urlBaseDatos = & $rutaPython -c "from configuracion import ConfiguracionBase as c; print(c.URL_BASE_DATOS)"
    if ($LASTEXITCODE -ne 0) {
        throw 'No se pudo leer la configuración de la base de datos.'
    }

    $urlBaseDatos = $urlBaseDatos.Trim()
    $prefijo = 'sqlite:///'
    if (-not $urlBaseDatos.StartsWith($prefijo)) {
        # Otro motor (por ejemplo PostgreSQL): la base no se administra localmente.
        return $null
    }

    $ruta = $urlBaseDatos.Substring($prefijo.Length)
    if ($ruta -match '^[A-Za-z]:/') {
        return $ruta
    }
    return (Join-Path $raizProyecto $ruta)
}

function Start-Servidor {
    param(
        [string]$Descripcion,
        [string[]]$Argumentos
    )

    # `Start-Process` lanza el servidor en segundo plano dentro de la misma
    # consola, para que sus registros queden visibles y Ctrl+C lo alcance.
    $proceso = Start-Process -FilePath $rutaPython -ArgumentList $Argumentos `
        -WorkingDirectory $raizProyecto -NoNewWindow -PassThru
    $script:procesosIniciados += $proceso
    Write-Host "  $Descripcion iniciado (PID $($proceso.Id))." -ForegroundColor DarkGray
    return $proceso
}

function Stop-ProcesosIniciados {
    foreach ($proceso in $script:procesosIniciados) {
        if ($proceso -and -not $proceso.HasExited) {
            # `taskkill /T` finaliza también el proceso hijo que crea el
            # recargador automático de Flask en modo depuración.
            & taskkill /PID $proceso.Id /T /F 2>$null | Out-Null
        }
    }
}

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

$rutaBaseDatos = Get-RutaBaseDeDatosSqlite
if ($rutaBaseDatos -and -not (Test-Path -LiteralPath $rutaBaseDatos)) {
    Escribir-Paso 'La base de datos no existe; se crean las tablas.'
    & $rutaPython run.py inicializar-base-de-datos
    if ($LASTEXITCODE -ne 0) {
        throw "Falló la inicialización de la base de datos (código de salida $LASTEXITCODE)."
    }

    if (-not $SinDatosDemostracion) {
        Escribir-Paso 'Se cargan los datos de demostración.'
        & $rutaPython run.py sembrar-datos-demostracion
        if ($LASTEXITCODE -ne 0) {
            throw "Falló la carga de datos de demostración (código de salida $LASTEXITCODE)."
        }
    }
}

try {
    Escribir-Paso "Iniciando backend en el puerto $puertoBackend."
    if (Test-PuertoOcupado -Puerto $puertoBackend) {
        Write-Host "  El puerto $puertoBackend ya está en uso; se reutiliza el servicio existente." -ForegroundColor Yellow
        $procesoBackend = $null
    }
    else {
        $procesoBackend = Start-Servidor -Descripcion 'Backend' -Argumentos @('run.py')
    }

    Escribir-Paso "Iniciando frontend en el puerto $puertoFrontend."
    if (Test-PuertoOcupado -Puerto $puertoFrontend) {
        Write-Host "  El puerto $puertoFrontend ya está en uso; se reutiliza el servicio existente." -ForegroundColor Yellow
        $procesoFrontend = $null
    }
    else {
        $procesoFrontend = Start-Servidor -Descripcion 'Frontend' -Argumentos @(
            '-m', 'http.server', $puertoFrontend, '--bind', '127.0.0.1', '--directory', 'frontend'
        )
    }

    Wait-PuertoDisponible -Puerto $puertoBackend -Descripcion 'backend' -Proceso $procesoBackend
    Wait-PuertoDisponible -Puerto $puertoFrontend -Descripcion 'frontend' -Proceso $procesoFrontend

    Escribir-Paso 'Aplicación disponible.'
    Write-Host "  Frontend: $urlFrontend"
    Write-Host "  API:      http://localhost:$puertoBackend/api/v1"
    Write-Host '  Credenciales de demostración: ver README.md'

    if (-not $SinNavegador) {
        # `Start-Process` sobre una URL abre el navegador predeterminado.
        Start-Process $urlFrontend
        Write-Host '  Navegador abierto.' -ForegroundColor DarkGray
    }

    if ($script:procesosIniciados.Count -eq 0) {
        Write-Host ''
        Write-Host 'Ambos servidores ya estaban en ejecución; no hay nada que detener.' -ForegroundColor DarkGray
        return
    }

    Write-Host ''
    Write-Host 'Presioná Ctrl+C para detener los servidores iniciados por este script.' -ForegroundColor Yellow

    while ($true) {
        Start-Sleep -Seconds 1
        foreach ($proceso in $script:procesosIniciados) {
            if ($proceso.HasExited) {
                throw "El proceso con PID $($proceso.Id) terminó inesperadamente."
            }
        }
    }
}
finally {
    Stop-ProcesosIniciados
}

<#
.SYNOPSIS
    Inicia el backend y el frontend del proyecto y abre el navegador.

.DESCRIPTION
    Levanta el servidor de desarrollo de Flask (puerto 5000) y el servidor
    estático del frontend (puerto 5173), espera a que ambos respondan y abre
    `http://localhost:5173` en el navegador predeterminado.

    También muestra la dirección de la red local (por ejemplo
    `http://192.168.0.10:5173`) para abrir la aplicación desde otros
    dispositivos conectados a la misma red. El frontend escucha en todas las
    interfaces y toma la dirección del backend del mismo host desde el que se
    abre la página.

    Al presionar una tecla (o Ctrl+C) se detienen los servidores iniciados por
    este script y la consola queda abierta hasta presionar Enter, para poder
    leer los mensajes.

    Si el entorno virtual no existe, se crea antes de continuar. Si la base de
    datos SQLite todavía no existe, se inicializa y se cargan los datos de
    demostración.

.PARAMETER SinNavegador
    Inicia los servidores pero no abre el navegador.

.PARAMETER SinDatosDemostracion
    Sólo crea las tablas cuando la base de datos no existe; no carga los datos
    de demostración.

.PARAMETER SinPausa
    Cierra la consola al terminar sin esperar a que se presione Enter.

.EXAMPLE
    .\scripts\iniciar-aplicacion.ps1

.EXAMPLE
    .\scripts\iniciar-aplicacion.ps1 -SinNavegador
#>
[CmdletBinding()]
param(
    [switch]$SinNavegador,

    [switch]$SinDatosDemostracion,

    [switch]$SinPausa
)

$ErrorActionPreference = 'Stop'

# El script vive en `scripts/`; la raíz del proyecto es la carpeta superior.
$carpetaScripts = Split-Path -Parent $MyInvocation.MyCommand.Path
$raizProyecto = Split-Path -Parent $carpetaScripts
Set-Location -LiteralPath $raizProyecto

$puertoBackend = 5000
$puertoFrontend = 5173
$urlFrontend = "http://localhost:$puertoFrontend"

$rutaPython = Join-Path $raizProyecto '.venv\Scripts\python.exe'
$rutaScriptEntorno = Join-Path $carpetaScripts 'configurar-entorno.ps1'

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

function Test-PuertoAccesibleEnLan {
    param([int]$Puerto)

    # `Get-NetTCPConnection` lista los sockets en escucha y su dirección local;
    # sólo `0.0.0.0` (o `::`) acepta conexiones desde otros equipos.
    $escuchas = Get-NetTCPConnection -LocalPort $Puerto -State Listen -ErrorAction SilentlyContinue
    return [bool]($escuchas | Where-Object { $_.LocalAddress -eq '0.0.0.0' -or $_.LocalAddress -eq '::' })
}

function Test-TeclaDisponible {
    try {
        # `KeyAvailable` no consume la tecla; sólo informa si hay una esperando.
        return [Console]::KeyAvailable
    }
    catch {
        # Sin consola interactiva (entrada redirigida) no hay teclas que leer.
        return $false
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

function Get-DireccionLan {
    # La interfaz con la ruta predeterminada es la que usa el equipo para salir
    # a la red; es la dirección que otros dispositivos de la LAN pueden usar.
    $rutaPredeterminada = Get-NetRoute -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue |
        Sort-Object RouteMetric, InterfaceMetric |
        Select-Object -First 1

    if ($rutaPredeterminada) {
        $direccion = Get-NetIPAddress -AddressFamily IPv4 -InterfaceIndex $rutaPredeterminada.InterfaceIndex -ErrorAction SilentlyContinue |
            Where-Object { $_.IPAddress -notlike '169.254.*' } |
            Select-Object -First 1
        if ($direccion) {
            return $direccion.IPAddress
        }
    }

    # Respaldo: el sistema informa qué dirección local usaría para salir a
    # Internet. Al ser UDP no se envía ningún paquete.
    $socket = [System.Net.Sockets.Socket]::new(
        [System.Net.Sockets.AddressFamily]::InterNetwork,
        [System.Net.Sockets.SocketType]::Dgram,
        [System.Net.Sockets.ProtocolType]::Udp
    )
    try {
        $socket.Connect('8.8.8.8', 53)
        return $socket.LocalEndPoint.Address.ToString()
    }
    catch {
        return $null
    }
    finally {
        $socket.Close()
    }
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
        # `--bind 0.0.0.0` publica el sitio en todas las interfaces, para que
        # también responda a otros dispositivos de la red local.
        $procesoFrontend = Start-Servidor -Descripcion 'Frontend' -Argumentos @(
            '-m', 'http.server', $puertoFrontend, '--bind', '0.0.0.0', '--directory', 'frontend'
        )
    }

    Wait-PuertoDisponible -Puerto $puertoBackend -Descripcion 'backend' -Proceso $procesoBackend
    Wait-PuertoDisponible -Puerto $puertoFrontend -Descripcion 'frontend' -Proceso $procesoFrontend

    $direccionLan = Get-DireccionLan

    Escribir-Paso 'Aplicación disponible.'
    Write-Host "  Frontend local:           $urlFrontend"
    Write-Host "  API local:                http://localhost:$puertoBackend/api/v1"
    if ($direccionLan) {
        Write-Host "  Frontend en la red local: http://${direccionLan}:$puertoFrontend" -ForegroundColor Green
        Write-Host "  API en la red local:      http://${direccionLan}:$puertoBackend/api/v1" -ForegroundColor Green
    }
    else {
        Write-Host '  No se pudo determinar la dirección de la red local.' -ForegroundColor Yellow
    }
    Write-Host '  Credenciales de demostración: ver README.md'

    if ($direccionLan) {
        if (-not (Test-PuertoAccesibleEnLan -Puerto $puertoFrontend)) {
            Write-Host '  El frontend sólo escucha en localhost; cerralo y volvé a ejecutar este script para acceder por la red local.' -ForegroundColor Yellow
        }
        Write-Host '  Si otro dispositivo no conecta, permití Python en el Firewall de Windows (redes privadas).' -ForegroundColor DarkGray
    }

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
    Write-Host 'Presioná una tecla en esta ventana para detener los servidores (o Ctrl+C).' -ForegroundColor Yellow

    while ($true) {
        Start-Sleep -Milliseconds 250
        foreach ($proceso in $script:procesosIniciados) {
            if ($proceso.HasExited) {
                throw "El proceso con PID $($proceso.Id) terminó inesperadamente."
            }
        }
        if (Test-TeclaDisponible) {
            # Se consume la tecla para que no la tome el Enter final.
            [void][Console]::ReadKey($true)
            break
        }
    }
}
catch {
    $codigoSalida = 1
    Write-Host ''
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
}
finally {
    $habiaProcesos = $script:procesosIniciados.Count -gt 0
    Stop-ProcesosIniciados
    if ($habiaProcesos) {
        Write-Host ''
        Write-Host 'Servidores detenidos.' -ForegroundColor DarkGray
    }
}

if (-not $SinPausa) {
    Write-Host ''
    # La ventana queda abierta para poder leer la dirección de la red local,
    # los registros de los servidores o un mensaje de error.
    Read-Host 'Presioná Enter para cerrar esta ventana' | Out-Null
}

exit $codigoSalida

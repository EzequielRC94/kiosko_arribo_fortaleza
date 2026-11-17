@echo off
setlocal enabledelayedexpansion
title Lanzador Universal Kiosko

:: 1. Obtenemos la ruta de la carpeta donde vive este archivo .bat (carpeta "app" en la nube)
:: Quitamos la barra invertida final para que robocopy no escape las comillas
set "RUTA_APP=%~dp0"
if "%RUTA_APP:~-1%"=="\" set "RUTA_APP=%RUTA_APP:~0,-1%"

set "ORIGEN=%RUTA_APP%\gui_arribo"
set "DESTINO=C:\kiosko_local\gui_arribo"

echo ===================================================
echo   Iniciando y actualizando Kiosko de Auto Arribo
echo ===================================================
echo Origen nube:  %ORIGEN%
echo Destino PC:   %DESTINO%
echo.

:: 2. Validar que exista la carpeta gui_arribo junto a este .bat
if not exist "%ORIGEN%\app\gui_arribo.py" (
    echo [ERROR] No se encontro la aplicacion en:
    echo         %ORIGEN%\app\gui_arribo.py
    echo Verifica que hayas copiado la carpeta "gui_arribo" completa dentro de "app".
    pause
    exit /b 1
)

:: 3. Cerrar instancia previa de este kiosko (si hubiera una abierta) para evitar archivos bloqueados
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*kiosko_local\gui_arribo\app\gui_arribo.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" >nul 2>&1

:: 4. Crear carpeta local si no existe
if not exist "%DESTINO%" mkdir "%DESTINO%"

:: 5. Sincronizar SOLO archivos nuevos o modificados desde la nube hacia la PC local
::    /MIR mantiene espejo exacto (actualiza nuevos y borra obsoletos)
::    /XD __pycache__ evita copiar caches innecesarios
::    /R:2 /W:2 evita quedarse colgado si un archivo esta temporalmente ocupado
echo Sincronizando ultima version a local...
robocopy "%ORIGEN%" "%DESTINO%" /MIR /XD __pycache__ /R:2 /W:2 /NFL /NDL /NJH /NJS /NC /NS

:: En robocopy, codigos 0 a 7 significan exito (8 o mayor es error real)
if %errorlevel% GEQ 8 (
    echo.
    echo [ADVERTENCIA] Hubo un problema al sincronizar desde la nube ^(codigo %errorlevel%^).
    if exist "%DESTINO%\app\gui_arribo.py" (
        echo Se intentara iniciar la copia local existente...
    ) else (
        echo No existe una copia local disponible para iniciar.
        pause
        exit /b 1
    )
) else (
    echo Sincronizacion completada correctamente.
)

:: 6. Detectar si el paquete fue generado en modo CONSOLA (debug) o SIN CONSOLA (oficial)
set "MODO=noconsole"
if exist "%DESTINO%\modo.txt" (
    set /p MODO=<"%DESTINO%\modo.txt"
)
:: Quitar posibles espacios
set "MODO=%MODO: =%"

echo Iniciando ejecucion local ^(modo: %MODO%^)...
if /I "%MODO%"=="console" (
    start "Kiosko Auto Arribo - Consola" /D "%DESTINO%\app" cmd /k ""%DESTINO%\python\python.exe" "%DESTINO%\app\gui_arribo.py""
) else (
    start "" /D "%DESTINO%\app" "%DESTINO%\python\pythonw.exe" "%DESTINO%\app\gui_arribo.py"
)

endlocal
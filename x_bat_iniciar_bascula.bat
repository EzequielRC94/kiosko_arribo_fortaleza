@echo off
title Lanzador Universal GUI Bascula

:: 1. Obtenemos la ruta de la carpeta donde vive este archivo .bat (carpeta "app" en la nube)
:: Quitamos la barra invertida final para que robocopy no escape las comillas
set "RUTA_APP=%~dp0"
if "%RUTA_APP:~-1%"=="\" set "RUTA_APP=%RUTA_APP:~0,-1%"

set "ORIGEN=%RUTA_APP%\gui_bascula"
set "DESTINO=C:\kiosko_local\gui_bascula"

echo ===================================================
echo   Iniciando y actualizando GUI Bascula
echo ===================================================
echo Origen nube:  %ORIGEN%
echo Destino PC:   %DESTINO%
echo.

:: 2. Validar que la carpeta gui_bascula exista junto a este .bat
if not exist "%ORIGEN%\gui_bascula.exe" (
    echo [ERROR] No se encontro la aplicacion en:
    echo         %ORIGEN%\gui_bascula.exe
    echo Verifica que hayas copiado la carpeta "gui_bascula" completa dentro de "app".
    pause
    exit /b 1
)

:: 3. Cerrar cualquier instancia previa abierta para evitar bloqueo de archivos al actualizar
taskkill /F /IM gui_bascula.exe >nul 2>&1

:: 4. Crear carpeta local si no existe
if not exist "%DESTINO%" mkdir "%DESTINO%"

:: 5. Sincronizar solo archivos nuevos o modificados desde la nube hacia la PC local
::    /MIR mantiene espejo exacto (actualiza nuevos y borra obsoletos)
::    /R:2 /W:2 evita quedarse colgado si un archivo esta temporalmente ocupado
echo Sincronizando ultima version a local...
robocopy "%ORIGEN%" "%DESTINO%" /MIR /R:2 /W:2 /NFL /NDL /NJH /NJS /NC /NS

:: En robocopy, codigos 0 a 7 significan exito (8 o mayor es error real)
if %errorlevel% GEQ 8 (
    echo.
    echo [ADVERTENCIA] Hubo un problema al sincronizar desde la nube ^(codigo %errorlevel%^).
    if exist "%DESTINO%\gui_bascula.exe" (
        echo Se intentara iniciar la copia local existente...
    ) else (
        echo No existe una copia local disponible para iniciar.
        pause
        exit /b 1
    )
) else (
    echo Sincronizacion completada correctamente.
)

:: 6. Ejecutar desde la carpeta local estableciendo su directorio de trabajo (/D)
echo Iniciando ejecucion local...
start "" /D "%DESTINO%" "%DESTINO%\gui_bascula.exe"

@echo off
title Auto-Empaquetador Kiosko Arribos (Con Consola / Debug)
echo ===================================================
echo   Empaquetando Kiosko de Auto Arribo (Modo Portable)
echo   Modo: DEBUG (con consola / python.exe)
echo ===================================================
echo.

if not exist "python_runtime\python.exe" (
    echo [ERROR] No se encontro la carpeta "python_runtime\python.exe".
    echo Asegurate de tener la carpeta base python_runtime junto a este .bat.
    pause
    exit /b 1
)

set "DIST_DIR=dist\gui_arribo"
set "APP_DIR=%DIST_DIR%\app"
set "PY_DIR=%DIST_DIR%\python"

echo [1/4] Preparando carpetas en %DIST_DIR%...
if not exist "%APP_DIR%" mkdir "%APP_DIR%"
if not exist "%PY_DIR%" mkdir "%PY_DIR%"

:: Limpiar archivos obsoletos de PyInstaller si existieran
if exist dist\gui_arribo.exe del /q dist\gui_arribo.exe
if exist "%DIST_DIR%\_internal" rmdir /s /q "%DIST_DIR%\_internal"

echo [2/4] Sincronizando runtime oficial de Python (sin falsos positivos)...
robocopy "python_runtime" "%PY_DIR%" /MIR /R:2 /W:2 /NFL /NDL /NJH /NJS /NC /NS
if %errorlevel% GEQ 8 (
    echo [ERROR] Fallo al copiar python_runtime ^(codigo %errorlevel%^).
    pause
    exit /b %errorlevel%
)

echo [3/4] Copiando scripts .py e imagenes de la aplicacion...
:: Lista de scripts necesarios para Kiosko Arribos
for %%F in (
    gui_arribo.py
    gui_selector_planta.py
    catalogos.py
    session_data.py
    manager_sap.py
    manager_logs.py
    manager_cloudfort.py
    mailer.py
    manager_arribos.py
    manager_descargas.py
    prevent_sleep.py
    _zql_robot.py
    parquets.py
) do (
    if exist "%%F" copy /Y "%%F" "%APP_DIR%\" >nul
)

robocopy "images" "%APP_DIR%\images" /MIR /R:2 /W:2 /NFL /NDL /NJH /NJS /NC /NS
if %errorlevel% GEQ 8 (
    echo [ERROR] Fallo al copiar carpeta images ^(codigo %errorlevel%^).
    pause
    exit /b %errorlevel%
)

echo [4/4] Configurando modo DEBUG (con consola)...
echo console> "%DIST_DIR%\modo.txt"

:: Crear lanzador directo dentro de dist\gui_arribo por si se prueba localmente
(
    echo @echo off
    echo title Kiosko Arribos - Consola Debug
    echo cd /d "%%~dp0app"
    echo "%%~dp0python\python.exe" "%%~dp0app\gui_arribo.py"
    echo pause
) > "%DIST_DIR%\ejecutar_kiosko.bat"

echo.
echo ===================================================
echo   Proceso terminado con exito!
echo   Carpeta generada: dist\gui_arribo\
echo   Modo configurado: DEBUG ^(con pantalla negra^)
echo.
echo   Siguiente paso:
echo   Copia la carpeta "dist\gui_arribo" completa a:
echo   ...\kiosko logistica cem - Documentos\app\
echo ===================================================
pause
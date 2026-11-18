@echo off
title Prueba Defender - PyInstaller --onedir (gui_arribo.exe)
echo ===================================================
echo   Compilando Kiosko de Auto Arribo (Prueba Defender)
echo   Modo: --onedir (carpeta) + --console (debug)
echo ===================================================
echo.
echo Limpiando compilaciones anteriores...
if exist build rmdir /s /q build
if exist dist\gui_arribo rmdir /s /q dist\gui_arribo
if exist dist\gui_arribo.exe del /q dist\gui_arribo.exe
if exist __pycache__ rmdir /s /q __pycache__
if exist gui_arribo.spec del /q gui_arribo.spec

echo.
echo Verificando entorno Python y empaquetando con PyInstaller...
if exist venv\Scripts\pyinstaller.exe (
    call venv\Scripts\activate.bat
    pyinstaller --console --onedir --noconfirm --add-data "images;images" --hidden-import win32timezone --icon="images/logo_short_ico.ico" gui_arribo.py
) else (
    echo [INFO] Usando PyInstaller del entorno global de Python...
    pyinstaller --console --onedir --noconfirm --add-data "images;images" --hidden-import win32timezone --icon="images/logo_short_ico.ico" gui_arribo.py
)

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] La compilacion fallo con codigo %errorlevel%.
    pause
    exit /b %errorlevel%
)

echo.
echo Verificando si el antivirus permitio generar gui_arribo.exe...
timeout /t 3 /nobreak >nul
if not exist "dist\gui_arribo\gui_arribo.exe" (
    echo [ALERTA] PyInstaller termino, pero NO existe dist\gui_arribo\gui_arribo.exe!
    echo          Es muy probable que el antivirus lo haya puesto en cuarentena.
    pause
    exit /b 1
)

echo.
echo ===================================================
echo   Prueba EXITOSA! gui_arribo.exe fue generado.
echo   Ruta: dist\gui_arribo\gui_arribo.exe
echo ===================================================
pause

@echo off
title Auto-Empaquetador Kiosko Arribos (Con Consola / Debug)
echo ===================================================
echo   Compilando Kiosko de Auto Arribo (Debug)
echo   Modo: --onedir (carpeta) + --console
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
echo Verificando generacion de dist\gui_arribo\gui_arribo.exe...
timeout /t 2 /nobreak >nul
if not exist "dist\gui_arribo\gui_arribo.exe" (
    echo [ALERTA] PyInstaller termino, pero NO existe dist\gui_arribo\gui_arribo.exe!
    echo          Verifica si el antivirus lo puso en cuarentena.
    pause
    exit /b 1
)

echo.
echo ===================================================
echo   Proceso terminado con exito!
echo   Carpeta generada: dist\gui_arribo\
echo   Modo: DEBUG ^(con consola / pantalla negra^)
echo.
echo   Siguiente paso:
echo   Copia la carpeta "dist\gui_arribo" completa a:
echo   ...\kiosko logistica cem - Documentos\app\
echo ===================================================
pause

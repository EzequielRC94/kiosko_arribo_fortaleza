@echo off
title Auto-Empaquetador Kiosko Arribos
echo ===================================================
echo   Compilando el proyecto Kiosko de Auto Arribo
echo ===================================================
echo.
echo Limpiando compilaciones anteriores...
if exist build rmdir /s /q build
if exist dist\gui_arribo.exe del /q dist\gui_arribo.exe
if exist __pycache__ rmdir /s /q __pycache__
if exist gui_arribo.spec del /q gui_arribo.spec

echo.
echo Activando entorno virtual y empaquetando...
:: Se asume que el script se ejecuta en la misma carpeta que el venv y el script python
:: Se usa call para que, si el script de activacion es otro .bat, retorne a este
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    pyinstaller --noconsole --onefile --add-data "images;images" --hidden-import win32timezone --icon="images/logo_short_ico.ico" gui_arribo.py
) else (
    echo [ADVERTENCIA] No se encontro el entorno virtual en venv\Scripts\activate.bat.
    echo Intentando empaquetar con el Python global...
    pyinstaller --noconsole --onefile --add-data "images;images" --hidden-import win32timezone --icon="images/logo_short_ico.ico" gui_arribo.py
)

echo.
echo ===================================================
echo   ¡Proceso terminado con exito!
echo   Tu archivo gui_arribo.exe esta en la carpeta "dist".
echo ===================================================
pause
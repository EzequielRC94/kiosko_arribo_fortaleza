import os

bat_content = """@echo off
title Compilador Kiosko Arribos
echo ===================================================
echo   Compilando el proyecto Kiosko de Auto Arribo
echo ===================================================
echo.
echo Limpiando compilaciones anteriores (opcional)...
if exist build rmdir /s /q build
if exist dist\\gui_arribo.exe del /q dist\\gui_arribo.exe

echo.
echo Empaquetando la aplicacion... Esto tomara un momento.
pyinstaller --noconsole --onefile --add-data "images;images" --icon="images/logo_short.png" gui_arribo.py

echo.
echo ===================================================
echo   ¡Proceso terminado con exito!
echo   Tu archivo gui_arribo.exe esta en la carpeta "dist".
echo ===================================================
pause
"""

bat_path = "/mnt/data/compilar_kiosko.bat"
with open(bat_path, "w") as f:
    f.write(bat_content)

print(f"BAT generado: [file-tag: {bat_path}]")
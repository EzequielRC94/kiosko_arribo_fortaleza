@echo off
title Auto-Empaquetador GUI Bascula (Oficial - Sin Consola)
echo ===================================================
echo   Compilando GUI Bascula (Oficial)
echo   Modo: --onedir (carpeta) + --noconsole
echo ===================================================
echo.
echo Limpiando compilaciones anteriores...
if exist build rmdir /s /q build
if exist dist\gui_bascula rmdir /s /q dist\gui_bascula
if exist dist\gui_bascula.exe del /q dist\gui_bascula.exe
if exist __pycache__ rmdir /s /q __pycache__
if exist gui_bascula.spec del /q gui_bascula.spec

echo.
echo Verificando entorno Python y empaquetando con PyInstaller...
if exist venv\Scripts\pyinstaller.exe (
    call venv\Scripts\activate.bat
    pyinstaller --noconsole --onedir --noconfirm --add-data "images;images" --hidden-import win32timezone --icon="images/logo_short_ico.ico" gui_bascula.py
) else (
    echo [INFO] Usando PyInstaller del entorno global de Python...
    pyinstaller --noconsole --onedir --noconfirm --add-data "images;images" --hidden-import win32timezone --icon="images/logo_short_ico.ico" gui_bascula.py
)

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] La compilacion fallo con codigo %errorlevel%.
    pause
    exit /b %errorlevel%
)

echo.
echo Verificando generacion de dist\gui_bascula\gui_bascula.exe...
timeout /t 2 /nobreak >nul
if not exist "dist\gui_bascula\gui_bascula.exe" (
    echo [ALERTA] PyInstaller termino, pero NO existe dist\gui_bascula\gui_bascula.exe!
    echo          Verifica si el antivirus lo puso en cuarentena.
    pause
    exit /b 1
)

echo.
echo ===================================================
echo   Proceso terminado con exito!
echo   Carpeta generada: dist\gui_bascula\
echo   Modo: OFICIAL ^(sin consola^)
echo.
echo   Siguiente paso:
echo   Copia la carpeta "dist\gui_bascula" completa a:
echo   ...\kiosko logistica cem - Documentos\app\
echo ===================================================
pause

@echo off
title Lanzador Universal Kiosko

:: 1. Obtenemos la ruta de la carpeta donde vive este archivo .bat
:: %~dp0 es un comando mágico que nos da la ruta del directorio actual
set RUTA_APP=%~dp0

echo Detectando planta desde: %RUTA_APP%

:: 2. Definimos una carpeta local fija en el Kiosko
set DESTINO="C:\kiosko_local\"

:: 3. Creamos carpeta local si no existe
if not exist %DESTINO% ( mkdir %DESTINO% )

:: 4. Copiamos el .exe desde la ruta donde está este .bat hacia el destino local
:: Usamos comillas para evitar errores con espacios en los nombres de las rutas de SharePoint
echo ...copiando app arribo a local...
xcopy "%RUTA_APP%gui_arribo.exe" %DESTINO% /Y /Q

echo Iniciando ejecucion local...
start "" "%DESTINO%gui_arribo.exe"
@echo off
chcp 65001 > nul
cls
echo ===============================================================================
echo        SISTEMA DE GESTION DE RESULTADOS (MATRIZ SGR) - I. MUNICIPALIDAD DE LA SERENA
echo ===============================================================================
echo.
echo Entorno: Puerto Unico 8000 (Arquitectura Django MVT)
echo.

cd /d "%~dp0backend"

if exist "venv\Scripts\python.exe" (
    set "PYTHON_CMD=venv\Scripts\python.exe"
) else (
    set "PYTHON_CMD=python"
)

echo [Paso 1/3] Aplicando migraciones de base de datos (evita error "no such table")...
%PYTHON_CMD% manage.py migrate --noinput
if errorlevel 1 (
    echo [ADVERTENCIA] Error al ejecutar migraciones. Continuando de todas formas...
)

echo [Paso 2/3] Verificando congruencia de modelos y estructura...
%PYTHON_CMD% manage.py check

echo [Paso 3/3] Iniciando servidor web en http://127.0.0.1:8000 ...
echo.
echo  - Plataforma Web: http://127.0.0.1:8000
echo  - Panel Admin:    http://127.0.0.1:8000/admin/
echo.
echo Presione [Ctrl + C] para detener el servidor.
echo ===============================================================================
echo.

%PYTHON_CMD% manage.py runserver 0.0.0.0:8000
pause

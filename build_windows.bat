@echo off
rem Genera AutoClick.exe + instalador AutoClickSetup.exe para Windows.
rem Ejecutar en Windows con el venv Python activo.
cd /d "%~dp0"

echo ==============================
echo 1) PyInstaller (.exe)
echo ==============================
python -m PyInstaller --noconfirm --clean AutoClick.spec
if errorlevel 1 goto :error
if not exist "dist\AutoClick.exe" (
    echo No se genero dist\AutoClick.exe
    goto :error
)

echo.
echo ==============================
echo 2) Inno Setup (instalador)
echo ==============================
set ISCC="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist %ISCC% (
    echo No se encontro Inno Setup. Instalalo desde https://jrsoftware.org/isinfo.php
    goto :error
)
%ISCC% installer\AutoClick.iss
if errorlevel 1 goto :error

echo.
echo ==============================
echo Listo:
echo   dist\AutoClick.exe
echo   installer\Output\AutoClickSetup.exe
echo ==============================
goto :eof

:error
echo Fallo durante el build.
exit /b 1
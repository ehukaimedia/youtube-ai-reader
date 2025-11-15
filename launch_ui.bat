@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "PROJECT_ROOT=%~dp0"
pushd "%PROJECT_ROOT%" >nul

set "PY_CMD=py -3"
%PY_CMD% -V >nul 2>&1
if errorlevel 1 (
    set "PY_CMD=python"
)
%PY_CMD% -V >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found on PATH. Install Python 3.10+ and try again.
    set "EXIT_CODE=1"
    goto :cleanup
)

set "VENV_DIR=.venv"
set "VENV_BIN=%PROJECT_ROOT%%VENV_DIR%\Scripts"
set "PATH=%VENV_BIN%;%PATH%"
set "PYTHON=%VENV_BIN%\python.exe"

if not exist "%PYTHON%" (
    echo [INFO] Creating virtual environment...
    %PY_CMD% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] Unable to create the virtual environment.
        set "EXIT_CODE=%ERRORLEVEL%"
        goto :cleanup
    )
)

set "SYNC_DEPS=0"
if /I "%~1"=="--sync" set "SYNC_DEPS=1"

set "NEED_INSTALL=0"
if not exist "%PROJECT_ROOT%%VENV_DIR%\Scripts\uvicorn.exe" set "NEED_INSTALL=1"
if "%SYNC_DEPS%"=="1" set "NEED_INSTALL=1"

if "%NEED_INSTALL%"=="1" goto :install_deps
goto :after_install

:install_deps
echo [INFO] Installing Python dependencies (this may take a minute)...
"%PYTHON%" -m pip install -r "%PROJECT_ROOT%requirements.txt"
if errorlevel 1 (
    echo [ERROR] pip install failed.
    set "EXIT_CODE=%ERRORLEVEL%"
    goto :cleanup
)

:after_install

where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo [WARN] FFmpeg was not found on PATH. Install it via "winget install Gyan.FFmpeg" so frame capture works.
)

echo [INFO] Opening your browser at http://127.0.0.1:8000/ ...
start "" powershell -NoProfile -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:8000/'" >nul 2>&1

echo [INFO] Starting FastAPI server (press Ctrl+C to stop)...
"%PYTHON%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
    echo [ERROR] Server exited with code %EXIT_CODE%.
    goto :cleanup
)

echo [INFO] Server stopped.

:cleanup
popd >nul
if "%EXIT_CODE%"=="" set "EXIT_CODE=%ERRORLEVEL%"
if "%EXIT_CODE%"=="0" (
    echo Press any key to close this window.
) else (
    echo Resolve the issue above and press any key to close.
)
pause >nul
endlocal & exit /b %EXIT_CODE%


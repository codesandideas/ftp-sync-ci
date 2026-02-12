@echo off
REM File Sync Tool - Windows launcher

SET SCRIPT_DIR=%~dp0
SET PYTHON_SCRIPT=%SCRIPT_DIR%file_sync.py
SET DEFAULT_CONFIG=%SCRIPT_DIR%config.json

REM Check if Python is installed
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if dependencies are installed
python -c "import watchdog" >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Installing dependencies...
    pip install -r "%SCRIPT_DIR%requirements.txt"
)

REM Parse arguments
SET CONFIG_FILE=%DEFAULT_CONFIG%

IF "%1"=="--setup" (
    python "%PYTHON_SCRIPT%" --create-config
    echo Configuration file created: config.json
    echo Please edit this file and run: sync.bat
    pause
    exit /b 0
)

IF "%1"=="--help" (
    echo File Sync Tool - Usage:
    echo.
    echo   sync.bat              Start sync with default config.json
    echo   sync.bat -c CONFIG    Start sync with custom config file
    echo   sync.bat --setup      Create example config file
    echo   sync.bat --help       Show this help message
    echo.
    pause
    exit /b 0
)

IF "%1"=="-c" (
    IF "%2"=="" (
        echo Error: -c requires a config file path
        pause
        exit /b 1
    )
    SET CONFIG_FILE=%2
)

REM Check if config exists
IF NOT EXIST "%CONFIG_FILE%" (
    echo Error: Configuration file not found: %CONFIG_FILE%
    echo Run 'sync.bat --setup' to create an example config file
    pause
    exit /b 1
)

REM Run the sync tool
echo Starting File Sync Tool...
python "%PYTHON_SCRIPT%" -c "%CONFIG_FILE%"
pause

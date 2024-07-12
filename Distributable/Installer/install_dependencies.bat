@echo off
setlocal

rem Set variables
set "INSTALL_DIR=%~dp0"
set "PYTHON_VERSION=3.11.6"  rem Update to Python version 3.11.6
set "GIT_VERSION=2.45.2"  rem Update to Git version 2.45.2
set "GIT_INSTALLER=%INSTALL_DIR%\Git-%GIT_VERSION%-64-bit.exe"
set "GIT_DOWNLOAD_URL=https://github.com/git-for-windows/git/releases/download/v%GIT_VERSION%.windows.1/Git-%GIT_VERSION%-64-bit.exe"

rem Function to check and install Scoop if not already installed
:install_scoop
powershell -command "& { Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force; irm get.scoop.sh | iex }"
if errorlevel 1 (
    echo Failed to install Scoop. Please check your internet connection or install manually from: https://scoop.sh
    pause
    exit /b 1
) else (
    echo Scoop installed successfully.
)

rem Install Git if not installed
if not exist "%GIT_INSTALLER%" (
    echo Git installer not found. Downloading Git %GIT_VERSION% installer...
    bitsadmin /transfer gitInstaller /download /priority normal "%GIT_DOWNLOAD_URL%" "%GIT_INSTALLER%"
    if errorlevel 1 (
        echo Failed to download Git installer. Please check your internet connection or download manually from:
        echo %GIT_DOWNLOAD_URL%
        pause
        exit /b 1
    )
)

rem Check if Git is installed
git --version > nul 2>&1
if errorlevel 1 (
    echo Git is not installed. Installing Git...
    rem Install Git
    "%GIT_INSTALLER%" /silent
    
    rem Check if Git installation was successful
    git --version > nul 2>&1
    if errorlevel 1 (
        echo Git installation should be finished. Close the installer and run it again. If the problem persists, install it manually. Press any key to close.
        pause
        exit /b 1
    ) else (
        echo Git installed successfully.
    )
) else (
    echo Git is already installed.
)

rem Check if Python is already installed
python --version > nul 2>&1
if not errorlevel 1 (
    echo Python is already installed. Skipping installation.
    goto install_packages
)

rem Install Python
echo Installing Python %PYTHON_VERSION%...
set "PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-amd64.exe"
set "PYTHON_FILE=%INSTALL_DIR%\python-%PYTHON_VERSION%-amd64.exe"

bitsadmin /transfer pythonInstaller /download /priority normal "%PYTHON_URL%" "%PYTHON_FILE%"
"%PYTHON_FILE%" /quiet InstallAllUsers=1 PrependPath=1

rem Check if Python installation was successful
python --version > install.log 2>&1
if errorlevel 1 (
    echo Python installation should be finished. Close the installer and run it again. If the problem persists, install it manually. Press any key to close.
    type install.log
    pause
    exit /b 1
)

del "%PYTHON_FILE%"

:install_packages
rem Install Python packages from requirements.txt
echo Installing Python packages...
python -m pip install -r "%INSTALL_DIR%\requirements.txt" --no-deps

rem Install Git-dependent package
echo Installing OpenVoice package from Git...
python -m pip install git+https://github.com/jeremyy5528/OpenVoice.git

rem Install ffmpeg using Scoop
echo Installing ffmpeg using Scoop...
scoop install ffmpeg

echo Installation complete.
pause

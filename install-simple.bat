@echo off
REM Simple Batch Script for Installing Minikube Prerequisites
REM Feature: 006-minikube-setup
REM Run this as Administrator

echo ========================================================================
echo    Minikube Prerequisites Installation (Simple Version)
echo    Feature: 006-minikube-setup
echo ========================================================================
echo.

REM Check if running as Administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator
    echo.
    echo To run as Administrator:
    echo   1. Right-click this file
    echo   2. Select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo [OK] Running with Administrator privileges
echo.

REM Check for Chocolatey
echo Checking for Chocolatey...
choco --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] Chocolatey not found. Installing Chocolatey...
    @"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
    if %errorLevel% neq 0 (
        echo [ERROR] Failed to install Chocolatey
        pause
        exit /b 1
    )
    echo [OK] Chocolatey installed successfully
) else (
    echo [OK] Chocolatey is already installed
)
echo.

REM Refresh environment
call refreshenv

REM Check current installations
echo Checking current installations...
echo.

docker --version >nul 2>&1
if %errorLevel% equ 0 (
    echo [SKIP] Docker is already installed
    set DOCKER_INSTALLED=1
) else (
    echo [ - ] Docker: Not installed
    set DOCKER_INSTALLED=0
)

kubectl version --client >nul 2>&1
if %errorLevel% equ 0 (
    echo [SKIP] kubectl is already installed
    set KUBECTL_INSTALLED=1
) else (
    echo [ - ] kubectl: Not installed
    set KUBECTL_INSTALLED=0
)

minikube version >nul 2>&1
if %errorLevel% equ 0 (
    echo [SKIP] Minikube is already installed
    set MINIKUBE_INSTALLED=1
) else (
    echo [ - ] Minikube: Not installed
    set MINIKUBE_INSTALLED=0
)
echo.

REM Confirm installation
echo ========================================================================
echo This will install:
if %DOCKER_INSTALLED% equ 0 echo   - Docker Desktop
if %KUBECTL_INSTALLED% equ 0 echo   - kubectl
if %MINIKUBE_INSTALLED% equ 0 echo   - Minikube
echo.
echo WARNING: Docker Desktop installation requires a system restart!
echo ========================================================================
echo.

set /p CONFIRM="Continue with installation? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo Installation cancelled by user
    pause
    exit /b 0
)
echo.

REM Install Docker Desktop
if %DOCKER_INSTALLED% equ 0 (
    echo ========================================================================
    echo Installing Docker Desktop...
    echo ========================================================================
    choco install docker-desktop -y
    if %errorLevel% neq 0 (
        echo [ERROR] Failed to install Docker Desktop
        echo You may need to install it manually from:
        echo https://www.docker.com/products/docker-desktop
    ) else (
        echo [OK] Docker Desktop installed successfully
        set NEEDS_RESTART=1
    )
    echo.
)

REM Install kubectl
if %KUBECTL_INSTALLED% equ 0 (
    echo ========================================================================
    echo Installing kubectl...
    echo ========================================================================
    choco install kubernetes-cli -y
    if %errorLevel% neq 0 (
        echo [ERROR] Failed to install kubectl
    ) else (
        echo [OK] kubectl installed successfully
    )
    echo.
)

REM Install Minikube
if %MINIKUBE_INSTALLED% equ 0 (
    echo ========================================================================
    echo Installing Minikube...
    echo ========================================================================
    choco install minikube -y
    if %errorLevel% neq 0 (
        echo [ERROR] Failed to install Minikube
    ) else (
        echo [OK] Minikube installed successfully
    )
    echo.
)

REM Refresh environment
call refreshenv

REM Final verification
echo ========================================================================
echo INSTALLATION SUMMARY
echo ========================================================================
echo.

docker --version >nul 2>&1
if %errorLevel% equ 0 (
    docker --version
    echo [OK] Docker Desktop: Installed
) else (
    echo [!] Docker Desktop: Not detected ^(may need restart^)
)

kubectl version --client >nul 2>&1
if %errorLevel% equ 0 (
    for /f "tokens=*" %%i in ('kubectl version --client --short 2^>nul') do echo %%i
    echo [OK] kubectl: Installed
) else (
    echo [!] kubectl: Not detected ^(restart terminal^)
)

minikube version >nul 2>&1
if %errorLevel% equ 0 (
    minikube version --short
    echo [OK] Minikube: Installed
) else (
    echo [!] Minikube: Not detected ^(restart terminal^)
)
echo.

REM Next steps
echo ========================================================================
echo NEXT STEPS
echo ========================================================================
echo.

if defined NEEDS_RESTART (
    echo [REQUIRED] RESTART YOUR COMPUTER for Docker Desktop to work
    echo.
    echo After restart:
    echo   1. Start Docker Desktop from the Start Menu
    echo   2. Wait for Docker to start ^(whale icon in system tray^)
    echo   3. Open Git Bash or PowerShell
    echo   4. Run: cd /c/Users/pc1/Desktop/full-stack-todo
    echo   5. Run: ./scripts/minikube/start-cluster.sh
    echo.
    set /p RESTART_NOW="Restart computer now? (Y/N): "
    if /i "%RESTART_NOW%"=="Y" (
        echo Restarting in 10 seconds... Press Ctrl+C to cancel
        timeout /t 10
        shutdown /r /t 0
    )
) else (
    echo To start using Minikube:
    echo.
    echo   1. Close and reopen your terminal
    echo   2. Verify installations:
    echo      docker --version
    echo      kubectl version --client
    echo      minikube version
    echo.
    echo   3. Start Minikube cluster:
    echo      cd /c/Users/pc1/Desktop/full-stack-todo
    echo      ./scripts/minikube/start-cluster.sh
    echo.
)

echo ========================================================================
echo Installation script completed!
echo ========================================================================
echo.
pause

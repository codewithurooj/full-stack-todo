# Minikube Prerequisites Installation Script
# Feature: 006-minikube-setup
# Platform: Windows 10+ with Chocolatey
#
# IMPORTANT: Run this script as Administrator
# Right-click PowerShell > Run as Administrator

#Requires -RunAsAdministrator

# Set error action preference
$ErrorActionPreference = "Stop"

# Colors for output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Banner
Write-ColorOutput "╔══════════════════════════════════════════════════════════════════╗" Cyan
Write-ColorOutput "║         Minikube Prerequisites Installation Script               ║" Cyan
Write-ColorOutput "║                  Feature: 006-minikube-setup                     ║" Cyan
Write-ColorOutput "╚══════════════════════════════════════════════════════════════════╝" Cyan
Write-Host ""

# Check if running as Administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-ColorOutput "❌ ERROR: This script must be run as Administrator" Red
    Write-ColorOutput "" White
    Write-ColorOutput "To run as Administrator:" Yellow
    Write-ColorOutput "  1. Right-click PowerShell" Yellow
    Write-ColorOutput "  2. Select 'Run as Administrator'" Yellow
    Write-ColorOutput "  3. Run this script again" Yellow
    exit 1
}

Write-ColorOutput "✅ Running with Administrator privileges" Green
Write-Host ""

# Check for Chocolatey
Write-ColorOutput "📦 Checking for Chocolatey package manager..." Cyan
try {
    $chocoVersion = choco --version 2>$null
    Write-ColorOutput "✅ Chocolatey $chocoVersion is installed" Green
} catch {
    Write-ColorOutput "❌ Chocolatey is not installed" Red
    Write-ColorOutput "" White
    Write-ColorOutput "Installing Chocolatey..." Yellow
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    Write-ColorOutput "✅ Chocolatey installed" Green
}
Write-Host ""

# Check current installations
Write-ColorOutput "🔍 Checking current installations..." Cyan
Write-Host ""

$dockerInstalled = Get-Command docker -ErrorAction SilentlyContinue
$kubectlInstalled = Get-Command kubectl -ErrorAction SilentlyContinue
$minikubeInstalled = Get-Command minikube -ErrorAction SilentlyContinue

if ($dockerInstalled) {
    $dockerVersion = docker --version 2>$null
    Write-ColorOutput "  Docker: $dockerVersion (already installed)" Yellow
} else {
    Write-ColorOutput "  Docker: Not installed" White
}

if ($kubectlInstalled) {
    $kubectlVersion = kubectl version --client --short 2>$null
    Write-ColorOutput "  kubectl: $kubectlVersion (already installed)" Yellow
} else {
    Write-ColorOutput "  kubectl: Not installed" White
}

if ($minikubeInstalled) {
    $minikubeVersion = minikube version --short 2>$null
    Write-ColorOutput "  Minikube: $minikubeVersion (already installed)" Yellow
} else {
    Write-ColorOutput "  Minikube: Not installed" White
}
Write-Host ""

# Confirm installation
Write-ColorOutput "════════════════════════════════════════════════════════════════════" Cyan
Write-ColorOutput "This script will install the following prerequisites:" White
Write-Host ""
if (-not $dockerInstalled) {
    Write-ColorOutput "  • Docker Desktop (container runtime)" White
}
if (-not $kubectlInstalled) {
    Write-ColorOutput "  • kubectl (Kubernetes CLI)" White
}
if (-not $minikubeInstalled) {
    Write-ColorOutput "  • Minikube (local Kubernetes cluster)" White
}
Write-Host ""
Write-ColorOutput "⚠️  WARNING: Docker Desktop installation requires a system restart!" Yellow
Write-ColorOutput "════════════════════════════════════════════════════════════════════" Cyan
Write-Host ""

$confirmation = Read-Host "Continue with installation? (Y/N)"
if ($confirmation -ne 'Y' -and $confirmation -ne 'y') {
    Write-ColorOutput "Installation cancelled by user" Yellow
    exit 0
}
Write-Host ""

# Install Docker Desktop
if (-not $dockerInstalled) {
    Write-ColorOutput "═══ Installing Docker Desktop ═══" Cyan
    try {
        choco install docker-desktop -y
        Write-ColorOutput "✅ Docker Desktop installed successfully" Green
        Write-ColorOutput "⚠️  You MUST restart your computer for Docker to work" Yellow
        $needsRestart = $true
    } catch {
        Write-ColorOutput "❌ Failed to install Docker Desktop: $_" Red
        Write-ColorOutput "   You may need to install it manually from:" White
        Write-ColorOutput "   https://www.docker.com/products/docker-desktop" White
    }
    Write-Host ""
} else {
    Write-ColorOutput "⏭️  Skipping Docker Desktop (already installed)" Yellow
    Write-Host ""
}

# Install kubectl
if (-not $kubectlInstalled) {
    Write-ColorOutput "═══ Installing kubectl ═══" Cyan
    try {
        choco install kubernetes-cli -y
        Write-ColorOutput "✅ kubectl installed successfully" Green
    } catch {
        Write-ColorOutput "❌ Failed to install kubectl: $_" Red
    }
    Write-Host ""
} else {
    Write-ColorOutput "⏭️  Skipping kubectl (already installed)" Yellow
    Write-Host ""
}

# Install Minikube
if (-not $minikubeInstalled) {
    Write-ColorOutput "═══ Installing Minikube ═══" Cyan
    try {
        choco install minikube -y
        Write-ColorOutput "✅ Minikube installed successfully" Green
    } catch {
        Write-ColorOutput "❌ Failed to install Minikube: $_" Red
    }
    Write-Host ""
} else {
    Write-ColorOutput "⏭️  Skipping Minikube (already installed)" Yellow
    Write-Host ""
}

# Refresh environment variables
Write-ColorOutput "🔄 Refreshing environment variables..." Cyan
try {
    refreshenv
    Write-ColorOutput "✅ Environment variables refreshed" Green
} catch {
    Write-ColorOutput "⚠️  Could not refresh environment automatically" Yellow
    Write-ColorOutput "   Please close and reopen your terminal" Yellow
}
Write-Host ""

# Final verification
Write-ColorOutput "════════════════════════════════════════════════════════════════════" Green
Write-ColorOutput "║                    INSTALLATION SUMMARY                          ║" Green
Write-ColorOutput "════════════════════════════════════════════════════════════════════" Green
Write-Host ""

# Check installations again
$dockerInstalled = Get-Command docker -ErrorAction SilentlyContinue
$kubectlInstalled = Get-Command kubectl -ErrorAction SilentlyContinue
$minikubeInstalled = Get-Command minikube -ErrorAction SilentlyContinue

if ($dockerInstalled) {
    Write-ColorOutput "✅ Docker Desktop: Installed" Green
} else {
    Write-ColorOutput "❌ Docker Desktop: Not detected (may need restart)" Yellow
}

if ($kubectlInstalled) {
    $kubectlVersion = kubectl version --client --short 2>$null
    Write-ColorOutput "✅ kubectl: $kubectlVersion" Green
} else {
    Write-ColorOutput "❌ kubectl: Not detected (restart terminal)" Yellow
}

if ($minikubeInstalled) {
    $minikubeVersion = minikube version --short 2>$null
    Write-ColorOutput "✅ Minikube: $minikubeVersion" Green
} else {
    Write-ColorOutput "❌ Minikube: Not detected (restart terminal)" Yellow
}

Write-Host ""
Write-ColorOutput "════════════════════════════════════════════════════════════════════" Cyan
Write-ColorOutput "║                         NEXT STEPS                               ║" Cyan
Write-ColorOutput "════════════════════════════════════════════════════════════════════" Cyan
Write-Host ""

if ($needsRestart) {
    Write-ColorOutput "🔴 REQUIRED: Restart your computer for Docker Desktop to work" Red
    Write-Host ""
    Write-ColorOutput "After restart:" Cyan
    Write-ColorOutput "  1. Start Docker Desktop from the Start Menu" White
    Write-ColorOutput "  2. Wait for Docker to start (whale icon in system tray)" White
    Write-ColorOutput "  3. Open Git Bash or PowerShell" White
    Write-ColorOutput "  4. Run: cd /c/Users/pc1/Desktop/full-stack-todo" White
    Write-ColorOutput "  5. Run: ./scripts/minikube/start-cluster.sh" White
    Write-Host ""

    $restartNow = Read-Host "Restart computer now? (Y/N)"
    if ($restartNow -eq 'Y' -or $restartNow -eq 'y') {
        Write-ColorOutput "Restarting computer in 10 seconds..." Yellow
        Write-ColorOutput "Press Ctrl+C to cancel" Yellow
        Start-Sleep -Seconds 10
        Restart-Computer -Force
    } else {
        Write-ColorOutput "⚠️  Remember to restart before using Docker!" Yellow
    }
} else {
    Write-ColorOutput "To start using Minikube:" Cyan
    Write-Host ""
    Write-ColorOutput "  1. Close and reopen your terminal" White
    Write-ColorOutput "  2. Verify installations:" White
    Write-ColorOutput "     docker --version" Gray
    Write-ColorOutput "     kubectl version --client" Gray
    Write-ColorOutput "     minikube version" Gray
    Write-Host ""
    Write-ColorOutput "  3. Start Minikube cluster:" White
    Write-ColorOutput "     cd /c/Users/pc1/Desktop/full-stack-todo" Gray
    Write-ColorOutput "     ./scripts/minikube/start-cluster.sh" Gray
    Write-Host ""
    Write-ColorOutput "  4. Enable addons:" White
    Write-ColorOutput "     ./scripts/minikube/enable-addons.sh all" Gray
    Write-Host ""
    Write-ColorOutput "  5. Verify health:" White
    Write-ColorOutput "     ./scripts/minikube/verify-health.sh" Gray
}

Write-Host ""
Write-ColorOutput "════════════════════════════════════════════════════════════════════" Green
Write-ColorOutput "Installation script completed!" Green
Write-ColorOutput "════════════════════════════════════════════════════════════════════" Green
Write-Host ""

# Minikube Prerequisites Installation Guide

**System**: Windows 10+
**Package Managers Detected**: Chocolatey 2.3.0, Winget v1.12.350

---

## Installation Steps

### Step 1: Open PowerShell as Administrator

1. Press `Windows + X`
2. Select "Windows PowerShell (Admin)" or "Terminal (Admin)"
3. Click "Yes" when prompted by UAC

---

### Step 2: Install Docker Desktop

**Option A: Using Chocolatey (Recommended)**
```powershell
choco install docker-desktop -y
```

**Option B: Using Winget**
```powershell
winget install Docker.DockerDesktop
```

**Option C: Manual Download**
- Download from: https://www.docker.com/products/docker-desktop
- Run installer
- Follow installation wizard

**After Installation:**
1. Restart your computer if prompted
2. Start Docker Desktop from Start Menu
3. Wait for Docker to start (whale icon in system tray)
4. Verify: Open new terminal and run `docker --version`

---

### Step 3: Install kubectl

**Option A: Using Chocolatey**
```powershell
choco install kubernetes-cli -y
```

**Option B: Using Winget**
```powershell
winget install Kubernetes.kubectl
```

**Verify Installation:**
```powershell
kubectl version --client
```

---

### Step 4: Install Minikube

**Option A: Using Chocolatey (Recommended)**
```powershell
choco install minikube -y
```

**Option B: Using Winget**
```powershell
winget install Kubernetes.minikube
```

**Verify Installation:**
```powershell
minikube version
```

---

### Step 5: Restart Terminal

Close and reopen your terminal (Git Bash or PowerShell) to ensure PATH updates are loaded.

---

## Quick Install Script (PowerShell Admin)

Run this in PowerShell as Administrator:

```powershell
# Install all prerequisites at once
Write-Host "Installing Docker Desktop..." -ForegroundColor Cyan
choco install docker-desktop -y

Write-Host "Installing kubectl..." -ForegroundColor Cyan
choco install kubernetes-cli -y

Write-Host "Installing Minikube..." -ForegroundColor Cyan
choco install minikube -y

Write-Host ""
Write-Host "Installation complete!" -ForegroundColor Green
Write-Host "Please restart your computer for Docker Desktop to work properly." -ForegroundColor Yellow
Write-Host ""
Write-Host "After restart, verify installations:" -ForegroundColor Cyan
Write-Host "  docker --version"
Write-Host "  kubectl version --client"
Write-Host "  minikube version"
```

---

## Post-Installation Verification

After restarting your computer and starting Docker Desktop, run:

```bash
# In Git Bash or PowerShell
cd /c/Users/pc1/Desktop/full-stack-todo

# Verify all tools are installed
docker --version
kubectl version --client
minikube version

# Run the cluster setup
./scripts/minikube/start-cluster.sh
```

---

## System Requirements

**Minimum:**
- Windows 10 Pro/Enterprise/Education (for Hyper-V) OR Windows 10 Home (with WSL 2)
- 6+ CPU cores (4 for cluster + 2 for host)
- 12GB+ RAM (8GB for cluster + 4GB for host)
- 20GB+ free disk space
- Virtualization enabled in BIOS (VT-x/AMD-v)

**Check Virtualization:**
```powershell
# Run in PowerShell
systeminfo | findstr /C:"Virtualization"
```

Should show: "Virtualization Enabled In Firmware: Yes"

If "No", you need to enable it in BIOS settings.

---

## Troubleshooting

### Docker Desktop Issues

**Problem**: Docker daemon not starting
**Solution**:
1. Ensure virtualization is enabled in BIOS
2. Windows 10 Home: Install WSL 2 first
3. Check Windows Services: "Docker Desktop Service" should be running

**Problem**: "WSL 2 installation is incomplete"
**Solution**:
```powershell
# Install WSL 2
wsl --install
```

### Minikube Driver Issues

**Problem**: Minikube fails to start with Docker driver
**Solution**:
1. Ensure Docker Desktop is running (whale icon in tray)
2. Try: `minikube start --driver=docker --force`
3. If fails, try alternative driver: `minikube start --driver=hyperv`

### Permission Issues

**Problem**: "Access denied" or "requires administrator"
**Solution**:
- Always run PowerShell as Administrator for installations
- For Minikube operations, regular user privileges are sufficient

---

## Expected Installation Time

- **Docker Desktop**: 5-10 minutes + restart
- **kubectl**: 1-2 minutes
- **Minikube**: 1-2 minutes
- **Total**: ~15-20 minutes (including restart)

---

## Next Steps After Installation

1. **Verify installations** with version commands
2. **Start Docker Desktop** and wait for it to be ready
3. **Run cluster setup**:
   ```bash
   cd /c/Users/pc1/Desktop/full-stack-todo
   ./scripts/minikube/start-cluster.sh
   ```
4. **Enable addons**:
   ```bash
   ./scripts/minikube/enable-addons.sh all
   ```
5. **Verify health**:
   ```bash
   ./scripts/minikube/verify-health.sh
   ```

---

**Created**: 2025-12-30
**For Feature**: 006-minikube-setup

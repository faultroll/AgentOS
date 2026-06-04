# .a AI Coding Workspace - Installation Script
# Portable setup for VSCodium + Continue + Kilo Code
# Reference: https://github.com/official-imvoiid/Portable-Miniconda-Setup-for-Window

param(
    [switch]$Force
)

# Error handling
$ErrorActionPreference = "Stop"

# Script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir

# Configuration from requirements.txt
# VSCodium 1.116.x (VSCode 1.116.0) - Latest stable with multi-agent support
# Multi-agent sessions introduced in VSCode 1.109 (Feb 2026)
# Continue v1.2.22 requires VSCode 1.70.0+
# Kilo Code v7.3.8 requires VSCode 1.84.0+, recommends 1.90.0+
$VSCodiumVersion = "1.116.02821"
$VSCodiumUrl = "https://github.com/VSCodium/vscodium/releases/download/${VSCodiumVersion}/VSCodium-win32-x64-${VSCodiumVersion}.zip"
# Continue - Latest STABLE version (v1.2.x series)
$ContinueVersion = "1.2.22"
$ContinueUrl = "https://github.com/continuedev/continue/releases/download/v${ContinueVersion}-vscode/continue-win32-x64-${ContinueVersion}.vsix"
# Kilo Code - Latest stable version (v7.3.x series)
# Platform-specific VSIX: kilo-vscode-win32-x64.vsix (no version in filename)
$KiloVersion = "7.3.8"
$KiloUrl = "https://github.com/Kilo-Org/kilocode/releases/download/v${KiloVersion}/kilo-vscode-win32-x64.vsix"
# Tiny Light Theme - VSCode Marketplace
$TinyLightUrl = "https://luqimin.gallery.vsassets.io/_apis/public/gallery/publisher/luqimin/extension/tiny-light/latest/assetbyname/Microsoft.VisualStudio.Services.VSIXPackage"
# Font: WenQuanYi Zen Hei - User provided link
$FontUrl = "https://github.com/Pengyu717/wqy/raw/main/fonts/wqy-zenhei-0.8.38-1.ttc"

# Paths
$VSCodiumDir = Join-Path $ScriptDir "vscodium"
$DataDir = Join-Path $VSCodiumDir "data"              # VSCode Portable Mode data folder
$ExtensionsDir = Join-Path $DataDir "extensions"      # Portable extensions
$UserDataDir = Join-Path $DataDir "user-data"         # Portable user settings
$DownloadsDir = Join-Path $ScriptDir "downloads"      # Download cache (outside vscodium dir)
$BinDir = Join-Path $VSCodiumDir "bin"
$FontsDir = Join-Path $DataDir "fonts"                # Portable fonts directory

# Helper functions
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Test-Command {
    param([string]$Command)
    $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

function Invoke-Download {
    param(
        [string]$Url,
        [string]$OutputPath,
        [string]$Description
    )

    if (Test-Path $OutputPath) {
        if (-not $Force) {
            Write-Warning "$Description already exists. Use -Force to re-download."
            return $true
        }
        Remove-Item $OutputPath -Force
    }

    Write-Info "Downloading $Description..."
    Write-Info "URL: $Url"

    try {
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $Url -OutFile $OutputPath -UseBasicParsing
        $ProgressPreference = 'Continue'
        Write-Success "Downloaded $Description"
        return $true
    }
    catch {
        Write-Error "Failed to download $Description`: $_"
        return $false
    }
}

function Expand-Zip {
    param(
        [string]$ZipPath,
        [string]$DestinationPath
    )

    Write-Info "Extracting $(Split-Path $ZipPath -Leaf)..."

    if (Test-Path $DestinationPath) {
        if ($Force) {
            Write-Warning "Removing existing directory: $DestinationPath"
            Remove-Item $DestinationPath -Recurse -Force
        }
        else {
            Write-Warning "Directory already exists: $DestinationPath"
            return $true
        }
    }

    try {
        Expand-Archive -Path $ZipPath -DestinationPath $DestinationPath -Force
        Write-Success "Extracted to $DestinationPath"
        return $true
    }
    catch {
        Write-Error "Failed to extract: $_"
        return $false
    }
}

# Main installation
function Install-AWorkspace {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Blue
    Write-Host "  .a AI Coding Workspace Installer" -ForegroundColor Blue
    Write-Host "========================================" -ForegroundColor Blue
    Write-Host ""

    # Check PowerShell execution policy
    $execPolicy = Get-ExecutionPolicy
    if ($execPolicy -eq 'Restricted') {
        Write-Error "PowerShell execution policy is Restricted."
        Write-Info "Please run: Set-ExecutionPolicy RemoteSigned -Scope CurrentUser"
        exit 1
    }

    # Create basic downloads directory
    Write-Info "Creating downloads directory..."
    if (-not (Test-Path $DownloadsDir)) {
        New-Item -ItemType Directory -Path $DownloadsDir -Force | Out-Null
    }


    # Install VSCodium
    $codiumBinary = Join-Path $BinDir "codium.cmd"
    $vscodiumExists = Test-Path $codiumBinary

    if ($vscodiumExists -and -not $Force) {
        Write-Warning "VSCodium already installed. Use -Force to re-install."
    }
    else {
        $zipPath = Join-Path $DownloadsDir "vscodium-${VSCodiumVersion}.zip"

        if (-not (Invoke-Download -Url $VSCodiumUrl -OutputPath $zipPath -Description "VSCodium v${VSCodiumVersion}")) {
            Write-Error "Failed to download VSCodium. Installation aborted."
            exit 1
        }

        # Backup existing installation only if it's a real install (not just an empty dir)
        if (Test-Path $codiumBinary) {
            $backupDir = "${VSCodiumDir}.backup.$(Get-Date -Format 'yyyyMMddHHmmss')"
            Write-Info "Backing up existing VSCodium to $backupDir"
            Move-Item $VSCodiumDir $backupDir
        }

        if (-not (Expand-Zip -ZipPath $zipPath -DestinationPath $VSCodiumDir)) {
            Write-Error "Failed to extract VSCodium. Installation aborted."
            exit 1
        }

        Write-Success "VSCodium installed successfully"
    }

    # Verify VSCodium binary
    if (-not (Test-Path $codiumBinary)) {
        Write-Error "VSCodium binary not found at $codiumBinary"
        exit 1
    }

    # Now create portable data directories
    Write-Info "Creating portable directories..."
    @($DataDir, $ExtensionsDir, $UserDataDir, $FontsDir) | ForEach-Object {
        if (-not (Test-Path $_)) {
            New-Item -ItemType Directory -Path $_ -Force | Out-Null
        }
    }

    # Download WenQuanYi Zen Hei font (portable)
    Write-Host ""
    Write-Info "Downloading WenQuanYi Zen Hei font..."
    $fontCache = Join-Path $DownloadsDir "wqy-zenhei.ttc"
    $fontTarget = Join-Path $FontsDir "wqy-zenhei.ttc"
    
    if (Invoke-Download -Url $FontUrl -OutputPath $fontCache -Description "WenQuanYi Zen Hei font (.ttc)") {
        Copy-Item -Path $fontCache -Destination $fontTarget -Force
        Write-Success "Font installed to $FontsDir"
        Write-Info "To use the font, set editor.fontFamily to 'WenQuanYi Zen Hei' in settings."
        Write-Info "Since you requested not to install the font globally, it will be loaded temporarily via bootstrap.ps1."
    }

    # Install Extensions (VSCode Portable Mode - auto-detected via data/ folder)
    Write-Host ""
    Write-Info "Installing VS Code extensions (portable mode)..."
    Write-Info "Extensions will be installed to: $ExtensionsDir"

    # Ensure extensions directory exists
    if (-not (Test-Path $ExtensionsDir)) {
        New-Item -ItemType Directory -Path $ExtensionsDir -Force | Out-Null
    }

    $extensionsInstalled = 0
    $extensionsFailed = 0

    # Download and install Continue
    $continueVsix = Join-Path $DownloadsDir "continue-${ContinueVersion}.vsix"
    if (Invoke-Download -Url $ContinueUrl -OutputPath $continueVsix -Description "Continue v${ContinueVersion}") {
        Write-Info "Installing Continue extension..."
        # Note: VSCodium auto-detects portable mode via data/ folder
        & $codiumBinary --install-extension $continueVsix --force 2>&1 | ForEach-Object {
            if ($_ -match "successfully|installed|already") {
                Write-Success $_
            }
            else {
                Write-Host "  $_"
            }
        }
        if ($LASTEXITCODE -eq 0) {
            $extensionsInstalled++
        }
        else {
            $extensionsFailed++
            Write-Error "Failed to install Continue extension"
        }
    }
    else {
        $extensionsFailed++
        Write-Error "Failed to download Continue extension"
    }

    # Download and install Kilo Code
    $kiloVsix = Join-Path $DownloadsDir "kilo-vscode-win32-x64.vsix"
    if (Invoke-Download -Url $KiloUrl -OutputPath $kiloVsix -Description "Kilo Code v${KiloVersion}") {
        Write-Info "Installing Kilo Code extension..."
        & $codiumBinary --install-extension $kiloVsix --force 2>&1 | ForEach-Object {
            if ($_ -match "successfully|installed|already") {
                Write-Success $_
            }
            else {
                Write-Host "  $_"
            }
        }
        if ($LASTEXITCODE -eq 0) {
            $extensionsInstalled++
        }
        else {
            $extensionsFailed++
            Write-Error "Failed to install Kilo Code extension"
        }
    }
    else {
        $extensionsFailed++
        Write-Error "Failed to download Kilo Code extension"
    }

    # Download and install Tiny Light Theme
    $tinyLightVsix = Join-Path $DownloadsDir "tiny-light.vsix"
    if (Invoke-Download -Url $TinyLightUrl -OutputPath $tinyLightVsix -Description "Tiny Light theme") {
        Write-Info "Installing Tiny Light theme..."
        & $codiumBinary --install-extension $tinyLightVsix --force 2>&1 | ForEach-Object {
            if ($_ -match "successfully|installed|already") {
                Write-Success $_
            }
            else {
                Write-Host "  $_"
            }
        }
        if ($LASTEXITCODE -eq 0) {
            $extensionsInstalled++
        }
        else {
            $extensionsFailed++
            Write-Error "Failed to install Tiny Light theme"
        }
    }
    else {
        $extensionsFailed++
        Write-Error "Failed to download Tiny Light theme"
    }

    if ($extensionsFailed -eq 0) {
        Write-Success "All extensions ($extensionsInstalled) installed successfully"
    }
    else {
        Write-Warning "Extensions installed: $extensionsInstalled, Failed: $extensionsFailed"
    }

    # Configure workspace settings
    Write-Host ""
    Write-Info "Configuring workspace settings..."

    $vscodeSettingsDir = Join-Path $RootDir ".vscode"
    if (-not (Test-Path $vscodeSettingsDir)) {
        New-Item -ItemType Directory -Path $vscodeSettingsDir -Force | Out-Null
    }

    $settingsPath = Join-Path $vscodeSettingsDir "settings.json"
    $settingsContent = @{
        "continue.configPath" = "${ScriptDir}/providers/continue.yaml"
        "continue.telemetryEnabled" = $false
        "kilo-code.provider" = "continue"
        "kilo-code.configPath" = "${ScriptDir}/providers/kilo.yaml"
    } | ConvertTo-Json -Depth 10

    # Always update .vscode/settings.json
    $settingsContent | Out-File -FilePath $settingsPath -Encoding UTF8
    Write-Success "Updated .vscode/settings.json"

    # Create launcher scripts
    Write-Host ""
    Write-Info "Creating launcher scripts..."

    # Create simple batch launcher for Windows
    $batchLauncher = Join-Path $ScriptDir "launch.bat"
    @"
@echo off
REM .a AI Coding Workspace Launcher
REM Generated by install.ps1

cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "bootstrap.ps1" %*
"@ | Out-File -FilePath $batchLauncher -Encoding ASCII

    Write-Success "Created launch.bat"

    # Installation summary
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  Installation Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Workspace location: $ScriptDir" -ForegroundColor White
    Write-Host "VSCodium location:  $VSCodiumDir" -ForegroundColor White
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Configure your LLM backend in:" -ForegroundColor White
    Write-Host "     $ScriptDir\providers\continue.yaml" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  2. Launch workspace with:" -ForegroundColor White
    Write-Host "     .a\bootstrap.ps1" -ForegroundColor Cyan
    Write-Host "     or" -ForegroundColor White
    Write-Host "     .a\launch.bat" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  3. Or use full path:" -ForegroundColor White
    Write-Host "     $ScriptDir\bootstrap.ps1" -ForegroundColor Gray
    Write-Host ""
}

# Run installation
Install-AWorkspace

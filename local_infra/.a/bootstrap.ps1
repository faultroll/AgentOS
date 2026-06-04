# .a AI Coding Workspace - Bootstrap/Launch Script
# Launches VSCodium with configured extensions and settings
# Reference: https://github.com/official-imvoiid/Portable-Miniconda-Setup-for-Window

param(
    [string]$WorkspacePath = "",
    [switch]$NewWindow,
    [switch]$Verbose,
    [switch]$CheckOnly
)

# Error handling
$ErrorActionPreference = "Stop"

# Script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir

# Paths
$VSCodiumDir = Join-Path $ScriptDir "vscodium"
$DataDir = Join-Path $VSCodiumDir "data"              # VSCode Portable Mode data folder
$ExtensionsDir = Join-Path $DataDir "extensions"      # Portable extensions
$UserDataDir = Join-Path $DataDir "user-data"         # Portable user settings
$BinDir = Join-Path $VSCodiumDir "bin"
$CodiumCmd = Join-Path $BinDir "codium.cmd"
$FontsDir = Join-Path $DataDir "fonts"
$ProvidersDir = Join-Path $ScriptDir "providers"
$ContinueConfig = Join-Path $ProvidersDir "continue.yaml"
$KiloConfig = Join-Path $ProvidersDir "kilo.yaml"

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

function Test-Configuration {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Blue
    Write-Host "  .a Workspace Configuration Check" -ForegroundColor Blue
    Write-Host "========================================" -ForegroundColor Blue
    Write-Host ""

    $allOk = $true

    # Check VSCodium
    Write-Info "Checking VSCodium installation..."
    if (Test-Path $CodiumCmd) {
        Write-Success "VSCodium found at $CodiumCmd"
        try {
            $version = & $CodiumCmd --version 2>$null | Select-Object -First 1
            Write-Info "Version: $version"
        }
        catch {
            Write-Warning "Could not determine VSCodium version"
        }
    }
    else {
        Write-Error "VSCodium not found at $CodiumCmd"
        Write-Info "Please run install.ps1 first"
        $allOk = $false
    }

    # Check extensions (portable directory)
    Write-Host ""
    Write-Info "Checking VS Code extensions (portable)..."
    if (Test-Path $CodiumCmd) {
        $extensions = & $CodiumCmd --list-extensions --extensions-dir $ExtensionsDir 2>$null

        if ($extensions -contains "continue.continue") {
            Write-Success "Continue extension installed (portable)"
        }
        else {
            Write-Warning "Continue extension not found in portable directory"
            Write-Info "Run install.ps1 to install extensions"
        }

        if ($extensions -contains "kilocode.kilo-code") {
            Write-Success "Kilo Code extension installed (portable)"
        }
        else {
            Write-Warning "Kilo Code extension not found in portable directory"
            Write-Info "Run install.ps1 to install extensions"
        }
    }

    # Check provider configs
    Write-Host ""
    Write-Info "Checking provider configurations..."

    if (Test-Path $ContinueConfig) {
        Write-Success "Continue config found at $ContinueConfig"

        # Basic YAML validation
        try {
            $content = Get-Content $ContinueConfig -Raw
            if ($content -match "apiBase|model|provider") {
                Write-Success "Continue config appears valid"
            }
            else {
                Write-Warning "Continue config may be incomplete"
            }
        }
        catch {
            Write-Warning "Could not validate Continue config"
        }
    }
    else {
        Write-Error "Continue config not found at $ContinueConfig"
        $allOk = $false
    }

    if (Test-Path $KiloConfig) {
        Write-Success "Kilo Code config found at $KiloConfig"
    }
    else {
        Write-Warning "Kilo Code config not found (optional)"
    }

    # Check workspace settings
    Write-Host ""
    Write-Info "Checking workspace settings..."
    $vscodeSettings = Join-Path $RootDir ".vscode\settings.json"
    if (Test-Path $vscodeSettings) {
        Write-Success "Workspace settings found"
    }
    else {
        Write-Warning "Workspace settings not found"
        Write-Info "Run install.ps1 to configure workspace"
    }

    # Check LLM backend
    Write-Host ""
    Write-Info "Checking LLM backend configuration..."

    if (Test-Path $ContinueConfig) {
        $configContent = Get-Content $ContinueConfig -Raw

        # Extract apiBase from YAML
        if ($configContent -match 'apiBase:\s*(.+)' -or $configContent -match 'apiBase:\s*["'']?([^"''\s]+)') {
            $apiBase = $Matches[1].Trim()
            Write-Info "Configured LLM endpoint: $apiBase"

            # Try to ping the endpoint
            try {
                $ProgressPreference = 'SilentlyContinue'
                $response = Invoke-WebRequest -Uri $apiBase -Method GET -TimeoutSec 5 -ErrorAction SilentlyContinue
                $ProgressPreference = 'Continue'
                Write-Success "LLM endpoint is reachable"
            }
            catch {
                Write-Warning "Could not reach LLM endpoint at $apiBase"
                Write-Info "Make sure your LLM backend (Ollama, etc.) is running"
            }
        }
        else {
            Write-Warning "No apiBase found in Continue config"
        }
    }

    # Check fonts
    Write-Host ""
    Write-Info "Checking portable fonts..."
    if (Test-Path $FontsDir) {
        $fontFiles = Get-ChildItem -Path $FontsDir -Include "*.ttf", "*.ttc" -Recurse
        if ($fontFiles.Count -gt 0) {
            Write-Success "Found $($fontFiles.Count) portable font(s)"
            # Temporary load fonts for the session
            try {
                $AddFontResource = Add-Type -MemberDefinition @"
                    [DllImport("gdi32.dll", CharSet = CharSet.Auto)]
                    public static extern int AddFontResource(string lpFileName);
"@ -Name "NativeMethods" -Namespace "Win32" -PassThru
                
                foreach ($font in $fontFiles) {
                    $res = $AddFontResource::AddFontResource($font.FullName)
                    if ($res -gt 0) {
                        Write-Info "Loaded font: $($font.Name) ($res variations)"
                    }
                }
            }
            catch {
                Write-Warning "Could not load portable fonts: $_"
            }
        }
        else {
            Write-Warning "No portable fonts found in $FontsDir"
        }
    }
    else {
        Write-Warning "Fonts directory not found at $FontsDir"
    }

    Write-Host ""
    if ($allOk) {
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "  Configuration Check PASSED" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
    }
    else {
        Write-Host "========================================" -ForegroundColor Red
        Write-Host "  Configuration Check FAILED" -ForegroundColor Red
        Write-Host "========================================" -ForegroundColor Red
        Write-Host ""
        Write-Info "Please run install.ps1 to fix issues"
    }
    Write-Host ""

    return $allOk
}

function Start-Workspace {
    param([string]$TargetPath)

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Blue
    Write-Host "  Starting .a AI Coding Workspace" -ForegroundColor Blue
    Write-Host "========================================" -ForegroundColor Blue
    Write-Host ""

    # Verify VSCodium exists
    if (-not (Test-Path $CodiumCmd)) {
        Write-Error "VSCodium not found at $CodiumCmd"
        Write-Info "Please run install.ps1 first"
        exit 1
    }

    # Determine workspace path
    $workspacePath = $TargetPath
    if ([string]::IsNullOrEmpty($workspacePath)) {
        $workspacePath = $RootDir
    }

    # Resolve to absolute path
    $workspacePath = Resolve-Path $workspacePath | Select-Object -ExpandProperty Path

    Write-Info "Workspace: $workspacePath"
    Write-Info "VSCodium:  $CodiumCmd"

    # Build launch arguments (portable mode)
    $launchArgs = @()

    # Portable extensions directory
    $launchArgs += "--extensions-dir"
    $launchArgs += $ExtensionsDir

    # Portable user data directory
    $launchArgs += "--user-data-dir"
    $launchArgs += $UserDataDir

    # Load .a/vscode/settings.json into portable User settings
    $sharedSettings = Join-Path $ScriptDir "vscode/settings.json"
    $targetSettingsDir = Join-Path $UserDataDir "User"
    if (Test-Path $sharedSettings) {
        if (-not (Test-Path $targetSettingsDir)) {
            New-Item -ItemType Directory -Path $targetSettingsDir -Force | Out-Null
        }
        $targetSettingsFile = Join-Path $targetSettingsDir "settings.json"
        Copy-Item -Path $sharedSettings -Destination $targetSettingsFile -Force
        Write-Info "Loaded settings from $sharedSettings"
    }

    if ($NewWindow) {
        $launchArgs += "--new-window"
    }

    # Add workspace path
    $launchArgs += $workspacePath

    # Set environment variables for extensions
    $env:CONTINUE_CONFIG_PATH = $ContinueConfig
    $env:KILO_CONFIG_PATH = $KiloConfig

    # Launch VSCodium
    Write-Host ""
    Write-Info "Launching VSCodium (portable mode)..."
    Write-Host ""

    if ($Verbose) {
        Write-Host "Command: $CodiumCmd $launchArgs" -ForegroundColor Gray
        Write-Host "Environment:" -ForegroundColor Gray
        Write-Host "  CONTINUE_CONFIG_PATH = $env:CONTINUE_CONFIG_PATH" -ForegroundColor Gray
        Write-Host "  KILO_CONFIG_PATH = $env:KILO_CONFIG_PATH" -ForegroundColor Gray
        Write-Host "Portable directories:" -ForegroundColor Gray
        Write-Host "  Extensions: $ExtensionsDir" -ForegroundColor Gray
        Write-Host "  User Data:  $UserDataDir" -ForegroundColor Gray
        Write-Host ""
    }

    try {
        & $CodiumCmd @launchArgs
    }
    catch {
        Write-Error "Failed to launch VSCodium: $_"
        exit 1
    }
}

# Main
if ($CheckOnly) {
    Test-Configuration
    exit 0
}

# Run configuration check first
$configOk = Test-Configuration

if (-not $configOk) {
    Write-Host ""
    $continue = Read-Host "Configuration issues detected. Continue anyway? (y/N)"
    if ($continue -notmatch '^[Yy]') {
        Write-Info "Exiting. Please run install.ps1 to fix configuration issues."
        exit 1
    }
}

# Start workspace
Start-Workspace -TargetPath $WorkspacePath

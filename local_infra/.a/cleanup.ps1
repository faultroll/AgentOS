# .a AI Coding Workspace - Cleanup/Uninstall Script
# Cleans up session resources and optionally removes portable directories

param(
    [switch]$FullUninstall
)

# Error handling
$ErrorActionPreference = "Continue"

# Script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Paths
$VSCodiumDir = Join-Path $ScriptDir "vscodium"
$DataDir = Join-Path $VSCodiumDir "data"
$FontsDir = Join-Path $DataDir "fonts"
$DownloadsDir = Join-Path $ScriptDir "downloads"

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Unregister-Fonts {
    if (Test-Path $FontsDir) {
        $fontFiles = Get-ChildItem -Path $FontsDir -Include "*.ttf", "*.ttc" -Recurse
        if ($fontFiles.Count -gt 0) {
            Write-Info "Unregistering portable fonts from current session..."
            try {
                $Unloader = Add-Type -MemberDefinition @"
                    [DllImport("gdi32.dll", CharSet = CharSet.Auto)]
                    public static extern int RemoveFontResource(string lpFileName);
"@ -Name "FontUnloader" -Namespace "Win32" -PassThru

                foreach ($font in $fontFiles) {
                    $res = $Unloader::RemoveFontResource($font.FullName)
                    if ($res -gt 0) {
                        Write-Success "Unloaded font: $($font.Name)"
                    }
                }
            }
            catch {
                Write-Host "Failed to unregister fonts: $_" -ForegroundColor Red
            }
        }
    }
}

function Get-BlockingProcesses {
    param([string]$TargetDir)
    try {
        $absPath = (Resolve-Path $TargetDir -ErrorAction SilentlyContinue).Path
        if (-not $absPath) { $absPath = $TargetDir }
        
        return Get-Process | Where-Object {
            try {
                $path = $_.MainModule.FileName
                $path.StartsWith($absPath, [System.StringComparison]::OrdinalIgnoreCase)
            } catch { $false }
        }
    } catch { return @() }
}

# 1. Clear session fonts
Unregister-Fonts

# 2. Full Uninstall
if ($FullUninstall) {
    Write-Info "Starting full uninstall..."
    
    $dirsToRemove = @($DownloadsDir, $VSCodiumDir)
    foreach ($dir in $dirsToRemove) {
        if (Test-Path $dir) {
            Write-Info "Removing directory: $dir"
            try {
                Remove-Item $dir -Recurse -Force -ErrorAction Stop
                Write-Success "Removed $dir"
            }
            catch {
                $blocking = Get-BlockingProcesses -TargetDir $dir
                if ($blocking.Count -gt 0) {
                    Write-Host "Removal failed! The following processes are still running from this directory:" -ForegroundColor Red
                    $blocking | Select-Object Name, Id, Path | Format-Table -AutoSize
                    Write-Host "Please close these programs and try again." -ForegroundColor Yellow
                }
                else {
                    Write-Host "Failed to remove $dir. The directory might be locked by an external tool (Explorer, Antivirus) or a shell is open inside it." -ForegroundColor Yellow
                }
            }
        }
    }

    # Remove generated scripts
    $scripts = @("launch.bat")
    foreach ($s in $scripts) {
        $p = Join-Path $ScriptDir $s
        if (Test-Path $p) {
            Remove-Item $p -Force
            Write-Success "Removed $s"
        }
    }

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  Cleanup Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
}
else {
    Write-Info "Session resources cleared. Use -FullUninstall to remove all files."
}

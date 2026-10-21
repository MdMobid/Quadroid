# ==============================================================================
#  QUADROID 3.0 // MASTER SETUP, INSTALLER, LAUNCHER AND UNINSTALL SUITE
# ==============================================================================

function Show-Header {
    Clear-Host
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "     QUADROID 3.0 - MASTER CONTROL AND SETUP CENTER" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Get-Python-Command {
    if (Test-Path "$PSScriptRoot\.venv\Scripts\python.exe") {
        return "$PSScriptRoot\.venv\Scripts\python.exe"
    }
    return "python"
}

function Get-Ollama-Command {
    $cli = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
    if (Test-Path $cli) { return $cli }
    $cli2 = "C:\Program Files\Ollama\ollama.exe"
    if (Test-Path $cli2) { return $cli2 }
    return "ollama"
}

function Set-EnvConfig {
    param(
        [string]$provider,
        [string]$model,
        [string]$mode
    )
    
    $envPath = Join-Path $PSScriptRoot ".env"
    if (-not (Test-Path $envPath)) {
        if (Test-Path "$PSScriptRoot\.env.example") {
            Copy-Item "$PSScriptRoot\.env.example" $envPath
        } else {
            return
        }
    }
    
    $content = Get-Content $envPath
    $newContent = @()
    
    foreach ($line in $content) {
        if ($line -match "^OPERATION_MODE=") {
            $newContent += "OPERATION_MODE=$mode"
        } elseif ($line -match "^LLM_PROVIDER=") {
            $newContent += "LLM_PROVIDER=$provider"
        } elseif ($line -match "^LLM_MODEL=") {
            $newContent += "LLM_MODEL=$model"
        } elseif ($line -match "^OLLAMA_MODEL=") {
            $newContent += "OLLAMA_MODEL=$model"
        } else {
            $newContent += $line
        }
    }
    
    Set-Content -Path $envPath -Value $newContent
    Write-Host "  [+] Updated .env -> Provider: $provider, Model: $model, Mode: $mode" -ForegroundColor Green
}

# -- 1. Launch Quadroid Mode Selector --
function Launch-Quadroid {
    while ($true) {
        Show-Header
        Write-Host "                    SELECT LAUNCH MODE" -ForegroundColor Cyan
        Write-Host "------------------------------------------------------------" -ForegroundColor Gray
        Write-Host "  [1] 3D Cyber Web HUD (Default - Holographic UI in Browser)" -ForegroundColor Green
        Write-Host "  [2] 100% Offline Mode (Forces Local Ollama Execution)" -ForegroundColor Yellow
        Write-Host "  [3] Interactive Terminal CLI (Fast Console Chat)" -ForegroundColor White
        Write-Host "  [4] Background Voice Daemon (Runs silently, wakes on voice)" -ForegroundColor White
        Write-Host "  [5] Classic Desktop GUI Window (Floating Orb)" -ForegroundColor White
        Write-Host "  [0] Back to Main Menu" -ForegroundColor Gray
        Write-Host ""
        
        $modeChoice = Read-Host "Select launch mode [1-5, or 0]"
        $py = Get-Python-Command
        
        switch ($modeChoice) {
            "1" {
                Show-Header
                Write-Host "Starting Quadroid 3D Web HUD on http://127.0.0.1:8000..." -ForegroundColor Green
                & $py "$PSScriptRoot\run.py"
                return
            }
            "2" {
                Show-Header
                Write-Host "Starting Quadroid in 100% Offline Mode (Ollama)..." -ForegroundColor Yellow
                & $py "$PSScriptRoot\run.py" --offline
                return
            }
            "3" {
                Show-Header
                Write-Host "Starting Quadroid Terminal CLI Mode..." -ForegroundColor Cyan
                & $py "$PSScriptRoot\run.py" --cli
                return
            }
            "4" {
                Show-Header
                Write-Host "Starting Quadroid Background Voice Daemon..." -ForegroundColor Magenta
                & $py "$PSScriptRoot\run.py" --voice-only
                return
            }
            "5" {
                Show-Header
                Write-Host "Starting Quadroid Desktop GUI..." -ForegroundColor Green
                & $py "$PSScriptRoot\run.py" --gui
                return
            }
            "0" {
                return
            }
            Default {
                Write-Host "Invalid choice. Please select 0 to 5." -ForegroundColor Yellow
                Start-Sleep -Seconds 1
            }
        }
    }
}

# -- 2. Install in .venv (Isolated) --
function Install-Venv {
    Show-Header
    Write-Host "[1/3] Creating virtual environment (.venv)..." -ForegroundColor Yellow
    python -m venv "$PSScriptRoot\.venv"
    
    Write-Host ""
    Write-Host "[2/3] Upgrading pip inside .venv..." -ForegroundColor Yellow
    & "$PSScriptRoot\.venv\Scripts\python.exe" -m pip install --upgrade pip
    
    Write-Host ""
    Write-Host "[3/3] Installing all dependencies from requirements.txt into .venv..." -ForegroundColor Yellow
    & "$PSScriptRoot\.venv\Scripts\python.exe" -m pip install -r "$PSScriptRoot\requirements.txt"
    
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "  SUCCESS: Virtual environment (.venv) is fully configured!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Read-Host "Press Enter to return to menu"
}

# -- 3. Install in Global / Local System Python --
function Install-System {
    Show-Header
    Write-Host "WARNING: Installing dependencies into System Global Python..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "[1/2] Upgrading system pip..." -ForegroundColor Yellow
    python -m pip install --upgrade pip
    
    Write-Host ""
    Write-Host "[2/2] Installing requirements.txt into system Python..." -ForegroundColor Yellow
    python -m pip install -r "$PSScriptRoot\requirements.txt"
    
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "  SUCCESS: System Python dependencies installed!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Read-Host "Press Enter to return to menu"
}

# -- 4. Ollama Installation and Model Download --
function Install-Ollama {
    param([string]$modelName = "llama3.2:3b")
    
    Show-Header
    Write-Host "[1/3] Checking / Installing Ollama..." -ForegroundColor Yellow
    winget install Ollama.Ollama --accept-package-agreements --accept-source-agreements
    
    Write-Host ""
    Write-Host "[2/3] Starting Ollama background engine..." -ForegroundColor Yellow
    $ollamaCli = Get-Ollama-Command
    
    # Check if port 11434 is responding
    $isOnline = $false
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $tcp.Connect("127.0.0.1", 11434)
        $tcp.Close()
        $isOnline = $true
    } catch {
        $isOnline = $false
    }
    
    if (-not $isOnline) {
        $ollamaApp = "$env:LOCALAPPDATA\Programs\Ollama\ollama app.exe"
        if (Test-Path $ollamaApp) {
            Start-Process $ollamaApp -ErrorAction SilentlyContinue
        } else {
            Start-Process -FilePath $ollamaCli -ArgumentList "serve" -WindowStyle Hidden -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 3
    }

    Write-Host ""
    Write-Host "[3/3] Downloading AI Model: $modelName..." -ForegroundColor Yellow
    Write-Host "      (This runs 100% offline with complete data privacy)" -ForegroundColor Gray
    
    & $ollamaCli pull $modelName
    
    Set-EnvConfig -provider "ollama" -model $modelName -mode "offline"
    
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "  SUCCESS: $modelName is ready to run 100% offline!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Read-Host "Press Enter to return to menu"
}

# -- 5. Ollama Model Manager (Delete Specific Model or Wipe All) --
function Menu-Manage-Models {
    while ($true) {
        Show-Header
        Write-Host "           OLLAMA MODEL MANAGER (FREE DISK SPACE)" -ForegroundColor Cyan
        Write-Host "------------------------------------------------------------" -ForegroundColor Gray
        
        $ollamaCli = Get-Ollama-Command
        $rawList = & $ollamaCli list 2>$null
        $modelNames = @()
        
        if ($rawList -and $rawList.Count -gt 1) {
            Write-Host "Currently Downloaded AI Models on your computer:" -ForegroundColor Yellow
            Write-Host ""
            $idx = 1
            foreach ($line in $rawList | Select-Object -Skip 1) {
                if ($line.Trim()) {
                    $tokens = $line -split '\s+'
                    if ($tokens.Count -ge 1) {
                        $mName = $tokens[0]
                        $mSize = if ($tokens.Count -ge 4) { "$($tokens[2]) $($tokens[3])" } else { "" }
                        $modelNames += $mName
                        Write-Host "  [$idx] $mName  ($mSize)" -ForegroundColor White
                        $idx++
                    }
                }
            }
            Write-Host ""
            Write-Host "------------------------------------------------------------" -ForegroundColor Gray
            Write-Host "  [A] Delete ALL models at once (Free all gigabytes of disk space)" -ForegroundColor Red
            Write-Host "  [0] Back to Menu" -ForegroundColor Gray
            Write-Host ""
            
            $sel = Read-Host "Select model number to delete, or A for all, or 0"
            
            if ($sel -eq "0" -or [string]::IsNullOrWhiteSpace($sel)) {
                return
            }
            
            if ($sel -match "^[Aa]$") {
                Write-Host "`nDeleting ALL models..." -ForegroundColor Yellow
                foreach ($m in $modelNames) {
                    & $ollamaCli rm $m
                    Write-Host "  [-] Deleted: $m" -ForegroundColor Green
                }
                $modelsDir = "$env:USERPROFILE\.ollama\models"
                if (Test-Path $modelsDir) {
                    Remove-Item -Path $modelsDir -Recurse -Force -ErrorAction SilentlyContinue
                }
                Write-Host "`nAll model weights deleted! Disk space freed." -ForegroundColor Green
                Start-Sleep -Seconds 2
            } else {
                $num = 0
                if ([int]::TryParse($sel, [ref]$num) -and $num -ge 1 -and $num -le $modelNames.Count) {
                    $target = $modelNames[$num - 1]
                    Write-Host "`nDeleting model: $target..." -ForegroundColor Yellow
                    & $ollamaCli rm $target
                    Write-Host "  [-] Successfully deleted $target!" -ForegroundColor Green
                    Start-Sleep -Seconds 2
                } else {
                    Write-Host "Invalid selection." -ForegroundColor Red
                    Start-Sleep -Seconds 1
                }
            }
        } else {
            Write-Host "No downloaded models found. (Disk space is already free!)" -ForegroundColor Green
            Write-Host ""
            Write-Host "Ollama software is installed and ready to pull any model." -ForegroundColor Gray
            Write-Host ""
            Read-Host "Press Enter to return to menu"
            return
        }
    }
}

# -- 6. Clean Uninstall and Purge Suite --
function Menu-Uninstall {
    while ($true) {
        Show-Header
        Write-Host "                    UNINSTALL AND CLEANUP SUITE" -ForegroundColor Red
        Write-Host "------------------------------------------------------------" -ForegroundColor Gray
        Write-Host "  [1] Uninstall dependencies from .venv and Delete .venv folder" -ForegroundColor White
        Write-Host "  [2] Uninstall dependencies from System/Global Python" -ForegroundColor White
        Write-Host "  [3] Delete AI Models (Select specific model or wipe all models)" -ForegroundColor Yellow
        Write-Host "  [4] Completely Uninstall Ollama App and All Files" -ForegroundColor White
        Write-Host "  [5] FULL FACTORY RESET (Delete .venv, Wipe Ollama, Clean All Caches)" -ForegroundColor Red
        Write-Host "  [0] Back to Main Menu" -ForegroundColor Gray
        Write-Host ""
        
        $uChoice = Read-Host "Select an option [0-5]"
        
        switch ($uChoice) {
            "1" {
                Show-Header
                Write-Host "Uninstalling .venv dependencies..." -ForegroundColor Yellow
                if (Test-Path "$PSScriptRoot\.venv\Scripts\python.exe") {
                    & "$PSScriptRoot\.venv\Scripts\python.exe" -m pip uninstall -r "$PSScriptRoot\requirements.txt" -y
                }
                if (Test-Path "$PSScriptRoot\.venv") {
                    Write-Host "Deleting .venv directory..." -ForegroundColor Yellow
                    Remove-Item -Path "$PSScriptRoot\.venv" -Recurse -Force -ErrorAction SilentlyContinue
                    Write-Host "  [+] .venv removed." -ForegroundColor Green
                } else {
                    Write-Host "  [-] .venv was not found." -ForegroundColor Gray
                }
                Write-Host "`nDone!" -ForegroundColor Green
                Start-Sleep -Seconds 2
            }
            "2" {
                Show-Header
                Write-Host "Uninstalling requirements.txt packages from Global/System Python..." -ForegroundColor Yellow
                python -m pip uninstall -r "$PSScriptRoot\requirements.txt" -y
                Write-Host "`nDone!" -ForegroundColor Green
                Start-Sleep -Seconds 2
            }
            "3" {
                Menu-Manage-Models
            }
            "4" {
                Show-Header
                Write-Host "Completely removing Ollama application and all files..." -ForegroundColor Yellow
                
                # Stop processes
                $procs = Get-Process -Name "ollama*", "ollama_app*" -ErrorAction SilentlyContinue
                if ($procs) {
                    foreach ($p in $procs) {
                        Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
                    }
                }
                
                # Run uninstaller
                $uninstaller = "$env:LOCALAPPDATA\Programs\Ollama\Uninstall.exe"
                if (Test-Path $uninstaller) {
                    Start-Process -FilePath $uninstaller -ArgumentList "/S" -Wait
                } else {
                    try { winget uninstall Ollama.Ollama --silent --accept-source-agreements | Out-Null } catch {}
                }
                
                # Purge files
                $dirs = @(
                    "$env:USERPROFILE\.ollama",
                    "$env:LOCALAPPDATA\Programs\Ollama",
                    "$env:LOCALAPPDATA\Ollama",
                    "$env:APPDATA\Ollama"
                )
                foreach ($d in $dirs) {
                    if (Test-Path $d) {
                        Remove-Item -Path $d -Recurse -Force -ErrorAction SilentlyContinue
                        Write-Host "  [+] Purged: $d" -ForegroundColor Green
                    }
                }
                
                # Clean PATH
                $uPath = [Environment]::GetEnvironmentVariable("Path", "User")
                if ($uPath -like "*Ollama*") {
                    $nPath = ($uPath -split ';' | Where-Object { $_ -and $_ -notlike "*Ollama*" }) -join ';'
                    [Environment]::SetEnvironmentVariable("Path", $nPath, "User")
                }
                
                Set-EnvConfig -provider "gemini" -model "gemini-2.0-flash" -mode "online"
                Write-Host "`nOllama software and models 100% removed (0 bytes left)!" -ForegroundColor Green
                Start-Sleep -Seconds 2
            }
            "5" {
                Show-Header
                Write-Host "PERFORMING FULL FACTORY RESET..." -ForegroundColor Red
                
                # 1. Clean .venv
                if (Test-Path "$PSScriptRoot\.venv") {
                    Remove-Item -Path "$PSScriptRoot\.venv" -Recurse -Force -ErrorAction SilentlyContinue
                    Write-Host "  [+] Deleted .venv" -ForegroundColor Green
                }
                
                # 2. Clean Ollama
                $procs = Get-Process -Name "ollama*", "ollama_app*" -ErrorAction SilentlyContinue
                if ($procs) { foreach ($p in $procs) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue } }
                $dirs = @("$env:USERPROFILE\.ollama", "$env:LOCALAPPDATA\Programs\Ollama", "$env:LOCALAPPDATA\Ollama", "$env:APPDATA\Ollama")
                foreach ($d in $dirs) { if (Test-Path $d) { Remove-Item -Path $d -Recurse -Force -ErrorAction SilentlyContinue } }
                
                # 3. Clean Memory and Databases
                if (Test-Path "$PSScriptRoot\Databases\memory") {
                    Remove-Item -Path "$PSScriptRoot\Databases\memory\*" -Recurse -Force -ErrorAction SilentlyContinue
                }
                
                # 4. Reset .env
                Set-EnvConfig -provider "gemini" -model "gemini-2.0-flash" -mode "online"
                
                Write-Host "`n============================================================" -ForegroundColor Green
                Write-Host "  FULL RESET COMPLETE: All dependencies, models, and caches wiped!" -ForegroundColor Green
                Write-Host "============================================================" -ForegroundColor Green
                Write-Host ""
                Read-Host "Press Enter to return to menu"
            }
            "0" { return }
            Default { Start-Sleep -Seconds 1 }
        }
    }
}

# -- Main Menu Loop --
while ($true) {
    Show-Header
    Write-Host "  [1] Launch Quadroid 3.0 (Select from 5 Modes)" -ForegroundColor Green
    Write-Host "  [2] Install Dependencies in Virtual Environment (.venv) [Recommended]" -ForegroundColor White
    Write-Host "  [3] Install Dependencies in System / Global Python" -ForegroundColor White
    Write-Host "  [4] Download Model: Qwen 2.5 7B (Offline Assistant - Best for Tools)" -ForegroundColor White
    Write-Host "  [5] Download Model: Llama 3.2 3B (Offline Assistant - Ultra-Fast 2GB)" -ForegroundColor White
    Write-Host "  [6] Manage / Delete Downloaded Models (Free Disk Space)" -ForegroundColor Yellow
    Write-Host "  [7] Switch Mode (Offline Ollama <---> Online Cloud Mode)" -ForegroundColor White
    Write-Host "  [8] Complete Uninstall and Factory Reset Suite" -ForegroundColor Red
    Write-Host "  [0] Exit" -ForegroundColor Gray
    Write-Host ""
    
    $choice = Read-Host "Select an option [0-8]"
    
    switch ($choice) {
        "1" { Launch-Quadroid }
        "2" { Install-Venv }
        "3" { Install-System }
        "4" { Install-Ollama -modelName "qwen2.5:7b" }
        "5" { Install-Ollama -modelName "llama3.2:3b" }
        "6" { Menu-Manage-Models }
        "7" {
            Show-Header
            $envPath = Join-Path $PSScriptRoot ".env"
            $curr = "online"
            if (Test-Path $envPath) {
                $line = Get-Content $envPath | Where-Object { $_ -match "^OPERATION_MODE=" }
                if ($line -match "offline") { $curr = "offline" }
            }
            
            if ($curr -eq "offline") {
                Set-EnvConfig -provider "gemini" -model "gemini-2.0-flash" -mode "online"
                Write-Host "`nSwitched Quadroid to Online Cloud Mode (Gemini)." -ForegroundColor Green
            } else {
                Set-EnvConfig -provider "ollama" -model "llama3.2:3b" -mode "offline"
                Write-Host "`nSwitched Quadroid to 100% Offline Mode (Ollama)." -ForegroundColor Green
            }
            Start-Sleep -Seconds 2
        }
        "8" { Menu-Uninstall }
        "0" {
            Write-Host "Exiting Quadroid Control Center..." -ForegroundColor Cyan
            exit
        }
        Default {
            Write-Host "Invalid choice. Please select 0 to 8." -ForegroundColor Yellow
            Start-Sleep -Seconds 1
        }
    }
}

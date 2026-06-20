# PSZ projekat - automatski setup (PowerShell)
# Koristi se: .\setup.ps1
# Proverava Python verziju, pravi venv i instalira zavisnosti.

$MIN_MAJOR = 3
$MIN_MINOR = 10

function Find-Python {
    foreach ($kandidat in @("python", "python3", "python3.11", "python3.10")) {
        $p = Get-Command $kandidat -ErrorAction SilentlyContinue
        if (-not $p) { continue }
        $ver = & $p.Source --version 2>&1
        if ($ver -match "Python (\d+)\.(\d+)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            if ($major -gt $MIN_MAJOR -or ($major -eq $MIN_MAJOR -and $minor -ge $MIN_MINOR)) {
                return $p.Source
            }
        }
    }
    return $null
}

Write-Host ""
Write-Host "=== PSZ projekat setup ===" -ForegroundColor Cyan

# 1) Pronadi Python >= 3.10
$python = Find-Python
if (-not $python) {
    Write-Host ""
    Write-Host "GRESKA: Python $MIN_MAJOR.$MIN_MINOR+ nije pronadjen." -ForegroundColor Red
    Write-Host "Skini Python 3.11 sa https://www.python.org/downloads/ i ponovo pokreni setup." -ForegroundColor Yellow
    exit 1
}
$verStr = & $python --version 2>&1
Write-Host "OK Python: $verStr ($python)" -ForegroundColor Green

# 2) Napravi .venv ako ne postoji ili je pogresna verzija
$venvPython = ".venv\Scripts\python.exe"
$praviVenv = $true
if (Test-Path $venvPython) {
    $venvVer = & $venvPython --version 2>&1
    if ($venvVer -match "Python (\d+)\.(\d+)") {
        $vMaj = [int]$Matches[1]; $vMin = [int]$Matches[2]
        if ($vMaj -gt $MIN_MAJOR -or ($vMaj -eq $MIN_MAJOR -and $vMin -ge $MIN_MINOR)) {
            Write-Host "OK .venv vec postoji ($venvVer)" -ForegroundColor Green
            $praviVenv = $false
        } else {
            Write-Host "UPOZ: .venv ima $venvVer - brisem i pravim novi..." -ForegroundColor Yellow
            Remove-Item -Recurse -Force .venv
        }
    }
}
if ($praviVenv) {
    Write-Host "Pravim .venv sa $python ..." -ForegroundColor Cyan
    & $python -m venv .venv
    if (-not $?) { Write-Host "GRESKA pri kreiranju venv!" -ForegroundColor Red; exit 1 }
    Write-Host "OK .venv kreiran" -ForegroundColor Green
}

# 3) Instaliraj zavisnosti
Write-Host "Instaliram zavisnosti (pip install -r requirements.txt)..." -ForegroundColor Cyan
& .venv\Scripts\pip install -r requirements.txt --quiet
if (-not $?) { Write-Host "GRESKA pri instalaciji!" -ForegroundColor Red; exit 1 }
Write-Host "OK zavisnosti instalirane" -ForegroundColor Green

# 4) Inicijalizuj SQLite bazu
Write-Host "Inicijalizujem SQLite bazu..." -ForegroundColor Cyan
& .venv\Scripts\python kod\db_init.py
if (-not $?) { Write-Host "GRESKA pri inicijalizaciji baze!" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "=== Setup gotov! ===" -ForegroundColor Green
Write-Host ""
Write-Host "Aktiviraj venv i pokreni projekat:" -ForegroundColor Cyan
Write-Host "  .venv\Scripts\activate" -ForegroundColor White
Write-Host "  make discover" -ForegroundColor White
Write-Host "  make test" -ForegroundColor White
Write-Host ""

# PSZ projekat - automatski setup (PowerShell)
# Koristi se: .\setup.ps1
# Proverava Python verziju, pravi venv i instalira zavisnosti.

$MIN_MAJOR = 3
$MIN_MINOR = 10

function Find-Python {
    # Eksplicitne putanje (conda/venv wrapperi ne blokiraju ove)
    $explicitni = @(
        "C:\Python311\python.exe",
        "C:\Python310\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe"
    )
    $kandidati = $explicitni + @("python", "python3", "py")
    foreach ($kandidat in $kandidati) {
        try {
            $ver = & $kandidat --version 2>&1
        } catch { continue }
        if ($ver -match "Python (\d+)\.(\d+)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            if ($major -gt $MIN_MAJOR -or ($major -eq $MIN_MAJOR -and $minor -ge $MIN_MINOR)) {
                return $kandidat
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
& .venv\Scripts\pip install -r requirements.txt
if (-not $?) { Write-Host "GRESKA pri instalaciji!" -ForegroundColor Red; exit 1 }
Write-Host "OK zavisnosti instalirane" -ForegroundColor Green

# 4) .env fajl (kopiraj iz .env.example ako ne postoji)
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Kreiran .env iz .env.example — UPISI svoju PostgreSQL lozinku u .env (DB_PASSWORD)." -ForegroundColor Yellow
}

# 5) Inicijalizuj PostgreSQL bazu (kreira bazu + tabele)
Write-Host "Inicijalizujem PostgreSQL bazu..." -ForegroundColor Cyan
& .venv\Scripts\python kod\db_init.py
if (-not $?) {
    Write-Host ""
    Write-Host "Baza nije inicijalizovana. Najcesci uzrok: PostgreSQL nije instaliran/pokrenut." -ForegroundColor Yellow
    Write-Host "1. Instaliraj PostgreSQL: https://www.postgresql.org/download/windows/" -ForegroundColor White
    Write-Host "2. Upisi DB_PASSWORD (lozinka 'postgres' korisnika) u .env" -ForegroundColor White
    Write-Host "3. Ponovo pokreni: .\setup.ps1" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "=== Setup gotov! ===" -ForegroundColor Green
Write-Host ""
Write-Host "Pokreni projekat:" -ForegroundColor Cyan
Write-Host "  .\run.ps1            (interaktivni meni)" -ForegroundColor White
Write-Host "  .\run.ps1 crawl      (prikupi podatke)" -ForegroundColor White
Write-Host "  .\run.ps1 test       (testovi)" -ForegroundColor White
Write-Host ""

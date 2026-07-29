# PSZ projekat - pakovanje za predaju na server fakulteta (Windows)
# Windows ekvivalent skripte alati\spakuj.sh
#
# Pravi ZIP u formatu koji zahteva postavka: Indeks_Ime_Prezime.zip
# sa folderima \kod \baza \izveštaj. Prvo generise SQL dump-ove baze
# da \baza sadrzi PODATKE (ne samo seme). Izbacuje .env, __pycache__, *.pyc.
#
# Koristi se:
#   .\package.ps1 <Indeks> <Ime> <Prezime>
#   .\package.ps1 2023_0123 Vuk Prezime
# Bez argumenata pravi Sea-Of-Sorrow.zip (za brzu proveru sadrzaja).

param(
    [Parameter(Position=0)][string]$Indeks = "",
    [Parameter(Position=1)][string]$Ime = "",
    [Parameter(Position=2)][string]$Prezime = ""
)

$ErrorActionPreference = "Stop"
$koren = $PSScriptRoot
Set-Location $koren

Write-Host ""
Write-Host "=== PSZ projekat - pakovanje za predaju ===" -ForegroundColor Cyan

# Naziv arhive
if ($Indeks -and $Ime -and $Prezime) {
    $naziv = "${Indeks}_${Ime}_${Prezime}"
} else {
    $naziv = "Sea-Of-Sorrow"
    Write-Host "UPOZ: nije zadat indeks/ime/prezime -> koristim '$naziv.zip'" -ForegroundColor Yellow
    Write-Host "      Za predaju: .\package.ps1 <Indeks> <Ime> <Prezime>" -ForegroundColor Yellow
}

$staging = Join-Path $env:TEMP $naziv
$zipPut = Join-Path $koren "$naziv.zip"

# 1) Generisi SQL dump-ove baze pre pakovanja (da \baza ima podatke)
$venvPy = ".venv\Scripts\python.exe"
$py = if (Test-Path $venvPy) { $venvPy } else { "python" }
Write-Host "Generisem SQL dump-ove baze..." -ForegroundColor Cyan
& $py kod\db_dump.py
if (-not $?) {
    Write-Host "UPOZ: db_dump nije uspeo (PostgreSQL pokrenut?). \baza ce imati samo seme." -ForegroundColor Yellow
}

# 2) Cist staging folder
if (Test-Path $staging) { Remove-Item -Recurse -Force $staging }
New-Item -ItemType Directory -Path $staging | Out-Null

# 3) Kopiraj samo tri foldera koje postavka trazi (izveštaj sa ć u arhivi)
Write-Host "Kopiram \kod \baza \izveštaj..." -ForegroundColor Cyan
Copy-Item -Recurse "kod"      (Join-Path $staging "kod")
Copy-Item -Recurse "baza"     (Join-Path $staging "baza")
Copy-Item -Recurse "izvestaj" (Join-Path $staging ([char]0x0069 + "zve" + [char]0x0161 + "taj"))  # "izveštaj"

# 4) Izbaci smece i tajne iz staging-a
Get-ChildItem $staging -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem $staging -Recurse -File -Include "*.pyc","*.pyo" | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem $staging -Recurse -File -Filter ".env" | Remove-Item -Force -ErrorAction SilentlyContinue

# 5) Provera: da li \baza sadrzi dump-ove?
$dumpovi = Get-ChildItem (Join-Path $staging "baza") -Filter "*_dump.sql" -ErrorAction SilentlyContinue
if (-not $dumpovi) {
    Write-Host "UPOZ: \baza nema *_dump.sql (samo seme). Pokreni PostgreSQL pa ponovo spakuj." -ForegroundColor Yellow
}

# 6) Napravi ZIP
Write-Host "Pravim ZIP..." -ForegroundColor Cyan
if (Test-Path $zipPut) { Remove-Item -Force $zipPut }
Compress-Archive -Path $staging -DestinationPath $zipPut -CompressionLevel Optimal

Remove-Item -Recurse -Force $staging

$vel = [math]::Round((Get-Item $zipPut).Length / 1MB, 2)
Write-Host ""
Write-Host "=== Gotovo! ===" -ForegroundColor Green
Write-Host "  ZIP: $zipPut" -ForegroundColor White
Write-Host "  Velicina: $vel MB" -ForegroundColor White
Write-Host ""

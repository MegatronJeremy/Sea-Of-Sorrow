# PSZ projekat - pokretanje komandi
# Koristi se: .\run.ps1 [komanda] [opcije]
# Bez argumenta: pokazuje interaktivni meni

param(
    [Parameter(Position=0)]
    [string]$Komanda = "",
    [string]$Kat = "",
    [int]$Workers = 0,
    [string]$Izvori = ""
)

$VENV = ".venv\Scripts\python.exe"

function Check-Venv {
    if (-not (Test-Path $VENV)) {
        Write-Host "GRESKA: .venv ne postoji. Pokreni: .\setup.ps1" -ForegroundColor Red
        exit 1
    }
}

function Run-Python {
    param([string]$Skript, [string[]]$Args = @())
    Check-Venv
    & $VENV $Skript @Args
}

function Show-Menu {
    Write-Host ""
    Write-Host "=== PSZ projekat ===" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  [1] setup      - instaliraj zavisnosti + inicijalizuj bazu" -ForegroundColor White
    Write-Host "  [2] discover   - proveri kategorije na sajtu (bez upisa)" -ForegroundColor White
    Write-Host "  [3] crawl      - pun crawl svih kategorija" -ForegroundColor White
    Write-Host "  [4] analiza    - cisti podatke + izvezi u Excel" -ForegroundColor White
    Write-Host "  [5] viz        - generisi grafike (PNG)" -ForegroundColor White
    Write-Host "  [6] app        - pokreni GUI aplikaciju" -ForegroundColor White
    Write-Host "  [7] test       - automatski testovi" -ForegroundColor White
    Write-Host "  [8] debug      - provera okruzenja" -ForegroundColor White
    Write-Host "  [9] debug-db   - provera okruzenja + baze" -ForegroundColor White
    Write-Host " [10] db-dump   - izvoz baza u baza\*_dump.sql (za predaju)" -ForegroundColor White
    Write-Host " [11] audit     - differential audit GUI logike" -ForegroundColor White
    Write-Host "  [0] izlaz" -ForegroundColor DarkGray
    Write-Host ""
    $izbor = Read-Host "Izbor"
    return $izbor
}

function Run-Komanda {
    param([string]$Cmd)
    switch ($Cmd) {
        { $_ -in "1","setup" } {
            & .\setup.ps1
        }
        { $_ -in "2","discover" } {
            Check-Venv
            Write-Host "Trazim kategorije na sajtu..." -ForegroundColor Cyan
            $da = @(); if ($Workers -gt 0) { $da += "--workers", $Workers }
            & $VENV kod\01_crawler\crawler.py --discover @da
        }
        { $_ -in "3","crawl" } {
            Check-Venv
            # Paralelni scrape sa svih izvora (gigatron + tehnomanija po defaultu)
            $da = @()
            if ($Izvori) { $da += "--izvori", $Izvori }
            Write-Host "Paralelni scrape sa svih izvora..." -ForegroundColor Cyan
            & $VENV kod\01_crawler\scrape.py @da
        }
        { $_ -in "4","analiza" } {
            Check-Venv
            Write-Host "Ciscenje podataka..." -ForegroundColor Cyan
            & $VENV kod\02_analiza\cisti_podatke.py
            Write-Host "Izvoz upita u Excel..." -ForegroundColor Cyan
            & $VENV kod\02_analiza\izvezi_upite.py
        }
        { $_ -in "5","viz" } {
            Check-Venv
            Write-Host "Generisanje grafika..." -ForegroundColor Cyan
            & $VENV kod\03_vizuelizacija\generisi_grafike.py
        }
        { $_ -in "6","app" } {
            Check-Venv
            Write-Host "Pokretanje GUI aplikacije..." -ForegroundColor Cyan
            & $VENV kod\aplikacija\app.py
        }
        { $_ -in "7","test" } {
            Check-Venv
            Write-Host "Pokretanje testova..." -ForegroundColor Cyan
            & $VENV -m pytest
        }
        { $_ -in "8","debug" } {
            Check-Venv
            & $VENV kod\debug.py
        }
        { $_ -in "9","debug-db" } {
            Check-Venv
            & $VENV kod\debug.py --db --verbose
        }
        { $_ -in "10","db-dump","dump" } {
            Check-Venv
            Write-Host "Izvoz baza u baza\*_dump.sql..." -ForegroundColor Cyan
            & $VENV kod\db_dump.py
        }
        { $_ -in "11","audit" } {
            Check-Venv
            Write-Host "Differential audit GUI logike (varirani ulazi -> izlaz)..." -ForegroundColor Cyan
            & $VENV alati\audit_gui.py
        }
        { $_ -in "0","izlaz","exit","q" } {
            Write-Host "Dovidjenja!" -ForegroundColor DarkGray
            exit 0
        }
        default {
            Write-Host "Nepoznata komanda: $Cmd" -ForegroundColor Red
            Write-Host "Dostupne komande: setup, discover, crawl, analiza, viz, app, test, debug, debug-db, db-dump, audit" -ForegroundColor Yellow
            exit 1
        }
    }
}

# Direktno izvrsavanje ako je prosledjena komanda
if ($Komanda) {
    Run-Komanda $Komanda
} else {
    # Interaktivni meni
    while ($true) {
        $izbor = Show-Menu
        if ($izbor -in @("0","izlaz","exit","q")) { Write-Host "Dovidjenja!" -ForegroundColor DarkGray; break }
        Run-Komanda $izbor
        Write-Host ""
        Write-Host "Pritisni Enter za nastavak..." -ForegroundColor DarkGray
        Read-Host | Out-Null
    }
}

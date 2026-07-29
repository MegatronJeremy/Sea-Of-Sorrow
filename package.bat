@echo off
REM PSZ projekat - pakovanje u ZIP za predaju (Windows .bat omotac)
REM Koristi se: package.bat [Indeks Ime Prezime]
REM Primer:     package.bat 2023_0123 Vuk Prezime
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0package.ps1" %*

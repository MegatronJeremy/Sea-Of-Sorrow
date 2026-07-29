@echo off
REM PSZ projekat - pokretanje (Windows .bat omotac oko run.ps1)
REM Koristi se: run.bat [komanda] [opcije]   (bez argumenta -> meni)
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run.ps1" %*

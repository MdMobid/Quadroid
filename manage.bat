@echo off
title Quadroid 3.0 Control Center
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0manage.ps1"
if %errorlevel% neq 0 pause

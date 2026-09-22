@echo off
cd /d "%~dp0"
python -m PyInstaller --noconfirm --onefile --windowed --name NyakoASCII --icon "assets\nyako.ico" --collect-submodules art --collect-all webview --add-data "web;web" --add-data "assets;assets" main.py

$ErrorActionPreference = 'Stop'

Write-Host 'Installing/updating PyInstaller...'
python -m pip install --upgrade pyinstaller

Write-Host 'Building Hangman executable...'
python -m PyInstaller --noconfirm --windowed --name Hangman app.py

Write-Host 'Build complete. Output: dist/Hangman/'

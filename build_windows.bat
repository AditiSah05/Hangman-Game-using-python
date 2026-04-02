@echo off
setlocal

echo Installing/updating PyInstaller...
python -m pip install --upgrade pyinstaller
if errorlevel 1 (
  echo Failed to install PyInstaller.
  exit /b 1
)

echo Building Hangman executable...
python -m PyInstaller --noconfirm --windowed --name Hangman app.py
if errorlevel 1 (
  echo Build failed.
  exit /b 1
)

echo Build complete. Check dist\Hangman\ for the executable.
endlocal

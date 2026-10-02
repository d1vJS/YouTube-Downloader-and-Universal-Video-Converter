@echo off
title Dependency Setup
echo ==========================================
echo   Installing Python, yt-dlp, and ffmpeg...
echo ==========================================
echo.

set HAS_WINGET=0
where winget >nul 2>nul
if %errorlevel%==0 set HAS_WINGET=1

set PY=
python --version >nul 2>nul
if %errorlevel%==0 set PY=python
if not defined PY py --version >nul 2>nul
if not defined PY if %errorlevel%==0 set PY=py

if defined PY goto PYOK

echo [1/3] Python not found, installing...
if %HAS_WINGET%==0 goto NOWINGET_PY
winget install --id Python.Python.3.12 -e --accept-source-agreements --accept-package-agreements
echo.
echo ==========================================
echo   Python installed. Close this window
echo   and double-click this .bat file AGAIN.
echo ==========================================
pause
exit /b 0

:NOWINGET_PY
echo ERROR: winget not found. Install Python manually from python.org.
echo Make sure to check the "Add python.exe to PATH" box during installation.
pause
exit /b 1

:PYOK
echo [1/3] Python is already installed, skipping.
echo.
echo [2/3] Installing / updating yt-dlp...
%PY% -m pip install -U yt-dlp
if errorlevel 1 goto PIPFAIL
echo.

where ffmpeg >nul 2>nul
if %errorlevel%==0 goto FFOK
if %HAS_WINGET%==0 goto NOWINGET_FF
echo [3/3] Installing ffmpeg...
winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
goto DONE

:FFOK
echo [3/3] ffmpeg is already installed, skipping.
goto DONE

:PIPFAIL
echo ERROR: Failed to install yt-dlp.
pause
exit /b 1

:NOWINGET_FF
echo ERROR: winget not found. You need to install ffmpeg manually.
pause
exit /b 1

:DONE
echo.
echo ==========================================
echo   Done! Close and reopen your programs.
echo ==========================================
pause
@echo off
title Maries YouTube MP3 Downloader

REM Pruefen ob Python installiert ist
python --version >nul 2>&1
if errorlevel 1 (
    echo Python ist nicht installiert!
    echo Bitte Python von https://www.python.org/downloads/ installieren.
    echo WICHTIG: Bei der Installation "Add Python to PATH" ankreuzen!
    pause
    exit /b 1
)

REM yt-dlp installieren falls noetig
pip show yt-dlp >nul 2>&1
if errorlevel 1 (
    echo Installiere yt-dlp...
    pip install yt-dlp
)

REM FFmpeg pruefen
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo.
    echo HINWEIS: FFmpeg wurde nicht gefunden.
    echo Fuer MP3-Konvertierung wird FFmpeg benoetigt.
    echo Download: https://www.gyan.dev/ffmpeg/builds/
    echo Die ffmpeg.exe in diesen Ordner legen oder in PATH installieren.
    echo.
    pause
)

REM App starten
python "%~dp0youtube2mp3.py"

@echo off
:: tapmusic.bat — wrapper to run tapmusic.py on Windows
:: Place this file anywhere; edit the paths below to match your system.

:: Path to your Python executable (or virtual env)
set PYTHON=python

:: Path to the script (edit this)
set SCRIPT=C:\path\to\LastfmAutomacao\tapmusic.py

:: Working directory (same folder as tapmusic.py)
set WORKDIR=C:\path\to\LastfmAutomacao

cd /d "%WORKDIR%"
"%PYTHON%" "%SCRIPT%"

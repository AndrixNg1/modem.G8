@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
    set "PY=py -3"
) else (
    set "PY=python"
)
%PY% --version || goto erreur
%PY% -m unittest discover -s tests -v > mesures\tests.txt 2>&1
set "TESTCODE=%ERRORLEVEL%"
type mesures\tests.txt
if not "%TESTCODE%"=="0" goto erreur
%PY% main.py crc || goto erreur
%PY% main.py mesures || goto erreur
echo.
echo Termine. Consultez le dossier mesures et le dossier reception.
pause
exit /b 0
:erreur
echo Echec. Consultez les erreurs ci-dessus et le README.
pause
exit /b 1

@echo off
chcp 65001 >nul
echo Überprüfe, ob benötigte Bibliotheken installiert sind...

REM Prüfe, ob PyInstaller verfügbar ist
pyinstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo PyInstaller ist nicht installiert!
    echo.
    SET /P INSTALL="Möchten Sie PyInstaller jetzt installieren? (J/N): "
    if /I "%INSTALL%"=="J" (
        echo Installiere PyInstaller...
        pip install pyinstaller
        if %errorlevel% neq 0 (
            echo Fehler bei der Installation von PyInstaller!
            echo Bitte installieren Sie PyInstaller manuell mit 'pip install pyinstaller'
            pause
            exit /b 1
        )
        echo PyInstaller wurde erfolgreich installiert.
    ) else (
        echo PyInstaller ist erforderlich, um die ausführbare Datei zu erstellen.
        echo Bitte installieren Sie PyInstaller mit 'pip install pyinstaller'
        pause
        exit /b 1
    )
)

REM Prüfe, ob reportlab verfügbar ist
pip show reportlab >nul 2>&1
if %errorlevel% neq 0 (
    echo ReportLab ist nicht installiert!
    echo.
    SET /P INSTALL="Möchten Sie ReportLab jetzt installieren? (J/N):"
    if /I "%INSTALL%"=="J" (
        echo Installiere ReportLab...
        pip install reportlab
        if %errorlevel% neq 0 (
            echo Fehler bei der Installation von ReportLab!
            echo Bitte installieren Sie ReportLab manuell mit 'pip install reportlab'
            echo Der Build wird fortgesetzt, aber die PDF-Export-Funktion wird nicht verfügbar sein.
            pause
        ) else (
            echo ReportLab wurde erfolgreich installiert.
        )
    ) else (
        echo Der Build wird fortgesetzt, aber die PDF-Export-Funktion wird nicht verfügbar sein.
    )
)

echo Erstelle ausführbare Datei mit PyInstaller...
cd /d "%~dp0"
pyinstaller --onefile -w Beurteilungsbogen.py
echo.
echo Build abgeschlossen! Die ausführbare Datei befindet sich im "dist"-Verzeichnis.
pause

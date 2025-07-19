# Backup & Wiederherstellung - Benutzeranleitung

## Übersicht

Die Schülerverwaltungsanwendung verfügt über eine umfassende Backup- und Wiederherstellungsfunktionalität, um Ihre Daten zu schützen und bei Bedarf wiederherzustellen.

## Funktionen

### 1. Datenbank-Informationen anzeigen

Im Dialog werden folgende Informationen angezeigt:
- **Anzahl Schüler**: Gesamtzahl der gespeicherten Schüler
- **Anzahl Arbeitstitel**: Gesamtzahl der Arbeitstitel aller Schüler
- **Anzahl Klassen**: Anzahl der verschiedenen Klassen
- **Dateigröße**: Größe der Datenbankdatei in KB
- **Letzte Änderung**: Zeitpunkt der letzten Datenbankänderung
- **Pfad**: Vollständiger Pfad zur Datenbankdatei

### 2. Backup erstellen

#### SQLite-Backup
- **Funktion**: Erstellt eine exakte Kopie der SQLite-Datenbankdatei
- **Dateityp**: `.db` (SQLite-Datenbank)
- **Verwendung**: Kann direkt als Wiederherstellungsquelle verwendet werden
- **Automatische Benennung**: `students_backup_YYYYMMDD_HHMMSS.db`

#### JSON-Export
- **Funktion**: Exportiert alle Daten in ein menschenlesbares JSON-Format
- **Dateityp**: `.json`
- **Verwendung**: Für manuelle Dateninspektion, externe Verarbeitung oder als Archiv
- **Struktur**:
  ```json
  {
    "metadata": {
      "export_date": "2025-01-19T...",
      "database_path": "...",
      "student_count": 123,
      "work_title_count": 456
    },
    "students": [...],
    "work_titles": [...]
  }
  ```

### 3. Backup wiederherstellen

#### Sicherheitsmaßnahmen
- **Doppelte Bestätigung**: Zwei Bestätigungsdialoge verhindern versehentliche Wiederherstellung
- **Automatische Sicherung**: Vor Wiederherstellung wird automatisch eine Sicherheitskopie der aktuellen DB erstellt
- **Rollback bei Fehlern**: Bei Problemen wird die ursprüngliche Datenbank automatisch wiederhergestellt
- **Validierung**: Backups werden vor und nach der Wiederherstellung validiert

#### Ablauf
1. Backup-Datei auswählen (`.db`-Datei)
2. Erste Warnung bestätigen
3. Letzte Bestätigung geben
4. Wiederherstellung wird durchgeführt
5. Anwendung wird automatisch aktualisiert

## Technische Details

### Backup-Validierung
Jedes Backup wird auf folgende Kriterien geprüft:
- **Datenbankintegrität**: SQLite PRAGMA integrity_check
- **Tabellenstruktur**: Vorhandensein aller erforderlichen Tabellen
- **Spaltenstruktur**: Korrekte Spalten in students und work_titles Tabellen

### Fehlerbehandlung
- **SQLite-Fehler**: Spezifische Behandlung von Datenbankfehlern
- **Dateisystem-Fehler**: Behandlung von Pfad- und Zugriffsproblemen
- **Validierungsfehler**: Überprüfung der Backup-Integrität
- **Rollback-Mechanismus**: Automatische Wiederherstellung bei Fehlern

### Unterstützte Dateiformate
- **Backup**: `.db` (SQLite-Datenbank)
- **Export**: `.json` (JSON-Format)
- **Alle Dateien**: `*.*` (als Fallback-Option)

## Anwendung

### Backup erstellen (Empfohlen vor wichtigen Änderungen)

1. Hauptfenster → **"Backup & Wiederherstellung"** klicken
2. Im Bereich **"Backup erstellen"**:
   - **"Durchsuchen..."** klicken
   - Speicherort und Dateiname wählen
   - **"Backup erstellen"** klicken
3. Erfolgsmeldung abwarten

### JSON-Export (für Archivierung)

1. Backup-Dialog öffnen
2. **"Als JSON exportieren"** klicken
3. Speicherort wählen
4. Export wird erstellt

### Wiederherstellung (Nur im Notfall!)

⚠️ **WARNUNG**: Überschreibt ALLE aktuellen Daten!

1. Backup-Dialog öffnen
2. Im Bereich **"Backup wiederherstellen"**:
   - **"Durchsuchen..."** klicken
   - Backup-Datei (`.db`) auswählen
   - **"Backup wiederherstellen"** klicken
3. **Beide Warnungen bestätigen**
4. Wiederherstellung abwarten
5. Anwendung wird automatisch aktualisiert

## Best Practices

### Regelmäßige Backups
- **Vor wichtigen Arbeiten**: Immer ein Backup erstellen
- **Wöchentlich**: Regelmäßige Backups zur Sicherheit
- **Vor Updates**: Backup vor Programmaktualisierungen

### Backup-Speicherung
- **Externe Speicher**: USB-Stick, externe Festplatte
- **Cloud-Speicher**: OneDrive, Dropbox, Google Drive
- **Netzwerklaufwerke**: Zentrale Speicherorte
- **Mehrere Kopien**: An verschiedenen Orten aufbewahren

### Backup-Benennung
Die automatische Benennung folgt dem Schema:
```
students_backup_YYYYMMDD_HHMMSS.db
students_export_YYYYMMDD_HHMMSS.json
```

Beispiel: `students_backup_20250119_143022.db`

### Backup-Verwaltung
- **Alte Backups**: Regelmäßig nicht mehr benötigte Backups löschen
- **Backup-Tests**: Gelegentlich Backups auf Funktionsfähigkeit prüfen
- **Dokumentation**: Notizen zu wichtigen Backups führen

## Fehlerbehebung

### Häufige Probleme

#### "Backup-Datei nicht gefunden"
- Pfad korrekt eingegeben?
- Datei wurde verschoben/gelöscht?
- Berechtigung zum Zugriff vorhanden?

#### "Backup-Validierung fehlgeschlagen"
- Datei beschädigt?
- Falsches Dateiformat?
- Unvollständiges Backup?

#### "Fehler beim Erstellen des Backups"
- Genug Speicherplatz vorhanden?
- Schreibberechtigung für Zielordner?
- Dateiname korrekt?

### Notfall-Wiederherstellung

Falls die Anwendung nicht mehr startet:
1. Originale `students.db` durch Backup ersetzen
2. Anwendung neu starten
3. Daten überprüfen

## Sicherheitshinweise

### Vertraulichkeit
- Backups enthalten alle Schülerdaten
- Sichere Speicherung erforderlich
- Zugriffsbeschränkungen beachten

### Datenschutz
- DSGVO-konforme Speicherung
- Regelmäßige Löschung alter Backups
- Verschlüsselung bei Cloud-Speicherung

### Integrität
- Nur vertrauenswürdige Backups verwenden
- Backups vor Manipulation schützen
- Regelmäßige Validierung durchführen

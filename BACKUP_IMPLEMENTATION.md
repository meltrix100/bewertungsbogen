# Backup/Restore-Funktionalität - Implementierungsübersicht

## ✅ Implementierte Funktionen

### 1. DatabaseManager Erweiterungen

#### Backup-Funktionen
- `create_backup(backup_path)` - Erstellt SQLite-Backup mit automatischer Validierung
- `export_to_json(export_path)` - Exportiert alle Daten als JSON
- `get_database_info()` - Liefert umfassende Datenbank-Statistiken

#### Wiederherstellungs-Funktionen  
- `restore_backup(backup_path)` - Sichere Wiederherstellung mit Rollback
- `_validate_backup(backup_path)` - Umfassende Backup-Validierung
- `_validate_database_structure()` - Strukturvalidierung nach Wiederherstellung

#### Sicherheitsfeatures
- Automatische Backup-Erstellung vor Wiederherstellung
- Rollback bei Fehlern während Wiederherstellung
- SQLite PRAGMA integrity_check Validierung
- Vollständige Struktur- und Inhaltsvalidierung

### 2. BackupRestoreDialog (Neue UI-Klasse)

#### Hauptbereiche
1. **Datenbank-Informationen**
   - Schüleranzahl, Arbeitstitel, Klassen
   - Dateigröße und letzte Änderung
   - Datenbankpfad-Anzeige
   - "Informationen aktualisieren" Button

2. **Backup erstellen**
   - Pfad-Auswahl mit Datei-Browser
   - Automatische Zeitstempel-Benennung
   - SQLite-Backup-Erstellung
   - JSON-Export-Option

3. **Backup wiederherstellen**
   - Sicherheitswarnung prominent angezeigt
   - Datei-Browser für Backup-Auswahl
   - Doppelte Bestätigungsdialoge
   - Fortschrittsanzeige während Wiederherstellung

#### UI-Features
- Farbkodierte Bereiche (Grün/Blau/Rot)
- Responsive Layout mit GroupBoxes
- Große, gut lesbare Buttons
- Statusanzeigen und Fortschritts-Feedback

### 3. MainWindow Integration

#### Neuer Button
- "Backup & Wiederherstellung" Button in der Hauptleiste
- Lila Hintergrund (#9C27B0) für eindeutige Identifikation
- Integration zwischen Klassen- und PDF-Export-Buttons

#### Dialog-Integration
- `open_backup_restore()` Methode
- Automatische UI-Aktualisierung nach Wiederherstellung
- Fehlerbehandlung mit spezifischen Fehlermeldungen

## 🔧 Technische Details

### Dateiformate
- **Backup**: `.db` (SQLite-Datenbank, 1:1 Kopie)
- **Export**: `.json` (Strukturiertes JSON mit Metadaten)

### Validierung
```python
# Integritätsprüfung
PRAGMA integrity_check

# Strukturvalidierung
- Tabellen: students, work_titles
- Spalten: Vollständige Überprüfung aller erforderlichen Felder
- Fremdschlüssel: PRAGMA foreign_keys = ON
```

### Zeitstempel-Format
```
students_backup_YYYYMMDD_HHMMSS.db
students_export_YYYYMMDD_HHMMSS.json
```

### JSON-Struktur
```json
{
  "metadata": {
    "export_date": "ISO-Format",
    "database_path": "Vollständiger Pfad",
    "student_count": 123,
    "work_title_count": 456
  },
  "students": [
    {
      "id": 1,
      "firstname": "...",
      "lastname": "...",
      "class": "...",
      "soziale_kompetenz": "...",
      "aktive_mitarbeit": "...",
      "sauberkeit": "...",
      "material": "...",
      "puenktlichkeit": "...",
      "kommentar": "..."
    }
  ],
  "work_titles": [
    {
      "id": 1,
      "student_id": 1,
      "title": "...",
      "note": "...",
      "soziale_kompetenz": "...",
      "aktive_mitarbeit": "...",
      "sauberkeit": "...",
      "material": "...",
      "puenktlichkeit": "...",
      "kommentar": "..."
    }
  ]
}
```

## 🛡️ Sicherheitsmaßnahmen

### Vor Wiederherstellung
1. Automatische Sicherung der aktuellen Datenbank
2. Backup-Validierung (Integrität und Struktur)
3. Doppelte Benutzerbestätigung

### Während Wiederherstellung
1. Transaktionale Durchführung
2. Kontinuierliche Validierung
3. Sofortiger Rollback bei Fehlern

### Nach Wiederherstellung
1. Strukturvalidierung der wiederhergestellten DB
2. Funktionstest der Datenbankverbindung
3. Automatische UI-Aktualisierung

## 📋 Fehlercodes und Behandlung

### SQLite-Fehler
- `sqlite3.Error` - Spezifische Datenbankfehler
- Verbindungsfehler, Schreibfehler, Constraints

### Dateisystem-Fehler
- `FileNotFoundError` - Backup-Datei nicht gefunden
- `PermissionError` - Keine Schreibberechtigung
- `OSError` - Allgemeine Dateisystemfehler

### Validierungsfehler
- `ValueError` - Strukturfehler im Backup
- `RuntimeError` - Kritische Wiederherstellungsfehler

### UI-Fehler
- `AttributeError` - UI-Komponentenfehler
- Graceful Degradation mit Fehlermeldungen

## 🔄 Workflow-Integration

### Backup-Erstellung
```
Benutzer → Button → Dialog → Pfad wählen → Backup erstellen → Validierung → Erfolgsmeldung
```

### Wiederherstellung
```
Benutzer → Button → Dialog → Backup wählen → Warnung 1 → Warnung 2 → 
Sicherung → Wiederherstellung → Validierung → UI-Update → Erfolgsmeldung
```

### JSON-Export
```
Benutzer → Button → JSON-Export → Pfad wählen → Export → Erfolgsmeldung
```

## 📊 Datenbank-Informationen

### Angezeigte Statistiken
- **Schüler**: `SELECT COUNT(*) FROM students`
- **Arbeitstitel**: `SELECT COUNT(*) FROM work_titles`
- **Klassen**: `SELECT COUNT(DISTINCT class) FROM students WHERE class IS NOT NULL`
- **Dateigröße**: `os.path.getsize(db_path)`
- **Letzte Änderung**: `os.path.getmtime(db_path)`

## 🎯 Benutzerfreundlichkeit

### Design-Prinzipien
- **Klarheit**: Eindeutige Beschriftungen und Warnungen
- **Sicherheit**: Mehrfache Bestätigungen für kritische Aktionen
- **Feedback**: Kontinuierliche Statusmeldungen
- **Konsistenz**: Einheitliches Design mit der Hauptanwendung

### Accessibility
- Große Buttons (min. 40px Höhe)
- Klare Farbkodierung
- Ausführliche Fehlermeldungen
- Tooltips bei deaktivierten Funktionen

## 🚀 Performance

### Optimierungen
- Streaming für große JSON-Exports
- Chunk-basierte Dateioperationen
- Minimale Memory-Footprint
- Transaktionale DB-Operationen

### Limitations
- Backups erfolgen synchron (UI blockiert kurz)
- JSON-Export kann bei sehr großen DBs langsam sein
- Keine komprimierte Backup-Option

## 🔮 Erweiterungsmöglichkeiten

### Mögliche Verbesserungen
- **Komprimierte Backups**: ZIP/GZIP-Unterstützung
- **Automatische Backups**: Zeitgesteuerte Sicherungen
- **Inkrementelle Backups**: Nur Änderungen sichern
- **Cloud-Integration**: Direkter Upload zu Cloud-Diensten
- **Backup-Verschlüsselung**: Passwort-geschützte Backups
- **Async Operations**: Hintergrund-Backup ohne UI-Blockierung

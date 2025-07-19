# Schülerverwaltung - Bewertungsbogen

Ein umfassendes Schülerverwaltungssystem mit PyQt6 für die Verwaltung von Schülerdaten, Arbeitstiteln und Bewertungen.

## 📋 Funktionen

### Schülerverwaltung
- ✅ Schüler anlegen, bearbeiten und löschen
- ✅ Erweiterte Suchfunktion nach Namen
- ✅ Klassenfilter für gezieltes Durchsuchen
- ✅ Sortierbare Schülertabelle
- ✅ Detailansicht für jeden Schüler

### Bewertungssystem
- ✅ Arbeitstitel mit Noten verwalten
- ✅ Bewertungskategorien:
  - Konzept
  - Ausführung
  - Technik
  - Selbstbeurteilung
  - Persönliche Eindrücke
- ✅ Kommentarfunktion für detailliertes Feedback

### Klassenverwaltung
- ✅ Klassenübersicht mit Schüleranzahl
- ✅ Zuweisung von Schülern zwischen Klassen
- ✅ Klassenumbenennung mit Bestätigungsdialog
- ✅ Automatische Aktualisierung aller Ansichten

### Export & Dokumentation
- ✅ PDF-Export von Schülerdaten und Bewertungen
- ✅ Professionelle PDF-Formatierung mit reportlab
- ✅ Automatisches Öffnen der generierten PDFs

### Backup & Datensicherheit
- ✅ SQLite-Backup-Erstellung mit Zeitstempel
- ✅ JSON-Export für externe Datenverarbeitung
- ✅ Sichere Wiederherstellung mit Validierung
- ✅ Automatische Integritätsprüfung
- ✅ Rollback-Mechanismus bei Fehlern
- ✅ Datenbank-Informationsanzeige

## 🚀 Installation

### Voraussetzungen
- Python 3.8 oder höher
- PyQt6
- reportlab (für PDF-Export)

### Setup
1. Repository klonen:
```bash
git clone https://github.com/meltrix100/bewertungsbogen.git
cd bewertungsbogen
```

2. Abhängigkeiten installieren:
```bash
pip install PyQt6 reportlab
```

3. Anwendung starten:
```bash
python Beurteilungsbogen.py
```

## 💾 Datenbank

Das System verwendet SQLite für die Datenspeicherung:
- **Datei**: `students.db`
- **Tabellen**: 
  - `students` - Schülerinformationen und Grundbewertungen
  - `work_titles` - Arbeitstitel mit detaillierten Bewertungen

## 🎯 Nutzung

### Schüler anlegen
1. Vor- und Nachname in die entsprechenden Felder eingeben
2. Klasse angeben
3. "Schüler anlegen" klicken

### Schülerdetails bearbeiten
1. Doppelklick auf einen Schüler in der Tabelle
2. Bewertungen in den Textfeldern eingeben
3. "Schülerdaten speichern" klicken

### Arbeitstitel verwalten
1. Im Schülerdetails-Dialog "Neuen Arbeitstitel anlegen" klicken
2. Titel, Note und Bewertungskategorien ausfüllen
3. Speichern

### Klassen bearbeiten
1. "Klassen bearbeiten" Button in der Hauptansicht klicken
2. Quellklasse aus Dropdown auswählen
3. Neue Klassenbezeichnung eingeben
4. "Klasse umbenennen" ausführen

### PDF-Export
1. Schüler in der Tabelle auswählen
2. "Export als PDF" klicken
3. PDF wird automatisch erstellt und geöffnet

### Backup & Wiederherstellung
1. "Backup & Wiederherstellung" Button klicken
2. **Backup erstellen:**
   - "Durchsuchen..." klicken und Speicherort wählen
   - "Backup erstellen" ausführen
3. **JSON-Export:**
   - "Als JSON exportieren" klicken
   - Speicherort wählen
4. **Wiederherstellung:**
   - ⚠️ WARNUNG: Überschreibt alle aktuellen Daten!
   - Backup-Datei (.db) auswählen
   - Beide Bestätigungen geben
   - Wiederherstellung wird durchgeführt

## 📁 Projektstruktur

```
bewertungsbogen/
├── Beurteilungsbogen.py      # Hauptanwendung
├── database_manager.py       # Datenbankfunktionen (Legacy)
├── dialogs.py               # Dialog-Klassen (Legacy)
├── main_window.py           # Hauptfenster (Legacy)
├── main.py                  # Einstiegspunkt (Legacy)
├── pdf_export.py            # PDF-Export-Funktionen (Legacy)
├── students.db              # SQLite-Datenbank
├── build.bat                # Build-Skript für Executable
├── Beurteilungsbogen.spec   # PyInstaller-Konfiguration
└── README.md                # Diese Datei
```

## 🔧 Technische Details

### Architektur
- **GUI Framework**: PyQt6
- **Datenbank**: SQLite3
- **PDF-Generierung**: reportlab
- **Programmiersprache**: Python 3.x

### Hauptklassen
- `DatabaseManager` - Datenbankoperationen
- `MainWindow` - Hauptfenster der Anwendung
- `StudentDetailDialog` - Schülerdetails und Bewertungen
- `WorkTitleEditDialog` - Arbeitstitel bearbeiten
- `ClassManagementDialog` - Klassenverwaltung

### Datenbankschema

#### Tabelle `students`
```sql
CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    firstname TEXT NOT NULL,
    lastname TEXT NOT NULL,
    class TEXT,
    soziale_kompetenz TEXT,
    aktive_mitarbeit TEXT,
    sauberkeit TEXT,
    material TEXT,
    puenktlichkeit TEXT,
    kommentar TEXT
);
```

#### Tabelle `work_titles`
```sql
CREATE TABLE work_titles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    title TEXT,
    note TEXT,
    soziale_kompetenz TEXT,
    aktive_mitarbeit TEXT,
    sauberkeit TEXT,
    material TEXT,
    puenktlichkeit TEXT,
    kommentar TEXT,
    FOREIGN KEY(student_id) REFERENCES students(id)
);
```

## 🏗️ Build als Executable

Eine ausführbare Datei kann mit PyInstaller erstellt werden:

```bash
# PyInstaller installieren
pip install pyinstaller

# Build ausführen
pyinstaller Beurteilungsbogen.spec
```

Oder verwenden Sie das bereitgestellte Build-Skript:
```bash
build.bat
```

## 🎨 UI-Features

### Design
- Modernes Fusion-Style-Design
- Responsive Layout mit automatischer Anpassung
- Farbkodierte Bereiche für bessere Übersicht
- Intuitive Bedienführung

### Benutzerfreundlichkeit
- Drag & Drop-Unterstützung in Tabellen
- Kontextmenüs für häufige Aktionen
- Tastaturkürzel für wichtige Funktionen
- Automatische Validierung von Eingaben

## 🐛 Fehlerbehebung

### Häufige Probleme

**PyQt6 nicht gefunden:**
```bash
pip install PyQt6
```

**Reportlab fehlt für PDF-Export:**
```bash
pip install reportlab
```

**Datenbank-Fehler:**
- Stellen Sie sicher, dass `students.db` beschreibbar ist
- Prüfen Sie Dateiberechtigungen im Projektordner

## 📈 Zukünftige Entwicklung

### Geplante Features
- [ ] Backup/Restore-Funktionalität
- [ ] Excel-Import/Export
- [ ] Erweiterte Statistiken und Berichte
- [ ] Multi-User-Unterstützung
- [ ] Cloud-Synchronisation
- [ ] Druckvorlagen anpassbar
- [ ] Notenverwaltung mit Berechnungen

### Verbesserungen
- [ ] Performance-Optimierung für große Datenmengen
- [ ] Erweiterte Suchfilter
- [ ] Benutzerdefinierte Bewertungskategorien
- [ ] Theming-System für unterschiedliche Designs

## 🤝 Beitragen

Beiträge sind willkommen! Bitte:

1. Fork des Repositories erstellen
2. Feature-Branch erstellen (`git checkout -b feature/AmazingFeature`)
3. Änderungen committen (`git commit -m 'Add some AmazingFeature'`)
4. Branch pushen (`git push origin feature/AmazingFeature`)
5. Pull Request öffnen

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe `LICENSE` Datei für Details.

## 👨‍💻 Autor

**David** - [meltrix100](https://github.com/meltrix100)

## 🙏 Danksagungen

- PyQt6-Team für das ausgezeichnete GUI-Framework
- reportlab-Entwickler für die PDF-Generierung
- SQLite-Team für die robuste Datenbank-Engine

---

**Version**: 2.0  
**Letztes Update**: Juli 2025  
**Python-Version**: 3.8+
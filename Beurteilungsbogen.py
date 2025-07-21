import sys, os, sqlite3
from typing import List, Tuple, Optional
import sys
import os
import sqlite3
import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QTableWidget, QTableWidgetItem,
    QDialog, QTextEdit, QGroupBox, QComboBox, QFileDialog, QProgressBar,
    QScrollArea, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

# Importieren der reportlab-Bibliothek für PDF-Erstellung
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# ----------------------- Datenbank -----------------------
class DatabaseManager:
    def __init__(self, db_path: str = "students.db") -> None:
        try:
            self.db_path: str = db_path
            self.conn: sqlite3.Connection = sqlite3.connect(self.db_path)
            # Aktiviere Foreign Key Constraints
            self.conn.execute("PRAGMA foreign_keys = ON")
            self.create_tables()
        except sqlite3.Error as e:
            raise RuntimeError(f"Fehler beim Verbinden mit der Datenbank '{db_path}': {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unerwarteter Fehler beim Initialisieren der Datenbank: {str(e)}")

    def create_tables(self) -> None:
        try:
            cursor = self.conn.cursor()
            # Tabelle für Schüler inklusive Zusatzfelder
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
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
                )
            """)
            # Tabelle für Arbeitstitel inkl. eigener Zusatzfelder und Note
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS work_titles (
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
                )
            """)
            self.conn.commit()
        except sqlite3.Error as e:
            raise RuntimeError(f"Fehler beim Erstellen der Datenbanktabellen: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unerwarteter Fehler beim Erstellen der Datenbank: {str(e)}")

    def add_student(self, firstname: str, lastname: str, klass: str) -> None:
        try:
            if not firstname.strip() or not lastname.strip():
                raise ValueError("Vor- und Nachname dürfen nicht leer sein")
            
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO students (firstname, lastname, class) VALUES (?, ?, ?)",
                (firstname.strip(), lastname.strip(), klass.strip() if klass else None)
            )
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Datenbankintegritätsfehler: {str(e)}")
        except sqlite3.Error as e:
            raise RuntimeError(f"Datenbankfehler beim Hinzufügen des Schülers: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unerwarteter Fehler beim Hinzufügen des Schülers: {str(e)}")

    def update_student_details(
        self, student_id: int, soziale_kompetenz: str, aktive_mitarbeit: str,
        sauberkeit: str, material: str, puenktlichkeit: str, kommentar: str
    ) -> None:
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE students
            SET soziale_kompetenz = ?, aktive_mitarbeit = ?, sauberkeit = ?,
                material = ?, puenktlichkeit = ?, kommentar = ?
            WHERE id = ?
        """, (soziale_kompetenz, aktive_mitarbeit, sauberkeit, material, puenktlichkeit, kommentar, student_id))
        self.conn.commit()

    def delete_student(self, student_id: int) -> None:
        try:
            if not isinstance(student_id, int) or student_id <= 0:
                raise ValueError("Ungültige Schüler-ID")
            
            cursor = self.conn.cursor()
            # Prüfe ob Schüler existiert
            cursor.execute("SELECT COUNT(*) FROM students WHERE id = ?", (student_id,))
            if cursor.fetchone()[0] == 0:
                raise ValueError(f"Schüler mit ID {student_id} nicht gefunden")
            
            # Lösche zuerst alle Arbeitstitel
            cursor.execute("DELETE FROM work_titles WHERE student_id = ?", (student_id,))
            # Dann den Schüler
            cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            raise RuntimeError(f"Datenbankfehler beim Löschen des Schülers: {str(e)}")
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Unerwarteter Fehler beim Löschen des Schülers: {str(e)}")

    def search_students(self, keyword: str) -> List[Tuple]:
        try:
            if not keyword or not keyword.strip():
                return self.get_students()
            
            cursor = self.conn.cursor()
            keyword = f"%{keyword.strip()}%"
            cursor.execute("""
                SELECT id, firstname, lastname, class FROM students
                WHERE firstname LIKE ? OR lastname LIKE ? 
                ORDER BY class
            """, (keyword, keyword))
            return cursor.fetchall()
        except sqlite3.Error as e:
            raise RuntimeError(f"Datenbankfehler bei der Schülersuche: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unerwarteter Fehler bei der Schülersuche: {str(e)}")

    def get_students(self) -> List[Tuple]:
        try:
            cursor = self.conn.cursor()
            # Standardmäßig nach Klasse sortieren (class ist Spalte 3)
            cursor.execute("SELECT id, firstname, lastname, class FROM students ORDER BY class")
            return cursor.fetchall()
        except sqlite3.Error as e:
            raise RuntimeError(f"Datenbankfehler beim Abrufen der Schüler: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unerwarteter Fehler beim Abrufen der Schüler: {str(e)}")

    def add_work_title(self, student_id: int, title: str, note: str,
                       soziale_kompetenz: str, aktive_mitarbeit: str,
                       sauberkeit: str, material: str, puenktlichkeit: str,
                       kommentar: str) -> None:
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO work_titles (
                student_id, title, note, soziale_kompetenz, aktive_mitarbeit,
                sauberkeit, material, puenktlichkeit, kommentar
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (student_id, title, note, soziale_kompetenz, aktive_mitarbeit,
              sauberkeit, material, puenktlichkeit, kommentar))
        self.conn.commit()

    def update_work_title(self, work_id: int, title: str, note: str,
                          soziale_kompetenz: str, aktive_mitarbeit: str,
                          sauberkeit: str, material: str, puenktlichkeit: str,
                          kommentar: str) -> None:
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE work_titles
            SET title = ?, note = ?, soziale_kompetenz = ?, aktive_mitarbeit = ?,
                sauberkeit = ?, material = ?, puenktlichkeit = ?, kommentar = ?
            WHERE id = ?
        """, (title, note, soziale_kompetenz, aktive_mitarbeit, sauberkeit,
              material, puenktlichkeit, kommentar, work_id))
        self.conn.commit()

    def delete_work_title(self, work_id: int) -> None:
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM work_titles WHERE id = ?", (work_id,))
        self.conn.commit()

    def get_work_titles(self, student_id: int) -> List[Tuple]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, title, note, soziale_kompetenz, aktive_mitarbeit,
                   sauberkeit, material, puenktlichkeit, kommentar
            FROM work_titles
            WHERE student_id = ?
        """, (student_id,))
        return cursor.fetchall()

    def close(self) -> None:
        self.conn.close()

    def get_unique_classes(self) -> List[str]:
        """Gibt eine Liste aller eindeutigen Klassennamen aus der Datenbank zurück."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT class FROM students WHERE class IS NOT NULL AND class != '' ORDER BY class")
        # Ergebnisse in eine Liste umwandeln und leere Einträge entfernen
        classes = [row[0] for row in cursor.fetchall() if row[0]]
        return classes

    def get_class_statistics(self) -> List[Tuple[str, int]]:
        """Gibt eine Liste mit Klassennamen und Schüleranzahl zurück."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT class, COUNT(*) as student_count 
            FROM students 
            WHERE class IS NOT NULL AND class != '' 
            GROUP BY class 
            ORDER BY class
        """)
        return cursor.fetchall()

    def update_students_class(self, old_class: str, new_class: str) -> int:
        """Weist alle Schüler einer Klasse einer neuen Klasse zu. Gibt die Anzahl der aktualisierten Schüler zurück."""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE students SET class = ? WHERE class = ?", (new_class, old_class))
        affected_rows = cursor.rowcount
        self.conn.commit()
        return affected_rows

    def get_students_in_class(self, class_name: str) -> List[Tuple]:
        """Gibt alle Schüler einer bestimmten Klasse zurück."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, firstname, lastname, class FROM students WHERE class = ? ORDER BY lastname, firstname",
            (class_name,)
        )
        return cursor.fetchall()

    def create_backup(self, backup_path: str) -> None:
        """Erstellt ein Backup der Datenbank."""
        try:
            import shutil
            import datetime
            
            # Stelle sicher, dass der Backup-Pfad existiert
            backup_dir = os.path.dirname(backup_path)
            if backup_dir and not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # Erstelle Backup mit Zeitstempel im Namen falls nicht spezifiziert
            if not backup_path.endswith('.db'):
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = os.path.join(backup_path, f"students_backup_{timestamp}.db")
            
            # Kopiere die Datenbankdatei
            shutil.copy2(self.db_path, backup_path)
            
            # Validiere das Backup
            self._validate_backup(backup_path)
            
        except Exception as e:
            raise RuntimeError(f"Fehler beim Erstellen des Backups: {str(e)}")

    def restore_backup(self, backup_path: str) -> None:
        """Stellt die Datenbank aus einem Backup wieder her."""
        try:
            import shutil
            
            # Validiere das Backup vor der Wiederherstellung
            if not os.path.exists(backup_path):
                raise ValueError(f"Backup-Datei nicht gefunden: {backup_path}")
            
            self._validate_backup(backup_path)
            
            # Schließe die aktuelle Verbindung
            self.conn.close()
            
            # Erstelle Sicherheitskopie der aktuellen DB
            current_backup = f"{self.db_path}.before_restore"
            shutil.copy2(self.db_path, current_backup)
            
            try:
                # Überschreibe die aktuelle Datenbank mit dem Backup
                shutil.copy2(backup_path, self.db_path)
                
                # Neue Verbindung zur wiederhergestellten Datenbank
                self.conn = sqlite3.connect(self.db_path)
                self.conn.execute("PRAGMA foreign_keys = ON")
                
                # Validiere die wiederhergestellte Datenbank
                self._validate_database_structure()
                
            except Exception as e:
                # Bei Fehler: Ursprüngliche Datenbank wiederherstellen
                shutil.copy2(current_backup, self.db_path)
                self.conn = sqlite3.connect(self.db_path)
                self.conn.execute("PRAGMA foreign_keys = ON")
                raise RuntimeError(f"Fehler beim Wiederherstellen. Original wiederhergestellt: {str(e)}")
            finally:
                # Lösche die Sicherheitskopie
                if os.path.exists(current_backup):
                    os.remove(current_backup)
                    
        except Exception as e:
            raise RuntimeError(f"Fehler bei der Wiederherstellung: {str(e)}")

    def _validate_backup(self, backup_path: str) -> None:
        """Validiert ein Backup auf Vollständigkeit und Integrität."""
        try:
            # Teste Verbindung zum Backup
            test_conn = sqlite3.connect(backup_path)
            cursor = test_conn.cursor()
            
            # Prüfe ob alle erforderlichen Tabellen existieren
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ['students', 'work_titles']
            for table in required_tables:
                if table not in tables:
                    raise ValueError(f"Erforderliche Tabelle '{table}' im Backup nicht gefunden")
            
            # Prüfe Datenbankintegrität
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            if integrity_result != "ok":
                raise ValueError(f"Backup-Integrität fehlgeschlagen: {integrity_result}")
            
            test_conn.close()
            
        except sqlite3.Error as e:
            raise ValueError(f"Backup-Validierung fehlgeschlagen: {str(e)}")

    def _validate_database_structure(self) -> None:
        """Validiert die Struktur der aktuellen Datenbank."""
        try:
            cursor = self.conn.cursor()
            
            # Prüfe students Tabelle
            cursor.execute("PRAGMA table_info(students)")
            students_columns = [row[1] for row in cursor.fetchall()]
            required_student_columns = [
                'id', 'firstname', 'lastname', 'class', 'soziale_kompetenz',
                'aktive_mitarbeit', 'sauberkeit', 'material', 'puenktlichkeit', 'kommentar'
            ]
            for col in required_student_columns:
                if col not in students_columns:
                    raise ValueError(f"Spalte '{col}' in Tabelle 'students' fehlt")
            
            # Prüfe work_titles Tabelle
            cursor.execute("PRAGMA table_info(work_titles)")
            work_titles_columns = [row[1] for row in cursor.fetchall()]
            required_work_columns = [
                'id', 'student_id', 'title', 'note', 'soziale_kompetenz',
                'aktive_mitarbeit', 'sauberkeit', 'material', 'puenktlichkeit', 'kommentar'
            ]
            for col in required_work_columns:
                if col not in work_titles_columns:
                    raise ValueError(f"Spalte '{col}' in Tabelle 'work_titles' fehlt")
                    
        except sqlite3.Error as e:
            raise ValueError(f"Datenbankstruktur-Validierung fehlgeschlagen: {str(e)}")

    def get_database_info(self) -> dict:
        """Gibt Informationen über die Datenbank zurück."""
        try:
            cursor = self.conn.cursor()
            
            # Anzahl Schüler
            cursor.execute("SELECT COUNT(*) FROM students")
            student_count = cursor.fetchone()[0]
            
            # Anzahl Arbeitstitel
            cursor.execute("SELECT COUNT(*) FROM work_titles")
            work_title_count = cursor.fetchone()[0]
            
            # Anzahl Klassen
            cursor.execute("SELECT COUNT(DISTINCT class) FROM students WHERE class IS NOT NULL AND class != ''")
            class_count = cursor.fetchone()[0]
            
            # Dateigröße
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            # Letzte Änderung
            last_modified = datetime.datetime.fromtimestamp(
                os.path.getmtime(self.db_path)
            ).strftime("%d.%m.%Y %H:%M:%S") if os.path.exists(self.db_path) else "Unbekannt"
            
            return {
                'students': student_count,
                'work_titles': work_title_count,
                'classes': class_count,
                'file_size': f"{db_size / 1024:.1f} KB",
                'last_modified': last_modified,
                'db_path': self.db_path
            }
            
        except Exception as e:
            raise RuntimeError(f"Fehler beim Abrufen der Datenbank-Informationen: {str(e)}")

    def export_to_json(self, export_path: str) -> None:
        """Exportiert alle Daten als JSON-Datei."""
        try:
            import json
            import datetime
            
            cursor = self.conn.cursor()
            
            # Alle Schülerdaten abrufen
            cursor.execute("""
                SELECT id, firstname, lastname, class, soziale_kompetenz, aktive_mitarbeit,
                       sauberkeit, material, puenktlichkeit, kommentar FROM students
            """)
            students_data = []
            for row in cursor.fetchall():
                students_data.append({
                    'id': row[0],
                    'firstname': row[1],
                    'lastname': row[2],
                    'class': row[3],
                    'soziale_kompetenz': row[4],
                    'aktive_mitarbeit': row[5],
                    'sauberkeit': row[6],
                    'material': row[7],
                    'puenktlichkeit': row[8],
                    'kommentar': row[9]
                })
            
            # Alle Arbeitstitel abrufen
            cursor.execute("""
                SELECT id, student_id, title, note, soziale_kompetenz, aktive_mitarbeit,
                       sauberkeit, material, puenktlichkeit, kommentar FROM work_titles
            """)
            work_titles_data = []
            for row in cursor.fetchall():
                work_titles_data.append({
                    'id': row[0],
                    'student_id': row[1],
                    'title': row[2],
                    'note': row[3],
                    'soziale_kompetenz': row[4],
                    'aktive_mitarbeit': row[5],
                    'sauberkeit': row[6],
                    'material': row[7],
                    'puenktlichkeit': row[8],
                    'kommentar': row[9]
                })
            
            # Erstelle Export-Datenstruktur
            export_data = {
                'metadata': {
                    'export_date': datetime.datetime.now().isoformat(),
                    'database_path': self.db_path,
                    'student_count': len(students_data),
                    'work_title_count': len(work_titles_data)
                },
                'students': students_data,
                'work_titles': work_titles_data
            }
            
            # Schreibe JSON-Datei
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            raise RuntimeError(f"Fehler beim JSON-Export: {str(e)}")

# ----------------------- BackupRestoreDialog -----------------------
class BackupRestoreDialog(QDialog):
    def __init__(self, db_manager: DatabaseManager) -> None:
        super().__init__()
        self.db_manager: DatabaseManager = db_manager
        self.setWindowTitle("Backup && Wiederherstellung")
        self.setMinimumSize(800, 600)
        self.setup_ui()
        self.load_database_info()

    def setup_ui(self) -> None:
        layout = QVBoxLayout()
        
        # Größere Schrift für Labels
        font = QFont()
        font.setPointSize(12)
        
        # ====================================================
        # BEREICH 1: Datenbank-Informationen
        # ====================================================
        info_group = QGroupBox("Datenbank-Informationen")
        info_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                padding-top: 15px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                background-color: #F0FFF0;
            }
        """)
        
        info_layout = QVBoxLayout(info_group)
        
        # Informationsanzeige
        self.info_label = QLabel()
        self.info_label.setFont(font)
        self.info_label.setStyleSheet("padding: 10px; background-color: #f9f9f9; border-radius: 4px;")
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)
        
        # Aktualisieren-Button
        self.refresh_info_button = QPushButton("Informationen aktualisieren")
        self.refresh_info_button.setMinimumHeight(35)
        self.refresh_info_button.clicked.connect(self.load_database_info)
        info_layout.addWidget(self.refresh_info_button)
        
        layout.addWidget(info_group)
        
        # ====================================================
        # BEREICH 2: Backup erstellen
        # ====================================================
        backup_group = QGroupBox("Backup erstellen")
        backup_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #2196F3;
                border-radius: 8px;
                padding-top: 15px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                background-color: #F0F8FF;
            }
        """)
        
        backup_layout = QVBoxLayout(backup_group)
        
        # Backup-Pfad auswählen
        backup_path_layout = QHBoxLayout()
        self.backup_path_edit = QLineEdit()
        self.backup_path_edit.setMinimumHeight(35)
        self.backup_path_edit.setPlaceholderText("Backup-Pfad auswählen...")
        self.backup_path_edit.setReadOnly(True)
        backup_path_layout.addWidget(self.backup_path_edit)
        
        self.browse_backup_button = QPushButton("Durchsuchen...")
        self.browse_backup_button.setMinimumHeight(35)
        self.browse_backup_button.clicked.connect(self.browse_backup_path)
        backup_path_layout.addWidget(self.browse_backup_button)
        
        backup_layout.addLayout(backup_path_layout)
        
        # Backup-Optionen
        options_layout = QHBoxLayout()
        
        self.create_backup_button = QPushButton("Backup erstellen")
        self.create_backup_button.setMinimumHeight(45)
        self.create_backup_button.setFont(font)
        self.create_backup_button.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        self.create_backup_button.clicked.connect(self.create_backup)
        options_layout.addWidget(self.create_backup_button)
        
        self.export_json_button = QPushButton("Als JSON exportieren")
        self.export_json_button.setMinimumHeight(45)
        self.export_json_button.setFont(font)
        self.export_json_button.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")
        self.export_json_button.clicked.connect(self.export_json)
        options_layout.addWidget(self.export_json_button)
        
        backup_layout.addLayout(options_layout)
        
        layout.addWidget(backup_group)
        
        # ====================================================
        # BEREICH 3: Backup wiederherstellen
        # ====================================================
        restore_group = QGroupBox("Backup wiederherstellen")
        restore_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #FF5722;
                border-radius: 8px;
                padding-top: 15px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                background-color: #FFF3E0;
            }
        """)
        
        restore_layout = QVBoxLayout(restore_group)
        
        # Warnung
        warning_label = QLabel("⚠️ WARNUNG: Das Wiederherstellen überschreibt alle aktuellen Daten!")
        warning_label.setFont(font)
        warning_label.setStyleSheet("color: #FF5722; background-color: #FFEBEE; padding: 10px; border-radius: 4px; font-weight: bold;")
        warning_label.setWordWrap(True)
        restore_layout.addWidget(warning_label)
        
        # Restore-Pfad auswählen
        restore_path_layout = QHBoxLayout()
        self.restore_path_edit = QLineEdit()
        self.restore_path_edit.setMinimumHeight(35)
        self.restore_path_edit.setPlaceholderText("Backup-Datei auswählen...")
        self.restore_path_edit.setReadOnly(True)
        restore_path_layout.addWidget(self.restore_path_edit)
        
        self.browse_restore_button = QPushButton("Durchsuchen...")
        self.browse_restore_button.setMinimumHeight(35)
        self.browse_restore_button.clicked.connect(self.browse_restore_path)
        restore_path_layout.addWidget(self.browse_restore_button)
        
        restore_layout.addLayout(restore_path_layout)
        
        # Restore-Button
        self.restore_backup_button = QPushButton("Backup wiederherstellen")
        self.restore_backup_button.setMinimumHeight(45)
        self.restore_backup_button.setFont(font)
        self.restore_backup_button.setStyleSheet("background-color: #FF5722; color: white; font-weight: bold;")
        self.restore_backup_button.clicked.connect(self.restore_backup)
        restore_layout.addWidget(self.restore_backup_button)
        
        layout.addWidget(restore_group)
        
        # ====================================================
        # BEREICH 4: Dialog-Buttons
        # ====================================================
        buttons_layout = QHBoxLayout()
        
        # Schließen-Button
        self.close_button = QPushButton("Schließen")
        self.close_button.setMinimumHeight(40)
        self.close_button.setFont(font)
        self.close_button.clicked.connect(self.close)
        buttons_layout.addWidget(self.close_button)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def load_database_info(self) -> None:
        """Lädt und zeigt Datenbank-Informationen an"""
        try:
            info = self.db_manager.get_database_info()
            
            info_text = f"""
<b>Datenbank-Status:</b><br>
• Schüler: {info['students']}<br>
• Arbeitstitel: {info['work_titles']}<br>
• Klassen: {info['classes']}<br>
• Dateigröße: {info['file_size']}<br>
• Letzte Änderung: {info['last_modified']}<br>
• Pfad: {info['db_path']}
            """.strip()
            
            self.info_label.setText(info_text)
            
        except Exception as e:
            self.info_label.setText(f"Fehler beim Laden der Datenbank-Informationen:\n{str(e)}")

    def browse_backup_path(self) -> None:
        """Öffnet Dialog zur Auswahl des Backup-Pfads"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"students_backup_{timestamp}.db"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Backup speichern unter...",
                default_filename,
                "SQLite Datenbank (*.db);;Alle Dateien (*.*)"
            )
            
            if file_path:
                self.backup_path_edit.setText(file_path)
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Auswählen des Backup-Pfads:\n{str(e)}")

    def browse_restore_path(self) -> None:
        """Öffnet Dialog zur Auswahl der Backup-Datei"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Backup-Datei auswählen...",
                "",
                "SQLite Datenbank (*.db);;Alle Dateien (*.*)"
            )
            
            if file_path:
                self.restore_path_edit.setText(file_path)
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Auswählen der Backup-Datei:\n{str(e)}")

    def create_backup(self) -> None:
        """Erstellt ein Backup der Datenbank"""
        backup_path = self.backup_path_edit.text().strip()
        
        if not backup_path:
            QMessageBox.warning(self, "Warnung", "Bitte wählen Sie einen Backup-Pfad aus.")
            return
        
        try:
            # Fortschrittsanzeige (einfach)
            self.create_backup_button.setEnabled(False)
            self.create_backup_button.setText("Backup wird erstellt...")
            
            # Backup erstellen
            self.db_manager.create_backup(backup_path)
            
            # Erfolgsmeldung
            QMessageBox.information(
                self, "Erfolg", 
                f"Backup wurde erfolgreich erstellt:\n{backup_path}"
            )
            
            # Informationen aktualisieren
            self.load_database_info()
            
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Erstellen des Backups:\n{str(e)}")
        finally:
            self.create_backup_button.setEnabled(True)
            self.create_backup_button.setText("Backup erstellen")

    def export_json(self) -> None:
        """Exportiert die Datenbank als JSON"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"students_export_{timestamp}.json"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "JSON-Export speichern unter...",
                default_filename,
                "JSON Dateien (*.json);;Alle Dateien (*.*)"
            )
            
            if file_path:
                # Fortschrittsanzeige
                self.export_json_button.setEnabled(False)
                self.export_json_button.setText("Export läuft...")
                
                # Export durchführen
                self.db_manager.export_to_json(file_path)
                
                # Erfolgsmeldung
                QMessageBox.information(
                    self, "Erfolg", 
                    f"JSON-Export wurde erfolgreich erstellt:\n{file_path}"
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim JSON-Export:\n{str(e)}")
        finally:
            self.export_json_button.setEnabled(True)
            self.export_json_button.setText("Als JSON exportieren")

    def restore_backup(self) -> None:
        """Stellt ein Backup wieder her"""
        restore_path = self.restore_path_edit.text().strip()
        
        if not restore_path:
            QMessageBox.warning(self, "Warnung", "Bitte wählen Sie eine Backup-Datei aus.")
            return
        
        if not os.path.exists(restore_path):
            QMessageBox.warning(self, "Warnung", "Die ausgewählte Backup-Datei existiert nicht.")
            return
        
        # Doppelte Bestätigung für Wiederherstellung
        reply = QMessageBox.question(
            self, 'WARNUNG: Daten überschreiben',
            "⚠️ ACHTUNG: Diese Aktion überschreibt ALLE aktuellen Daten!\n\n"
            f"Backup-Datei: {restore_path}\n\n"
            "Alle aktuellen Schüler, Arbeitstitel und Klassen werden durch die "
            "Daten aus dem Backup ersetzt.\n\n"
            "Diese Aktion kann NICHT rückgängig gemacht werden!\n\n"
            "Möchten Sie wirklich fortfahren?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Zweite Bestätigung
        reply2 = QMessageBox.question(
            self, 'Letzte Bestätigung',
            "Sind Sie sich ABSOLUT sicher?\n\n"
            "Dies ist Ihre letzte Chance, die Wiederherstellung abzubrechen!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply2 != QMessageBox.StandardButton.Yes:
            return
        
        try:
            # Fortschrittsanzeige
            self.restore_backup_button.setEnabled(False)
            self.restore_backup_button.setText("Wiederherstellung läuft...")
            
            # Backup wiederherstellen
            self.db_manager.restore_backup(restore_path)
            
            # Erfolgsmeldung
            QMessageBox.information(
                self, "Erfolg", 
                "Backup wurde erfolgreich wiederhergestellt!\n\n"
                "Die Anwendung wird nun aktualisiert."
            )
            
            # Informationen aktualisieren
            self.load_database_info()
            
            # Dialog schließen damit Hauptfenster aktualisiert werden kann
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler bei der Wiederherstellung:\n{str(e)}")
        finally:
            self.restore_backup_button.setEnabled(True)
            self.restore_backup_button.setText("Backup wiederherstellen")

# ----------------------- ClassManagementDialog -----------------------
class ClassManagementDialog(QDialog):
    def __init__(self, db_manager: DatabaseManager) -> None:
        super().__init__()
        self.db_manager: DatabaseManager = db_manager
        self.setWindowTitle("Klassen bearbeiten")
        
        # Dynamische Größenanpassung basierend auf Bildschirmauflösung und DPI
        self._setup_dynamic_sizing()
        
        self.setup_ui()
        self.load_class_overview()
    
    def _setup_dynamic_sizing(self) -> None:
        """Berechnet und setzt die optimale Fenstergröße basierend auf Bildschirm und DPI"""
        screen = QApplication.primaryScreen()
        if not screen:
            # Fallback für sehr kleine Bildschirme
            self.setMinimumSize(600, 500)
            self.resize(700, 600)
            return
        
        screen_geometry = screen.geometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        
        # DPI-Skalierung berücksichtigen
        dpi_ratio = screen.devicePixelRatio()
        logical_dpi = screen.logicalDotsPerInch()
        
        # Basis-DPI (typisch 96 DPI bei 100% Skalierung)
        base_dpi = 96.0
        dpi_scale_factor = logical_dpi / base_dpi
        
        # Kategorisierung der Bildschirmgröße
        if screen_width <= 1366 and screen_height <= 768:
            # Kleine Bildschirme (HD, kleine Laptops)
            width_factor = 0.85
            height_factor = 0.90
            min_width_factor = 0.70
            min_height_factor = 0.75
        elif screen_width <= 1920 and screen_height <= 1080:
            # Mittlere Bildschirme (Full HD)
            width_factor = 0.70
            height_factor = 0.85
            min_width_factor = 0.50
            min_height_factor = 0.65
        elif screen_width <= 2560 and screen_height <= 1440:
            # Große Bildschirme (2K)
            width_factor = 0.60
            height_factor = 0.80
            min_width_factor = 0.45
            min_height_factor = 0.60
        else:
            # Sehr große Bildschirme (4K und größer)
            width_factor = 0.50
            height_factor = 0.75
            min_width_factor = 0.40
            min_height_factor = 0.55
        
        # DPI-Skalierung anwenden
        width_factor *= dpi_scale_factor
        height_factor *= dpi_scale_factor
        min_width_factor *= dpi_scale_factor
        min_height_factor *= dpi_scale_factor
        
        # Berechnete Größen mit Grenzen
        target_width = max(600, min(int(screen_width * width_factor), screen_width - 100))
        target_height = max(500, min(int(screen_height * height_factor), screen_height - 100))
        
        min_width = max(500, int(screen_width * min_width_factor))
        min_height = max(400, int(screen_height * min_height_factor))
        
        # Größen setzen
        self.resize(target_width, target_height)
        self.setMinimumSize(min_width, min_height)
        
        # Dialog zentrieren
        x = (screen_width - target_width) // 2
        y = (screen_height - target_height) // 2
        self.move(x, y)

    def setup_ui(self) -> None:
        # Hauptlayout für den gesamten Dialog
        main_layout = QVBoxLayout()
        
        # Dynamische Schriftgröße basierend auf Bildschirmgröße
        font = self._get_scaled_font()
        
        # Dynamische Elementgrößen
        element_heights = self._get_scaled_element_heights()
        
        # ====================================================
        # BEREICH 1: Klassenübersicht
        # ====================================================
        overview_group = QGroupBox("Klassenübersicht")
        overview_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: {font.pointSize() + 2}px;
                border: 2px solid #2196F3;
                border-radius: 8px;
                padding-top: 15px;
                margin-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                background-color: #F0F8FF;
            }}
        """)
        
        overview_layout = QVBoxLayout(overview_group)
        
        # Tabelle für Klassenübersicht
        self.class_overview_table = QTableWidget()
        self.class_overview_table.setColumnCount(2)
        self.class_overview_table.setHorizontalHeaderLabels(["Klasse", "Anzahl Schüler"])
        self.class_overview_table.setMinimumHeight(element_heights['table_min'])
        self.class_overview_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Dynamische Schriftgröße für Tabelle
        self.class_overview_table.setFont(font)
        
        # Spaltenbreite anpassen
        header = self.class_overview_table.horizontalHeader()
        header.setSectionResizeMode(0, header.ResizeMode.Stretch)
        header.setSectionResizeMode(1, header.ResizeMode.ResizeToContents)
        
        overview_layout.addWidget(self.class_overview_table)
        
        # ====================================================
        # BEREICH 2: Klasse umbenennen
        # ====================================================
        assignment_group = QGroupBox("Klasse umbenennen")
        assignment_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: {font.pointSize() + 2}px;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                padding-top: 15px;
                margin-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                background-color: #F0FFF0;
            }}
        """)
        
        assignment_layout = QVBoxLayout(assignment_group)
        
        # Quellklasse auswählen
        source_layout = QHBoxLayout()
        source_label = QLabel("Von Klasse:")
        source_label.setFont(font)
        source_label.setMinimumWidth(element_heights['label_width'])
        source_layout.addWidget(source_label)
        
        self.source_class_combo = QComboBox()
        self.source_class_combo.setMinimumHeight(element_heights['input'])
        self.source_class_combo.setFont(font)
        self.source_class_combo.currentTextChanged.connect(self.update_student_count_preview)
        source_layout.addWidget(self.source_class_combo)
        
        assignment_layout.addLayout(source_layout)
        
        # Zielklasse eingeben
        target_layout = QHBoxLayout()
        target_label = QLabel("Zu Klasse:")
        target_label.setFont(font)
        target_label.setMinimumWidth(element_heights['label_width'])
        target_layout.addWidget(target_label)
        
        self.target_class_edit = QLineEdit()
        self.target_class_edit.setMinimumHeight(element_heights['input'])
        self.target_class_edit.setFont(font)
        self.target_class_edit.setPlaceholderText("Neue Klassenbezeichnung eingeben...")
        target_layout.addWidget(self.target_class_edit)
        
        assignment_layout.addLayout(target_layout)
        
        # Vorschau der betroffenen Schüler
        self.preview_label = QLabel("Wählen Sie eine Quellklasse aus.")
        self.preview_label.setFont(font)
        self.preview_label.setStyleSheet("color: #666; padding: 10px; background-color: #f9f9f9; border-radius: 4px;")
        self.preview_label.setWordWrap(True)  # Ermöglicht Textumbruch
        self.preview_label.setMinimumHeight(element_heights['preview'])  # Mindesthöhe für mehrzeiligen Text
        assignment_layout.addWidget(self.preview_label)
        
        # Button für Klasse umbenennen
        self.rename_class_button = QPushButton("Klasse umbenennen")
        self.rename_class_button.setMinimumHeight(element_heights['button'])
        self.rename_class_button.setFont(font)
        self.rename_class_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.rename_class_button.clicked.connect(self.perform_mass_assignment)
        self.rename_class_button.setEnabled(False)
        assignment_layout.addWidget(self.rename_class_button)
        
        # ====================================================
        # BEREICH 3: Klasse löschen
        # ====================================================
        delete_group = QGroupBox("Klasse löschen")
        delete_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: {font.pointSize() + 2}px;
                border: 2px solid #FF5722;
                border-radius: 8px;
                padding-top: 15px;
                margin-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                background-color: #FFEBEE;
            }}
        """)
        
        delete_layout = QVBoxLayout(delete_group)
        
        # Warnung
        delete_warning_label = QLabel("⚠️ WARNUNG: Das Löschen einer Klasse entfernt alle Schüler und deren Arbeitstitel permanent!")
        delete_warning_label.setFont(font)
        delete_warning_label.setStyleSheet("color: #FF5722; background-color: #FFEBEE; padding: 10px; border-radius: 4px; font-weight: bold;")
        delete_warning_label.setWordWrap(True)
        delete_layout.addWidget(delete_warning_label)
        
        # Klasse zum Löschen auswählen
        delete_class_layout = QHBoxLayout()
        delete_class_label = QLabel("Klasse löschen:")
        delete_class_label.setFont(font)
        delete_class_label.setMinimumWidth(element_heights['label_width'])
        delete_class_layout.addWidget(delete_class_label)
        
        self.delete_class_combo = QComboBox()
        self.delete_class_combo.setMinimumHeight(element_heights['input'])
        self.delete_class_combo.setFont(font)
        self.delete_class_combo.currentTextChanged.connect(self.update_delete_preview)
        delete_class_layout.addWidget(self.delete_class_combo)
        
        delete_layout.addLayout(delete_class_layout)
        
        # Vorschau der zu löschenden Schüler
        self.delete_preview_label = QLabel("Wählen Sie eine Klasse zum Löschen aus.")
        self.delete_preview_label.setFont(font)
        self.delete_preview_label.setStyleSheet("color: #666; padding: 10px; background-color: #f9f9f9; border-radius: 4px;")
        self.delete_preview_label.setWordWrap(True)
        self.delete_preview_label.setMinimumHeight(element_heights['preview'])
        delete_layout.addWidget(self.delete_preview_label)
        
        # Button für Klasse löschen
        self.delete_class_button = QPushButton("Klasse löschen")
        self.delete_class_button.setMinimumHeight(element_heights['button'])
        self.delete_class_button.setFont(font)
        self.delete_class_button.setStyleSheet("background-color: #FF5722; color: white; font-weight: bold;")
        self.delete_class_button.clicked.connect(self.perform_class_deletion)
        self.delete_class_button.setEnabled(False)
        delete_layout.addWidget(self.delete_class_button)
        
        # ====================================================
        # BEREICH 4: Dialog-Buttons
        # ====================================================
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        
        # Aktualisieren-Button
        self.refresh_button = QPushButton("Übersicht aktualisieren")
        self.refresh_button.setMinimumHeight(element_heights['button_small'])
        self.refresh_button.setFont(font)
        self.refresh_button.clicked.connect(self.load_class_overview)
        buttons_layout.addWidget(self.refresh_button)
        
        # Schließen-Button
        self.close_button = QPushButton("Schließen")
        self.close_button.setMinimumHeight(element_heights['button_small'])
        self.close_button.setFont(font)
        self.close_button.setStyleSheet("background-color: #FF5555; color: white;")
        self.close_button.clicked.connect(self.close)
        buttons_layout.addWidget(self.close_button)
        
        # ====================================================
        # QSplitter für verschiebbare Bereiche erstellen
        # ====================================================
        # Hauptsplitter (vertikal) für die drei Hauptbereiche
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        main_splitter.addWidget(overview_group)
        
        # Untersplitter für Umbenennen und Löschen (vertikal)
        operations_splitter = QSplitter(Qt.Orientation.Vertical)
        operations_splitter.addWidget(assignment_group)
        operations_splitter.addWidget(delete_group)
        
        # Dynamische Anfangsgrößen basierend auf verfügbarem Platz
        available_height = self.height() - element_heights['button_small'] - 60  # Platz für Buttons und Ränder
        overview_height = int(available_height * 0.4)
        operations_height = int(available_height * 0.6)
        
        # Verhältnis für Umbenennen/Löschen setzen (50/50)
        operations_splitter.setSizes([operations_height // 2, operations_height // 2])
        operations_splitter.setChildrenCollapsible(False)
        
        main_splitter.addWidget(operations_splitter)
        
        # Anfangsverhältnis der Hauptbereiche setzen
        main_splitter.setSizes([overview_height, operations_height])
        main_splitter.setChildrenCollapsible(False)
        
        # Dynamische Mindestgrößen für die Bereiche festlegen
        overview_group.setMinimumHeight(element_heights['group_min'])
        assignment_group.setMinimumHeight(element_heights['group_min'])
        delete_group.setMinimumHeight(element_heights['group_min'])
        
        # Hauptlayout zusammensetzen
        main_layout.addWidget(main_splitter)
        main_layout.addWidget(buttons_widget)
        
        # Gesamtlayout für den Dialog anwenden
        self.setLayout(main_layout)
    
    def _get_scaled_font(self) -> QFont:
        """Berechnet eine skalierte Schriftgröße basierend auf Bildschirmgröße und DPI"""
        screen = QApplication.primaryScreen()
        if not screen:
            font = QFont()
            font.setPointSize(10)
            return font
        
        screen_geometry = screen.geometry()
        screen_height = screen_geometry.height()
        logical_dpi = screen.logicalDotsPerInch()
        
        # Basis-Schriftgröße je nach Bildschirmhöhe
        if screen_height <= 768:
            base_size = 9
        elif screen_height <= 1080:
            base_size = 10
        elif screen_height <= 1440:
            base_size = 11
        else:
            base_size = 12
        
        # DPI-Anpassung
        dpi_scale = logical_dpi / 96.0
        scaled_size = max(8, int(base_size * min(dpi_scale, 1.3)))  # Maximal 30% Vergrößerung durch DPI
        
        font = QFont()
        font.setPointSize(scaled_size)
        return font
    
    def _get_scaled_element_heights(self) -> dict:
        """Berechnet skalierte Elementhöhen basierend auf Bildschirmgröße"""
        screen = QApplication.primaryScreen()
        if not screen:
            return {
                'input': 30, 'button': 40, 'button_small': 35, 'preview': 50,
                'table_min': 120, 'group_min': 150, 'label_width': 100
            }
        
        screen_geometry = screen.geometry()
        screen_height = screen_geometry.height()
        logical_dpi = screen.logicalDotsPerInch()
        
        # Basis-Skalierungsfaktor
        if screen_height <= 768:
            scale = 0.85
        elif screen_height <= 1080:
            scale = 1.0
        elif screen_height <= 1440:
            scale = 1.15
        else:
            scale = 1.3
        
        # DPI-Anpassung
        dpi_scale = logical_dpi / 96.0
        total_scale = scale * min(dpi_scale, 1.2)  # Maximal 20% DPI-Vergrößerung
        
        return {
            'input': max(25, int(35 * total_scale)),
            'button': max(35, int(45 * total_scale)),
            'button_small': max(30, int(40 * total_scale)),
            'preview': max(40, int(60 * total_scale)),
            'table_min': max(100, int(150 * total_scale)),
            'group_min': max(120, int(180 * total_scale)),
            'label_width': max(80, int(120 * total_scale))
        }

    def update_student_count_preview(self) -> None:
        """Aktualisiert die Vorschau der betroffenen Schüler"""
        source_class = self.source_class_combo.currentText()
        
        if source_class == "-- Klasse auswählen --" or not source_class:
            self.preview_label.setText("Wählen Sie eine Quellklasse aus.")
            self.rename_class_button.setEnabled(False)
            return
        
        try:
            students_in_class = self.db_manager.get_students_in_class(source_class)
            count = len(students_in_class)
            
            if count == 0:
                self.preview_label.setText(f"Keine Schüler in Klasse '{source_class}' gefunden.")
                self.rename_class_button.setEnabled(False)
            else:
                # Zeige auch die Namen der ersten paar Schüler als Vorschau
                preview_names = [f"{s[1]} {s[2]}" for s in students_in_class[:3]]
                names_preview = ", ".join(preview_names)
                if count > 3:
                    names_preview += f" und {count - 3} weitere"
                
                self.preview_label.setText(
                    f"Es werden {count} Schüler aus Klasse '{source_class}' umbenannt.\n"
                    f"Betroffene Schüler: {names_preview}"
                )
                self.rename_class_button.setEnabled(True)
                
        except Exception as e:
            self.preview_label.setText(f"Fehler beim Abrufen der Schüleranzahl: {str(e)}")
            self.rename_class_button.setEnabled(False)

    def perform_mass_assignment(self) -> None:
        """Führt die Klasse umbenennen durch"""
        source_class = self.source_class_combo.currentText()
        target_class = self.target_class_edit.text().strip().upper()
        
        # Eingabevalidierung
        if source_class == "-- Klasse auswählen --" or not source_class:
            QMessageBox.warning(self, "Warnung", "Bitte wählen Sie eine Quellklasse aus.")
            return
            
        if not target_class:
            QMessageBox.warning(self, "Warnung", "Bitte geben Sie eine Zielklasse ein.")
            return
            
        if source_class == target_class:
            QMessageBox.warning(self, "Warnung", "Quell- und Zielklasse dürfen nicht identisch sein.")
            return
        
        try:
            # Schüler in der Quellklasse ermitteln
            students_in_class = self.db_manager.get_students_in_class(source_class)
            student_count = len(students_in_class)
            
            if student_count == 0:
                QMessageBox.information(self, "Information", 
                                      f"Keine Schüler in Klasse '{source_class}' gefunden.")
                return
            
            # Bestätigungsdialog mit Schülerliste
            student_names = [f"• {s[1]} {s[2]}" for s in students_in_class]
            student_list = "\n".join(student_names[:10])  # Zeige maximal 10 Namen
            if student_count > 10:
                student_list += f"\n... und {student_count - 10} weitere Schüler"
            
            reply = QMessageBox.question(
                self, 'Klasse umbenennen bestätigen',
                f"Möchten Sie wirklich {student_count} Schüler von Klasse '{source_class}' "
                f"zu Klasse '{target_class}' umbenennen?\n\n"
                f"Betroffene Schüler:\n{student_list}\n\n"
                f"Diese Aktion kann nicht rückgängig gemacht werden.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Klassen umbenennen durchführen
                affected_rows = self.db_manager.update_students_class(source_class, target_class)
                
                # Erfolgsmeldung
                QMessageBox.information(
                    self, "Erfolg", 
                    f"Erfolgreich {affected_rows} Schüler von Klasse '{source_class}' "
                    f"zu Klasse '{target_class}' umbenannt."
                )
                
                # UI aktualisieren
                self.target_class_edit.clear()
                self.load_class_overview()
                self.update_student_count_preview()
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler bei der Klassenumbenennung:\n{str(e)}")

    def update_delete_preview(self) -> None:
        """Aktualisiert die Vorschau der zu löschenden Schüler und Arbeitstitel"""
        delete_class = self.delete_class_combo.currentText()
        
        if delete_class == "-- Klasse auswählen --" or not delete_class:
            self.delete_preview_label.setText("Wählen Sie eine Klasse zum Löschen aus.")
            self.delete_class_button.setEnabled(False)
            return
        
        try:
            # Schüler in der Klasse ermitteln
            students_in_class = self.db_manager.get_students_in_class(delete_class)
            student_count = len(students_in_class)
            
            if student_count == 0:
                self.delete_preview_label.setText(f"Keine Schüler in Klasse '{delete_class}' gefunden.")
                self.delete_class_button.setEnabled(False)
                return
            
            # Arbeitstitel zählen
            total_work_titles = 0
            for student in students_in_class:
                student_id = student[0]
                work_titles = self.db_manager.get_work_titles(student_id)
                total_work_titles += len(work_titles)
            
            # Zeige die ersten paar Schüler als Vorschau
            preview_names = [f"{s[1]} {s[2]}" for s in students_in_class[:3]]
            names_preview = ", ".join(preview_names)
            if student_count > 3:
                names_preview += f" und {student_count - 3} weitere"
            
            self.delete_preview_label.setText(
                f"🗑️ Es werden {student_count} Schüler und {total_work_titles} Arbeitstitel "
                f"aus Klasse '{delete_class}' PERMANENT gelöscht!\n\n"
                f"Betroffene Schüler: {names_preview}\n\n"
                f"⚠️ Diese Aktion kann NICHT rückgängig gemacht werden!"
            )
            self.delete_class_button.setEnabled(True)
                
        except Exception as e:
            self.delete_preview_label.setText(f"Fehler beim Abrufen der Klasseninformationen: {str(e)}")
            self.delete_class_button.setEnabled(False)

    def perform_class_deletion(self) -> None:
        """Führt die Klassenlöschung durch"""
        delete_class = self.delete_class_combo.currentText()
        
        # Eingabevalidierung
        if delete_class == "-- Klasse auswählen --" or not delete_class:
            QMessageBox.warning(self, "Warnung", "Bitte wählen Sie eine Klasse zum Löschen aus.")
            return
        
        try:
            # Schüler in der Klasse ermitteln
            students_in_class = self.db_manager.get_students_in_class(delete_class)
            student_count = len(students_in_class)
            
            if student_count == 0:
                QMessageBox.information(self, "Information", 
                                      f"Keine Schüler in Klasse '{delete_class}' gefunden.")
                return
            
            # Arbeitstitel zählen
            total_work_titles = 0
            for student in students_in_class:
                student_id = student[0]
                work_titles = self.db_manager.get_work_titles(student_id)
                total_work_titles += len(work_titles)
            
            # Detaillierte Schülerliste für Bestätigung
            student_details = []
            for student in students_in_class:
                student_id, vorname, nachname, klasse = student
                work_titles = self.db_manager.get_work_titles(student_id)
                work_count = len(work_titles)
                student_details.append(f"• {vorname} {nachname} ({work_count} Arbeitstitel)")
            
            student_list = "\n".join(student_details[:10])  # Zeige maximal 10 Namen
            if student_count > 10:
                student_list += f"\n... und {student_count - 10} weitere Schüler"
            
            # Erste Sicherheitsabfrage
            reply1 = QMessageBox.question(
                self, '⚠️ WARNUNG: Klasse löschen',
                f"Sie sind dabei, die gesamte Klasse '{delete_class}' zu löschen!\n\n"
                f"Folgende Daten werden PERMANENT gelöscht:\n"
                f"• {student_count} Schüler\n"
                f"• {total_work_titles} Arbeitstitel\n"
                f"• Alle zugehörigen Bewertungen\n\n"
                f"Betroffene Schüler:\n{student_list}\n\n"
                f"⚠️ Diese Aktion kann NICHT rückgängig gemacht werden!\n\n"
                f"Möchten Sie wirklich fortfahren?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply1 != QMessageBox.StandardButton.Yes:
                return
            
            # Zweite Sicherheitsabfrage
            reply2 = QMessageBox.question(
                self, '🔴 LETZTE WARNUNG: Klasse löschen',
                f"LETZTE BESTÄTIGUNG ERFORDERLICH!\n\n"
                f"Klasse '{delete_class}' mit {student_count} Schülern und "
                f"{total_work_titles} Arbeitstiteln wird PERMANENT gelöscht!\n\n"
                f"Sind Sie absolut sicher, dass Sie fortfahren möchten?\n\n"
                f"💡 Tipp: Erstellen Sie vorher ein Backup über das Hauptmenü!",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply2 == QMessageBox.StandardButton.Yes:
                # Klassenlöschung durchführen
                deleted_work_titles = 0
                deleted_students = 0
                
                # Zuerst alle Arbeitstitel der Schüler in dieser Klasse löschen
                for student in students_in_class:
                    student_id = student[0]
                    work_titles = self.db_manager.get_work_titles(student_id)
                    for work_title in work_titles:
                        work_title_id = work_title[0]
                        self.db_manager.delete_work_title(work_title_id)
                        deleted_work_titles += 1
                
                # Dann alle Schüler in dieser Klasse löschen
                for student in students_in_class:
                    student_id = student[0]
                    self.db_manager.delete_student(student_id)
                    deleted_students += 1
                
                # Erfolgsmeldung
                QMessageBox.information(
                    self, "✅ Klasse gelöscht", 
                    f"Klasse '{delete_class}' wurde erfolgreich gelöscht!\n\n"
                    f"Gelöscht:\n"
                    f"• {deleted_students} Schüler\n"
                    f"• {deleted_work_titles} Arbeitstitel\n\n"
                    f"Die Klassenübersicht wurde aktualisiert."
                )
                
                # UI aktualisieren
                self.load_class_overview()
                self.update_student_count_preview()
                self.update_delete_preview()
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Löschen der Klasse:\n{str(e)}")

    def load_class_overview(self) -> None:
        """Lädt die Klassenübersicht mit Schüleranzahl pro Klasse"""
        try:
            class_data = self.db_manager.get_class_statistics()
            
            # Tabelle aktualisieren
            self.class_overview_table.setRowCount(0)
            for row_index, (class_name, count) in enumerate(class_data):
                self.class_overview_table.insertRow(row_index)
                self.class_overview_table.setItem(row_index, 0, QTableWidgetItem(str(class_name)))
                self.class_overview_table.setItem(row_index, 1, QTableWidgetItem(str(count)))
            
            # Quellklassen-ComboBox aktualisieren (für Umbenennung)
            current_source = self.source_class_combo.currentText()
            self.source_class_combo.clear()
            self.source_class_combo.addItem("-- Klasse auswählen --")
            for class_name, _ in class_data:
                self.source_class_combo.addItem(class_name)
            # Vorherige Auswahl wiederherstellen, falls möglich
            if current_source and current_source != "-- Klasse auswählen --":
                index = self.source_class_combo.findText(current_source)
                if index >= 0:
                    self.source_class_combo.setCurrentIndex(index)
            
            # Löschklassen-ComboBox aktualisieren
            current_delete = self.delete_class_combo.currentText()
            self.delete_class_combo.clear()
            self.delete_class_combo.addItem("-- Klasse auswählen --")
            for class_name, _ in class_data:
                self.delete_class_combo.addItem(class_name)
            # Vorherige Auswahl wiederherstellen, falls möglich
            if current_delete and current_delete != "-- Klasse auswählen --":
                index = self.delete_class_combo.findText(current_delete)
                if index >= 0:
                    self.delete_class_combo.setCurrentIndex(index)
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Klassenübersicht:\n{str(e)}")

# ----------------------- WorkTitleEditDialog -----------------------
class WorkTitleEditDialog(QDialog):
    def __init__(self, student_id: int, db_manager: DatabaseManager,
                 work_data: Optional[Tuple] = None) -> None:
        """
        Falls work_data None ist, wird ein neuer Arbeitstitel angelegt.
        Andernfalls wird work_data zum Bearbeiten geladen.
        """
        super().__init__()
        self.student_id: int = student_id
        self.db_manager: DatabaseManager = db_manager
        self.work_data: Optional[Tuple] = work_data
        self.setWindowTitle("Arbeitstitel bearbeiten" if work_data else "Neuen Arbeitstitel anlegen")
        # Deutlich größeres Fenster
        self.setMinimumSize(1200, 700)  
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QVBoxLayout()

        self.title_edit = QLineEdit()
        self.title_edit.setMinimumHeight(50)  # Höheres Eingabefeld
        self.note_edit = QLineEdit()
        self.note_edit.setMinimumHeight(50)  # Höheres Eingabefeld
        self.soziale_kompetenz_edit = QTextEdit()
        self.aktive_mitarbeit_edit = QTextEdit()
        self.sauberkeit_edit = QTextEdit()
        self.material_edit = QTextEdit()
        self.puenktlichkeit_edit = QTextEdit()
        self.kommentar_edit = QTextEdit()
        
        # Größere Schrift für Labels
        font = QFont()
        font.setPointSize(12)  # Größere Schrift
        
        # Neue Labels für Arbeitstitel
        labels = [
            "Arbeitstitel:", "Note:", "Konzept:", "Ausführung:",
            "Technik:", "Selbstbeurteilung:", "Hat mir gefallen/Nicht gefallen:", "Kommentar:"
        ]
        
        for label_text in labels:
            label = QLabel(label_text)
            label.setFont(font)
            layout.addWidget(label)
            
            if label_text == "Arbeitstitel:":
                layout.addWidget(self.title_edit)
            elif label_text == "Note:":
                layout.addWidget(self.note_edit)
            elif label_text == "Konzept:":  # Ersetzt "Soziale Kompetenz"
                layout.addWidget(self.soziale_kompetenz_edit)
                self.soziale_kompetenz_edit.setMinimumHeight(150)  # Deutlich größer
            elif label_text == "Ausführung:":  # Ersetzt "Aktive Mitarbeit"
                layout.addWidget(self.aktive_mitarbeit_edit)
                self.aktive_mitarbeit_edit.setMinimumHeight(150)  # Deutlich größer
            elif label_text == "Technik:":  # Ersetzt "Sauberkeit"
                layout.addWidget(self.sauberkeit_edit)
                self.sauberkeit_edit.setMinimumHeight(150)  # Deutlich größer
            elif label_text == "Selbstbeurteilung:":  # Ersetzt "Material"
                layout.addWidget(self.material_edit)
                self.material_edit.setMinimumHeight(150)  # Deutlich größer
            elif label_text == "Hat mir gefallen/Nicht gefallen:":  # Ersetzt "Pünktlichkeit"
                layout.addWidget(self.puenktlichkeit_edit)
                self.puenktlichkeit_edit.setMinimumHeight(150)  # Deutlich größer
            elif label_text == "Kommentar:":
                layout.addWidget(self.kommentar_edit)
                self.kommentar_edit.setMinimumHeight(180)  # Deutlich größer

        self.save_button = QPushButton("Speichern")
        self.save_button.setMinimumHeight(50)  # Größerer Button
        self.save_button.setFont(font)  # Größere Schrift für Button
        self.save_button.clicked.connect(self.save_work_title)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

        # Vorbefüllen, falls work_data vorhanden ist
        if self.work_data:
            self.title_edit.setText(self.work_data[1])
            self.note_edit.setText(self.work_data[2])
            self.soziale_kompetenz_edit.setText(self.work_data[3] if self.work_data[3] else "")
            self.aktive_mitarbeit_edit.setText(self.work_data[4] if self.work_data[4] else "")
            self.sauberkeit_edit.setText(self.work_data[5] if self.work_data[5] else "")
            self.material_edit.setText(self.work_data[6] if self.work_data[6] else "")
            self.puenktlichkeit_edit.setText(self.work_data[7] if self.work_data[7] else "")
            self.kommentar_edit.setText(self.work_data[8] if self.work_data[8] else "")

    def save_work_title(self) -> None:
        try:
            title = self.title_edit.text().strip()
            note = self.note_edit.text().strip()
            soziale_kompetenz = self.soziale_kompetenz_edit.toPlainText().strip()
            aktive_mitarbeit = self.aktive_mitarbeit_edit.toPlainText().strip()
            sauberkeit = self.sauberkeit_edit.toPlainText().strip()
            material = self.material_edit.toPlainText().strip()
            puenktlichkeit = self.puenktlichkeit_edit.toPlainText().strip()
            kommentar = self.kommentar_edit.toPlainText().strip()

            if self.work_data:
                work_id = self.work_data[0]
                self.db_manager.update_work_title(
                    work_id, title, note, soziale_kompetenz, aktive_mitarbeit,
                    sauberkeit, material, puenktlichkeit, kommentar
                )
            else:
                self.db_manager.add_work_title(
                    self.student_id, title, note, soziale_kompetenz, aktive_mitarbeit,
                    sauberkeit, material, puenktlichkeit, kommentar
                )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern des Arbeitstitels:\n{str(e)}")

# ----------------------- StudentDetailDialog -----------------------
class StudentDetailDialog(QDialog):
    def __init__(self, student_data: Tuple, db_manager: DatabaseManager) -> None:
        """
        student_data: (id, firstname, lastname, class)
        """
        super().__init__()
        self.student_data: Tuple = student_data
        self.db_manager: DatabaseManager = db_manager
        self.setWindowTitle(f"Schülerdetails: {student_data[1]} {student_data[2]}")
        # Größeres Dialog-Fenster für mehr Platz für die Arbeitstitel
        self.setMinimumSize(1000, 1000)
        self.setup_ui()
        self.load_work_titles()

    def setup_ui(self) -> None:
        # Erstelle ein zentrales Widget für den ScrollArea-Inhalt
        central_widget = QWidget()
        
        # Hauptlayout für den gesamten Dialog-Inhalt
        main_layout = QVBoxLayout(central_widget)
        
        # Standard-Schriftart für Labels
        font = QFont()
        font.setPointSize(11)
        
        # ====================================================
        # BEREICH 1: Schülerdetails (mit eigener ScrollArea)
        # ====================================================
        schueler_group = QGroupBox("Schülerdetails")
        schueler_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                background-color: #F0FFF0;
            }
        """)
        
        # Hauptlayout für die Schülerdetails-GroupBox
        schueler_main_layout = QVBoxLayout(schueler_group)
        
        # ScrollArea für die Schülerdetails-Eingabefelder
        schueler_scroll_area = QScrollArea()
        schueler_scroll_area.setWidgetResizable(True)
        schueler_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        schueler_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        schueler_scroll_area.setMinimumHeight(300)  # Mindesthöhe für bessere Sichtbarkeit
        
        # Widget für den ScrollArea-Inhalt
        schueler_content_widget = QWidget()
        schueler_layout = QVBoxLayout(schueler_content_widget)
        
        # Erstellen der Eingabefelder für Schülerdetails
        self.soziale_kompetenz_edit = QTextEdit()
        self.aktive_mitarbeit_edit = QTextEdit()
        self.sauberkeit_edit = QTextEdit()
        self.material_edit = QTextEdit()
        self.puenktlichkeit_edit = QTextEdit()
        self.kommentar_edit = QTextEdit()
        
        # Daten laden, falls vorhanden
        cursor = self.db_manager.conn.cursor()
        cursor.execute(
            "SELECT soziale_kompetenz, aktive_mitarbeit, sauberkeit, material, puenktlichkeit, kommentar FROM students WHERE id = ?",
            (self.student_data[0],)
        )
        result = cursor.fetchone()
        if result:
            self.soziale_kompetenz_edit.setText(result[0] if result[0] else "")
            self.aktive_mitarbeit_edit.setText(result[1] if result[1] else "")
            self.sauberkeit_edit.setText(result[2] if result[2] else "")
            self.material_edit.setText(result[3] if result[3] else "")
            self.puenktlichkeit_edit.setText(result[4] if result[4] else "")
            self.kommentar_edit.setText(result[5] if result[5] else "")
        
        # Labels und Eingabefelder hinzufügen
        fields = [
            ("Soziale Kompetenz:", self.soziale_kompetenz_edit),
            ("Aktive Mitarbeit:", self.aktive_mitarbeit_edit),
            ("Sauberkeit:", self.sauberkeit_edit),
            ("Material:", self.material_edit),
            ("Pünktlichkeit:", self.puenktlichkeit_edit),
            ("Kommentar:", self.kommentar_edit)
        ]
        
        for label_text, field in fields:
            label = QLabel(label_text)
            label.setFont(font)
            schueler_layout.addWidget(label)
            field.setMinimumHeight(80)
            schueler_layout.addWidget(field)
        
        # ScrollArea-Inhalt setzen
        schueler_scroll_area.setWidget(schueler_content_widget)
        schueler_main_layout.addWidget(schueler_scroll_area)
        
        # Speichern-Button außerhalb der ScrollArea hinzufügen
        self.save_student_button = QPushButton("Schülerdaten speichern")
        self.save_student_button.setMinimumHeight(40)
        self.save_student_button.clicked.connect(self.save_student_details)
        schueler_main_layout.addWidget(self.save_student_button)
        
        # ====================================================
        # BEREICH 2: Arbeitstitel-Liste + Buttons kombiniert
        # ====================================================
        arbeitstitel_widget = QWidget()
        arbeitstitel_main_layout = QVBoxLayout(arbeitstitel_widget)
        
        # Arbeitstitel-Liste
        arbeitstitel_group = QGroupBox("Arbeitstitel")
        arbeitstitel_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #2196F3;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                background-color: #F0F8FF;
            }
        """)
        
        arbeitstitel_layout = QVBoxLayout(arbeitstitel_group)
        
        # Tabelle für Arbeitstitel
        self.work_title_table = QTableWidget()
        self.work_title_table.setColumnCount(3)
        self.work_title_table.setHorizontalHeaderLabels(["", "Titel", "Note"])
        self.work_title_table.cellDoubleClicked.connect(self.edit_work_title)
        
        # ID-Spalte ausblenden
        self.work_title_table.setColumnHidden(0, True)
        
        # Tabellengröße reduzieren (von 400px auf 250px)
        self.work_title_table.setMinimumHeight(200)
        self.work_title_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        
        # Spaltenbreiten optimieren
        header = self.work_title_table.horizontalHeader()
        header.setSectionResizeMode(0, header.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, header.ResizeMode.Stretch)
        header.setSectionResizeMode(2, header.ResizeMode.ResizeToContents)
        
        # Tabelle zum Layout hinzufügen
        arbeitstitel_layout.addWidget(self.work_title_table)
        
        # Kompaktere Innenabstände für das Layout
        arbeitstitel_layout.setContentsMargins(10, 10, 10, 10)
        arbeitstitel_layout.setSpacing(6)  # Reduzierter Abstand zwischen Elementen
        
        arbeitstitel_main_layout.addWidget(arbeitstitel_group)
        
        # ====================================================
        # BEREICH 3: Buttons für Arbeitstitel-Verwaltung
        # ====================================================
        buttons_group = QGroupBox("Arbeitstitel verwalten")
        buttons_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #FF9800;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                background-color: #FFF8E1;
            }
        """)
        
        buttons_layout = QHBoxLayout(buttons_group)
        
        # Buttons erstellen
        self.add_work_title_button = QPushButton("Neuen Arbeitstitel anlegen")
        self.add_work_title_button.setMinimumHeight(50)
        self.add_work_title_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.add_work_title_button.setFont(font)
        self.add_work_title_button.clicked.connect(self.add_work_title)
        
        self.delete_work_title_button = QPushButton("Arbeitstitel löschen")
        self.delete_work_title_button.setMinimumHeight(50)
        self.delete_work_title_button.setStyleSheet("background-color: #FF5555; color: white;")
        self.delete_work_title_button.setFont(font)
        self.delete_work_title_button.clicked.connect(self.delete_work_title)
        
        # Buttons zum Layout hinzufügen
        buttons_layout.addWidget(self.add_work_title_button)
        buttons_layout.addWidget(self.delete_work_title_button)
        
        arbeitstitel_main_layout.addWidget(buttons_group)
        
        # ====================================================
        # QSplitter für verschiebbare Bereiche erstellen
        # ====================================================
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(schueler_group)
        splitter.addWidget(arbeitstitel_widget)
        
        # Anfangsverhältnis der Bereiche setzen (40% Schülerdetails, 60% Arbeitstitel)
        splitter.setSizes([400, 600])
        
        # Mindestgrößen für die Bereiche festlegen
        splitter.setChildrenCollapsible(False)  # Verhindert vollständiges Ausblenden
        schueler_group.setMinimumHeight(200)
        arbeitstitel_widget.setMinimumHeight(200)
        
        # Splitter zum Hauptlayout hinzufügen
        main_layout.addWidget(splitter)
        
        # QScrollArea für den gesamten Dialog erstellen
        dialog_scroll = QScrollArea()
        dialog_scroll.setWidget(central_widget)
        dialog_scroll.setWidgetResizable(True)
        dialog_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        dialog_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Dialog-Layout erstellen und ScrollArea hinzufügen
        dialog_layout = QVBoxLayout()
        dialog_layout.addWidget(dialog_scroll)
        dialog_layout.setContentsMargins(0, 0, 0, 0)  # Keine zusätzlichen Ränder
        
        # Gesamtlayout für den Dialog anwenden
        self.setLayout(dialog_layout)

    def save_student_details(self) -> None:
        try:
            soziale_kompetenz = self.soziale_kompetenz_edit.toPlainText().strip()
            aktive_mitarbeit = self.aktive_mitarbeit_edit.toPlainText().strip()
            sauberkeit = self.sauberkeit_edit.toPlainText().strip()
            material = self.material_edit.toPlainText().strip()
            puenktlichkeit = self.puenktlichkeit_edit.toPlainText().strip()
            kommentar = self.kommentar_edit.toPlainText().strip()
            self.db_manager.update_student_details(
                self.student_data[0], soziale_kompetenz, aktive_mitarbeit, sauberkeit,
                material, puenktlichkeit, kommentar
            )
            QMessageBox.information(self, "Erfolg", "Schülerdaten aktualisiert.")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern der Schülerdaten:\n{str(e)}")

    def load_work_titles(self) -> None:
        work_titles = self.db_manager.get_work_titles(self.student_data[0])
        self.work_title_table.setRowCount(0)
        for row_index, wt in enumerate(work_titles):
            self.work_title_table.insertRow(row_index)
            # ID wird weiterhin in versteckte Spalte geladen, wird für Funktionalität benötigt
            self.work_title_table.setItem(row_index, 0, QTableWidgetItem(str(wt[0])))
            self.work_title_table.setItem(row_index, 1, QTableWidgetItem(wt[1]))
            self.work_title_table.setItem(row_index, 2, QTableWidgetItem(wt[2]))

    def add_work_title(self) -> None:
        dialog = WorkTitleEditDialog(self.student_data[0], self.db_manager)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_work_titles()

    def delete_work_title(self) -> None:
        selected_row = self.work_title_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Warnung", "Bitte wählen Sie einen Arbeitstitel aus.")
            return
        work_id = int(self.work_title_table.item(selected_row, 0).text())
        self.db_manager.delete_work_title(work_id)
        self.load_work_titles()

    def edit_work_title(self, row: int, column: int) -> None:
        work_id = int(self.work_title_table.item(row, 0).text())
        work_titles = self.db_manager.get_work_titles(self.student_data[0])
        work_data: Optional[Tuple] = None
        for wt in work_titles:
            if wt[0] == work_id:
                work_data = wt
                break
        if not work_data:
            QMessageBox.warning(self, "Fehler", "Arbeitstiteldaten nicht gefunden.")
            return
        dialog = WorkTitleEditDialog(self.student_data[0], self.db_manager, work_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_work_titles()

# ----------------------- MainWindow -----------------------
class MainWindow(QMainWindow):
    def __init__(self) -> None:
        try:
            super().__init__()
            self.setWindowTitle("Schülerverwaltung")
            
            # Datenbank-Manager initialisieren
            try:
                self.db_manager = DatabaseManager()
            except Exception as e:
                QMessageBox.critical(None, "Datenbankfehler", 
                                   f"Fehler beim Initialisieren der Datenbank:\n{str(e)}")
                raise
            
            # Fenstergröße basierend auf Bildschirmauflösung einstellen
            screen = QApplication.primaryScreen()
            if screen:
                screen_geometry = screen.geometry()
                width = int(screen_geometry.width() * 0.8)  # 80% der Bildschirmbreite
                height = int(screen_geometry.height() * 0.8) # 80% der Bildschirmhöhe
                self.resize(width, height)
                self.setMinimumSize(int(screen_geometry.width() * 0.5), int(screen_geometry.height() * 0.5))
            else:
                self.setMinimumSize(600, 600)  # Minimale Fenstergröße als Fallback

            self.setup_ui()
            self.load_students()
            
        except Exception as e:
            QMessageBox.critical(None, "Initialisierungsfehler", 
                               f"Fehler beim Initialisieren des Hauptfensters:\n{str(e)}")
            raise

    def setup_ui(self) -> None:
        layout = QVBoxLayout()
        
        # Größere Schrift für die ganze App
        font = QFont()
        font.setPointSize(11)
        QApplication.instance().setFont(font)

        # Formular zum Anlegen eines Schülers
        form_layout = QHBoxLayout()
        self.firstname_edit = QLineEdit()
        self.firstname_edit.setPlaceholderText("Vorname")
        self.firstname_edit.setMinimumHeight(35)
        self.lastname_edit = QLineEdit()
        self.lastname_edit.setPlaceholderText("Nachname")
        self.lastname_edit.setMinimumHeight(35)
        self.class_edit = QLineEdit()
        self.class_edit.setPlaceholderText("Klasse")
        self.class_edit.setMinimumHeight(35)
        form_layout.addWidget(self.firstname_edit)
        form_layout.addWidget(self.lastname_edit)
        form_layout.addWidget(self.class_edit)

        self.add_student_button = QPushButton("Schüler anlegen")
        self.add_student_button.setMinimumHeight(35)
        self.add_student_button.clicked.connect(self.add_student)
        form_layout.addWidget(self.add_student_button)

        layout.addLayout(form_layout)

        # Suchfeld und Klassenfilter
        filter_layout = QHBoxLayout()
        
        # Suchfeld für Namen
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Nach Schüler suchen...")
        self.search_edit.setMinimumHeight(35)
        self.search_edit.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.search_edit)
        
        # Klassenfilter-ComboBox
        self.class_filter_combo = QComboBox()
        self.class_filter_combo.setMinimumHeight(35)
        self.class_filter_combo.setMinimumWidth(150)
        self.class_filter_combo.setEditable(True)  # Ermöglicht Texteingabe
        self.class_filter_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)  # Verhindert Hinzufügen durch Benutzer
        self.class_filter_combo.currentTextChanged.connect(self.apply_filters)  # Für Echtzeit-Filterung
        filter_layout.addWidget(self.class_filter_combo)
        
        # Suchbutton (optional)
        self.search_button = QPushButton("Suchen")
        self.search_button.setMinimumHeight(35)
        self.search_button.clicked.connect(self.apply_filters)
        filter_layout.addWidget(self.search_button)
        
        layout.addLayout(filter_layout)

        # Tabelle der Schüler
        self.student_table = QTableWidget()
        self.student_table.setColumnCount(4)  # Behalten wir bei 4 Spalten
        self.student_table.setHorizontalHeaderLabels(["", "Vorname", "Nachname", "Klasse"])
        self.student_table.cellDoubleClicked.connect(self.open_student_details)
        
        # ID-Spalte komplett ausblenden
        self.student_table.setColumnHidden(0, True)
        
        # Tabelle soll den verfügbaren Platz nutzen
        self.student_table.horizontalHeader().setStretchLastSection(True)
        # Verbinden der row selection mit der Aktivierung des PDF-Export-Buttons
        self.student_table.itemSelectionChanged.connect(self.update_button_states)
        
        # Sortierung aktivieren
        self.student_table.setSortingEnabled(True)
        # Sortierfilter für bestimmte Spalten konfigurieren
        self.student_table.horizontalHeader().setSortIndicatorShown(True)
        
        # Spalte für ID kleiner machen, da sie kein Label mehr hat
        header = self.student_table.horizontalHeader()
        # Alle Spalten gleich breit
        for i in range(self.student_table.columnCount()):
            header.setSectionResizeMode(i, header.ResizeMode.Stretch)
        
        layout.addWidget(self.student_table)

        # Button-Layouts für Aktionen unter der Schülertabelle
        buttons_layout = QHBoxLayout()
        
        self.delete_student_button = QPushButton("Schüler löschen")
        self.delete_student_button.setMinimumHeight(40)
        self.delete_student_button.setStyleSheet("background-color: #FF5555;")
        self.delete_student_button.clicked.connect(self.delete_student)
        buttons_layout.addWidget(self.delete_student_button)
        
        # Klassen bearbeiten Button hinzufügen
        self.manage_classes_button = QPushButton("Klassen bearbeiten")
        self.manage_classes_button.setMinimumHeight(40)
        self.manage_classes_button.setStyleSheet("background-color: #2196F3; color: white;")
        self.manage_classes_button.clicked.connect(self.open_class_management)
        buttons_layout.addWidget(self.manage_classes_button)
        
        # Backup/Restore Button hinzufügen
        self.backup_restore_button = QPushButton("Backup && Wiederherstellung")
        self.backup_restore_button.setMinimumHeight(40)
        self.backup_restore_button.setStyleSheet("background-color: #9C27B0; color: white;")
        self.backup_restore_button.clicked.connect(self.open_backup_restore)
        buttons_layout.addWidget(self.backup_restore_button)
        
        # PDF-Export-Button hinzufügen
        self.export_pdf_button = QPushButton("Export als PDF")
        self.export_pdf_button.setMinimumHeight(40)
        self.export_pdf_button.setStyleSheet("background-color: #55AA55;")
        self.export_pdf_button.clicked.connect(self.export_to_pdf)
        self.export_pdf_button.setEnabled(False)  # Initial deaktiviert
        buttons_layout.addWidget(self.export_pdf_button)
        
        # Beenden-Button hinzufügen
        self.exit_button = QPushButton("Beenden")
        self.exit_button.setMinimumHeight(40)
        self.exit_button.setStyleSheet("background-color: #FF5555;")
        self.exit_button.clicked.connect(self.close_application)
        buttons_layout.addWidget(self.exit_button)
        
        layout.addLayout(buttons_layout)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
    
    def update_button_states(self) -> None:
        """Aktiviert oder deaktiviert Buttons basierend auf der Schülerauswahl"""
        selected_rows = self.student_table.selectedItems()
        self.export_pdf_button.setEnabled(len(selected_rows) > 0)
        # Nur bei verfügbarer reportlab Bibliothek aktivieren
        if not REPORTLAB_AVAILABLE:
            self.export_pdf_button.setEnabled(False)
            self.export_pdf_button.setToolTip("Reportlab-Bibliothek nicht verfügbar. Bitte installieren Sie 'reportlab'.")
    
    def export_to_pdf(self) -> None:
        """Exportiert die Daten des ausgewählten Schülers als PDF"""
        if not REPORTLAB_AVAILABLE:
            QMessageBox.warning(self, "Fehler", 
                                "Reportlab-Bibliothek nicht verfügbar. Bitte installieren Sie 'reportlab' mit dem Befehl:\npip install reportlab")
            return
            
        selected_row = self.student_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Warnung", "Bitte wählen Sie einen Schüler aus.")
            return
        
        student_id = int(self.student_table.item(selected_row, 0).text())
        firstname = self.student_table.item(selected_row, 1).text()
        lastname = self.student_table.item(selected_row, 2).text()
        klass = self.student_table.item(selected_row, 3).text()
        
        # Dateinamen erstellen und Sonderzeichen ersetzen
        safe_firstname = firstname.replace(" ", "_").replace("/", "_").replace("\\", "_")
        safe_lastname = lastname.replace(" ", "_").replace("/", "_").replace("\\", "_")
        safe_klass = klass.replace(" ", "_").replace("/", "_").replace("\\", "_")
        filename = f"{safe_firstname}_{safe_lastname}_{safe_klass}.pdf"
        
        # Alle Daten des Schülers abrufen
        cursor = self.db_manager.conn.cursor()
        cursor.execute(
            "SELECT soziale_kompetenz, aktive_mitarbeit, sauberkeit, material, puenktlichkeit, kommentar "
            "FROM students WHERE id = ?", (student_id,)
        )
        student_details = cursor.fetchone()
        
        # Arbeitstitel des Schülers abrufen
        work_titles = self.db_manager.get_work_titles(student_id)
        
        try:
            # PDF erstellen
            doc = SimpleDocTemplate(filename, pagesize=A4,
                                   topMargin=1*cm, bottomMargin=1*cm,
                                   leftMargin=1.5*cm, rightMargin=1.5*cm)
            styles = getSampleStyleSheet()
            
            # Eigene Styles definieren
            title_style = ParagraphStyle(
                'TitleStyle',
                parent=styles['Heading1'],
                fontSize=18,
                leading=22,
                alignment=1,  # Zentriert
                spaceAfter=12
            )
            heading2_style = ParagraphStyle(
                'Heading2Style',
                parent=styles['Heading2'],
                fontSize=14,
                leading=18,
                spaceBefore=6,
                spaceAfter=6
            )
            heading3_style = ParagraphStyle(
                'Heading3Style',
                parent=styles['Heading3'],
                fontSize=12,
                leading=14,
                spaceBefore=4,
                spaceAfter=4
            )
            normal_style = ParagraphStyle(
                'NormalStyle',
                parent=styles['Normal'],
                fontSize=10,
                leading=12,
                spaceAfter=3
            )
            
            elements = []
            
            # Titel
            elements.append(Paragraph(f"Schülerdaten: {firstname} {lastname}, Klasse: {klass}", title_style))
            elements.append(Spacer(1, 0.5*cm))
            
            # Schülerdetails als Tabelle
            if student_details:
                data = [
                    ["Soziale Kompetenz", student_details[0] if student_details[0] else ""],
                    ["Aktive Mitarbeit", student_details[1] if student_details[1] else ""],
                    ["Sauberkeit", student_details[2] if student_details[2] else ""],
                    ["Material", student_details[3] if student_details[3] else ""],
                    ["Pünktlichkeit", student_details[4] if student_details[4] else ""],
                    ["Kommentar", student_details[5] if student_details[5] else ""]
                ]
                
                table = Table(data, colWidths=[5*cm, 11*cm])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
                    ('TEXTCOLOR', (0,0), (0,-1), colors.black),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,0), 10),
                    ('BOTTOMPADDING', (0,0), (-1,0), 6),
                    ('BACKGROUND', (0,1), (-1,-1), colors.white),
                    ('GRID', (0,0), (-1,-1), 1, colors.black)
                ]))
                elements.append(Paragraph("<b>Schülerdetails:</b>", heading2_style))
                elements.append(table)
                elements.append(Spacer(1, 0.5*cm))
            
            # Arbeitstitel: Pro Arbeitstitel eine eigene Tabelle
            if work_titles:
                elements.append(Paragraph("<b>Arbeitstitel:</b>", heading2_style))
                for work in work_titles:
                    table_data = [
                        ["Titel", work[1] if work[1] else ""],
                        ["Note", work[2] if work[2] else ""],
                        ["Konzept", work[3] if work[3] else ""],
                        ["Ausführung", work[4] if work[4] else ""],
                        ["Technik", work[5] if work[5] else ""],
                        ["Selbstbeurteilung", work[6] if work[6] else ""],
                        ["Hat mir gefallen/Nicht gefallen", work[7] if work[7] else ""],
                        ["Kommentar", work[8] if work[8] else ""]
                    ]
                    
                    work_table = Table(table_data, colWidths=[5*cm, 11*cm])
                    work_table.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
                        ('TEXTCOLOR', (0,0), (0,-1), colors.black),
                        ('FONTNAME', (0,0), (0,0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0,0), (0,0), 10),
                        ('BOTTOMPADDING', (0,0), (0,0), 6),
                        ('BACKGROUND', (0,1), (-1,-1), colors.white),
                        ('GRID', (0,0), (-1,-1), 1, colors.black),
                        ('FONTSIZE', (0,1), (-1,-1), 8)
                    ]))
                    elements.append(Paragraph(f"<b>Arbeitstitel:</b>", heading3_style))
                    elements.append(work_table)
                    elements.append(Spacer(1, 0.3*cm))
            
            # PDF generieren
            doc.build(elements)
            
            # Erfolgsmeldung anzeigen
            QMessageBox.information(self, "Erfolg", f"PDF wurde erfolgreich erstellt:\n{filename}")
            
            # Optional: PDF direkt öffnen
            try:
                if sys.platform == 'win32':
                    os.startfile(filename)
                elif sys.platform == 'darwin':  # macOS
                    import subprocess
                    subprocess.call(['open', filename])
                else:  # Linux
                    import subprocess
                    subprocess.call(['xdg-open', filename])
            except Exception as e:
                print(f"Fehler beim Öffnen der PDF: {e}")
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Erstellen der PDF:\n{str(e)}")

    def add_student(self) -> None:
        firstname = self.firstname_edit.text().strip()
        lastname = self.lastname_edit.text().strip()
        klass = self.class_edit.text().strip().upper()
        if not firstname or not lastname:
            QMessageBox.warning(self, "Warnung", "Vor- und Nachname sind erforderlich.")
            return
        try:
            self.db_manager.add_student(firstname, lastname, klass)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Hinzufügen des Schülers:\n{str(e)}")
            return
        self.firstname_edit.clear()
        self.lastname_edit.clear()
        self.class_edit.clear()
        
        # Klassenfilter aktualisieren, falls neue Klasse hinzugefügt wurde
        self.update_class_filter()
        
        self.load_students()

    def update_class_filter(self) -> None:
        """Aktualisiert die Klassenfilter-ComboBox mit allen vorhandenen Klassen"""
        # Aktuelle Auswahl merken
        current_text = self.class_filter_combo.currentText()
        
        # ComboBox leeren
        self.class_filter_combo.clear()
        
        # "Alle Klassen" Option hinzufügen
        self.class_filter_combo.addItem("Alle Klassen")
        
        # Alle Klassen aus der Datenbank abrufen und hinzufügen
        classes = self.db_manager.get_unique_classes()
        for class_name in classes:
            self.class_filter_combo.addItem(class_name)
            
        # Vorherige Auswahl wiederherstellen, wenn möglich
        index = self.class_filter_combo.findText(current_text)
        if index >= 0:
            self.class_filter_combo.setCurrentIndex(index)
        else:
            self.class_filter_combo.setCurrentIndex(0)  # "Alle Klassen" auswählen

    def load_students(self) -> None:
        try:
            # Sortierung während des Ladens deaktivieren
            self.student_table.setSortingEnabled(False)
            
            # Klassenfilterliste beim ersten Laden der App aktualisieren
            if not hasattr(self, 'class_filter_initialized'):
                self.update_class_filter()
                self.class_filter_initialized = True
            
            # Restliche Logik für das Laden von Studenten...
            students = self.db_manager.get_students()  # Bereits nach Klasse sortiert
            self.student_table.setRowCount(0)
            for row_index, student in enumerate(students):
                self.student_table.insertRow(row_index)
                # ID wird in versteckte Spalte geladen, wird für Funktionalität benötigt
                for col_index, value in enumerate(student):
                    self.student_table.setItem(row_index, col_index, QTableWidgetItem(str(value)))
            
            # Sortierung wieder aktivieren
            self.student_table.setSortingEnabled(True)
            
            # Standardsortierung nach Klasse (Spalte 3)
            self.student_table.sortItems(3, Qt.SortOrder.AscendingOrder)
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Datenbankfehler", f"Fehler beim Laden der Schülerdaten:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Unerwarteter Fehler beim Laden der Schülerdaten:\n{str(e)}")

    def search_students(self) -> None:
        """Veraltete Methode, wird durch apply_filters ersetzt"""
        self.apply_filters()

    def apply_filters(self) -> None:
        """Wendet sowohl den Textfilter als auch den Klassenfilter auf die Schülerliste an"""
        try:
            # Sortierung während des Filterns deaktivieren
            self.student_table.setSortingEnabled(False)
            
            keyword = self.search_edit.text().strip()
            class_filter = self.class_filter_combo.currentText()
            
            # Wenn "Alle Klassen" gewählt ist oder leer, dann keine Klassenfilterung
            if class_filter == "Alle Klassen" or not class_filter:
                if not keyword:
                    # Weder Name- noch Klassenfilter aktiv
                    students = self.db_manager.get_students()
                else:
                    # Nur Namenfilter aktiv
                    students = self.db_manager.search_students(keyword)
            else:
                # Klassenfilter (und optional Namenfilter) aktiv
                cursor = self.db_manager.conn.cursor()
                if not keyword:
                    # Nur Klassenfilter
                    cursor.execute("""
                        SELECT id, firstname, lastname, class FROM students
                        WHERE class = ? ORDER BY class
                    """, (class_filter,))
                else:
                    # Klassen- und Namenfilter
                    cursor.execute("""
                        SELECT id, firstname, lastname, class FROM students
                        WHERE (firstname LIKE ? OR lastname LIKE ?) AND class = ?
                        ORDER BY class
                    """, (f"%{keyword}%", f"%{keyword}%", class_filter))
                students = cursor.fetchall()
            
            # Tabelle mit gefilterten Ergebnissen aktualisieren
            self.student_table.setRowCount(0)
            for row_index, student in enumerate(students):
                self.student_table.insertRow(row_index)
                for col_index, value in enumerate(student):
                    self.student_table.setItem(row_index, col_index, QTableWidgetItem(str(value)))
                    
            # Sortierung wieder aktivieren
            self.student_table.setSortingEnabled(True)
            
            # Standardsortierung nach Klasse
            self.student_table.sortItems(3, Qt.SortOrder.AscendingOrder)
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Datenbankfehler", f"Fehler beim Filtern der Schülerdaten:\n{str(e)}")
            # Bei Datenbankfehler alle Schüler laden
            try:
                self.load_students()
            except Exception:
                pass
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Unerwarteter Fehler beim Filtern:\n{str(e)}")
            # Bei unbekanntem Fehler alle Schüler laden
            try:
                self.load_students()
            except Exception:
                pass

    # Diese Methode überschreiben, da wir jetzt apply_filters verwenden
    def search_students(self) -> None:
        self.apply_filters()

    def delete_student(self) -> None:
        try:
            selected_row = self.student_table.currentRow()
            if selected_row == -1:
                QMessageBox.warning(self, "Warnung", "Bitte wählen Sie einen Schüler aus.")
                return
            
            # Bestätigungsdialog
            student_name = f"{self.student_table.item(selected_row, 1).text()} {self.student_table.item(selected_row, 2).text()}"
            reply = QMessageBox.question(
                self, 'Schüler löschen',
                f"Möchten Sie den Schüler '{student_name}' wirklich löschen?\n\n"
                f"Alle zugehörigen Arbeitstitel werden ebenfalls gelöscht.\n"
                f"Diese Aktion kann nicht rückgängig gemacht werden.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                student_id = int(self.student_table.item(selected_row, 0).text())
                self.db_manager.delete_student(student_id)
                self.load_students()
                QMessageBox.information(self, "Erfolg", f"Schüler '{student_name}' wurde erfolgreich gelöscht.")
                
        except ValueError as e:
            QMessageBox.critical(self, "Fehler", f"Ungültige Schüler-ID:\n{str(e)}")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Datenbankfehler", f"Fehler beim Löschen des Schülers:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Unerwarteter Fehler beim Löschen:\n{str(e)}")

    def open_student_details(self, row: int, column: int) -> None:
        try:
            student_id = int(self.student_table.item(row, 0).text())
            firstname = self.student_table.item(row, 1).text()
            lastname = self.student_table.item(row, 2).text()
            klass = self.student_table.item(row, 3).text()
            student_data = (student_id, firstname, lastname, klass)
            dialog = StudentDetailDialog(student_data, self.db_manager)
            dialog.exec()
            self.load_students()
        except ValueError as e:
            QMessageBox.critical(self, "Fehler", f"Ungültige Schülerdaten:\n{str(e)}")
        except AttributeError as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Zugriff auf Schülerdaten:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Unerwarteter Fehler beim Öffnen der Schülerdetails:\n{str(e)}")

    def open_class_management(self) -> None:
        """Öffnet den Klassenverwaltungsdialog"""
        try:
            dialog = ClassManagementDialog(self.db_manager)
            dialog.exec()
            # Nach dem Schließen des Dialogs immer aktualisieren
            self.update_class_filter()
            self.load_students()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Datenbankfehler", f"Fehler beim Öffnen der Klassenverwaltung:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Unerwarteter Fehler beim Öffnen der Klassenverwaltung:\n{str(e)}")

    def open_backup_restore(self) -> None:
        """Öffnet den Backup/Restore-Dialog"""
        try:
            dialog = BackupRestoreDialog(self.db_manager)
            result = dialog.exec()
            
            # Nach Wiederherstellung alle Daten neu laden
            if result == QDialog.DialogCode.Accepted:
                self.update_class_filter()
                self.load_students()
                QMessageBox.information(
                    self, "Aktualisierung", 
                    "Die Anwendung wurde nach der Wiederherstellung aktualisiert."
                )
                
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Datenbankfehler", f"Fehler beim Öffnen der Backup-Verwaltung:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Unerwarteter Fehler beim Öffnen der Backup-Verwaltung:\n{str(e)}")

    # Neue Methode zum Beenden der Anwendung
    def close_application(self) -> None:
        try:
            # Optional: Bestätigungsdialog anzeigen
            reply = QMessageBox.question(
                self, 'Bestätigung',
                "Möchten Sie die Anwendung wirklich beenden?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Datenbank sicher schließen
                try:
                    self.db_manager.close()
                except Exception:
                    pass  # Ignoriere Fehler beim Schließen der DB
                
                QApplication.instance().quit()
        except Exception as e:
            # Bei Fehlern trotzdem beenden
            print(f"Fehler beim Beenden der Anwendung: {e}")
            QApplication.instance().quit()

def main() -> None:
    try:
        app = QApplication(sys.argv)
        
        # Allgemeine Stylesheet-Einstellungen für die gesamte App
        app.setStyle('Fusion')  # Modern-aussehender Style
        
        # Hauptfenster erstellen und anzeigen
        try:
            window = MainWindow()
            window.showMaximized()  # Maximiert das Fenster
            sys.exit(app.exec())
        except Exception as e:
            QMessageBox.critical(None, "Initialisierungsfehler", 
                               f"Fehler beim Erstellen des Hauptfensters:\n{str(e)}")
            sys.exit(1)
            
    except ImportError as e:
        print(f"Fehlende Abhängigkeit: {str(e)}")
        print("Bitte installieren Sie die erforderlichen Pakete mit: pip install PyQt6 reportlab")
        sys.exit(1)
    except Exception as e:
        print(f"Kritischer Fehler beim Starten der Anwendung: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

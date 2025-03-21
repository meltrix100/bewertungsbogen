import sys, os, sqlite3
from typing import List, Tuple, Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QTableWidget, QTableWidgetItem,
    QDialog, QTextEdit, QGroupBox, QComboBox
)
from PyQt6.QtCore import Qt
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
        self.db_path: str = db_path
        self.conn: sqlite3.Connection = sqlite3.connect(self.db_path)
        self.create_tables()

    def create_tables(self) -> None:
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

    def add_student(self, firstname: str, lastname: str, klass: str) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO students (firstname, lastname, class) VALUES (?, ?, ?)",
            (firstname, lastname, klass)
        )
        self.conn.commit()

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
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM work_titles WHERE student_id = ?", (student_id,))
        cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
        self.conn.commit()

    def search_students(self, keyword: str) -> List[Tuple]:
        cursor = self.conn.cursor()
        keyword = f"%{keyword}%"
        cursor.execute("""
            SELECT id, firstname, lastname, class FROM students
            WHERE firstname LIKE ? OR lastname LIKE ? 
            ORDER BY class
        """, (keyword, keyword))
        return cursor.fetchall()

    def get_students(self) -> List[Tuple]:
        cursor = self.conn.cursor()
        # Standardmäßig nach Klasse sortieren (class ist Spalte 3)
        cursor.execute("SELECT id, firstname, lastname, class FROM students ORDER BY class")
        return cursor.fetchall()

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
            "Technik:", "Selbstbeurteilung:", "Hat mir gefalle/Nicht gefallen:", "Kommentar:"
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
        # Hauptlayout für den gesamten Dialog
        main_layout = QVBoxLayout()
        
        # Standard-Schriftart für Labels
        font = QFont()
        font.setPointSize(11)
        
        # ====================================================
        # BEREICH 1: Schülerdetails
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
        
        schueler_layout = QVBoxLayout(schueler_group)
        
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
        
        # Speichern-Button zum Schülerdetail-Bereich hinzufügen
        self.save_student_button = QPushButton("Schülerdaten speichern")
        self.save_student_button.setMinimumHeight(40)
        self.save_student_button.clicked.connect(self.save_student_details)
        schueler_layout.addWidget(self.save_student_button)
        
        # Schülerdetails zum Hauptlayout hinzufügen
        main_layout.addWidget(schueler_group)
        
        # ====================================================
        # BEREICH 2: Arbeitstitel-Liste
        # ====================================================
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
        
        # Arbeitstitel-Bereich zum Hauptlayout hinzufügen
        main_layout.addWidget(arbeitstitel_group)
        
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
        
        # Buttons-Bereich zum Hauptlayout hinzufügen
        main_layout.addWidget(buttons_group)
        
        # Gesamtlayout anwenden
        self.setLayout(main_layout)

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
        super().__init__()
        self.setWindowTitle("Schülerverwaltung")
        self.db_manager = DatabaseManager()
        #self.showFullScreen()  # Jetzt im Vollbildmodus
        #self.showMaximized()  # Maximiert das Fenster
        #self.setMinimumSize(1000, 800)  # Minimale Fenstergröße

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

    def search_students(self) -> None:
        """Veraltete Methode, wird durch apply_filters ersetzt"""
        self.apply_filters()

    def apply_filters(self) -> None:
        """Wendet sowohl den Textfilter als auch den Klassenfilter auf die Schülerliste an"""
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

    # Diese Methode überschreiben, da wir jetzt apply_filters verwenden
    def search_students(self) -> None:
        self.apply_filters()

    def delete_student(self) -> None:
        selected_row = self.student_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Warnung", "Bitte wählen Sie einen Schüler aus.")
            return
        student_id = int(self.student_table.item(selected_row, 0).text())
        self.db_manager.delete_student(student_id)
        self.load_students()

    def open_student_details(self, row: int, column: int) -> None:
        student_id = int(self.student_table.item(row, 0).text())
        firstname = self.student_table.item(row, 1).text()
        lastname = self.student_table.item(row, 2).text()
        klass = self.student_table.item(row, 3).text()
        student_data = (student_id, firstname, lastname, klass)
        dialog = StudentDetailDialog(student_data, self.db_manager)
        dialog.exec()
        self.load_students()

    # Neue Methode zum Beenden der Anwendung
    def close_application(self) -> None:
        # Optional: Bestätigungsdialog anzeigen
        reply = QMessageBox.question(
            self, 'Bestätigung',
            "Möchten Sie die Anwendung wirklich beenden?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            QApplication.instance().quit()

def main() -> None:
    app = QApplication(sys.argv)
    
    # Allgemeine Stylesheet-Einstellungen für die gesamte App
    app.setStyle('Fusion')  # Modern-aussehender Style
    
    window = MainWindow()
    #window.show()
    window.showMaximized()  # Maximiert das Fenster
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

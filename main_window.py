import sys
from typing import List, Tuple, Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QTableWidget, QTableWidgetItem,
    QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from database_manager import DatabaseManager
from dialogs import StudentDetailDialog
from pdf_export import export_student_to_pdf, open_pdf, REPORTLAB_AVAILABLE

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Schülerverwaltung")
        self.db_manager = DatabaseManager()

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
        
        # Flag für die Initialisierung des Klassenfilters
        self.class_filter_initialized = False

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
        self.student_table.setColumnCount(4)
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
        
        try:
            student_id = int(self.student_table.item(selected_row, 0).text())
            firstname = self.student_table.item(selected_row, 1).text()
            lastname = self.student_table.item(selected_row, 2).text()
            klass = self.student_table.item(selected_row, 3).text()
            
            # Alle Daten des Schülers abrufen
            student_details = self.db_manager.get_student_details(student_id)
            
            # Arbeitstitel des Schülers abrufen
            work_titles = self.db_manager.get_work_titles(student_id)
            
            # PDF erstellen
            filename = export_student_to_pdf(student_id, firstname, lastname, klass, student_details, work_titles)
            
            # Erfolgsmeldung anzeigen
            QMessageBox.information(self, "Erfolg", f"PDF wurde erfolgreich erstellt:\n{filename}")
            
            # PDF öffnen
            open_pdf(filename)
                
        except ImportError:
            QMessageBox.critical(self, "Fehler", "Reportlab-Bibliothek nicht verfügbar.")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Erstellen oder Öffnen der PDF:\n{str(e)}")

    def add_student(self) -> None:
        firstname = self.firstname_edit.text().strip()
        lastname = self.lastname_edit.text().strip()
        klass = self.class_edit.text().strip().upper()
        
        try:
            # Validierung in der Datenbank-Klasse
            self.db_manager.add_student(firstname, lastname, klass)
            self.firstname_edit.clear()
            self.lastname_edit.clear()
            self.class_edit.clear()
            
            # Klassenfilter aktualisieren, falls neue Klasse hinzugefügt wurde
            self.update_class_filter()
            
            self.load_students()
        except ValueError as e:
            QMessageBox.warning(self, "Warnung", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Hinzufügen des Schülers:\n{str(e)}")

    def update_class_filter(self) -> None:
        """Aktualisiert die Klassenfilter-ComboBox mit allen vorhandenen Klassen"""
        try:
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
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Aktualisieren des Klassenfilters:\n{str(e)}")

    def load_students(self) -> None:
        try:
            # Sortierung während des Ladens deaktivieren
            self.student_table.setSortingEnabled(False)
            
            # Klassenfilterliste beim ersten Laden der App aktualisieren
            if not self.class_filter_initialized:
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
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Schüler:\n{str(e)}")

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
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Anwenden der Filter:\n{str(e)}")

    def delete_student(self) -> None:
        try:
            selected_row = self.student_table.currentRow()
            if selected_row == -1:
                QMessageBox.warning(self, "Warnung", "Bitte wählen Sie einen Schüler aus.")
                return
                
            # Bestätigung anfordern
            student_name = f"{self.student_table.item(selected_row, 1).text()} {self.student_table.item(selected_row, 2).text()}"
            reply = QMessageBox.question(
                self, "Schüler löschen",
                f"Möchten Sie den Schüler '{student_name}' wirklich löschen?\nDies löscht auch alle zugehörigen Arbeitstitel.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                student_id = int(self.student_table.item(selected_row, 0).text())
                self.db_manager.delete_student(student_id)
                # Klassenfilter aktualisieren, falls sich Klassen geändert haben
                self.update_class_filter()
                self.load_students()
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Löschen des Schülers:\n{str(e)}")

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
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Öffnen der Schülerdetails:\n{str(e)}")

    def close_application(self) -> None:
        # Bestätigungsdialog anzeigen
        reply = QMessageBox.question(
            self, 'Bestätigung',
            "Möchten Sie die Anwendung wirklich beenden?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Datenbank-Verbindung sauber schließen
            try:
                self.db_manager.close()
            except:
                pass
            QApplication.instance().quit()

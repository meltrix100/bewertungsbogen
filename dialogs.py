from typing import Tuple, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QTableWidget, QTableWidgetItem, QTextEdit, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from database_manager import DatabaseManager

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
        result = self.db_manager.get_student_details(self.student_data[0])
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
        try:
            work_titles = self.db_manager.get_work_titles(self.student_data[0])
            self.work_title_table.setRowCount(0)
            for row_index, wt in enumerate(work_titles):
                self.work_title_table.insertRow(row_index)
                # ID wird weiterhin in versteckte Spalte geladen, wird für Funktionalität benötigt
                self.work_title_table.setItem(row_index, 0, QTableWidgetItem(str(wt[0])))
                self.work_title_table.setItem(row_index, 1, QTableWidgetItem(wt[1]))
                self.work_title_table.setItem(row_index, 2, QTableWidgetItem(wt[2]))
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Arbeitstitel:\n{str(e)}")

    def add_work_title(self) -> None:
        dialog = WorkTitleEditDialog(self.student_data[0], self.db_manager)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_work_titles()

    def delete_work_title(self) -> None:
        selected_row = self.work_title_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Warnung", "Bitte wählen Sie einen Arbeitstitel aus.")
            return
        try:
            work_id = int(self.work_title_table.item(selected_row, 0).text())
            self.db_manager.delete_work_title(work_id)
            self.load_work_titles()
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Löschen des Arbeitstitels:\n{str(e)}")

    def edit_work_title(self, row: int, column: int) -> None:
        try:
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
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Bearbeiten des Arbeitstitels:\n{str(e)}")

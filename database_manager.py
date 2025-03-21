import sqlite3
from typing import List, Tuple, Optional

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
        if not firstname or not lastname:
            raise ValueError("Vor- und Nachname dürfen nicht leer sein")
        
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
        if not isinstance(student_id, int) or student_id <= 0:
            raise ValueError("Ungültige Schüler-ID")
            
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE students
            SET soziale_kompetenz = ?, aktive_mitarbeit = ?, sauberkeit = ?,
                material = ?, puenktlichkeit = ?, kommentar = ?
            WHERE id = ?
        """, (soziale_kompetenz, aktive_mitarbeit, sauberkeit, material, puenktlichkeit, kommentar, student_id))
        self.conn.commit()

    def delete_student(self, student_id: int) -> None:
        if not isinstance(student_id, int) or student_id <= 0:
            raise ValueError("Ungültige Schüler-ID")
            
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
        if not isinstance(student_id, int) or student_id <= 0:
            raise ValueError("Ungültige Schüler-ID")
            
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
        if not isinstance(work_id, int) or work_id <= 0:
            raise ValueError("Ungültige Arbeitstitel-ID")
            
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
        if not isinstance(work_id, int) or work_id <= 0:
            raise ValueError("Ungültige Arbeitstitel-ID")
            
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM work_titles WHERE id = ?", (work_id,))
        self.conn.commit()

    def get_work_titles(self, student_id: int) -> List[Tuple]:
        if not isinstance(student_id, int) or student_id <= 0:
            raise ValueError("Ungültige Schüler-ID")
            
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

    def get_student_details(self, student_id: int) -> Optional[Tuple]:
        """Holt die Details eines Schülers aus der Datenbank."""
        if not isinstance(student_id, int) or student_id <= 0:
            raise ValueError("Ungültige Schüler-ID")
            
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT soziale_kompetenz, aktive_mitarbeit, sauberkeit, material, puenktlichkeit, kommentar FROM students WHERE id = ?",
            (student_id,)
        )
        return cursor.fetchone()

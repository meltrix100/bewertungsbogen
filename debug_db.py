import sqlite3

conn = sqlite3.connect('students.db')
cursor = conn.cursor()

print("=== Alle Schüler mit Klassen ===")
cursor.execute('SELECT id, firstname, lastname, class FROM students ORDER BY class, lastname')
students = cursor.fetchall()
for student in students:
    print(f"ID: {student[0]}, Name: {student[1]} {student[2]}, Klasse: '{student[3]}'")

print("\n=== Klassenstatistiken ===")
cursor.execute('SELECT class, COUNT(*) FROM students WHERE class IS NOT NULL AND class != "" GROUP BY class ORDER BY class')
class_stats = cursor.fetchall()
for class_name, count in class_stats:
    print(f"Klasse: '{class_name}', Anzahl: {count}")

conn.close()

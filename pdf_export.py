import os
import sys
from typing import List, Tuple, Optional

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

def export_student_to_pdf(
        student_id: int, 
        firstname: str, 
        lastname: str, 
        klass: str, 
        student_details: Optional[Tuple], 
        work_titles: List[Tuple]
    ) -> str:
    """
    Exportiert die Daten eines Schülers als PDF und gibt den Dateinamen zurück.
    
    Args:
        student_id: Die ID des Schülers
        firstname: Der Vorname des Schülers
        lastname: Der Nachname des Schülers
        klass: Die Klasse des Schülers
        student_details: Die Details des Schülers als Tupel
        work_titles: Liste von Arbeitstiteln des Schülers
        
    Returns:
        str: Der Dateiname der erstellten PDF
        
    Raises:
        ImportError: Wenn reportlab nicht verfügbar ist
        Exception: Bei sonstigen Fehlern während der PDF-Erstellung
    """
    if not REPORTLAB_AVAILABLE:
        raise ImportError("Reportlab-Bibliothek nicht verfügbar. Bitte installieren Sie 'reportlab'.")
    
    # Dateinamen erstellen und Sonderzeichen ersetzen
    safe_firstname = firstname.replace(" ", "_").replace("/", "_").replace("\\", "_")
    safe_lastname = lastname.replace(" ", "_").replace("/", "_").replace("\\", "_")
    safe_klass = klass.replace(" ", "_").replace("/", "_").replace("\\", "_")
    filename = f"{safe_firstname}_{safe_lastname}_{safe_klass}.pdf"
    
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
        
        return filename
        
    except Exception as e:
        raise Exception(f"Fehler beim Erstellen der PDF: {str(e)}")

def open_pdf(filename: str) -> None:
    """
    Öffnet eine PDF-Datei mit dem Standardprogramm des Betriebssystems.
    
    Args:
        filename: Der Pfad zur PDF-Datei
        
    Raises:
        FileNotFoundError: Wenn die Datei nicht gefunden wird
        Exception: Bei sonstigen Fehlern beim Öffnen der Datei
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Die Datei {filename} wurde nicht gefunden.")
    
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
        raise Exception(f"Fehler beim Öffnen der PDF: {str(e)}")

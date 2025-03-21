import sys
import multiprocessing

from PyQt6.QtWidgets import QApplication

from main_window import MainWindow

def main() -> None:
    # Notwendig für Windows-Anwendungen mit PyInstaller
    multiprocessing.freeze_support()
    
    app = QApplication(sys.argv)
    
    # Allgemeine Stylesheet-Einstellungen für die gesamte App
    app.setStyle('Fusion')  # Modern-aussehender Style
    
    window = MainWindow()
    window.showMaximized()  # Maximiert das Fenster
    
    sys.exit(app.exec())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print(f"Kritischer Fehler: {e}")
        print(traceback.format_exc())
        sys.exit(1)

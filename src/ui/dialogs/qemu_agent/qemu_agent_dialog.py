"""
Interface principale
"""
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

class QemuAgentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Interface principale")
        self.init_ui()
    
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        layout = QVBoxLayout()
        
        # TODO: Ajouter les composants UI
        label = QLabel("Interface principale")
        layout.addWidget(label)
        
        self.setLayout(layout)

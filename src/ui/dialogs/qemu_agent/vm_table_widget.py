"""
Tableau des VMs
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class VmTableWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        layout = QVBoxLayout()
        
        # TODO: Ajouter les composants UI
        label = QLabel("Tableau des VMs")
        layout.addWidget(label)
        
        self.setLayout(layout)

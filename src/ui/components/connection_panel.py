"""
Panneau de connexion Proxmox
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class ConnectionPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        layout = QVBoxLayout()
        
        # TODO: Ajouter les composants UI
        label = QLabel("Panneau de connexion Proxmox")
        layout.addWidget(label)
        
        self.setLayout(layout)

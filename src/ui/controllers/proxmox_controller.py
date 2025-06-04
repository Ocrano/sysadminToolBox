"""
Contrôleur Proxmox
"""
from PyQt6.QtCore import QObject, pyqtSignal

class ProxmoxController(QObject):
    # Signaux
    status_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup()
    
    def setup(self):
        """Configuration initiale"""
        # TODO: Initialisation du contrôleur
        pass

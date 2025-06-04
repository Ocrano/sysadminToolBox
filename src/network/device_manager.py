"""
Gestion des équipements
"""
from PyQt6.QtCore import QObject, pyqtSignal

class DeviceManager(QObject):
    # Signaux
    operation_completed = pyqtSignal(bool, str)  # success, message
    
    def __init__(self):
        super().__init__()
        self.setup()
    
    def setup(self):
        """Configuration initiale"""
        # TODO: Initialisation du service
        pass

# src/ui/dialogs/network_config_dialog.py
"""
Dialogue de configuration SSH pour équipements réseau
Fichier manquant qui cause l'erreur d'import
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QCheckBox, QGroupBox, QFormLayout, QDialogButtonBox,
    QMessageBox
)
from PyQt6.QtCore import Qt

class NetworkConfigDialog(QDialog):
    """Dialogue de configuration SSH pour équipements réseau"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration SSH")
        self.setModal(True)
        self.setFixedSize(400, 300)
        self.ssh_config = {}
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Titre
        title = QLabel("🔐 Configuration SSH Réseau")
        title.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px; color: #007bff;")
        layout.addWidget(title)
        
        # Description
        desc = QLabel("Configurez les identifiants SSH pour vous connecter aux équipements réseau.")
        desc.setStyleSheet("color: #6c757d; margin-bottom: 15px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Formulaire
        form_group = QGroupBox("Identifiants SSH")
        form_layout = QFormLayout()
        
        # Nom d'utilisateur
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Ex: admin, root, cisco...")
        form_layout.addRow("Utilisateur:", self.username_input)
        
        # Mot de passe
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Mot de passe SSH")
        form_layout.addRow("Mot de passe:", self.password_input)
        
        # Afficher mot de passe
        self.show_password = QCheckBox("Afficher le mot de passe")
        self.show_password.toggled.connect(self.toggle_password)
        form_layout.addRow("", self.show_password)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Info importante
        info = QLabel("⚠️ Ces identifiants seront utilisés pour TOUS les équipements réseau.")
        info.setStyleSheet("""
            QLabel {
                color: #856404;
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 4px;
                padding: 8px;
                margin: 10px 0;
            }
        """)
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Boutons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Sauvegarder")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Annuler")
        
        buttons.accepted.connect(self.accept_config)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
        # Focus sur le premier champ
        self.username_input.setFocus()
    
    def toggle_password(self, checked):
        """Basculer l'affichage du mot de passe"""
        if checked:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
    
    def accept_config(self):
        """Valider la configuration"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        # Validation
        if not username:
            QMessageBox.warning(self, "Champ requis", "Le nom d'utilisateur est requis.")
            self.username_input.setFocus()
            return
        
        if not password:
            QMessageBox.warning(self, "Champ requis", "Le mot de passe est requis.")
            self.password_input.setFocus()
            return
        
        # Validation du nom d'utilisateur
        if not username.replace('.', '').replace('-', '').replace('_', '').isalnum():
            QMessageBox.warning(
                self, 
                "Nom d'utilisateur invalide", 
                "Le nom d'utilisateur ne doit contenir que des lettres, chiffres, points, traits d'union et underscores."
            )
            self.username_input.setFocus()
            return
        
        # Stocker la configuration
        self.ssh_config = {
            'username': username,
            'password': password
        }
        
        self.accept()
    
    def get_config(self):
        """Retourne la configuration SSH"""
        return self.ssh_config


# Pour des tests si nécessaire
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = NetworkConfigDialog()
    
    if dialog.exec():
        config = dialog.get_config()
        print(f"Configuration: {config}")
    else:
        print("Configuration annulée")
    
    sys.exit()
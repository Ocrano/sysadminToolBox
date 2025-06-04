from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QCheckBox, QGroupBox, QFormLayout, QMessageBox
)
from PyQt6.QtGui import QFont


class NetworkConfigDialog(QDialog):
    """Dialogue moderne de configuration SSH pour les équipements réseau"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ssh_config = {}
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Configuration SSH Réseau")
        self.setModal(True)
        self.setFixedSize(500, 400)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        
        # Style moderne pour la fenêtre
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 15px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #495057;
                background-color: #f8f9fa;
            }
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                font-size: 13px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #007bff;
                outline: none;
            }
            QLabel {
                color: #495057;
                font-size: 13px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # === EN-TÊTE ===
        header_layout = QVBoxLayout()
        
        title_label = QLabel("🔐 Configuration SSH Réseau")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #212529; margin-bottom: 10px;")
        header_layout.addWidget(title_label)
        
        desc_label = QLabel(
            "Configurez un compte unique utilisé pour tous les équipements réseau.\n"
            "Ce doit être le même login/mot de passe sur tous vos équipements."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            color: #6c757d; 
            font-size: 12px; 
            line-height: 18px;
            background-color: #e3f2fd;
            padding: 12px;
            border-radius: 6px;
            border-left: 4px solid #2196f3;
        """)
        header_layout.addWidget(desc_label)
        
        layout.addLayout(header_layout)
        
        # === FORMULAIRE CREDENTIALS ===
        credentials_group = QGroupBox("Informations de connexion")
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # Nom d'utilisateur
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("ex: admin, root, ou votre compte AD")
        form_layout.addRow("👤 Nom d'utilisateur:", self.username_input)
        
        # Mot de passe
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Mot de passe SSH identique sur tous les équipements")
        form_layout.addRow("🔑 Mot de passe:", self.password_input)
        
        # Checkbox afficher mot de passe
        self.show_password_cb = QCheckBox("Afficher le mot de passe")
        self.show_password_cb.toggled.connect(self.toggle_password_visibility)
        self.show_password_cb.setStyleSheet("margin-top: 8px; color: #6c757d;")
        form_layout.addRow("", self.show_password_cb)
        
        credentials_group.setLayout(form_layout)
        layout.addWidget(credentials_group)
        
        # === INFORMATIONS IMPORTANTES ===
        info_group = QGroupBox("ℹ️ Prérequis")
        info_layout = QVBoxLayout()
        
        info_text = QLabel("""
<b>Conditions nécessaires :</b><br>
• <b>Même compte</b> sur tous les équipements (ex: admin/admin123)<br>
• <b>SSH activé</b> sur tous les équipements réseau<br>
• <b>Accès réseau</b> depuis ce poste vers les équipements<br>
• <b>Droits suffisants</b> pour exécuter les commandes show/get<br><br>

<b>Types supportés :</b> Cisco, Allied Telesis, Fortinet, Stormshield, HP/Aruba, pfSense
        """)
        info_text.setWordWrap(True)
        info_text.setStyleSheet("""
            color: #495057;
            font-size: 11px;
            line-height: 16px;
            background-color: #fff3cd;
            padding: 12px;
            border-radius: 6px;
            border-left: 4px solid #ffc107;
        """)
        info_layout.addWidget(info_text)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # === BOUTONS ===
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # Bouton Test (optionnel)
        self.test_btn = QPushButton("🔍 Tester")
        self.test_btn.clicked.connect(self.test_connection)
        self.test_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
        """)
        buttons_layout.addWidget(self.test_btn)
        
        buttons_layout.addStretch()
        
        # Bouton Annuler
        self.cancel_btn = QPushButton("❌ Annuler")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        buttons_layout.addWidget(self.cancel_btn)
        
        # Bouton Valider
        self.ok_btn = QPushButton("✅ Sauvegarder")
        self.ok_btn.clicked.connect(self.save_and_accept)
        self.ok_btn.setDefault(True)
        self.ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        buttons_layout.addWidget(self.ok_btn)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
        
        # Focus sur le premier champ
        self.username_input.setFocus()

    def toggle_password_visibility(self, checked):
        """Bascule la visibilité du mot de passe"""
        if checked:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

    def test_connection(self):
        """Test de base (placeholder)"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username or not password:
            QMessageBox.warning(
                self, 
                "Champs requis", 
                "Veuillez remplir le nom d'utilisateur et le mot de passe"
            )
            return
        
        QMessageBox.information(
            self, 
            "Test SSH", 
            f"Test de configuration SSH :\n\n"
            f"Utilisateur : {username}\n"
            f"Mot de passe : {'*' * len(password)}\n\n"
            f"Pour tester réellement, importez d'abord vos équipements\n"
            f"et utilisez les boutons d'actions."
        )

    def save_and_accept(self):
        """Valide et sauvegarde la configuration"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        # Validation
        if not username:
            QMessageBox.warning(self, "Champ requis", "Le nom d'utilisateur est requis")
            self.username_input.setFocus()
            return
        
        if not password:
            QMessageBox.warning(self, "Champ requis", "Le mot de passe est requis")
            self.password_input.setFocus()
            return
        
        if len(password) < 3:
            QMessageBox.warning(self, "Mot de passe", "Le mot de passe doit faire au moins 3 caractères")
            self.password_input.setFocus()
            return
        
        # Sauvegarder la configuration
        self.ssh_config = {
            'username': username,
            'password': password
        }
        
        QMessageBox.information(
            self, 
            "Configuration SSH", 
            f"Configuration SSH sauvegardée !\n\n"
            f"Utilisateur : {username}\n"
            f"Les commandes SSH utiliseront ces credentials\n"
            f"sur tous vos équipements réseau."
        )
        
        self.accept()

    def get_config(self):
        """Retourne la configuration SSH"""
        return self.ssh_config
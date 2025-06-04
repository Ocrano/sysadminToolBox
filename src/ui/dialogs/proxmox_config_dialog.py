import json
import os
import keyring
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, 
    QCheckBox, QLabel, QMessageBox, QHBoxLayout, QProgressBar,
    QComboBox, QSpinBox, QGroupBox, QTextEdit
)
from PyQt6.QtGui import QPixmap, QPalette
from ...services.proxmox_service import ProxmoxService  # Import du service refactorisé

class ConnectionTestThread(QThread):
    """Thread pour tester la connexion Proxmox en arrière-plan"""
    connection_result = pyqtSignal(bool, str)  # success, message
    progress_update = pyqtSignal(str)  # status message
    
    def __init__(self, config):
        super().__init__()
        self.config = config
    
    def run(self):
        try:
            self.progress_update.emit("Connexion en cours...")
            
            # Créer une instance temporaire pour le test
            temp_handler = ProxmoxService()
            
            # Test de connexion
            success = temp_handler.connect(self.config)
            
            if success:
                self.progress_update.emit("Récupération des informations...")
                
                # Récupérer quelques infos pour valider la connexion
                version = temp_handler.get_version()
                nodes = len(temp_handler.nodes)
                
                message = f"Connexion réussie!\nVersion: {version}\nNœuds détectés: {nodes}"
                self.connection_result.emit(True, message)
            else:
                self.connection_result.emit(False, "Échec de la connexion à Proxmox")
                
        except Exception as e:
            self.connection_result.emit(False, f"Erreur de connexion: {str(e)}")

class ProxmoxConfigDialog(QDialog):
    def __init__(self, parent=None, proxmox_handler=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration Proxmox VE")
        self.resize(450, 600)
        self.proxmox_handler = proxmox_handler  # Garde la référence mais pas obligatoire pour le test
        self.config = {}
        self.config_file = "proxmox_config.json"
        self.test_thread = None
        self.init_ui()
        self.load_saved_config()

    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # === Titre et description ===
        title_label = QLabel("Configuration Proxmox VE")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        desc_label = QLabel("Configurez la connexion à votre serveur Proxmox Virtual Environment")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: gray; margin-bottom: 15px;")
        main_layout.addWidget(desc_label)
        
        # === Groupe Connexion ===
        connection_group = QGroupBox("Paramètres de connexion")
        connection_layout = QFormLayout()
        
        # Champs de saisie
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Ex: 192.168.1.100 ou proxmox.local")
        self.ip_input.textChanged.connect(self.on_config_changed)
        
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(8006)
        self.port_input.valueChanged.connect(self.on_config_changed)
        
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Ex: root@pam ou admin@pve")
        self.user_input.textChanged.connect(self.on_config_changed)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Mot de passe")
        self.password_input.textChanged.connect(self.on_config_changed)
        
        # Checkbox pour montrer/masquer le mot de passe
        self.show_password_checkbox = QCheckBox("Afficher le mot de passe")
        self.show_password_checkbox.toggled.connect(self.toggle_password_visibility)
        
        # Options SSL
        self.verify_ssl_checkbox = QCheckBox("Vérifier le certificat SSL")
        self.verify_ssl_checkbox.setToolTip("Décochez si vous utilisez un certificat auto-signé")
        
        connection_layout.addRow("Adresse IP/Hostname:", self.ip_input)
        connection_layout.addRow("Port:", self.port_input)
        connection_layout.addRow("Utilisateur:", self.user_input)
        connection_layout.addRow("Mot de passe:", self.password_input)
        connection_layout.addRow("", self.show_password_checkbox)
        connection_layout.addRow("", self.verify_ssl_checkbox)
        
        connection_group.setLayout(connection_layout)
        main_layout.addWidget(connection_group)
        
        # === Groupe Options ===
        options_group = QGroupBox("Options")
        options_layout = QFormLayout()
        
        self.save_password_checkbox = QCheckBox("Sauvegarder le mot de passe (sécurisé)")
        self.save_password_checkbox.setToolTip("Le mot de passe sera stocké de manière sécurisée dans le trousseau système")
        
        self.auto_connect_checkbox = QCheckBox("Connexion automatique au démarrage")
        
        options_layout.addRow("", self.save_password_checkbox)
        options_layout.addRow("", self.auto_connect_checkbox)
        
        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)
        
        # === Test de connexion ===
        test_group = QGroupBox("Test de connexion")
        test_layout = QVBoxLayout()
        
        self.test_button = QPushButton("Tester la connexion")
        self.test_button.clicked.connect(self.test_connection)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        
        test_layout.addWidget(self.test_button)
        test_layout.addWidget(self.progress_bar)
        test_layout.addWidget(self.status_label)
        
        test_group.setLayout(test_layout)
        main_layout.addWidget(test_group)
        
        # === Informations de connexion ===
        self.info_group = QGroupBox("Informations serveur")
        self.info_layout = QVBoxLayout()
        self.info_text = QTextEdit()
        self.info_text.setMaximumHeight(100)
        self.info_text.setReadOnly(True)
        self.info_layout.addWidget(self.info_text)
        self.info_group.setLayout(self.info_layout)
        self.info_group.setVisible(False)
        main_layout.addWidget(self.info_group)
        
        # === Boutons de validation ===
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Sauvegarder")
        self.save_button.clicked.connect(self.save_config)
        
        self.ok_button = QPushButton("Valider")
        self.ok_button.clicked.connect(self.accept_config)
        self.ok_button.setDefault(True)
        
        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        
        # État initial
        self.update_button_states()

    def on_config_changed(self):
        """Appelé quand la configuration change"""
        self.status_label.setText("")
        self.info_group.setVisible(False)
        self.update_button_states()

    def update_button_states(self):
        """Met à jour l'état des boutons selon la validité de la config"""
        has_required_fields = bool(
            self.ip_input.text().strip() and 
            self.user_input.text().strip() and 
            self.password_input.text().strip()
        )
        
        self.test_button.setEnabled(has_required_fields)
        self.ok_button.setEnabled(has_required_fields)

    def toggle_password_visibility(self, checked):
        """Bascule la visibilité du mot de passe"""
        if checked:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

    def test_connection(self):
        """Lance le test de connexion en arrière-plan"""
        config = self.get_current_config()
        
        # Démarrer l'animation de progression
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Animation infinie
        self.test_button.setEnabled(False)
        self.status_label.setText("Test en cours...")
        
        # Lancer le thread de test (qui créera sa propre instance de ProxmoxService)
        self.test_thread = ConnectionTestThread(config)
        self.test_thread.connection_result.connect(self.on_connection_tested)
        self.test_thread.progress_update.connect(self.on_progress_update)
        self.test_thread.start()

    def on_progress_update(self, message):
        """Met à jour le message de progression"""
        self.status_label.setText(message)

    def on_connection_tested(self, success, message):
        """Appelé quand le test de connexion est terminé"""
        self.progress_bar.setVisible(False)
        self.test_button.setEnabled(True)
        
        if success:
            self.status_label.setText("✅ " + message)
            self.status_label.setStyleSheet("color: green;")
            self.info_text.setText(message)
            self.info_group.setVisible(True)
        else:
            self.status_label.setText("❌ " + message)
            self.status_label.setStyleSheet("color: red;")
            self.info_group.setVisible(False)

    def get_current_config(self):
        """Récupère la configuration actuelle"""
        return {
            "ip": self.ip_input.text().strip(),
            "port": self.port_input.value(),
            "user": self.user_input.text().strip(),
            "password": self.password_input.text().strip(),
            "verify_ssl": self.verify_ssl_checkbox.isChecked()
        }

    def save_config(self):
        """Sauvegarde la configuration"""
        try:
            config = self.get_current_config()
            
            # Configuration à sauvegarder (sans mot de passe)
            save_config = {
                "ip": config["ip"],
                "port": config["port"],
                "user": config["user"],
                "verify_ssl": config["verify_ssl"],
                "auto_connect": self.auto_connect_checkbox.isChecked()
            }
            
            # Sauvegarder dans le fichier JSON
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(save_config, f, indent=2, ensure_ascii=False)
            
            # Sauvegarder le mot de passe dans le trousseau si demandé
            if self.save_password_checkbox.isChecked() and config["password"]:
                try:
                    keyring.set_password("proxmox_toolbox", config["user"], config["password"])
                except Exception as e:
                    print(f"Impossible de sauvegarder le mot de passe: {e}")
            
            QMessageBox.information(self, "Sauvegarde", "Configuration sauvegardée avec succès!")
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de sauvegarder la configuration: {e}")

    def load_saved_config(self):
        """Charge la configuration sauvegardée"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                
                # Charger les valeurs
                self.ip_input.setText(config.get("ip", ""))
                self.port_input.setValue(config.get("port", 8006))
                self.user_input.setText(config.get("user", ""))
                self.verify_ssl_checkbox.setChecked(config.get("verify_ssl", False))
                self.auto_connect_checkbox.setChecked(config.get("auto_connect", False))
                
                # Essayer de récupérer le mot de passe du trousseau
                username = config.get("user", "")
                if username:
                    try:
                        password = keyring.get_password("proxmox_toolbox", username)
                        if password:
                            self.password_input.setText(password)
                            self.save_password_checkbox.setChecked(True)
                    except Exception as e:
                        print(f"Impossible de récupérer le mot de passe: {e}")
                
        except Exception as e:
            print(f"Impossible de charger la configuration: {e}")

    def accept_config(self):
        """Valide et accepte la configuration"""
        config = self.get_current_config()
        
        # Validation des champs requis
        if not config["ip"]:
            QMessageBox.warning(self, "Champ requis", "L'adresse IP est requise")
            self.ip_input.setFocus()
            return
        
        if not config["user"]:
            QMessageBox.warning(self, "Champ requis", "Le nom d'utilisateur est requis")
            self.user_input.setFocus()
            return
        
        if not config["password"]:
            QMessageBox.warning(self, "Champ requis", "Le mot de passe est requis")
            self.password_input.setFocus()
            return
        
        self.config = config
        self.accept()

    def get_config(self):
        """Retourne la configuration validée"""
        return self.config

    def should_auto_connect(self):
        """Retourne True si la connexion automatique est activée"""
        return self.auto_connect_checkbox.isChecked()

    def closeEvent(self, event):
        """Nettoie les threads en cours lors de la fermeture"""
        if self.test_thread and self.test_thread.isRunning():
            self.test_thread.terminate()
            self.test_thread.wait()
        event.accept()
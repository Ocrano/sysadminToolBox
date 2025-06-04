import csv
import os
import paramiko
import time
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QGroupBox,
    QPushButton, QLabel, QTextEdit, QCheckBox, QFileDialog,
    QMessageBox, QTableWidget, QTableWidgetItem, QComboBox,
    QInputDialog, QLineEdit, QProgressBar, QDialog, QFormLayout,
    QDialogButtonBox, QFrame, QScrollArea
)
from PyQt6.QtGui import QFont, QTextCharFormat, QColor, QPixmap, QIcon

# Import du système de logging
from ...core.logger import log_info, log_debug, log_error, log_success, log_warning


class NetworkConfigDialog(QDialog):
    """Dialogue modal de configuration SSH pour les équipements réseau - VERSION SIMPLIFIÉE"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration SSH")
        self.setModal(True)
        self.setFixedSize(450, 400)  # Taille réduite
        self.ssh_config = {}
        
        # Style simplifié
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #555;
                border-radius: 4px;
                background-color: #3c3c3c;
                color: white;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #007bff;
            }
            QLabel {
                color: #e0e0e0;
                font-size: 12px;
            }
        """)
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # En-tête simple
        title = QLabel("Configuration SSH Réseau")
        title.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold; 
            color: #007bff;
            margin-bottom: 10px;
        """)
        layout.addWidget(title)
        
        # Prérequis condensés
        prereq_group = QGroupBox("Prérequis")
        prereq_layout = QVBoxLayout()
        
        prereq_text = QLabel("""• Même compte SSH sur tous les équipements
- Service SSH actif et accessible
- Privilèges suffisants pour les commandes""")
        prereq_text.setWordWrap(True)
        prereq_text.setStyleSheet("""
            QLabel {
                color: #ffd43b;
                background-color: #3a3a3a;
                padding: 10px;
                border-radius: 4px;
                font-size: 11px;
            }
        """)
        prereq_layout.addWidget(prereq_text)
        prereq_group.setLayout(prereq_layout)
        layout.addWidget(prereq_group)
        
        # Configuration
        config_group = QGroupBox("Identifiants")
        form_layout = QFormLayout()
        form_layout.setSpacing(8)
        
        # Username
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Nom d'utilisateur SSH")
        form_layout.addRow("Utilisateur:", self.username_input)
        
        # Password
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Mot de passe SSH")
        form_layout.addRow("Mot de passe:", self.password_input)
        
        # Show password
        self.show_pass_cb = QCheckBox("Afficher le mot de passe")
        self.show_pass_cb.toggled.connect(self.toggle_password)
        self.show_pass_cb.setStyleSheet("color: #74c0fc; margin-top: 5px;")
        form_layout.addRow("", self.show_pass_cb)
        
        config_group.setLayout(form_layout)
        layout.addWidget(config_group)
        
        # Sécurité simplifiée
        security_text = QLabel("Les identifiants sont stockés temporairement en mémoire uniquement.")
        security_text.setWordWrap(True)
        security_text.setStyleSheet("""
            QLabel {
                color: #dc3545;
                background-color: #3a1f1f;
                padding: 8px;
                border-radius: 4px;
                font-size: 10px;
                border-left: 3px solid #dc3545;
            }
        """)
        layout.addWidget(security_text)
        
        # Boutons
        button_layout = QHBoxLayout()
        
        # Bouton Test
        self.test_btn = QPushButton("Tester")
        self.test_btn.clicked.connect(self.test_ssh_config)
        self.test_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        button_layout.addWidget(self.test_btn)
        
        button_layout.addStretch()
        
        # Boutons OK/Cancel
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Sauvegarder")
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("Annuler")
        
        # Style des boutons
        button_box.button(QDialogButtonBox.StandardButton.Ok).setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
        """)
        
        button_box.accepted.connect(self.accept_config)
        button_box.rejected.connect(self.reject)
        
        button_layout.addWidget(button_box)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

    def toggle_password(self, checked):
        """Basculer l'affichage du mot de passe"""
        if checked:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

    def test_ssh_config(self):
        """Test de configuration SSH"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username or not password:
            QMessageBox.warning(
                self, 
                "Champs manquants", 
                "Veuillez remplir le nom d'utilisateur et le mot de passe."
            )
            return
        
        QMessageBox.information(
            self, 
            "Test SSH", 
            f"Configuration prête:\n\nUtilisateur: {username}\n\n"
            f"Pour tester, importez d'abord un fichier CSV avec vos équipements."
        )

    def accept_config(self):
        """Valider et sauvegarder la configuration"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username:
            QMessageBox.warning(self, "Champ requis", "Veuillez saisir un nom d'utilisateur.")
            self.username_input.setFocus()
            return
        
        if not password:
            QMessageBox.warning(self, "Champ requis", "Veuillez saisir un mot de passe.")
            self.password_input.setFocus()
            return
        
        # Validation simple du nom d'utilisateur
        if not username.replace('.', '').replace('-', '').replace('_', '').isalnum():
            QMessageBox.warning(
                self, 
                "Nom d'utilisateur invalide", 
                "Le nom d'utilisateur ne doit contenir que des lettres, chiffres, points, traits d'union et underscores."
            )
            self.username_input.setFocus()
            return
        
        self.ssh_config = {
            'username': username,
            'password': password
        }
        self.accept()

    def get_config(self):
        """Retourne la configuration SSH"""
        return self.ssh_config


class NetworkCommandThread(QThread):
    """Thread pour exécuter des commandes SSH sur équipements réseau"""
    command_result = pyqtSignal(str, str, str)  # hostname, command, result
    command_error = pyqtSignal(str, str, str)   # hostname, command, error
    progress_update = pyqtSignal(str)
    
    def __init__(self, devices, ssh_config, commands, device_type):
        super().__init__()
        self.devices = devices
        self.ssh_config = ssh_config
        self.commands = commands
        self.device_type = device_type
    
    def run(self):
        """Exécute les commandes sur tous les équipements"""
        for device in self.devices:
            hostname = device.get('hostname', 'Unknown')
            ip = device.get('ip', '')
            
            if not ip:
                self.command_error.emit(hostname, "Connection", "IP address missing")
                continue
            
            self.progress_update.emit(f"Connexion à {hostname} ({ip})...")
            
            try:
                # Connexion SSH
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(
                    ip,
                    username=self.ssh_config['username'],
                    password=self.ssh_config['password'],
                    timeout=10
                )
                
                # Exécuter les commandes
                for command in self.commands:
                    self.progress_update.emit(f"Exécution '{command}' sur {hostname}...")
                    
                    stdin, stdout, stderr = client.exec_command(command, timeout=30)
                    
                    # Attendre la completion
                    start_time = time.time()
                    while not stdout.channel.exit_status_ready():
                        if time.time() - start_time > 30:
                            break
                        time.sleep(0.1)
                    
                    output = stdout.read().decode('utf-8', errors='ignore')
                    error = stderr.read().decode('utf-8', errors='ignore')
                    
                    if error:
                        self.command_error.emit(hostname, command, error)
                    else:
                        self.command_result.emit(hostname, command, output)
                
                client.close()
                
            except Exception as e:
                self.command_error.emit(hostname, "SSH Connection", str(e))


class NetworkTab(QWidget):
    """Onglet Network pour gestion des équipements réseau"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.devices = []
        self.ssh_config = {}
        self.command_thread = None
        self.init_ui()
        
    def init_ui(self):
        """Interface similaire à l'onglet Tools"""
        main_layout = QVBoxLayout()
        
        # === SECTION CONFIGURATION SSH (en haut) ===
        config_group = QGroupBox("🔐 Configuration SSH Réseau")
        config_group.setMaximumHeight(80)
        config_layout = QHBoxLayout()
        config_layout.setContentsMargins(10, 5, 10, 5)
        
        # Bouton configuration SSH
        self.config_ssh_btn = QPushButton("⚙️ Configurer SSH")
        self.config_ssh_btn.clicked.connect(self.configure_ssh)
        self.config_ssh_btn.setFixedWidth(140)
        self.config_ssh_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        config_layout.addWidget(self.config_ssh_btn)
        
        # Statut SSH
        self.ssh_status_label = QLabel("❌ Non configuré")
        self.ssh_status_label.setFixedWidth(120)
        self.ssh_status_label.setStyleSheet("""
            QLabel {
                padding: 6px 10px;
                border-radius: 4px;
                background-color: #f8d7da;
                color: #721c24;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        config_layout.addWidget(self.ssh_status_label)
        
        # Bouton import équipements
        self.import_devices_btn = QPushButton("📁 Importer CSV")
        self.import_devices_btn.clicked.connect(self.import_devices_csv)
        self.import_devices_btn.setFixedWidth(120)
        self.import_devices_btn.setStyleSheet("""
            QPushButton {
                background-color: #6f42c1;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a2d91;
            }
        """)
        config_layout.addWidget(self.import_devices_btn)
        
        # Info équipements
        self.devices_info_label = QLabel("Aucun équipement chargé")
        self.devices_info_label.setStyleSheet("color: #495057; font-size: 12px; margin-left: 10px;")
        config_layout.addWidget(self.devices_info_label)
        
        config_layout.addStretch()
        
        # Version
        version_label = QLabel("Alpha 0.0.6 • by ocrano")
        version_label.setStyleSheet("color: #6c757d; font-size: 10px; font-style: italic;")
        config_layout.addWidget(version_label)
        
        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)
        
        # === SPLITTER PRINCIPAL ===
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # === SECTION ACTIONS (à gauche) ===
        actions_widget = QWidget()
        actions_layout = QVBoxLayout()
        
        actions_title = QLabel("🌐 Actions Réseau")
        actions_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        actions_layout.addWidget(actions_title)
        
        # === SÉLECTION TYPE D'ÉQUIPEMENT ===
        device_type_group = QGroupBox("🔧 Type d'équipement")
        device_type_layout = QVBoxLayout()
        
        self.device_type_combo = QComboBox()
        self.device_type_combo.addItems([
            "Cisco Switch/Router",
            "Allied Telesis Switch", 
            "HP/Aruba Switch",
            "Fortinet Firewall",
            "Stormshield Firewall",
            "pfSense Firewall",
            "Générique (Linux)"
        ])
        self.device_type_combo.currentTextChanged.connect(self.on_device_type_changed)
        device_type_layout.addWidget(self.device_type_combo)
        
        device_type_group.setLayout(device_type_layout)
        actions_layout.addWidget(device_type_group)
        
        # === ACTIONS SPÉCIALISÉES ===
        self.actions_group = QGroupBox("📋 Actions disponibles")
        self.actions_layout = QVBoxLayout()
        
        # Actions par défaut (Cisco)
        self.create_cisco_actions()
        
        self.actions_group.setLayout(self.actions_layout)
        actions_layout.addWidget(self.actions_group)
        
        # === ÉQUIPEMENTS CHARGÉS ===
        devices_group = QGroupBox("📡 Équipements")
        devices_layout = QVBoxLayout()
        
        self.devices_table = QTableWidget()
        self.devices_table.setColumnCount(3)
        self.devices_table.setHorizontalHeaderLabels(["Hostname", "IP", "Type"])
        self.devices_table.setMaximumHeight(150)
        devices_layout.addWidget(self.devices_table)
        
        devices_group.setLayout(devices_layout)
        actions_layout.addWidget(devices_group)
        
        actions_layout.addStretch()
        actions_widget.setLayout(actions_layout)
        main_splitter.addWidget(actions_widget)
        
        # === SECTION RÉSULTATS (à droite) ===
        results_widget = QWidget()
        results_layout = QVBoxLayout()
        
        # Header résultats
        results_header = QHBoxLayout()
        results_title = QLabel("📋 Résultats en temps réel")
        results_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        results_header.addWidget(results_title)
        
        results_header.addStretch()
        
        # Filtres
        filters_group = QGroupBox("Filtres")
        filters_layout = QHBoxLayout()
        filters_layout.setContentsMargins(5, 2, 5, 2)
        
        self.success_filter = QCheckBox("SUCCESS")
        self.success_filter.setChecked(True)
        self.success_filter.setStyleSheet("color: #28a745; font-size: 11px;")
        filters_layout.addWidget(self.success_filter)
        
        self.error_filter = QCheckBox("ERROR")
        self.error_filter.setChecked(True)
        self.error_filter.setStyleSheet("color: #dc3545; font-size: 11px;")
        filters_layout.addWidget(self.error_filter)
        
        self.info_filter = QCheckBox("INFO")
        self.info_filter.setChecked(True)
        self.info_filter.setStyleSheet("color: #17a2b8; font-size: 11px;")
        filters_layout.addWidget(self.info_filter)
        
        filters_group.setLayout(filters_layout)
        filters_group.setMaximumHeight(50)
        results_header.addWidget(filters_group)
        
        # Boutons export/clear
        self.export_results_btn = QPushButton("💾 Exporter")
        self.export_results_btn.clicked.connect(self.export_results)
        self.export_results_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                font-size: 12px;
                margin-right: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        results_header.addWidget(self.export_results_btn)
        
        self.clear_results_btn = QPushButton("🗑️ Effacer")
        self.clear_results_btn.clicked.connect(self.clear_results)
        self.clear_results_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        results_header.addWidget(self.clear_results_btn)
        
        results_layout.addLayout(results_header)
        
        # Zone résultats avec fond noir et coloration
        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)
        self.results_display.setFont(QFont("Consolas", 10))
        self.results_display.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 15px;
                line-height: 1.4;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            }
        """)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        results_layout.addWidget(self.progress_bar)
        
        # Messages d'accueil
        self.add_initial_messages()
        
        results_layout.addWidget(self.results_display)
        results_widget.setLayout(results_layout)
        main_splitter.addWidget(results_widget)
        
        # Répartition 30/70
        main_splitter.setStretchFactor(0, 30)
        main_splitter.setStretchFactor(1, 70)
        
        main_layout.addWidget(main_splitter)
        self.setLayout(main_layout)
        
        log_debug("Onglet Network configuré avec dialogue SSH corrigé", "Network")

    def configure_ssh(self):
        """Configuration SSH avec dialogue modal corrigé"""
        log_info("Ouverture dialogue configuration SSH", "Network")
        
        dialog = NetworkConfigDialog(self)
        result = dialog.exec()  # Dialogue modal
        
        if result == QDialog.DialogCode.Accepted:
            config = dialog.get_config()
            if config and config.get('username') and config.get('password'):
                self.ssh_config = config
                self.update_ssh_status(True)
                log_success(f"Configuration SSH sauvegardée pour utilisateur: {config['username']}", "Network")
                self.add_colored_result(f"SUCCESS: SSH configured for user '{config['username']}'", "SUCCESS")
                
                # Message de confirmation
                QMessageBox.information(
                    self, 
                    "✅ Configuration SSH",
                    f"""<b>Configuration SSH sauvegardée avec succès !</b>

<b>Utilisateur :</b> {config['username']}
<b>Mot de passe :</b> {'•' * len(config['password'])} caractères

<b>✅ Prêt pour :</b>
• Exécution de commandes sur les équipements
• Actions automatisées selon le type d'équipement
• Gestion centralisée de votre infrastructure réseau
                    """
                )
            else:
                log_warning("Configuration SSH annulée ou incomplète", "Network")
        else:
            log_info("Configuration SSH annulée par l'utilisateur", "Network")

    # [Le reste des méthodes reste identique...]
    
    def add_initial_messages(self):
        """Messages d'accueil colorés"""
        cursor = self.results_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        
        # En-tête
        format_header = QTextCharFormat()
        format_header.setForeground(QColor("#74c0fc"))
        format_header.setFontWeight(QFont.Weight.Bold)
        cursor.setCharFormat(format_header)
        cursor.insertText("=" * 80 + "\n")
        cursor.insertText("                      NETWORK MANAGEMENT - SESSION STARTED\n")
        cursor.insertText("=" * 80 + "\n\n")
        
        # Messages système
        format_system = QTextCharFormat()
        format_system.setForeground(QColor("#51cf66"))
        cursor.setCharFormat(format_system)
        cursor.insertText("SYSTEM: Welcome to Network Management\n")
        cursor.insertText("SYSTEM: Configure SSH credentials and import devices CSV\n")
        cursor.insertText("SYSTEM: Select device type and execute network commands\n")
        cursor.insertText("SYSTEM: Results will appear here in real-time\n\n")
        
        # Info d'attente
        format_info = QTextCharFormat()
        format_info.setForeground(QColor("#74c0fc"))
        cursor.setCharFormat(format_info)
        cursor.insertText("INFO: Ready for network operations...\n\n")

    def add_colored_result(self, message, level="INFO"):
        """Ajoute un résultat coloré"""
        cursor = self.results_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        
        format = QTextCharFormat()
        
        if level == "SUCCESS":
            format.setForeground(QColor("#51cf66"))
            format.setFontWeight(QFont.Weight.Bold)
        elif level == "ERROR":
            format.setForeground(QColor("#ff6b6b"))
            format.setFontWeight(QFont.Weight.Bold)
        elif level == "WARNING":
            format.setForeground(QColor("#ffd43b"))
        else:  # INFO
            format.setForeground(QColor("#74c0fc"))
        
        cursor.setCharFormat(format)
        timestamp = time.strftime("%H:%M:%S")
        cursor.insertText(f"[{timestamp}] {level} | {message}\n")
        
        # Auto-scroll
        scrollbar = self.results_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def create_cisco_actions(self):
        """Crée les boutons d'actions pour Cisco"""
        # Supprimer les anciens boutons
        self.clear_action_buttons()
        
        # Actions Cisco
        actions = [
            ("📋 Show Version", self.show_version),
            ("🔧 Show Running-Config", self.show_running_config),
            ("📊 Show Interfaces Status", self.show_interfaces),
            ("🌐 Show IP Route", self.show_ip_route),
            ("📝 Show MAC Address Table", self.show_mac_table),
            ("⚡ Show Power Status", self.show_power),
            ("🔍 Show VLAN", self.show_vlans),
            ("📶 Show CDP Neighbors", self.show_cdp)
        ]
        
        for text, callback in actions:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            btn.setEnabled(False)  # Désactivé par défaut
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #17a2b8;
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 4px;
                    font-weight: bold;
                    text-align: left;
                    font-size: 12px;
                    margin: 2px;
                }
                QPushButton:hover {
                    background-color: #138496;
                }
                QPushButton:disabled {
                    background-color: #6c757d;
                }
            """)
            self.actions_layout.addWidget(btn)

    def create_fortinet_actions(self):
        """Actions pour Fortinet"""
        self.clear_action_buttons()
        
        actions = [
            ("📋 Get System Status", self.fortinet_system_status),
            ("🔧 Get System Configuration", self.fortinet_config),
            ("🌐 Show Routing Table", self.fortinet_routes),
            ("🔥 Show Firewall Policies", self.fortinet_policies),
            ("📊 Show Interface Status", self.fortinet_interfaces),
            ("👥 Show Session List", self.fortinet_sessions),
            ("📈 Show System Performance", self.fortinet_performance)
        ]
        
        for text, callback in actions:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            btn.setEnabled(False)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #e83e8c;
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 4px;
                    font-weight: bold;
                    text-align: left;
                    font-size: 12px;
                    margin: 2px;
                }
                QPushButton:hover {
                    background-color: #c82166;
                }
                QPushButton:disabled {
                    background-color: #6c757d;
                }
            """)
            self.actions_layout.addWidget(btn)

    def clear_action_buttons(self):
        """Supprime tous les boutons d'actions"""
        for i in reversed(range(self.actions_layout.count())):
            child = self.actions_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

    def on_device_type_changed(self, device_type):
        """Change les actions selon le type d'équipement"""
        log_info(f"Type d'équipement changé: {device_type}", "Network")
        
        if "Cisco" in device_type:
            self.create_cisco_actions()
        elif "Fortinet" in device_type:
            self.create_fortinet_actions()
        elif "Allied" in device_type:
            self.create_allied_actions()
        elif "Stormshield" in device_type:
            self.create_stormshield_actions()
        else:
            self.create_generic_actions()
        
        # Activer les boutons si SSH configuré et équipements chargés
        self.update_buttons_state()

    def create_allied_actions(self):
        """Actions pour Allied Telesis"""
        self.clear_action_buttons()
        
        actions = [
            ("📋 Show System", self.allied_show_system),
            ("🔧 Show Running-Config", self.allied_show_config),
            ("📊 Show Interface", self.allied_show_interface),
            ("🌐 Show IP Route", self.allied_show_route),
            ("📝 Show Switch", self.allied_show_switch),
            ("🔍 Show VLAN", self.allied_show_vlan)
        ]
        
        for text, callback in actions:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            btn.setEnabled(False)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #fd7e14;
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 4px;
                    font-weight: bold;
                    text-align: left;
                    font-size: 12px;
                    margin: 2px;
                }
                QPushButton:hover {
                    background-color: #e55100;
                }
                QPushButton:disabled {
                    background-color: #6c757d;
                }
            """)
            self.actions_layout.addWidget(btn)

    def create_stormshield_actions(self):
        """Actions pour Stormshield"""
        self.clear_action_buttons()
        
        actions = [
            ("📋 System Info", self.stormshield_system),
            ("🔧 Show Config", self.stormshield_config),
            ("🌐 Show Routes", self.stormshield_routes),
            ("🔥 Show Filter Rules", self.stormshield_rules),
            ("📊 Show Connections", self.stormshield_connections),
            ("📈 Show Monitor", self.stormshield_monitor)
        ]
        
        for text, callback in actions:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            btn.setEnabled(False)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #6f42c1;
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 4px;
                    font-weight: bold;
                    text-align: left;
                    font-size: 12px;
                    margin: 2px;
                }
                QPushButton:hover {
                    background-color: #5a2d91;
                }
                QPushButton:disabled {
                    background-color: #6c757d;
                }
            """)
            self.actions_layout.addWidget(btn)

    def create_generic_actions(self):
        """Actions génériques Linux"""
        self.clear_action_buttons()
        
        actions = [
            ("📋 System Info", self.generic_system_info),
            ("🌐 Network Config", self.generic_network),
            ("📊 Interface Status", self.generic_interfaces),
            ("🔧 Process List", self.generic_processes),
            ("💾 Disk Usage", self.generic_disk),
            ("🔍 Custom Command", self.generic_custom)
        ]
        
        for text, callback in actions:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            btn.setEnabled(False)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 4px;
                    font-weight: bold;
                    text-align: left;
                    font-size: 12px;
                    margin: 2px;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
                QPushButton:disabled {
                    background-color: #6c757d;
                }
            """)
            self.actions_layout.addWidget(btn)

    def update_ssh_status(self, configured):
        """Met à jour le statut SSH"""
        if configured:
            self.ssh_status_label.setText("✅ Configuré")
            self.ssh_status_label.setStyleSheet("""
                QLabel {
                    padding: 6px 10px;
                    border-radius: 4px;
                    background-color: #d4edda;
                    color: #155724;
                    font-weight: bold;
                    font-size: 12px;
                }
            """)
        else:
            self.ssh_status_label.setText("❌ Non configuré")
            self.ssh_status_label.setStyleSheet("""
                QLabel {
                    padding: 6px 10px;
                    border-radius: 4px;
                    background-color: #f8d7da;
                    color: #721c24;
                    font-weight: bold;
                    font-size: 12px;
                }
            """)
        
        self.update_buttons_state()

    def import_devices_csv(self):
        """Import des équipements depuis un CSV avec validation améliorée"""
        # Afficher d'abord les instructions pour le format CSV
        csv_help = QMessageBox(self)
        csv_help.setWindowTitle("📋 Format CSV attendu")
        csv_help.setIcon(QMessageBox.Icon.Information)
        csv_help.setText("""<b>Format CSV requis pour l'import :</b>""")
        csv_help.setDetailedText("""Le fichier CSV doit contenir les colonnes suivantes (avec en-têtes) :

COLONNES OBLIGATOIRES:
• hostname : Nom de l'équipement (ex: SW-CORE-01)
• ip : Adresse IP de management (ex: 192.168.1.10)

COLONNES OPTIONNELLES:
• type : Type d'équipement (ex: Cisco, Fortinet, Allied...)
• description : Description libre de l'équipement
• location : Localisation physique

EXEMPLE DE CONTENU CSV:
hostname,ip,type,description,location
SW-CORE-01,192.168.1.10,Cisco,Switch Core Batiment A,Baie-A1
FW-DMZ-01,192.168.1.1,Fortinet,Firewall DMZ,Baie-Securite
SW-ACCESS-02,192.168.1.20,Allied,Switch Access Bureau,Bureau-RDC

IMPORTANT:
✓ Utilisez des virgules comme séparateurs
✓ Pas d'espaces dans les noms de colonnes
✓ Encodage UTF-8 recommandé
✓ Extension .csv obligatoire""")
        
        csv_help.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        csv_help.button(QMessageBox.StandardButton.Ok).setText("📁 Continuer l'import")
        csv_help.button(QMessageBox.StandardButton.Cancel).setText("❌ Annuler")
        
        if csv_help.exec() != QMessageBox.StandardButton.Ok:
            return
        
        # Sélection du fichier CSV
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Importer équipements réseau", 
            "", 
            "Fichiers CSV (*.csv);;Tous les fichiers (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            self.devices = []
            imported_count = 0
            error_count = 0
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Vérifier les colonnes obligatoires
                required_columns = ['hostname', 'ip']
                available_columns = [col.strip().lower() for col in reader.fieldnames]
                
                missing_columns = [col for col in required_columns if col not in available_columns]
                if missing_columns:
                    QMessageBox.critical(
                        self, 
                        "❌ Colonnes manquantes", 
                        f"Les colonnes suivantes sont manquantes dans votre CSV:\n\n"
                        f"{'• ' + chr(10) + '• '.join(missing_columns)}\n\n"
                        f"Colonnes trouvées: {', '.join(reader.fieldnames)}"
                    )
                    return
                
                for row_num, row in enumerate(reader, start=2):  # Start=2 car ligne 1 = en-têtes
                    # Nettoyer et valider les données
                    hostname = row.get('hostname', '').strip()
                    ip = row.get('ip', '').strip()
                    device_type = row.get('type', 'Generic').strip()
                    description = row.get('description', '').strip()
                    location = row.get('location', '').strip()
                    
                    # Validation hostname
                    if not hostname:
                        log_warning(f"Ligne {row_num}: hostname vide, ignorée", "Network")
                        error_count += 1
                        continue
                    
                    # Validation IP basique
                    if not ip:
                        log_warning(f"Ligne {row_num}: IP vide pour {hostname}, ignorée", "Network")
                        error_count += 1
                        continue
                    
                    # Validation format IP simple
                    ip_parts = ip.split('.')
                    if len(ip_parts) != 4 or not all(part.isdigit() and 0 <= int(part) <= 255 for part in ip_parts):
                        log_warning(f"Ligne {row_num}: IP invalide '{ip}' pour {hostname}, ignorée", "Network")
                        error_count += 1
                        continue
                    
                    # Vérifier les doublons
                    if any(device['hostname'] == hostname for device in self.devices):
                        log_warning(f"Ligne {row_num}: hostname '{hostname}' en doublon, ignorée", "Network")
                        error_count += 1
                        continue
                    
                    if any(device['ip'] == ip for device in self.devices):
                        log_warning(f"Ligne {row_num}: IP '{ip}' en doublon, ignorée", "Network")
                        error_count += 1
                        continue
                    
                    # Ajouter l'équipement validé
                    device = {
                        'hostname': hostname,
                        'ip': ip,
                        'type': device_type or 'Generic',
                        'description': description,
                        'location': location
                    }
                    self.devices.append(device)
                    imported_count += 1
                    
                    log_debug(f"Équipement importé: {hostname} ({ip})", "Network")
            
            # Mettre à jour l'affichage
            self.update_devices_table()
            self.update_devices_info()
            self.update_buttons_state()
            
            # Message de résultat
            result_msg = f"✅ Import terminé: {imported_count} équipements importés"
            if error_count > 0:
                result_msg += f"\n⚠️ {error_count} erreurs ignorées"
            
            log_success(f"{imported_count} équipements importés depuis {file_path}", "Network")
            self.add_colored_result(f"SUCCESS: {imported_count} devices imported", "SUCCESS")
            
            if error_count > 0:
                self.add_colored_result(f"WARNING: {error_count} lines ignored due to errors", "WARNING")
            
            # Dialogue de confirmation
            QMessageBox.information(
                self, 
                "📋 Import CSV",
                f"""{result_msg}

<b>Fichier :</b> {os.path.basename(file_path)}
<b>Équipements valides :</b> {imported_count}
<b>Erreurs :</b> {error_count}

<b>Prochaines étapes :</b>
1. Configurez vos identifiants SSH
2. Sélectionnez le type d'équipement approprié
3. Exécutez les commandes de votre choix
                """
            )
            
        except UnicodeDecodeError:
            error_msg = "Erreur d'encodage du fichier CSV. Essayez UTF-8 ou ISO-8859-1."
            log_error(error_msg, "Network")
            self.add_colored_result(f"ERROR: {error_msg}", "ERROR")
            QMessageBox.critical(self, "❌ Erreur d'encodage", error_msg)
            
        except Exception as e:
            log_error(f"Erreur import CSV: {str(e)}", "Network")
            self.add_colored_result(f"ERROR: Import failed - {str(e)}", "ERROR")
            QMessageBox.critical(self, "❌ Erreur Import", f"Impossible d'importer le CSV:\n{str(e)}")

    def update_devices_table(self):
        """Met à jour le tableau des équipements avec plus d'informations"""
        self.devices_table.setColumnCount(4)
        self.devices_table.setHorizontalHeaderLabels(["Hostname", "IP", "Type", "Description"])
        self.devices_table.setRowCount(len(self.devices))
        
        for row, device in enumerate(self.devices):
            self.devices_table.setItem(row, 0, QTableWidgetItem(device['hostname']))
            self.devices_table.setItem(row, 1, QTableWidgetItem(device['ip']))
            self.devices_table.setItem(row, 2, QTableWidgetItem(device['type']))
            self.devices_table.setItem(row, 3, QTableWidgetItem(device.get('description', '')))
        
        self.devices_table.resizeColumnsToContents()

    def update_devices_info(self):
        """Met à jour les infos d'équipements avec détails par type"""
        if self.devices:
            # Compter par type
            type_counts = {}
            for device in self.devices:
                device_type = device['type']
                type_counts[device_type] = type_counts.get(device_type, 0) + 1
            
            # Créer le texte d'info
            total = len(self.devices)
            if len(type_counts) == 1:
                self.devices_info_label.setText(f"{total} équipements chargés ({list(type_counts.keys())[0]})")
            else:
                type_summary = ", ".join([f"{count} {dtype}" for dtype, count in type_counts.items()])
                self.devices_info_label.setText(f"{total} équipements chargés ({type_summary})")
        else:
            self.devices_info_label.setText("Aucun équipement chargé")

    def update_buttons_state(self):
        """Active/désactive les boutons selon l'état"""
        enabled = bool(self.ssh_config and self.devices)
        
        # Activer/désactiver tous les boutons d'actions
        for i in range(self.actions_layout.count()):
            widget = self.actions_layout.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                widget.setEnabled(enabled)
        
        # Message dans les résultats si les prérequis ne sont pas remplis
        if self.devices and not self.ssh_config:
            self.add_colored_result("INFO: Devices loaded. Configure SSH to enable actions.", "INFO")
        elif self.ssh_config and not self.devices:
            self.add_colored_result("INFO: SSH configured. Import devices CSV to enable actions.", "INFO")

    def execute_commands(self, commands):
        """Exécute des commandes sur tous les équipements avec validation"""
        if not self.ssh_config:
            self.add_colored_result("ERROR: SSH not configured", "ERROR")
            QMessageBox.warning(self, "⚠️ SSH requis", "Configurez d'abord vos identifiants SSH.")
            return
        
        if not self.devices:
            self.add_colored_result("ERROR: No devices loaded", "ERROR")
            QMessageBox.warning(self, "⚠️ Équipements requis", "Importez d'abord un fichier CSV avec vos équipements.")
            return
        
        if self.command_thread and self.command_thread.isRunning():
            self.add_colored_result("WARNING: Command already running", "WARNING")
            QMessageBox.information(self, "⏳ Commande en cours", "Une commande est déjà en cours d'exécution.")
            return
        
        # Confirmation avant exécution
        reply = QMessageBox.question(
            self,
            "🚀 Confirmer l'exécution",
            f"""<b>Exécuter les commandes suivantes ?</b>

<b>Commandes :</b>
{'• ' + chr(10) + '• '.join(commands)}

<b>Équipements cibles :</b> {len(self.devices)} équipements
<b>Utilisateur SSH :</b> {self.ssh_config['username']}

<b>⚠️ Attention :</b> Cette action va se connecter à tous vos équipements.
            """,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            self.add_colored_result("INFO: Command execution cancelled by user", "INFO")
            return
        
        # Démarrer le thread de commandes
        device_type = self.device_type_combo.currentText()
        self.command_thread = NetworkCommandThread(
            self.devices, self.ssh_config, commands, device_type
        )
        
        self.command_thread.command_result.connect(self.on_command_success)
        self.command_thread.command_error.connect(self.on_command_error)
        self.command_thread.progress_update.connect(self.on_progress_update)
        self.command_thread.finished.connect(self.on_commands_finished)
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Mode indéterminé
        
        self.add_colored_result(f"INFO: Starting commands on {len(self.devices)} devices...", "INFO")
        self.command_thread.start()

    def on_command_success(self, hostname, command, result):
        """Callback succès de commande"""
        self.add_colored_result(f"SUCCESS: {hostname} - {command}", "SUCCESS")
        
        # Afficher les résultats (tronqués si trop longs)
        lines = result.strip().split('\n')
        if len(lines) > 20:
            result_preview = '\n'.join(lines[:20]) + f"\n... ({len(lines)-20} more lines)"
        else:
            result_preview = result.strip()
        
        # Ajouter le résultat en gris pour ne pas encombrer
        cursor = self.results_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        format = QTextCharFormat()
        format.setForeground(QColor("#868e96"))
        cursor.setCharFormat(format)
        timestamp = time.strftime("%H:%M:%S")
        cursor.insertText(f"[{timestamp}] RESULT | {hostname}:\n{result_preview}\n\n")
        
        # Auto-scroll
        scrollbar = self.results_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def on_command_error(self, hostname, command, error):
        """Callback erreur de commande"""
        self.add_colored_result(f"ERROR: {hostname} - {command}: {error}", "ERROR")

    def on_progress_update(self, message):
        """Callback mise à jour progression"""
        self.add_colored_result(f"INFO: {message}", "INFO")

    def on_commands_finished(self):
        """Callback fin des commandes"""
        self.progress_bar.setVisible(False)
        self.add_colored_result("INFO: All commands completed", "INFO")
        
        # Message de fin avec résumé
        QMessageBox.information(
            self,
            "✅ Commandes terminées",
            "L'exécution des commandes sur tous les équipements est terminée.\n\n"
            "Consultez les résultats détaillés dans la zone d'affichage."
        )

    # === MÉTHODES CISCO ===
    def show_version(self):
        """Show version Cisco"""
        self.execute_commands(["show version"])

    def show_running_config(self):
        """Show running-config Cisco"""
        self.execute_commands(["show running-config"])

    def show_interfaces(self):
        """Show interfaces status Cisco"""
        self.execute_commands(["show interfaces status", "show ip interface brief"])

    def show_ip_route(self):
        """Show IP route Cisco"""
        self.execute_commands(["show ip route"])

    def show_mac_table(self):
        """Show MAC address table Cisco"""
        self.execute_commands(["show mac address-table"])

    def show_power(self):
        """Show power status Cisco"""
        self.execute_commands(["show power", "show environment power"])

    def show_vlans(self):
        """Show VLAN Cisco"""
        self.execute_commands(["show vlan brief"])

    def show_cdp(self):
        """Show CDP neighbors Cisco"""
        self.execute_commands(["show cdp neighbors detail"])

    # === MÉTHODES FORTINET ===
    def fortinet_system_status(self):
        """System status Fortinet"""
        self.execute_commands(["get system status"])

    def fortinet_config(self):
        """Configuration Fortinet"""
        self.execute_commands(["show full-configuration"])

    def fortinet_routes(self):
        """Routes Fortinet"""
        self.execute_commands(["get router info routing-table all"])

    def fortinet_policies(self):
        """Policies Fortinet"""
        self.execute_commands(["show firewall policy"])

    def fortinet_interfaces(self):
        """Interfaces Fortinet"""
        self.execute_commands(["get system interface"])

    def fortinet_sessions(self):
        """Sessions Fortinet"""
        self.execute_commands(["get system session list"])

    def fortinet_performance(self):
        """Performance Fortinet"""
        self.execute_commands(["get system performance status"])

    # === MÉTHODES ALLIED TELESIS ===
    def allied_show_system(self):
        """System Allied"""
        self.execute_commands(["show system"])

    def allied_show_config(self):
        """Config Allied"""
        self.execute_commands(["show running-config"])

    def allied_show_interface(self):
        """Interfaces Allied"""
        self.execute_commands(["show interface"])

    def allied_show_route(self):
        """Routes Allied"""
        self.execute_commands(["show ip route"])

    def allied_show_switch(self):
        """Switch info Allied"""
        self.execute_commands(["show switch"])

    def allied_show_vlan(self):
        """VLAN Allied"""
        self.execute_commands(["show vlan all"])

    # === MÉTHODES STORMSHIELD ===
    def stormshield_system(self):
        """System Stormshield"""
        self.execute_commands(["system info"])

    def stormshield_config(self):
        """Config Stormshield"""
        self.execute_commands(["config system global show"])

    def stormshield_routes(self):
        """Routes Stormshield"""
        self.execute_commands(["network route list"])

    def stormshield_rules(self):
        """Rules Stormshield"""
        self.execute_commands(["config firewall policy show"])

    def stormshield_connections(self):
        """Connections Stormshield"""
        self.execute_commands(["monitor connection list"])

    def stormshield_monitor(self):
        """Monitor Stormshield"""
        self.execute_commands(["monitor system status"])

    # === MÉTHODES GÉNÉRIQUES ===
    def generic_system_info(self):
        """Info système générique"""
        self.execute_commands(["uname -a", "uptime", "whoami"])

    def generic_network(self):
        """Config réseau générique"""
        self.execute_commands(["ip addr show", "ip route show"])

    def generic_interfaces(self):
        """Interfaces génériques"""
        self.execute_commands(["ifconfig -a", "netstat -i"])

    def generic_processes(self):
        """Processus génériques"""
        self.execute_commands(["ps aux", "top -n 1"])

    def generic_disk(self):
        """Disque générique"""
        self.execute_commands(["df -h", "free -h"])

    def generic_custom(self):
        """Commande personnalisée"""
        command, ok = QInputDialog.getText(
            self, 
            "🔍 Commande personnalisée", 
            "Entrez la commande à exécuter sur tous les équipements:"
        )
        
        if ok and command.strip():
            # Demander confirmation pour les commandes personnalisées
            reply = QMessageBox.question(
                self,
                "⚠️ Commande personnalisée",
                f"""<b>Exécuter cette commande personnalisée ?</b>

<b>Commande :</b> {command.strip()}
<b>Équipements :</b> {len(self.devices)}

<b>⚠️ Attention :</b> Assurez-vous que cette commande est sûre et compatible avec vos équipements.
                """,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.execute_commands([command.strip()])

    def export_results(self):
        """Export des résultats avec métadonnées"""
        try:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            default_filename = f"network_results_{timestamp}.txt"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Exporter les résultats réseau",
                default_filename,
                "Fichiers texte (*.txt);;Fichiers CSV (*.csv);;Tous les fichiers (*.*)"
            )
            
            if file_path:
                content = self.results_display.toPlainText()
                
                # Ajouter des métadonnées en en-tête
                metadata = f"""
================================================================================
                     EXPORT RESULTATS NETWORK MANAGEMENT
================================================================================
Date d'export       : {time.strftime('%Y-%m-%d %H:%M:%S')}
Version Toolbox     : Alpha 0.0.6
Développeur         : ocrano
================================================================================
Configuration SSH   : {'✅ Configuré' if self.ssh_config else '❌ Non configuré'}
Utilisateur SSH     : {self.ssh_config.get('username', 'N/A')}
Équipements chargés : {len(self.devices)}
Type d'équipement   : {self.device_type_combo.currentText()}
================================================================================

ÉQUIPEMENTS DANS LA SESSION:
"""
                
                if self.devices:
                    for i, device in enumerate(self.devices, 1):
                        metadata += f"{i:2d}. {device['hostname']:<20} | {device['ip']:<15} | {device['type']:<15} | {device.get('description', '')}\n"
                else:
                    metadata += "Aucun équipement chargé\n"
                
                metadata += "\n" + "="*80 + "\n"
                metadata += "                           RÉSULTATS DÉTAILLÉS\n"
                metadata += "="*80 + "\n\n"
                
                # Écrire le fichier complet
                full_content = metadata + content
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(full_content)
                
                self.add_colored_result(f"SUCCESS: Results exported to {os.path.basename(file_path)}", "SUCCESS")
                log_success(f"Résultats Network exportés vers {file_path}", "Network")
                
                # Message de confirmation
                QMessageBox.information(
                    self,
                    "✅ Export réussi",
                    f"""<b>Résultats exportés avec succès !</b>

<b>Fichier :</b> {os.path.basename(file_path)}
<b>Taille :</b> {len(full_content)} caractères
<b>Métadonnées :</b> Incluses (config, équipements, horodatage)

Le fichier contient tous les résultats de votre session Network Management.
                    """
                )
                
        except Exception as e:
            self.add_colored_result(f"ERROR: Export failed - {str(e)}", "ERROR")
            log_error(f"Erreur export Network: {str(e)}", "Network")
            QMessageBox.critical(
                self, 
                "❌ Erreur d'export", 
                f"Impossible d'exporter les résultats:\n{str(e)}"
            )

    def clear_results(self):
        """Efface les résultats avec confirmation"""
        reply = QMessageBox.question(
            self,
            "🗑️ Effacer les résultats",
            "Êtes-vous sûr de vouloir effacer tous les résultats affichés ?\n\n"
            "Cette action est irréversible.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.results_display.clear()
            self.add_initial_messages()
            
            # Message de nettoyage
            cursor = self.results_display.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            format = QTextCharFormat()
            format.setForeground(QColor("#ffd43b"))
            cursor.setCharFormat(format)
            timestamp = time.strftime("%H:%M:%S")
            cursor.insertText(f"[{timestamp}] SYSTEM | Results cleared by user\n\n")
            
            log_info("Résultats Network effacés par l'utilisateur", "Network")
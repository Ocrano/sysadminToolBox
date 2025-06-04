import os
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow, QPushButton, QListWidget, QVBoxLayout,
    QWidget, QInputDialog, QLineEdit, QMessageBox, QTabWidget,
    QComboBox, QCheckBox, QListWidgetItem, QTextEdit, QLabel, QFileDialog,
    QTableWidget, QTableWidgetItem, QGroupBox, QFormLayout, QProgressBar,
    QHBoxLayout, QSplitter, QGridLayout
)
from PyQt6.QtGui import QColor, QFont, QTextCharFormat
from .dialogs.proxmox_config_dialog import ProxmoxConfigDialog
from .dialogs.qemu_agent_dialog import QemuAgentManagerDialog
from ..utils.ip_plan_importer import IPPlanImporter
import pandas as pd
import datetime

# Import du système de logging
from ..core.logger import toolbox_logger, log_info, log_debug, log_error, log_success, log_warning


class MainWindow(QMainWindow):
    # Constantes de version
    VERSION = "Alpha 0.0.6"
    DEVELOPER = "ocrano"
    
    def __init__(self, git_manager, script_runner, proxmox_handler):
        super().__init__()
        self.git_manager = git_manager
        self.script_runner = script_runner
        self.proxmox_handler = proxmox_handler
        self.importer = IPPlanImporter()
        
        # Initialisation du logging pour la fenêtre principale
        log_info("Initialisation de la fenêtre principale", "MainWindow")
        
        self.init_ui()
        self.setup_logging()  # Configuration du logging en temps réel

    def get_version_label(self):
        """Retourne un QLabel avec la version et le développeur"""
        version_label = QLabel(f"{self.VERSION} • by {self.DEVELOPER}")
        version_label.setStyleSheet("color: #6c757d; font-size: 10px; font-style: italic;")
        return version_label

    def setup_logging(self):
        """Configure la redirection des logs vers l'interface principale"""
        # Connecter le handler de logging à notre zone de logs
        qt_handler = toolbox_logger.get_qt_handler()
        qt_handler.log_message.connect(self.on_log_message)
        
        # Initialiser les filtres de logs
        self.log_filters = {
            'DEBUG': False,  # DEBUG désactivé par défaut
            'INFO': True,
            'WARNING': True,
            'ERROR': True,
            'SUCCESS': True
        }
        
        # Système de déduplication intelligent
        self.last_messages = {}  # Dernier message par catégorie
        self.message_count = {}  # Compteur de messages similaires
        self.dedup_window = 10   # Fenêtre de déduplication (secondes)
        
        # Mise à jour des checkboxes pour refléter l'état initial
        if hasattr(self, 'debug_checkbox'):
            self.debug_checkbox.setChecked(False)
        
        # Log initial
        log_info("Système de logs en temps réel avec déduplication activé", "MainWindow")

    def add_colored_log_message(self, message):
        """Ajoute un message coloré dans les logs avec meilleure séparation"""
        if not hasattr(self, 'tools_logs'):
            return
            
        # Parser le message pour extraire les composants
        parts = self.parse_log_message(message)
        
        if parts:
            timestamp = parts.get('timestamp', '')
            level = parts.get('level', 'INFO')
            logger_name = parts.get('logger_name', '')
            component = parts.get('component', '')
            content = parts.get('content', message)
            
            # Construire le message formaté avec séparation claire
            formatted_message = f"[{timestamp}] {level:<7} | {logger_name:<12} | [{component}] | {content}"
            
            # Appliquer la couleur selon le niveau
            cursor = self.tools_logs.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            
            # Format par défaut
            format = QTextCharFormat()
            format.setForeground(QColor("#e0e0e0"))  # Blanc par défaut
            
            # Appliquer les couleurs selon le niveau
            if level == 'ERROR':
                format.setForeground(QColor("#ff6b6b"))  # Rouge
                format.setFontWeight(QFont.Weight.Bold)
            elif 'SUCCESS' in content:
                format.setForeground(QColor("#51cf66"))  # Vert
                format.setFontWeight(QFont.Weight.Bold)
            elif level == 'WARNING':
                format.setForeground(QColor("#ffd43b"))  # Jaune
            elif level == 'DEBUG':
                format.setForeground(QColor("#868e96"))  # Gris
            else:  # INFO
                format.setForeground(QColor("#74c0fc"))  # Bleu clair
            
            cursor.setCharFormat(format)
            cursor.insertText(formatted_message + "\n")
            
            # Auto-scroll vers le bas
            scrollbar = self.tools_logs.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        else:
            # Fallback pour les messages non parsables
            cursor = self.tools_logs.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            format = QTextCharFormat()
            format.setForeground(QColor("#e0e0e0"))
            cursor.setCharFormat(format)
            cursor.insertText(message + "\n")

    def parse_log_message(self, message):
        """Parse un message de log pour extraire ses composants"""
        import re
        
        # Pattern pour parser: [timestamp] LEVEL [logger_name] [component] message
        pattern = r'\[(\d{2}:\d{2}:\d{2})\]\s+(\w+)\s+\[([^\]]+)\]\s+\[([^\]]+)\]\s+(.*)'
        match = re.match(pattern, message)
        
        if match:
            return {
                'timestamp': match.group(1),
                'level': match.group(2),
                'logger_name': match.group(3),
                'component': match.group(4),
                'content': match.group(5)
            }
        
        # Pattern alternatif plus simple: [timestamp] LEVEL [component] message
        pattern2 = r'\[(\d{2}:\d{2}:\d{2})\]\s+(\w+)\s+\[([^\]]+)\]\s+(.*)'
        match2 = re.match(pattern2, message)
        
        if match2:
            return {
                'timestamp': match2.group(1),
                'level': match2.group(2),
                'logger_name': 'ToolboxPyQt6',
                'component': match2.group(3),
                'content': match2.group(4)
            }
        
        return None

    def categorize_message(self, message):
        """Catégorise un message pour la déduplication"""
        message_lower = message.lower()
        
        # Catégories spécifiques pour éviter les doublons
        if 'vms trouvées' in message_lower or 'vm trouvées' in message_lower:
            return 'vm_count'
        elif 'vms linux' in message_lower and 'trouvées' in message_lower:
            return 'linux_vm_count'
        elif 'connexion' in message_lower and ('réussie' in message_lower or 'établie' in message_lower):
            return 'connection_success'
        elif 'récupération' in message_lower and ('statut' in message_lower or 'informations' in message_lower):
            return 'status_retrieval'
        elif 'statut de' in message_lower and 'nœud' in message_lower:
            return 'node_status'
        elif 'stockage' in message_lower and ('trouvés' in message_lower or 'analysé' in message_lower):
            return 'storage_info'
        elif 'interface tools' in message_lower:
            return 'tools_interface'
        elif 'version proxmox' in message_lower:
            return 'proxmox_version'
        
        return 'general'

    def should_deduplicate(self, message, category):
        """Détermine si un message doit être dédupliqué"""
        import time
        current_time = time.time()
        
        # Ne jamais dédupliquer les erreurs et warnings
        if 'ERROR' in message or 'WARNING' in message:
            return False
        
        # Ne jamais dédupliquer les succès importants
        if 'SUCCESS:' in message and any(word in message.lower() for word in ['installation', 'export', 'sauvegarde']):
            return False
        
        # Vérifier la fenêtre de déduplication
        if category in self.last_messages:
            last_time, last_msg = self.last_messages[category]
            
            if current_time - last_time < self.dedup_window:
                if self.messages_are_similar(message, last_msg):
                    self.message_count[category] = self.message_count.get(category, 1) + 1
                    return True
        
        # Sauvegarder ce message comme référence
        self.last_messages[category] = (current_time, message)
        self.message_count[category] = 1
        return False

    def messages_are_similar(self, msg1, msg2):
        """Compare deux messages pour voir s'ils sont similaires"""
        clean1 = self.clean_message_for_comparison(msg1)
        clean2 = self.clean_message_for_comparison(msg2)
        
        if clean1 == clean2:
            return True
        
        similar_patterns = [
            (['vms trouvées', 'vm trouvées'], 'count_vms'),
            (['connexion réussie', 'connexion établie'], 'connection'),
            (['récupération', 'récupération de'], 'retrieval'),
            (['statut récupéré', 'statut de'], 'status'),
        ]
        
        for patterns, pattern_type in similar_patterns:
            if any(p in clean1 for p in patterns) and any(p in clean2 for p in patterns):
                return True
        
        return False

    def clean_message_for_comparison(self, message):
        """Nettoie un message pour la comparaison"""
        import re
        
        cleaned = re.sub(r'\[\d{2}:\d{2}:\d{2}\]', '', message)
        cleaned = re.sub(r'(DEBUG|INFO|WARNING|ERROR|SUCCESS):', '', cleaned)
        cleaned = re.sub(r'\[[\w\s\-]+\]', '', cleaned)
        cleaned = re.sub(r'\d+', 'X', cleaned)
        cleaned = ' '.join(cleaned.split()).strip().lower()
        
        return cleaned

    def create_summary_message(self, category, count, last_message):
        """Crée un message de résumé pour les messages dédupliqués"""
        if category == 'vm_count':
            return f"SUMMARY: {count} VM count requests (last: list updated)"
        elif category == 'linux_vm_count':
            return f"SUMMARY: {count} Linux VM scans performed"
        elif category == 'connection_success':
            return f"SUMMARY: Proxmox connection confirmed ({count} checks)"
        elif category == 'status_retrieval':
            return f"SUMMARY: {count} status retrievals performed"
        elif category == 'node_status':
            return f"SUMMARY: Node status updated ({count} times)"
        elif category == 'storage_info':
            return f"SUMMARY: Storage information analyzed ({count} times)"
        else:
            return f"SUMMARY: {count} similar messages grouped"

    def on_log_message(self, message):
        """Appelé quand un nouveau message de log arrive avec coloration"""
        if hasattr(self, 'tools_logs'):
            # Sauvegarder le message dans la liste complète
            if not hasattr(self, 'all_logs'):
                self.all_logs = []
            self.all_logs.append(message)
            
            # Déterminer le niveau du log
            log_level = self.extract_log_level(message)
            
            # Vérifier les filtres
            if not self.log_filters.get(log_level, True):
                return
            
            # Système de déduplication
            category = self.categorize_message(message)
            
            if self.should_deduplicate(message, category):
                # Message dédupliqué
                if self.message_count[category] == 2:  # Premier doublon
                    summary = self.create_summary_message(category, self.message_count[category], message)
                    self.add_colored_log_message(f"DEDUP: {summary}")
                elif self.message_count[category] > 2 and self.message_count[category] % 5 == 0:
                    summary = self.create_summary_message(category, self.message_count[category], message)
                    self.add_colored_log_message(f"DEDUP: {summary}")
            else:
                # Message unique - l'afficher avec coloration
                self.add_colored_log_message(message)

    def extract_log_level(self, message):
        """Extrait le niveau de log d'un message"""
        if 'DEBUG' in message:
            return 'DEBUG'
        elif 'INFO' in message:
            return 'INFO'
        elif 'WARNING' in message:
            return 'WARNING'
        elif 'ERROR' in message:
            return 'ERROR'
        elif 'SUCCESS:' in message:
            return 'SUCCESS'
        else:
            return 'INFO'

    def init_ui(self):
        self.setWindowTitle("Toolbox PyQt6")
        self.setGeometry(200, 200, 1200, 800)
        self.setMinimumSize(1000, 600)
        log_debug("Configuration fenêtre principale: 1200x800 (redimensionnable, min: 1000x600)", "MainWindow")

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.scripts_tab = QWidget()
        self.setup_scripts_tab()
        self.tabs.addTab(self.scripts_tab, "Scripts PowerShell")

        self.settings_tab = QWidget()
        self.setup_settings_tab()
        self.tabs.addTab(self.settings_tab, "Paramètres")

        # ONGLET SCANNER réseau
        try:
            from .tabs.network_scanner_tab import NetworkScannerTab
            self.scan_tab = NetworkScannerTab(self, self.proxmox_handler)
            self.tabs.addTab(self.scan_tab, "SCAN")
            
            try:
                scan_layout = self.scan_tab.layout()
                if scan_layout:
                    scan_header = QHBoxLayout()
                    scan_title = QLabel("Scanner Réseau")
                    scan_title.setStyleSheet("font-size: 14px; font-weight: bold;")
                    scan_header.addWidget(scan_title)
                    scan_header.addStretch()
                    scan_header.addWidget(self.get_version_label())
                    scan_layout.insertLayout(0, scan_header)
                else:
                    log_debug("Impossible d'ajouter la version à l'onglet Scanner - Layout non trouvé", "MainWindow")
            except Exception as e:
                log_debug(f"Erreur ajout version onglet Scanner: {e}", "MainWindow")
            
            log_debug("Onglet Scanner réseau ajouté", "MainWindow")
        except ImportError as e:
            log_warning(f"Onglet Scanner non disponible: {e}", "MainWindow")

        # ONGLET TOOLS
        self.tools_tab = QWidget()
        self.setup_tools_tab()
        self.tabs.addTab(self.tools_tab, "Tools")

        # NOUVEAU: ONGLET NETWORK
        try:
            from .tabs.network_tab import NetworkTab
            self.network_tab = NetworkTab(self)
            self.tabs.addTab(self.network_tab, "Network")
            log_debug("Onglet Network ajouté", "MainWindow")
        except ImportError as e:
            log_warning(f"Onglet Network non disponible: {e}", "MainWindow")
        except Exception as e:
            log_error(f"Erreur création onglet Network: {e}", "MainWindow")

        self.import_tab = QWidget()
        self.setup_import_tab()
        self.tabs.addTab(self.import_tab, "Import IP Plan")

        log_success("Interface utilisateur initialisée", "MainWindow")
        self.load_existing_scripts()

    def setup_scripts_tab(self):
        layout = QVBoxLayout()
        
        header_layout = QHBoxLayout()
        title_label = QLabel("Scripts PowerShell")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.get_version_label())
        layout.addLayout(header_layout)
        
        self.scripts_list = QListWidget()
        layout.addWidget(self.scripts_list)

        self.fetch_scripts_btn = QPushButton("Récupérer Scripts")
        self.fetch_scripts_btn.clicked.connect(self.load_scripts)
        layout.addWidget(self.fetch_scripts_btn)

        self.run_script_btn = QPushButton("Exécuter Script Sélectionné")
        self.run_script_btn.clicked.connect(self.run_selected_script)
        layout.addWidget(self.run_script_btn)

        self.scripts_tab.setLayout(layout)
        log_debug("Onglet Scripts PowerShell configuré", "MainWindow")

    def setup_settings_tab(self):
        layout = QVBoxLayout()
        
        header_layout = QHBoxLayout()
        title_label = QLabel("Paramètres")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.get_version_label())
        layout.addLayout(header_layout)
        
        self.set_token_btn = QPushButton("Entrer un Token GitLab")
        self.set_token_btn.clicked.connect(self.ask_gitlab_token)
        layout.addWidget(self.set_token_btn)
        self.settings_tab.setLayout(layout)
        log_debug("Onglet Paramètres configuré", "MainWindow")

    def setup_tools_tab(self):
        """Configure l'onglet Tools avec affichage logs colorés"""
        main_layout = QVBoxLayout()
        
        # === SECTION CONNEXION PROXMOX ===
        connection_group = QGroupBox("🔗 Connexion Proxmox")
        connection_group.setMaximumHeight(80)
        connection_layout = QHBoxLayout()
        connection_layout.setContentsMargins(10, 5, 10, 5)
        
        self.config_proxmox_btn = QPushButton("⚙️ Configurer")
        self.config_proxmox_btn.clicked.connect(self.configure_proxmox)
        self.config_proxmox_btn.setFixedWidth(120)
        self.config_proxmox_btn.setStyleSheet("""
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
        connection_layout.addWidget(self.config_proxmox_btn)
        
        self.connection_status_label = QLabel("❌ Non connecté")
        self.connection_status_label.setFixedWidth(100)
        self.connection_status_label.setStyleSheet("""
            QLabel {
                padding: 6px 10px;
                border-radius: 4px;
                background-color: #f8d7da;
                color: #721c24;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        connection_layout.addWidget(self.connection_status_label)
        
        self.proxmox_info_label = QLabel("")
        self.proxmox_info_label.setStyleSheet("color: #495057; font-size: 12px; margin-left: 10px;")
        connection_layout.addWidget(self.proxmox_info_label)
        
        self.system_info_label = QLabel("")
        self.system_info_label.setStyleSheet("color: #6c757d; font-size: 11px;")
        connection_layout.addWidget(self.system_info_label)
        
        connection_layout.addStretch()
        connection_layout.addWidget(self.get_version_label())
        
        connection_group.setLayout(connection_layout)
        main_layout.addWidget(connection_group)
        
        # === SPLITTER PRINCIPAL ===
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # === SECTION ACTIONS ===
        actions_widget = QWidget()
        actions_layout = QVBoxLayout()
        
        actions_title = QLabel("🛠️ Actions disponibles")
        actions_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        actions_layout.addWidget(actions_title)
        
        # === GROUPE VM MANAGEMENT ===
        vm_group = QGroupBox("🖥️ Gestion des VMs")
        vm_layout = QVBoxLayout()
        
        self.qemu_agent_btn = QPushButton("🔧 Gestionnaire QEMU Agent")
        self.qemu_agent_btn.clicked.connect(self.open_qemu_agent_manager)
        self.qemu_agent_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 5px;
                font-weight: bold;
                text-align: left;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.qemu_agent_btn.setEnabled(False)
        vm_layout.addWidget(self.qemu_agent_btn)
        
        self.list_vms_btn = QPushButton("📋 Lister toutes les VMs")
        self.list_vms_btn.clicked.connect(self.list_all_vms)
        self.list_vms_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 5px;
                font-weight: bold;
                text-align: left;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.list_vms_btn.setEnabled(False)
        vm_layout.addWidget(self.list_vms_btn)
        
        self.scan_linux_btn = QPushButton("🐧 Scanner VMs Linux")
        self.scan_linux_btn.clicked.connect(self.scan_linux_vms)
        self.scan_linux_btn.setStyleSheet("""
            QPushButton {
                background-color: #fd7e14;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 5px;
                font-weight: bold;
                text-align: left;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #e55100;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.scan_linux_btn.setEnabled(False)
        vm_layout.addWidget(self.scan_linux_btn)
        
        vm_group.setLayout(vm_layout)
        actions_layout.addWidget(vm_group)
        
        # === GROUPE INFRASTRUCTURE ===
        infra_group = QGroupBox("🏗️ Infrastructure")
        infra_layout = QVBoxLayout()
        
        self.nodes_status_btn = QPushButton("📊 Statut des nœuds")
        self.nodes_status_btn.clicked.connect(self.show_nodes_status)
        self.nodes_status_btn.setStyleSheet("""
            QPushButton {
                background-color: #6f42c1;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 5px;
                font-weight: bold;
                text-align: left;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #5a2d91;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.nodes_status_btn.setEnabled(False)
        infra_layout.addWidget(self.nodes_status_btn)
        
        self.storage_info_btn = QPushButton("💾 Informations stockage")
        self.storage_info_btn.clicked.connect(self.show_storage_info)
        self.storage_info_btn.setStyleSheet("""
            QPushButton {
                background-color: #e83e8c;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 5px;
                font-weight: bold;
                text-align: left;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #c82166;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.storage_info_btn.setEnabled(False)
        infra_layout.addWidget(self.storage_info_btn)
        
        infra_group.setLayout(infra_layout)
        actions_layout.addWidget(infra_group)
        
        # === GROUPE FUTURES FONCTIONNALITÉS ===
        future_group = QGroupBox("🚀 Prochainement")
        future_layout = QVBoxLayout()
        
        future_info = QLabel("• Gestion des snapshots\n• Sauvegarde automatique\n• Monitoring avancé\n• Scripts d'automatisation")
        future_info.setStyleSheet("color: #6c757d; font-style: italic; padding: 10px;")
        future_layout.addWidget(future_info)
        
        future_group.setLayout(future_layout)
        actions_layout.addWidget(future_group)
        
        actions_layout.addStretch()
        actions_widget.setLayout(actions_layout)
        main_splitter.addWidget(actions_widget)
        
        # === SECTION LOGS COLORÉS ===
        logs_widget = QWidget()
        logs_layout = QVBoxLayout()
        
        logs_header_layout = QHBoxLayout()
        logs_title = QLabel("📋 Logs en temps réel")
        logs_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        logs_header_layout.addWidget(logs_title)
        
        logs_header_layout.addStretch()
        
        # === SECTION FILTRES DE LOGS ===
        filters_group = QGroupBox("Filtres")
        filters_layout = QHBoxLayout()
        filters_layout.setContentsMargins(5, 2, 5, 2)
        
        self.debug_checkbox = QCheckBox("DEBUG")
        self.debug_checkbox.setChecked(False)
        self.debug_checkbox.setStyleSheet("color: #6c757d; font-size: 11px;")
        self.debug_checkbox.toggled.connect(lambda checked: self.update_log_filter('DEBUG', checked))
        filters_layout.addWidget(self.debug_checkbox)
        
        self.info_checkbox = QCheckBox("INFO")
        self.info_checkbox.setChecked(True)
        self.info_checkbox.setStyleSheet("color: #17a2b8; font-size: 11px;")
        self.info_checkbox.toggled.connect(lambda checked: self.update_log_filter('INFO', checked))
        filters_layout.addWidget(self.info_checkbox)
        
        self.warning_checkbox = QCheckBox("WARNING")
        self.warning_checkbox.setChecked(True)
        self.warning_checkbox.setStyleSheet("color: #ffc107; font-size: 11px;")
        self.warning_checkbox.toggled.connect(lambda checked: self.update_log_filter('WARNING', checked))
        filters_layout.addWidget(self.warning_checkbox)
        
        self.error_checkbox = QCheckBox("ERROR")
        self.error_checkbox.setChecked(True)
        self.error_checkbox.setStyleSheet("color: #dc3545; font-size: 11px;")
        self.error_checkbox.toggled.connect(lambda checked: self.update_log_filter('ERROR', checked))
        filters_layout.addWidget(self.error_checkbox)
        
        self.success_checkbox = QCheckBox("SUCCESS")
        self.success_checkbox.setChecked(True)
        self.success_checkbox.setStyleSheet("color: #28a745; font-size: 11px;")
        self.success_checkbox.toggled.connect(lambda checked: self.update_log_filter('SUCCESS', checked))
        filters_layout.addWidget(self.success_checkbox)
        
        filters_group.setLayout(filters_layout)
        filters_group.setMaximumHeight(50)
        logs_header_layout.addWidget(filters_group)
        
        self.export_logs_btn = QPushButton("💾 Exporter")
        self.export_logs_btn.clicked.connect(self.export_logs_to_file)
        self.export_logs_btn.setStyleSheet("""
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
        logs_header_layout.addWidget(self.export_logs_btn)
        
        self.clear_logs_btn = QPushButton("🗑️ Effacer")
        self.clear_logs_btn.clicked.connect(self.clear_tools_logs)
        self.clear_logs_btn.setStyleSheet("""
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
        logs_header_layout.addWidget(self.clear_logs_btn)
        
        logs_layout.addLayout(logs_header_layout)
        
        # === ZONE DE LOGS COLORÉS AVEC FOND NOIR ===
        self.tools_logs = QTextEdit()
        self.tools_logs.setReadOnly(True)
        self.tools_logs.setFont(QFont("Consolas", 10))
        
        # Style avec fond noir pour meilleure lisibilité
        self.tools_logs.setStyleSheet("""
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
        
        # Messages d'accueil avec format coloré
        self.add_initial_log_messages()
        
        # Initialiser la liste complète des logs
        self.all_logs = []
        
        logs_layout.addWidget(self.tools_logs)
        logs_widget.setLayout(logs_layout)
        main_splitter.addWidget(logs_widget)
        
        # Répartition 30/70 entre actions et logs
        main_splitter.setStretchFactor(0, 30)
        main_splitter.setStretchFactor(1, 70)
        
        main_layout.addWidget(main_splitter)
        self.tools_tab.setLayout(main_layout)
        
        log_debug("Onglet Tools configuré avec affichage logs colorés", "MainWindow")

    def add_initial_log_messages(self):
        """Ajoute les messages d'accueil colorés"""
        cursor = self.tools_logs.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        
        # En-tête avec couleur spéciale
        format_header = QTextCharFormat()
        format_header.setForeground(QColor("#74c0fc"))  # Bleu clair
        format_header.setFontWeight(QFont.Weight.Bold)
        cursor.setCharFormat(format_header)
        cursor.insertText("=" * 80 + "\n")
        cursor.insertText("                        TOOLBOX LOGS - SESSION STARTED\n")
        cursor.insertText("=" * 80 + "\n\n")
        
        # Messages système en couleur
        format_system = QTextCharFormat()
        format_system.setForeground(QColor("#51cf66"))  # Vert
        cursor.setCharFormat(format_system)
        cursor.insertText("SYSTEM: Welcome to Tools section\n")
        cursor.insertText("SYSTEM: All Proxmox/VM action logs will appear here\n")
        cursor.insertText("SYSTEM: Use checkboxes above to filter by log level\n")
        cursor.insertText("SYSTEM: SUCCESS messages appear in GREEN, ERROR messages in RED\n\n")
        
        # Message d'attente en bleu
        format_info = QTextCharFormat()
        format_info.setForeground(QColor("#74c0fc"))  # Bleu clair
        cursor.setCharFormat(format_info)
        cursor.insertText("INFO: Waiting for Proxmox connection...\n\n")

    def update_log_filter(self, level, enabled):
        """Met à jour les filtres de logs et rafraîchit l'affichage"""
        self.log_filters[level] = enabled
        log_debug(f"Filtre {level} {'activé' if enabled else 'désactivé'}", "Tools")
        
        # Rafraîchir l'affichage des logs
        self.refresh_logs_display()

    def refresh_logs_display(self):
        """Rafraîchit l'affichage des logs selon les filtres actifs"""
        if not hasattr(self, 'tools_logs') or not hasattr(self, 'all_logs'):
            return
        
        # Sauvegarder la position de scroll
        scrollbar = self.tools_logs.verticalScrollBar()
        scroll_position = scrollbar.value()
        was_at_bottom = scroll_position == scrollbar.maximum()
        
        # Vider l'affichage
        self.tools_logs.clear()
        
        # Réafficher les messages de bienvenue
        self.add_initial_log_messages()
        
        # Réafficher les logs filtrés avec coloration
        for message in self.all_logs:
            log_level = self.extract_log_level(message)
            if self.log_filters.get(log_level, True):
                self.add_colored_log_message(message)
        
        # Restaurer la position de scroll
        if was_at_bottom:
            scrollbar.setValue(scrollbar.maximum())
        else:
            scrollbar.setValue(scroll_position)

    def clear_tools_logs(self):
        """Efface la zone de logs de l'onglet Tools"""
        self.tools_logs.clear()
        self.all_logs = []
        
        # Réafficher uniquement les messages d'accueil
        self.add_initial_log_messages()
        
        # Ajouter message de nettoyage en couleur
        cursor = self.tools_logs.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        format_clear = QTextCharFormat()
        format_clear.setForeground(QColor("#ffd43b"))  # Jaune
        cursor.setCharFormat(format_clear)
        cursor.insertText("SYSTEM: Logs cleared by user\n\n")
        
        log_info("Logs Tools effacés par l'utilisateur", "Tools")

    def export_logs_to_file(self):
        """Exporte les logs dans un fichier choisi par l'utilisateur"""
        try:
            from PyQt6.QtWidgets import QFileDialog, QMessageBox
            import datetime
            
            reply = QMessageBox.question(
                self,
                "Type d'export",
                "Quel type de logs voulez-vous exporter ?\n\n" +
                "• OUI = Logs actuellement affichés (filtrés)\n" +
                "• NON = Tous les logs (complets)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Cancel:
                return
            
            export_type = "filtered" if reply == QMessageBox.StandardButton.Yes else "complete"
            default_filename = f"toolbox_logs_{export_type}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Exporter les logs",
                default_filename,
                "Fichiers log (*.log);;Fichiers texte (*.txt);;Tous les fichiers (*.*)"
            )
            
            if file_path:
                if reply == QMessageBox.StandardButton.Yes:
                    logs_content = self.tools_logs.toPlainText()
                    logs_info = "Logs filtrés selon les préférences utilisateur"
                    active_filters = [level for level, enabled in self.log_filters.items() if enabled]
                    logs_info += f"\nFiltres actifs: {', '.join(active_filters)}"
                else:
                    logs_content = '\n'.join(self.all_logs) if hasattr(self, 'all_logs') else self.tools_logs.toPlainText()
                    logs_info = "Logs complets (tous niveaux inclus)"
                
                export_content = f"""
================================================================================
                        TOOLBOX PyQt6 - EXPORT DES LOGS
================================================================================
Version         : {self.VERSION}
Développeur     : {self.DEVELOPER}
Date d'export   : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Système         : Toolbox PyQt6 - Section Tools
Type d'export   : {logs_info}
================================================================================

{logs_content}

================================================================================
                            FIN DE L'EXPORT
================================================================================
""".strip()
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(export_content)
                
                log_success(f"Logs exportés vers: {file_path}", "Tools")
                
                QMessageBox.information(
                    self,
                    "Export réussi",
                    f"Les logs ont été exportés avec succès vers:\n{file_path}\n\nType: {logs_info}"
                )
                
        except Exception as e:
            log_error(f"Erreur lors de l'export des logs: {str(e)}", "Tools")
            QMessageBox.critical(
                self,
                "Erreur d'export",
                f"Impossible d'exporter les logs:\n{str(e)}"
            )

    def configure_proxmox(self):
        """Configure la connexion Proxmox"""
        log_info("Ouverture dialogue configuration Proxmox", "Tools")
        
        dialog = ProxmoxConfigDialog(self)
        if dialog.exec():
            config = dialog.get_config()
            log_debug(f"Configuration Proxmox reçue pour {config['ip']}", "Tools")
            
            connected = self.proxmox_handler.connect(config)
            if connected:
                log_success("Connexion Proxmox établie", "Tools")
                QMessageBox.information(self, "Connexion réussie", "Connexion à Proxmox réussie.")
                self.update_connection_status(True)
            else:
                log_error("Échec connexion Proxmox", "Tools")
                QMessageBox.critical(self, "Échec", "Échec de la connexion à Proxmox.")
                self.update_connection_status(False)

    def update_connection_status(self, connected):
        """Met à jour le statut de connexion et active/désactive les boutons"""
        if connected:
            version = self.proxmox_handler.get_version()
            nodes_count = len(self.proxmox_handler.nodes)
            
            self.connection_status_label.setText("✅ Connecté")
            self.connection_status_label.setStyleSheet("""
                QLabel {
                    padding: 6px 10px;
                    border-radius: 4px;
                    background-color: #d4edda;
                    color: #155724;
                    font-weight: bold;
                    font-size: 12px;
                }
            """)
            
            self.proxmox_info_label.setText(f"Proxmox VE {version} • {nodes_count} nœud(s)")
            
            try:
                statuses = self.proxmox_handler.get_node_status()
                if statuses:
                    total_vms = len(self.proxmox_handler.list_vms())
                    running_vms = len([vm for vm in self.proxmox_handler.list_vms() if vm['status'] == 'running'])
                    
                    self.system_info_label.setText(f"VMs: {running_vms}/{total_vms} actives")
                else:
                    self.system_info_label.setText("Stats en cours...")
            except:
                self.system_info_label.setText("Stats indisponibles")
            
            self.qemu_agent_btn.setEnabled(True)
            self.list_vms_btn.setEnabled(True)
            self.scan_linux_btn.setEnabled(True)
            self.nodes_status_btn.setEnabled(True)
            self.storage_info_btn.setEnabled(True)
            
            log_success(f"Interface Tools activée - Proxmox {version} avec {nodes_count} nœud(s)", "Tools")
        else:
            self.connection_status_label.setText("❌ Non connecté")
            self.connection_status_label.setStyleSheet("""
                QLabel {
                    padding: 6px 10px;
                    border-radius: 4px;
                    background-color: #f8d7da;
                    color: #721c24;
                    font-weight: bold;
                    font-size: 12px;
                }
            """)
            
            self.proxmox_info_label.setText("")
            self.system_info_label.setText("")
            
            self.qemu_agent_btn.setEnabled(False)
            self.list_vms_btn.setEnabled(False)
            self.scan_linux_btn.setEnabled(False)
            self.nodes_status_btn.setEnabled(False)
            self.storage_info_btn.setEnabled(False)
            
            log_info("Interface Tools désactivée - Aucune connexion Proxmox", "Tools")

    def open_qemu_agent_manager(self):
        """Ouvre le gestionnaire QEMU Agent"""
        log_info("Ouverture du gestionnaire QEMU Agent", "Tools")
        
        if not self.proxmox_handler.is_connected():
            log_error("Pas de connexion Proxmox pour QEMU Agent", "Tools")
            return
        
        try:
            dialog = QemuAgentManagerDialog(self, self.proxmox_handler)
            dialog.exec()
            log_info("Fermeture du gestionnaire QEMU Agent", "Tools")
        except Exception as e:
            log_error(f"Erreur ouverture gestionnaire QEMU Agent: {str(e)}", "Tools")

    def list_all_vms(self):
        """Liste toutes les VMs du cluster"""
        log_info("Listing de toutes les VMs", "Tools")
        
        try:
            vms = self.proxmox_handler.list_vms()
            log_success(f"{len(vms)} VMs trouvées dans le cluster", "Tools")
            
            for vm in vms:
                status_text = "RUNNING" if vm['status'] == 'running' else "STOPPED"
                log_info(f"VM: {vm['name']} (ID: {vm['vmid']}) on {vm['node']} - Status: {status_text}", "Tools")
                
        except Exception as e:
            log_error(f"Erreur listing VMs: {str(e)}", "Tools")

    def scan_linux_vms(self):
        """Scanne spécifiquement les VMs Linux"""
        log_info("Scan des VMs Linux actives", "Tools")
        
        try:
            linux_vms = self.proxmox_handler.get_linux_vms()
            log_success(f"{len(linux_vms)} VMs Linux actives trouvées", "Tools")
            
            for vm in linux_vms:
                log_info(f"Linux VM: {vm['name']} - IP: {vm.get('ip', 'N/A')} on {vm['node']}", "Tools")
                
        except Exception as e:
            log_error(f"Erreur scan VMs Linux: {str(e)}", "Tools")

    def show_nodes_status(self):
        """Affiche le statut de tous les nœuds"""
        log_info("Récupération du statut des nœuds", "Tools")
        
        try:
            statuses = self.proxmox_handler.get_node_status()
            log_success(f"Statut de {len(statuses)} nœud(s) récupéré", "Tools")
            
            for status in statuses:
                node_name = status['node']
                cpu_percent = status['cpu'] * 100
                mem_total_gb = status['mem_total'] / (1024**3)
                mem_used_gb = status['mem_used'] / (1024**3)
                mem_percent = (status['mem_used'] / status['mem_total'] * 100) if status['mem_total'] > 0 else 0
                uptime_str = str(datetime.timedelta(seconds=status['uptime']))
                
                log_info(f"Node: {node_name}", "Tools")
                log_info(f"  CPU: {cpu_percent:.1f}% | RAM: {mem_used_gb:.1f}G/{mem_total_gb:.1f}G ({mem_percent:.1f}%)", "Tools")
                log_info(f"  Uptime: {uptime_str}", "Tools")
                
        except Exception as e:
            log_error(f"Erreur statut nœuds: {str(e)}", "Tools")

    def show_storage_info(self):
        """Affiche les informations de stockage"""
        log_info("Récupération des informations de stockage", "Tools")
        
        try:
            storages = self.proxmox_handler.get_storage_info()
            log_success(f"{len(storages)} stockage(s) analysé(s)", "Tools")
            
            for storage in storages:
                storage_name = storage['storage']
                storage_type = storage['type']
                node_name = storage['node']
                total = storage.get('total', 0)
                used = storage.get('used', 0)
                available = storage.get('available', 0)
                
                if total > 0:
                    total_gb = total / (1024**3)
                    used_gb = used / (1024**3)
                    available_gb = available / (1024**3)
                    percent_used = (used / total * 100)
                    
                    log_info(f"Storage: {storage_name} ({storage_type}) on {node_name}", "Tools")
                    log_info(f"  Used: {used_gb:.1f}G / {total_gb:.1f}G ({percent_used:.1f}%)", "Tools")
                    log_info(f"  Available: {available_gb:.1f}G", "Tools")
                else:
                    log_info(f"Storage: {storage_name} ({storage_type}) on {node_name}: Info unavailable", "Tools")
                    
        except Exception as e:
            log_error(f"Erreur informations stockage: {str(e)}", "Tools")

    def setup_import_tab(self):
        layout = QVBoxLayout()
        
        header_layout = QHBoxLayout()
        title_label = QLabel("Import IP Plan")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.get_version_label())
        layout.addLayout(header_layout)

        self.import_button = QPushButton("Importer un plan d'adressage (.xlsx)")
        self.import_button.clicked.connect(self.import_ip_plan)
        layout.addWidget(self.import_button)

        self.ip_table = QTableWidget()
        layout.addWidget(self.ip_table)

        self.import_tab.setLayout(layout)
        log_debug("Onglet Import IP Plan configuré", "MainWindow")

    def ask_gitlab_token(self):
        """Demande et configure le token GitLab"""
        log_info("Demande de token GitLab", "MainWindow")
        
        token, ok = QInputDialog.getText(self, "GitLab Token", "Entrez votre token GitLab :", QLineEdit.EchoMode.Password)
        
        if ok and token:
            self.git_manager.set_token(token)
            log_success("Token GitLab configuré", "MainWindow")
            QMessageBox.information(self, "Succès", "Token GitLab mis à jour.")
        else:
            log_info("Configuration token GitLab annulée", "MainWindow")

    def load_scripts(self):
        """Charge les scripts depuis GitLab"""
        log_info("Chargement des scripts depuis GitLab", "MainWindow")
        
        scripts = self.git_manager.fetch_and_download_scripts()
        self.scripts_list.clear()
        
        if scripts:
            log_success(f"{len(scripts)} scripts récupérés depuis GitLab", "MainWindow")
            for script_name in scripts:
                self.scripts_list.addItem(f"{script_name} (Téléchargé)")
                log_debug(f"Script ajouté: {script_name}", "MainWindow")
        else:
            log_info("Aucun script trouvé sur GitLab", "MainWindow")
            self.scripts_list.addItem("Aucun script trouvé.")

    def load_existing_scripts(self):
        """Charge les scripts existants localement"""
        log_debug("Chargement des scripts locaux", "MainWindow")
        
        if os.path.exists("scripts"):
            self.scripts_list.clear()
            local_scripts = []
            
            for file in os.listdir("scripts"):
                if file.endswith(".ps1"):
                    self.scripts_list.addItem(f"{file} (Local)")
                    local_scripts.append(file)
                    log_debug(f"Script local trouvé: {file}", "MainWindow")
            
            if local_scripts:
                log_success(f"{len(local_scripts)} scripts locaux chargés", "MainWindow")
            else:
                log_info("Aucun script local trouvé", "MainWindow")
        else:
            log_debug("Dossier scripts inexistant", "MainWindow")

    def run_selected_script(self):
        """Exécute le script sélectionné"""
        selected_item = self.scripts_list.currentItem()
        
        if selected_item:
            script_name = selected_item.text().split(' ')[0]
            script_path = os.path.join("scripts", script_name)
            
            log_info(f"Exécution du script: {script_name}", "MainWindow")
            
            if os.path.exists(script_path):
                self.script_runner.run_script(script_path)
                log_success(f"Script lancé: {script_name}", "MainWindow")
            else:
                log_error(f"Script non trouvé: {script_name}", "MainWindow")
                QMessageBox.warning(self, "Erreur", f"Le fichier {script_name} n'existe pas.")
        else:
            log_warning("Aucun script sélectionné", "MainWindow")

    def import_ip_plan(self):
        """Importe un plan d'adressage IP depuis un fichier Excel"""
        log_info("Début import plan d'adressage IP", "MainWindow")
        
        file_path, _ = QFileDialog.getOpenFileName(self, "Sélectionner un fichier Excel", "", "Fichiers Excel (*.xlsx)")
        
        if file_path:
            log_debug(f"Fichier sélectionné: {file_path}", "MainWindow")
            
            try:
                df = pd.read_excel(file_path, sheet_name="Nommage HL-RL", header=None)
                log_debug("Fichier Excel lu avec succès", "MainWindow")

                col_h = df.iloc[:, 7].astype(str).tolist()
                col_k = df.iloc[:, 10].astype(str).tolist()
                col_p = df.iloc[:, 15].astype(str).tolist()
                col_u = df.iloc[:, 20].astype(str).tolist()

                clean_data = []
                for h, k, p, u in zip(col_h, col_k, col_p, col_u):
                    h_str = h.strip().lower()
                    k_str = k.strip().lower()
                    p_str = p.strip().lower()
                    u_str = u.strip().lower()

                    if h_str == "hostname" or k_str == "prod ip" or p_str == "mgt ip" or u_str == "idrac ip":
                        continue

                    h = '' if h_str == "nan" else h.strip()
                    k = '' if k_str == "nan" else k.strip()
                    p = '' if p_str == "nan" else p.strip()
                    u = '' if u_str == "nan" else u.strip()

                    if not any([h, k, p, u]):
                        continue

                    clean_data.append((h, k, p, u))

                log_success(f"Import terminé - {len(clean_data)} entrées traitées", "MainWindow")

                self.ip_table.clear()
                self.ip_table.setColumnCount(4)
                self.ip_table.setRowCount(len(clean_data))
                self.ip_table.setHorizontalHeaderLabels(["Hostname", "Prod IP", "Mgt IP", "Idrac IP"])

                for row_idx, (hostname, prod_ip, mgt_ip, idrac_ip) in enumerate(clean_data):
                    self.ip_table.setItem(row_idx, 0, QTableWidgetItem(hostname))
                    self.ip_table.setItem(row_idx, 1, QTableWidgetItem(prod_ip))
                    self.ip_table.setItem(row_idx, 2, QTableWidgetItem(mgt_ip))
                    self.ip_table.setItem(row_idx, 3, QTableWidgetItem(idrac_ip))

                log_debug("Tableau IP plan mis à jour", "MainWindow")

            except Exception as e:
                log_error(f"Erreur import plan IP: {str(e)}", "MainWindow")
                QMessageBox.critical(self, "Erreur", str(e))
        else:
            log_info("Import plan IP annulé", "MainWindow")

    # === MÉTHODES DE COMPATIBILITÉ ===
    def update_proxmox_info(self):
        """Méthode de compatibilité - redirige vers update_connection_status"""
        if self.proxmox_handler.is_connected():
            self.update_connection_status(True)
        else:
            self.update_connection_status(False)

    def populate_proxmox_vm_table(self):
        """Méthode de compatibilité - pas utilisée dans le nouveau design"""
        log_debug("populate_proxmox_vm_table appelée (compatibilité)", "MainWindow")
        pass

    def on_vm_ip_edited(self, item):
        """Méthode de compatibilité - pas utilisée dans le nouveau design"""
        log_debug("on_vm_ip_edited appelée (compatibilité)", "MainWindow")
        pass

    def get_vm_manual_ips(self):
        """Méthode de compatibilité - retourne dictionnaire vide"""
        log_debug("get_vm_manual_ips appelée (compatibilité)", "MainWindow")
        return {}

    def apply_discovered_ips(self, ip_assignments):
        """Méthode de compatibilité - affiche dans les logs"""
        if ip_assignments:
            log_info(f"IPs découvertes reçues: {len(ip_assignments)} assignations", "Tools")
            for vmid, ip in ip_assignments.items():
                log_info(f"  VM {vmid}: {ip}", "Tools")

    def update_proxmox_details(self):
        """Méthode de compatibilité - pas utilisée dans le nouveau design"""
        log_debug("update_proxmox_details appelée (compatibilité)", "MainWindow")
        pass

    def run_export(self):
        """Méthode de compatibilité - redirige vers Tools"""
        log_info("Fonction d'export appelée - Utilisez l'onglet Tools", "MainWindow")
        if hasattr(self, 'tools_logs'):
            cursor = self.tools_logs.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            format_info = QTextCharFormat()
            format_info.setForeground(QColor("#74c0fc"))
            cursor.setCharFormat(format_info)
            cursor.insertText("INFO: La fonctionnalité d'export a été déplacée vers l'onglet Tools\n")

    def executer_sur_vms_selectionnees(self):
        """Méthode de compatibilité - pas utilisée"""
        log_debug("executer_sur_vms_selectionnees appelée (compatibilité)", "MainWindow")
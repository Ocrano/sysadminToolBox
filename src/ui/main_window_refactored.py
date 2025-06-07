# src/ui/main_window_refactored.py
"""
MainWindow refactorisée - Layout propre avec Connection Manager - VERSION CORRIGÉE COMPLÈTE
"""

import os
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QMessageBox, QFileDialog, QInputDialog, QLineEdit,
    QLabel, QPushButton, QFrame
)

# Import des composants refactorisés
from .controllers.main_controller import MainController
from .components.common_widgets import (
    VersionLabel, ActionButton, LogDisplay,
    LogControlPanel, SectionHeader, ConfigurationGroup, ActionGrid,
    WidgetFactory, MetricsDisplay
)
from .components.connection_manager import ConnectionManager
from .dialogs.proxmox_config_dialog import ProxmoxConfigDialog
from .dialogs.qemu_agent_dialog import QemuAgentManagerDialog
from ..utils.ip_plan_importer import IPPlanImporter

# Import du système de logging
from ..core.logger import toolbox_logger, log_info, log_debug, log_error, log_success, log_warning


class MainWindowRefactored(QMainWindow):
    """Fenêtre principale refactorisée - Layout propre et épuré"""
    
    VERSION = "Alpha 0.0.7"
    DEVELOPER = "ocrano"
    
    def __init__(self, git_manager, script_runner, proxmox_service):
        super().__init__()
        
        # Initialiser le contrôleur avec le service unifié
        self.controller = MainController(git_manager, script_runner, proxmox_service)
        self.importer = IPPlanImporter()
        
        # Connection Manager
        self.connection_manager = None
        
        # Connecter les signaux du contrôleur
        self.controller.proxmox_connection_changed.connect(self.on_proxmox_connection_changed)
        self.controller.scripts_loaded.connect(self.on_scripts_loaded)
        self.controller.service_connection_changed.connect(self.on_service_connection_changed)
        
        log_info("MainWindow refactorisée avec Connection Manager initialisée", "MainWindow")
        
        self.init_ui()
        self.setup_logging()

    def init_ui(self):
        """Interface utilisateur finale"""
        self.setWindowTitle("Toolbox PyQt6 - Connection Manager")
        self.setGeometry(200, 200, 1400, 900)
        self.setMinimumSize(1200, 700)
        
        # Onglets principaux SANS marges
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                margin: 0px;
                padding: 0px;
            }
            QTabWidget::tab-bar {
                alignment: left;
            }
            QTabWidget > QWidget {
                padding: 0px;
                margin: 0px;
            }
        """)
        self.setCentralWidget(self.tabs)
        
        # Créer les onglets dans le nouvel ordre
        self.create_dashboard_tab()
        self.create_scripts_tab()
        self.create_settings_tab()
        self.create_tools_tab()
        self.create_import_tab()
        
        # Ajouter les onglets externes (Network, Scanner)
        self.add_external_tabs()
        
        log_success("Interface refactorisée avec Connection Manager initialisée", "MainWindow")

    def create_dashboard_tab(self):
        """NOUVEAU - Onglet Dashboard avec Connection Manager"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # === CONNECTION MANAGER COMPACT ===
        self.connection_manager = ConnectionManager()
        self.connection_manager.setMaximumHeight(200)
        
        # Connecter les signaux du Connection Manager
        self.connection_manager.connection_status_changed.connect(self.handle_connection_manager_request)
        self.connection_manager.configuration_requested.connect(self.handle_configuration_request)
        
        layout.addWidget(self.connection_manager)
        
        # === SÉPARATEUR ===
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("color: #555; margin: 0px;")
        layout.addWidget(separator)
        
        # === VUE D'ENSEMBLE DES SERVICES ===
        overview_widget = self.create_services_overview()
        layout.addWidget(overview_widget, 1)
        
        tab.setLayout(layout)
        self.tabs.addTab(tab, "🏠 Dashboard")

    def create_services_overview(self):
        """Vue d'ensemble des services - CORRECTION COMPLÈTE"""
        widget = QWidget()
        layout = QVBoxLayout()  # CORRECTION: Variable cohérente
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # === TITRE ULTRA-COMPACT ===
        title_container = QWidget()
        title_container.setFixedHeight(25)
        title_container.setStyleSheet("background-color: transparent; margin: 0px; padding: 0px;")
        
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(15, 5, 15, 5)
        title_layout.setSpacing(0)
        
        title_label = QLabel("Vue d'ensemble des services")
        title_label.setStyleSheet("""
            font-size: 13px; 
            font-weight: bold; 
            color: #ffffff;
            padding: 0px;
            margin: 0px;
            background-color: transparent;
        """)
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        version_label = VersionLabel(self.VERSION, self.DEVELOPER)
        title_layout.addWidget(version_label)
        
        title_container.setLayout(title_layout)
        layout.addWidget(title_container)  # CORRECTION: Utilise 'layout'
        
        # === CONTENU PRINCIPAL ===
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(15, 10, 15, 15)
        content_layout.setSpacing(8)
        
        # Conteneur principal avec splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # === MÉTRIQUES GLOBALES ===
        metrics_widget = QWidget()
        metrics_layout = QVBoxLayout()
        metrics_layout.setContentsMargins(10, 5, 10, 10)
        metrics_layout.setSpacing(6)
        
        metrics_title = QLabel("Métriques en temps réel")
        metrics_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff; margin-bottom: 6px;")
        metrics_layout.addWidget(metrics_title)
        
        self.global_metrics = MetricsDisplay()
        self.global_metrics.add_metric("Services connectés", "0", "🔗", "#17a2b8")
        self.global_metrics.add_metric("VMs totales", "0", "🖥️", "#6f42c1")
        self.global_metrics.add_metric("VMs actives", "0", "🟢", "#28a745")
        self.global_metrics.add_metric("Nœuds", "0", "🏗️", "#fd7e14")
        
        metrics_layout.addWidget(self.global_metrics)
        metrics_layout.addStretch()
        
        metrics_widget.setLayout(metrics_layout)
        main_splitter.addWidget(metrics_widget)
        
        # === LOGS SYSTÈME ===
        logs_widget = QWidget()
        logs_layout = QVBoxLayout()
        logs_layout.setContentsMargins(5, 5, 10, 10)
        logs_layout.setSpacing(5)
        
        # En-tête avec contrôles
        logs_header_layout = QHBoxLayout()
        logs_header_layout.setContentsMargins(0, 0, 0, 0)
        logs_header_layout.setSpacing(0)
        
        logs_title_label = QLabel("📋 Activité système")
        logs_title_label.setStyleSheet("""
            font-size: 13px; 
            font-weight: bold; 
            color: #ffffff;
            padding: 0px;
            margin: 0px;
        """)
        logs_header_layout.addWidget(logs_title_label)
        logs_header_layout.addStretch()
        
        # Mini panneau de contrôle
        self.dashboard_log_controls = LogControlPanel()
        self.dashboard_log_controls.filter_changed.connect(self.on_dashboard_log_filter_changed)
        self.dashboard_log_controls.export_requested.connect(self.export_logs)
        self.dashboard_log_controls.clear_requested.connect(self.clear_dashboard_logs)
        logs_header_layout.addWidget(self.dashboard_log_controls)
        
        logs_layout.addLayout(logs_header_layout)
        
        # Zone d'affichage des logs du dashboard
        self.dashboard_logs = LogDisplay("DASHBOARD")
        logs_layout.addWidget(self.dashboard_logs)
        
        logs_widget.setLayout(logs_layout)
        main_splitter.addWidget(logs_widget)
        
        # Répartition 30/70
        main_splitter.setStretchFactor(0, 30)
        main_splitter.setStretchFactor(1, 70)
        
        content_layout.addWidget(main_splitter)
        content_widget.setLayout(content_layout)
        
        layout.addWidget(content_widget)  # CORRECTION: Utilise 'layout'
        
        widget.setLayout(layout)  # CORRECTION: Utilise 'layout'
        return widget

    def create_scripts_tab(self):
        """Onglet Scripts PowerShell"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 3, 8, 8)
        layout.setSpacing(3)
        
        header = SectionHeader("Scripts PowerShell", "📜", VersionLabel(self.VERSION, self.DEVELOPER))
        layout.addWidget(header)
        
        from PyQt6.QtWidgets import QListWidget
        self.scripts_list = QListWidget()
        layout.addWidget(self.scripts_list)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(3)
        
        fetch_btn = ActionButton("Récupérer Scripts", 'info', "📥")
        fetch_btn.clicked.connect(self.load_scripts_from_gitlab)
        buttons_layout.addWidget(fetch_btn)
        
        run_btn = ActionButton("Exécuter Script", 'success', "▶️")
        run_btn.clicked.connect(self.run_selected_script)
        buttons_layout.addWidget(run_btn)
        
        layout.addLayout(buttons_layout)
        tab.setLayout(layout)
        
        self.tabs.addTab(tab, "📜 Scripts")
        self.load_local_scripts()

    def create_settings_tab(self):
        """Onglet Paramètres"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 3, 8, 8)
        layout.setSpacing(3)
        
        header = SectionHeader("Paramètres", "⚙️", VersionLabel(self.VERSION, self.DEVELOPER))
        layout.addWidget(header)
        
        gitlab_group = ConfigurationGroup("Configuration GitLab", "🦊")
        gitlab_layout = QHBoxLayout()
        gitlab_layout.setContentsMargins(3, 1, 3, 1)
        
        token_btn = WidgetFactory.create_config_button("Configurer Token GitLab", 'warning', "🔑")
        token_btn.clicked.connect(self.configure_gitlab_token)
        gitlab_layout.addWidget(token_btn)
        
        gitlab_layout.addStretch()
        gitlab_group.setLayout(gitlab_layout)
        layout.addWidget(gitlab_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        
        self.tabs.addTab(tab, "⚙️ Paramètres")

    def create_tools_tab(self):
        """Onglet Tools - VERSION SIMPLIFIÉE SANS ESPACES"""
        tab = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # === TITRE ULTRA-COMPACT ===
        title_container = QWidget()
        title_container.setFixedHeight(25)
        title_container.setStyleSheet("background-color: transparent; margin: 0px; padding: 0px;")
        
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(15, 5, 15, 5)
        title_layout.setSpacing(0)
        
        title_layout.addStretch()
        
        version_label = VersionLabel(self.VERSION, self.DEVELOPER)
        title_layout.addWidget(version_label)
        
        title_container.setLayout(title_layout)
        main_layout.addWidget(title_container)
        
        # === CONTENU PRINCIPAL ===
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(8)
        
        # === SPLITTER ACTIONS / LOGS ===
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setContentsMargins(0, 0, 0, 0)
        
        # Actions à gauche
        actions_widget = self.create_actions_section()
        main_splitter.addWidget(actions_widget)
        
        # Logs à droite
        logs_widget = self.create_logs_section()
        main_splitter.addWidget(logs_widget)
        
        # Répartition 35/65
        main_splitter.setStretchFactor(0, 35)
        main_splitter.setStretchFactor(1, 65)
        
        content_layout.addWidget(main_splitter)
        content_widget.setLayout(content_layout)
        
        main_layout.addWidget(content_widget)
        tab.setLayout(main_layout)
        
        self.tabs.addTab(tab, "🛠️ Proxmox")

    def create_actions_section(self):
        """Section des actions Proxmox - COMPACTE"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 0, 5, 5)
        layout.setSpacing(3)
    
       # === GRILLE D'ACTIONS AVEC BOUTONS ===
        self.actions_grid = ActionGrid()
        
        # Groupe VM Management
        vm_group = self.actions_grid.add_group("Gestion des VMs", "🖥️")
        
        self.qemu_btn = ActionButton("Gestionnaire QEMU Agent", 'success', "🔧")
        self.qemu_btn.clicked.connect(self.open_qemu_agent_manager)
        self.qemu_btn.setEnabled(False)
        self.actions_grid.add_action_to_group("Gestion des VMs", self.qemu_btn)
        
        self.list_vms_btn = ActionButton("Lister toutes les VMs", 'primary')
        self.list_vms_btn.clicked.connect(self.list_all_vms)
        self.list_vms_btn.setEnabled(False)
        self.actions_grid.add_action_to_group("Gestion des VMs", self.list_vms_btn)
        
        self.scan_linux_btn = ActionButton("Scanner VMs Linux", 'primary')
        self.scan_linux_btn.clicked.connect(self.scan_linux_vms)
        self.scan_linux_btn.setEnabled(False)
        self.actions_grid.add_action_to_group("Gestion des VMs", self.scan_linux_btn)
        
        # Groupe Infrastructure
        infra_group = self.actions_grid.add_group("Infrastructure", "🏗️")
        
        self.nodes_btn = ActionButton("Statut des nœuds", 'primary')
        self.nodes_btn.clicked.connect(self.show_nodes_status)
        self.nodes_btn.setEnabled(False)
        self.actions_grid.add_action_to_group("Infrastructure", self.nodes_btn)
        
        self.storage_btn = ActionButton("Informations stockage", 'primary')
        self.storage_btn.clicked.connect(self.show_storage_info)
        self.storage_btn.setEnabled(False)
        self.actions_grid.add_action_to_group("Infrastructure", self.storage_btn)
        
        layout.addWidget(self.actions_grid)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget

    def create_logs_section(self):
        """Section des logs avec contrôles - COMPACTE"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 0, 5, 5)
        layout.setSpacing(3)
        
        # En-tête avec contrôles
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)
        
        title_label = QLabel("📋 Logs Proxmox")
        title_label.setStyleSheet("""
            font-size: 13px; 
            font-weight: bold; 
            color: #ffffff;
            padding: 5px 0px;
            margin: 0px;
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Panneau de contrôle des logs
        self.log_controls = LogControlPanel()
        self.log_controls.filter_changed.connect(self.on_log_filter_changed)
        self.log_controls.export_requested.connect(self.export_logs)
        self.log_controls.clear_requested.connect(self.clear_logs)
        header_layout.addWidget(self.log_controls)
        
        layout.addLayout(header_layout)
        
        # Zone d'affichage des logs
        self.tools_logs = LogDisplay("PROXMOX TOOLS")
        layout.addWidget(self.tools_logs)
        
        widget.setLayout(layout)
        return widget

    def create_import_tab(self):
        """Onglet Import IP Plan"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 3, 8, 8)
        layout.setSpacing(3)
        
        header = SectionHeader("Import IP Plan", "📊", VersionLabel(self.VERSION, self.DEVELOPER))
        layout.addWidget(header)
        
        import_btn = ActionButton("Importer un plan d'adressage (.xlsx)", 'primary', "📁")
        import_btn.clicked.connect(self.import_ip_plan)
        layout.addWidget(import_btn)
        
        from PyQt6.QtWidgets import QTableWidget
        self.ip_table = QTableWidget()
        layout.addWidget(self.ip_table)
        
        tab.setLayout(layout)
        self.tabs.addTab(tab, "📊 Import IP")

    def add_external_tabs(self):
        """Ajoute les onglets externes (Network, Scanner)"""
        # Onglet Scanner
        try:
            from .tabs.network_scanner_tab import NetworkScannerTab
            scanner_tab = NetworkScannerTab(self, self.controller.proxmox_service)
            self.tabs.addTab(scanner_tab, "🔍 Scanner")
            log_debug("Onglet Scanner ajouté", "MainWindow")
        except ImportError as e:
            log_warning(f"Onglet Scanner non disponible: {e}", "MainWindow")
        
        # Onglet Network
        try:
            from .tabs.network_tab_refactored import NetworkTabRefactored as NetworkTab
            network_tab = NetworkTab(self)
            self.tabs.addTab(network_tab, "🌐 Network")
            log_debug("Onglet Network ajouté", "MainWindow")
        except ImportError as e:
            log_warning(f"Onglet Network non disponible: {e}", "MainWindow")
        
        # Alternative si network_tab_refactored n'existe pas
        except:
            try:
                from .tabs.network_tab import NetworkTab
                network_tab = NetworkTab(self)
                self.tabs.addTab(network_tab, "🌐 Network")
                log_debug("Onglet Network (version originale) ajouté", "MainWindow")
            except ImportError as e:
                log_warning(f"Onglet Network non disponible: {e}", "MainWindow")

    def setup_logging(self):
        """Configure la redirection des logs"""
        qt_handler = toolbox_logger.get_qt_handler()
        qt_handler.log_message.connect(self.on_log_message)
        log_info("Système de logs refactorisé activé", "MainWindow")

    # === GESTIONNAIRES DU CONNECTION MANAGER ===
    
    def handle_connection_manager_request(self, service_name, connect, info):
        """Gère les demandes du Connection Manager"""
        log_info(f"Connection Manager: {service_name} - {'Connexion' if connect else 'Déconnexion'}", "MainWindow")
        
        if connect:
            if info.get('refresh'):
                # Demande d'actualisation
                self.refresh_service(service_name)
            else:
                # Nouvelle connexion
                self.connect_service(service_name)
        else:
            # Déconnexion
            self.disconnect_service(service_name)
    
    def handle_configuration_request(self, service_name):
        """Gère les demandes de configuration"""
        log_info(f"Configuration demandée pour: {service_name}", "MainWindow")
        
        if service_name == "Proxmox VE":
            self.configure_proxmox()
        elif service_name == "VMware vSphere":
            QMessageBox.information(self, "vSphere", "Configuration vSphere pas encore disponible.")
        else:
            QMessageBox.warning(self, "Service inconnu", f"Configuration de {service_name} non supportée.")
    
    def connect_service(self, service_name):
        """Connecte un service via le contrôleur"""
        if service_name == "Proxmox VE":
            # Vérifier si déjà configuré
            success, message = self.controller.handle_service_connection_request(service_name, True)
            if not success and "Configuration requise" in message:
                self.configure_proxmox()
        else:
            # Autres services (à implémenter)
            self.connection_manager.set_service_disconnected(service_name, "Service non implémenté")
    
    def disconnect_service(self, service_name):
        """Déconnecte un service"""
        success, message = self.controller.handle_service_connection_request(service_name, False)
        if success:
            self.dashboard_logs.add_log(f"Service {service_name} déconnecté", "INFO")
        else:
            self.dashboard_logs.add_log(f"Erreur déconnexion {service_name}: {message}", "ERROR")
    
    def refresh_service(self, service_name):
        """Actualise un service connecté"""
        if service_name == "Proxmox VE":
            if self.controller.refresh_proxmox_info():
                self.dashboard_logs.add_log(f"Informations {service_name} actualisées", "SUCCESS")
            else:
                self.dashboard_logs.add_log(f"Impossible d'actualiser {service_name}", "WARNING")
        else:
            self.dashboard_logs.add_log(f"Actualisation {service_name} non implémentée", "WARNING")

    # === SLOTS DU CONTRÔLEUR ===
    
    def on_proxmox_connection_changed(self, connected):
        """Réagit aux changements de connexion Proxmox (compatibilité)"""
        # Ce signal est maintenant géré par on_service_connection_changed
        pass
    
    def on_service_connection_changed(self, service_name, connected, info):
        """Réagit aux changements de connexion des services"""
        log_info(f"Service {service_name}: {'Connecté' if connected else 'Déconnecté'}", "MainWindow")
        
        if connected:
            # Mettre à jour le Connection Manager
            self.connection_manager.set_service_connected(service_name, info)
            
            # Mettre à jour les métriques globales
            self.update_global_metrics()
            
            # Log dans le dashboard
            self.dashboard_logs.add_log(f"✅ {service_name} connecté avec succès", "SUCCESS")
            
            # Activer les actions spécifiques
            if service_name == "Proxmox VE":
                self.actions_grid.enable_group("Gestion des VMs", True)
                self.actions_grid.enable_group("Infrastructure", True)
        else:
            # Marquer comme déconnecté
            self.connection_manager.set_service_disconnected(service_name)
            
            # Mettre à jour les métriques
            self.update_global_metrics()
            
            # Log dans le dashboard
            if info.get('error'):
                self.dashboard_logs.add_log(f"❌ {service_name} déconnecté: {info['error']}", "ERROR")
            else:
                self.dashboard_logs.add_log(f"🔌 {service_name} déconnecté", "INFO")
            
            # Désactiver les actions spécifiques
            if service_name == "Proxmox VE":
                self.actions_grid.enable_group("Gestion des VMs", False)
                self.actions_grid.enable_group("Infrastructure", False)

    def on_scripts_loaded(self, script_list):
        """Réagit au chargement des scripts"""
        self.scripts_list.clear()
        for script in script_list:
            self.scripts_list.addItem(script)
        
        self.dashboard_logs.add_log(f"📜 {len(script_list)} script(s) chargé(s)", "INFO")

    def on_log_message(self, message):
        """Réagit aux nouveaux logs"""
        level = "INFO"
        if "ERROR" in message:
            level = "ERROR"
        elif "SUCCESS" in message:
            level = "SUCCESS"
        elif "WARNING" in message:
            level = "WARNING"
        elif "DEBUG" in message:
            level = "DEBUG"
        
        # Ajouter aux logs des outils ET du dashboard
        if hasattr(self, 'tools_logs'):
            self.tools_logs.add_log(message, level)
        if hasattr(self, 'dashboard_logs'):
            self.dashboard_logs.add_log(message, level)

    def on_log_filter_changed(self, level, enabled):
        """Réagit aux changements de filtres des logs outils"""
        try:
            if hasattr(self, 'tools_logs'):
                self.tools_logs.update_filter(level, enabled)
        except Exception as e:
            print(f"Erreur filtre logs outils {level}: {e}")
    
    def on_dashboard_log_filter_changed(self, level, enabled):
        """Réagit aux changements de filtres des logs dashboard"""
        try:
            if hasattr(self, 'dashboard_logs'):
                self.dashboard_logs.update_filter(level, enabled)
        except Exception as e:
            print(f"Erreur filtre logs dashboard {level}: {e}")

    # CORRECTION : Fin de la méthode update_global_metrics et reste du fichier

    def update_global_metrics(self):
        """Met à jour les métriques globales du dashboard"""
        try:
            connected_services = self.connection_manager.get_connected_services()
            
            # Métriques de base
            self.global_metrics.update_metric("Services connectés", len(connected_services), "🔗")
            
            # Métriques Proxmox si connecté
            if "Proxmox VE" in connected_services:
                proxmox_info = self.controller.get_service_info("Proxmox VE")
                if proxmox_info:
                    self.global_metrics.update_metric("VMs totales", proxmox_info.get('total_vms', 0), "🖥️")
                    self.global_metrics.update_metric("VMs actives", proxmox_info.get('running_vms', 0), "🟢")
                    self.global_metrics.update_metric("Nœuds", proxmox_info.get('nodes_count', 0), "🏗️")
            else:
                # Réinitialiser les métriques Proxmox
                self.global_metrics.update_metric("VMs totales", 0, "🖥️")
                self.global_metrics.update_metric("VMs actives", 0, "🟢")
                self.global_metrics.update_metric("Nœuds", 0, "🏗️")
        except Exception as e:
            log_error(f"Erreur mise à jour métriques: {e}", "MainWindow")

    # === MÉTHODES D'ACTION ===
    
    def configure_proxmox(self):
        """Configure Proxmox via le dialog"""
        # CORRECTION : Passer le service unifié au dialogue
        dialog = ProxmoxConfigDialog(self, self.controller.proxmox_service)
        if dialog.exec():
            config = dialog.get_config()
            
            # Marquer le service en connexion
            self.connection_manager.set_service_connecting("Proxmox VE")
            
            success, message = self.controller.configure_proxmox(config)
            if success:
                QMessageBox.information(self, "Connexion réussie", message)
            else:
                QMessageBox.critical(self, "Échec", message)
                self.connection_manager.set_service_disconnected("Proxmox VE", message)

    def configure_gitlab_token(self):
        """Configure le token GitLab"""
        token, ok = QInputDialog.getText(self, "GitLab Token", "Entrez votre token GitLab :", QLineEdit.EchoMode.Password)
        if ok:
            success, message = self.controller.configure_gitlab_token(token)
            if success:
                QMessageBox.information(self, "Succès", message)
                self.dashboard_logs.add_log("🔑 Token GitLab configuré", "SUCCESS")
            else:
                QMessageBox.critical(self, "Erreur", message)
                self.dashboard_logs.add_log(f"❌ Erreur GitLab: {message}", "ERROR")

    def load_scripts_from_gitlab(self):
        """Charge les scripts depuis GitLab"""
        scripts = self.controller.load_scripts_from_gitlab()
        if not scripts:
            QMessageBox.information(self, "Scripts", "Aucun script trouvé sur GitLab.")

    def load_local_scripts(self):
        """Charge les scripts locaux"""
        self.controller.load_local_scripts()

    def run_selected_script(self):
        """Exécute le script sélectionné"""
        selected_item = self.scripts_list.currentItem()
        if selected_item:
            script_name = selected_item.text()
            success, message = self.controller.run_script(script_name)
            if success:
                QMessageBox.information(self, "Script exécuté", f"Script {script_name} terminé avec succès.")
                self.dashboard_logs.add_log(f"▶️ Script {script_name} exécuté", "SUCCESS")
            else:
                QMessageBox.warning(self, "Erreur", message)
                self.dashboard_logs.add_log(f"❌ Erreur script {script_name}", "ERROR")
        else:
            QMessageBox.warning(self, "Sélection", "Aucun script sélectionné.")

    def open_qemu_agent_manager(self):
        """Ouvre le gestionnaire QEMU Agent"""
        dialog = QemuAgentManagerDialog(self, self.controller.proxmox_service)
        dialog.exec()

    def list_all_vms(self):
        """Liste toutes les VMs"""
        try:
            vms = self.controller.proxmox_service.list_vms()
            self.tools_logs.add_log(f"{len(vms)} VMs trouvées dans le cluster", "SUCCESS")
            for vm in vms:
                status = "RUNNING" if vm['status'] == 'running' else "STOPPED"
                self.tools_logs.add_log(f"VM: {vm['name']} (ID: {vm['vmid']}) on {vm['node']} - {status}", "INFO")
        except Exception as e:
            self.tools_logs.add_log(f"Erreur listage VMs: {e}", "ERROR")

    def scan_linux_vms(self):
        """Scanne les VMs Linux"""
        try:
            linux_vms = self.controller.proxmox_service.get_linux_vms()
            self.tools_logs.add_log(f"{len(linux_vms)} VMs Linux actives trouvées", "SUCCESS")
            for vm in linux_vms:
                self.tools_logs.add_log(f"Linux VM: {vm['name']} - IP: {vm.get('ip', 'N/A')} on {vm['node']}", "INFO")
        except Exception as e:
            self.tools_logs.add_log(f"Erreur scan VMs Linux: {e}", "ERROR")

    def show_nodes_status(self):
        """Affiche le statut des nœuds"""
        try:
            statuses = self.controller.proxmox_service.get_node_status()
            self.tools_logs.add_log(f"Statut de {len(statuses)} nœud(s) récupéré", "SUCCESS")
            for status in statuses:
                import datetime
                cpu_percent = status['cpu'] * 100
                mem_total_gb = status['mem_total'] / (1024**3)
                mem_used_gb = status['mem_used'] / (1024**3)
                mem_percent = (status['mem_used'] / status['mem_total'] * 100) if status['mem_total'] > 0 else 0
                uptime_str = str(datetime.timedelta(seconds=status['uptime']))
                self.tools_logs.add_log(f"Node: {status['node']}", "INFO")
                self.tools_logs.add_log(f"  CPU: {cpu_percent:.1f}% | RAM: {mem_used_gb:.1f}G/{mem_total_gb:.1f}G ({mem_percent:.1f}%)", "INFO")
                self.tools_logs.add_log(f"  Uptime: {uptime_str}", "INFO")
        except Exception as e:
            self.tools_logs.add_log(f"Erreur statut nœuds: {e}", "ERROR")

    def show_storage_info(self):
        """Affiche les informations de stockage"""
        try:
            storages = self.controller.proxmox_service.get_storage_info()
            self.tools_logs.add_log(f"{len(storages)} stockage(s) analysé(s)", "SUCCESS")
            for storage in storages:
                if storage.get('total', 0) > 0:
                    total_gb = storage['total'] / (1024**3)
                    used_gb = storage['used'] / (1024**3)
                    available_gb = storage['available'] / (1024**3)
                    percent_used = (storage['used'] / storage['total'] * 100)
                    self.tools_logs.add_log(f"Storage: {storage['storage']} ({storage['type']}) on {storage['node']}", "INFO")
                    self.tools_logs.add_log(f"  Used: {used_gb:.1f}G / {total_gb:.1f}G ({percent_used:.1f}%)", "INFO")
                    self.tools_logs.add_log(f"  Available: {available_gb:.1f}G", "INFO")
                else:
                    self.tools_logs.add_log(f"Storage: {storage['storage']} ({storage['type']}) on {storage['node']}: Info unavailable", "INFO")
        except Exception as e:
            self.tools_logs.add_log(f"Erreur infos stockage: {e}", "ERROR")

    def import_ip_plan(self):
        """Importe un plan d'adressage IP"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Sélectionner un fichier Excel", "", "Fichiers Excel (*.xlsx)")
        if file_path:
            success, data, message = self.controller.import_ip_plan(file_path)
            if success:
                self.ip_table.clear()
                self.ip_table.setColumnCount(4)
                self.ip_table.setRowCount(len(data))
                self.ip_table.setHorizontalHeaderLabels(["Hostname", "Prod IP", "Mgt IP", "Idrac IP"])
                for row_idx, (hostname, prod_ip, mgt_ip, idrac_ip) in enumerate(data):
                    from PyQt6.QtWidgets import QTableWidgetItem
                    self.ip_table.setItem(row_idx, 0, QTableWidgetItem(hostname))
                    self.ip_table.setItem(row_idx, 1, QTableWidgetItem(prod_ip))
                    self.ip_table.setItem(row_idx, 2, QTableWidgetItem(mgt_ip))
                    self.ip_table.setItem(row_idx, 3, QTableWidgetItem(idrac_ip))
                QMessageBox.information(self, "Import réussi", message)
                self.dashboard_logs.add_log(f"📊 {message}", "SUCCESS")
            else:
                QMessageBox.critical(self, "Erreur", message)
                self.dashboard_logs.add_log(f"❌ Erreur import: {message}", "ERROR")

    def export_logs(self):
        """Exporte les logs"""
        try:
            # Déterminer quelle zone de logs exporter
            current_tab = self.tabs.currentIndex()
            tab_name = self.tabs.tabText(current_tab)
            
            if "Dashboard" in tab_name:
                logs_display = self.dashboard_logs
                logs_type = "dashboard"
            else:
                logs_display = self.tools_logs if hasattr(self, 'tools_logs') else self.dashboard_logs
                logs_type = "tools"
            
            reply = QMessageBox.question(self, "Type d'export", 
                f"Quel type de logs voulez-vous exporter de {logs_type} ?\n\n• OUI = Logs actuellement affichés (filtrés)\n• NON = Tous les logs (complets)", 
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
            
            if reply == QMessageBox.StandardButton.Cancel:
                return
            
            export_type = "filtered" if reply == QMessageBox.StandardButton.Yes else "complete"
            
            if reply == QMessageBox.StandardButton.Yes:
                logs_content = logs_display.get_filtered_logs_text() if hasattr(logs_display, 'get_filtered_logs_text') else logs_display.toPlainText()
            else:
                logs_content = logs_display.get_all_logs_text() if hasattr(logs_display, 'get_all_logs_text') else logs_display.toPlainText()
            
            success, export_content, filename = self.controller.export_logs(logs_content, f"{logs_type}_{export_type}")
            
            if success:
                file_path, _ = QFileDialog.getSaveFileName(self, "Exporter les logs", filename, "Fichiers log (*.log);;Fichiers texte (*.txt);;Tous les fichiers (*.*)")
                if file_path:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(export_content)
                    QMessageBox.information(self, "Export réussi", f"Logs exportés vers:\n{file_path}")
                    self.dashboard_logs.add_log(f"📁 Logs exportés: {os.path.basename(file_path)}", "SUCCESS")
            else:
                QMessageBox.critical(self, "Erreur", "Impossible d'exporter les logs")
        except Exception as e:
            QMessageBox.critical(self, "Erreur d'export", f"Erreur lors de l'export:\n{str(e)}")
            self.dashboard_logs.add_log(f"❌ Erreur export: {str(e)}", "ERROR")

    def clear_logs(self):
        """Efface les logs des outils"""
        reply = QMessageBox.question(self, "Effacer les logs", "Êtes-vous sûr de vouloir effacer tous les logs des outils ?\n\nCette action est irréversible.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if hasattr(self, 'tools_logs'):
                self.tools_logs.clear_logs()
                self.dashboard_logs.add_log("🗑️ Logs outils effacés", "WARNING")
    
    def clear_dashboard_logs(self):
        """Efface les logs du dashboard"""
        reply = QMessageBox.question(self, "Effacer les logs", "Êtes-vous sûr de vouloir effacer tous les logs du dashboard ?\n\nCette action est irréversible.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if hasattr(self, 'dashboard_logs'):
                self.dashboard_logs.clear_logs()
                self.dashboard_logs.add_log("🗑️ Logs dashboard effacés par l'utilisateur", "WARNING")
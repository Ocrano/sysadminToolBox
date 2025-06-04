# src/ui/main_window_refactored.py
"""
MainWindow refactorisée utilisant le pattern MVC
- Layout amélioré avec version unique par onglet
- Meilleure organisation des contrôles de logs
- Titres de sections plus visibles
"""

import os
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QMessageBox, QFileDialog, QInputDialog, QLineEdit
)

# Import des composants refactorisés
from .controllers.main_controller import MainController
from .components.common_widgets import (
    VersionLabel, ConnectionStatusWidget, ActionButton, LogDisplay,
    LogControlPanel, SectionHeader, ConfigurationGroup, ActionGrid,
    WidgetFactory, MetricsDisplay
)
from .dialogs.proxmox_config_dialog import ProxmoxConfigDialog
from .dialogs.qemu_agent_dialog import QemuAgentManagerDialog
from ..utils.ip_plan_importer import IPPlanImporter

# Import du système de logging
from ..core.logger import toolbox_logger, log_info, log_debug, log_error, log_success, log_warning


class MainWindowRefactored(QMainWindow):
    """Fenêtre principale refactorisée - Version courte et maintenable"""
    
    VERSION = "Alpha 0.0.6"
    DEVELOPER = "ocrano"
    
    def __init__(self, git_manager, script_runner, proxmox_service):
        super().__init__()
        
        # Initialiser le contrôleur
        self.controller = MainController(git_manager, script_runner, proxmox_service)
        self.importer = IPPlanImporter()
        
        # Connecter les signaux du contrôleur
        self.controller.proxmox_connection_changed.connect(self.on_proxmox_connection_changed)
        self.controller.scripts_loaded.connect(self.on_scripts_loaded)
        
        log_info("MainWindow refactorisée initialisée", "MainWindow")
        
        self.init_ui()
        self.setup_logging()

    def init_ui(self):
        """Interface utilisateur simplifiée"""
        self.setWindowTitle("Toolbox PyQt6 - Refactorisé")
        self.setGeometry(200, 200, 1200, 800)
        self.setMinimumSize(1000, 600)
        
        # Onglets principaux
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Créer les onglets
        self.create_scripts_tab()
        self.create_settings_tab()
        self.create_tools_tab()
        self.create_import_tab()
        
        # Ajouter les onglets externes (Network, Scanner)
        self.add_external_tabs()
        
        log_success("Interface refactorisée initialisée", "MainWindow")

    def create_scripts_tab(self):
        """Onglet Scripts PowerShell simplifié"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # En-tête avec version (UNE SEULE FOIS par onglet)
        header = SectionHeader("Scripts PowerShell", "📜", VersionLabel(self.VERSION, self.DEVELOPER))
        layout.addWidget(header)
        
        # Liste des scripts
        from PyQt6.QtWidgets import QListWidget
        self.scripts_list = QListWidget()
        layout.addWidget(self.scripts_list)
        
        # Boutons d'action
        buttons_layout = QHBoxLayout()
        
        fetch_btn = ActionButton("Récupérer Scripts", 'info', "📥")
        fetch_btn.clicked.connect(self.load_scripts_from_gitlab)
        buttons_layout.addWidget(fetch_btn)
        
        run_btn = ActionButton("Exécuter Script", 'success', "▶️")
        run_btn.clicked.connect(self.run_selected_script)
        buttons_layout.addWidget(run_btn)
        
        layout.addLayout(buttons_layout)
        tab.setLayout(layout)
        
        self.tabs.addTab(tab, "Scripts PowerShell")
        self.load_local_scripts()  # Charger les scripts locaux au démarrage

    def create_settings_tab(self):
        """Onglet Paramètres simplifié"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # En-tête avec version (UNE SEULE FOIS par onglet)
        header = SectionHeader("Paramètres", "⚙️", VersionLabel(self.VERSION, self.DEVELOPER))
        layout.addWidget(header)
        
        # Configuration GitLab
        gitlab_group = ConfigurationGroup("Configuration GitLab", "🦊")
        gitlab_layout = QHBoxLayout()
        
        token_btn = WidgetFactory.create_config_button("Configurer Token GitLab", 'warning', "🔑")
        token_btn.clicked.connect(self.configure_gitlab_token)
        gitlab_layout.addWidget(token_btn)
        
        gitlab_layout.addStretch()
        gitlab_group.setLayout(gitlab_layout)
        layout.addWidget(gitlab_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        
        self.tabs.addTab(tab, "Paramètres")

    def create_tools_tab(self):
        """Onglet Tools refactorisé avec composants"""
        tab = QWidget()
        main_layout = QVBoxLayout()
        
        # En-tête avec version (UNE SEULE FOIS par onglet)
        header = SectionHeader("Tools", "🛠️", VersionLabel(self.VERSION, self.DEVELOPER))
        main_layout.addWidget(header)
        
        # === SECTION CONNEXION PROXMOX ===
        connection_group = ConfigurationGroup("Connexion Proxmox")
        connection_layout = QHBoxLayout()
        
        # Bouton configuration
        self.config_proxmox_btn = WidgetFactory.create_config_button("Configurer", 'primary', "⚙️")
        self.config_proxmox_btn.clicked.connect(self.configure_proxmox)
        connection_layout.addWidget(self.config_proxmox_btn)
        
        # Statut de connexion
        self.connection_status = ConnectionStatusWidget("Proxmox")
        connection_layout.addWidget(self.connection_status)
        
        # Métriques Proxmox
        self.proxmox_metrics = MetricsDisplay()
        connection_layout.addWidget(self.proxmox_metrics)
        
        connection_layout.addStretch()
        
        connection_group.setLayout(connection_layout)
        main_layout.addWidget(connection_group)
        
        # === SPLITTER ACTIONS / LOGS ===
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Actions à gauche
        actions_widget = self.create_actions_section()
        main_splitter.addWidget(actions_widget)
        
        # Logs à droite
        logs_widget = self.create_logs_section()
        main_splitter.addWidget(logs_widget)
        
        # Répartition 30/70
        main_splitter.setStretchFactor(0, 30)
        main_splitter.setStretchFactor(1, 70)
        
        main_layout.addWidget(main_splitter)
        tab.setLayout(main_layout)
        
        self.tabs.addTab(tab, "Tools")

    def create_actions_section(self):
        """Section des actions Proxmox"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        title = SectionHeader("Actions disponibles")
        layout.addWidget(title)
        
        # Grille d'actions organisée
        self.actions_grid = ActionGrid()
        
        # Groupe VM Management
        vm_group = self.actions_grid.add_group("Gestion des VMs")
        
        self.qemu_btn = ActionButton("Gestionnaire QEMU Agent", 'success', "🔧")
        self.qemu_btn.clicked.connect(self.open_qemu_agent_manager)
        self.qemu_btn.setEnabled(False)
        self.actions_grid.add_action_to_group("Gestion des VMs", self.qemu_btn)
        
        self.list_vms_btn = ActionButton("Lister toutes les VMs", 'info', "📋")
        self.list_vms_btn.clicked.connect(self.list_all_vms)
        self.list_vms_btn.setEnabled(False)
        self.actions_grid.add_action_to_group("Gestion des VMs", self.list_vms_btn)
        
        self.scan_linux_btn = ActionButton("Scanner VMs Linux", 'orange', "🐧")
        self.scan_linux_btn.clicked.connect(self.scan_linux_vms)
        self.scan_linux_btn.setEnabled(False)
        self.actions_grid.add_action_to_group("Gestion des VMs", self.scan_linux_btn)
        
        # Groupe Infrastructure
        infra_group = self.actions_grid.add_group("Infrastructure")
        
        self.nodes_btn = ActionButton("Statut des nœuds", 'purple', "📊")
        self.nodes_btn.clicked.connect(self.show_nodes_status)
        self.nodes_btn.setEnabled(False)
        self.actions_grid.add_action_to_group("Infrastructure", self.nodes_btn)
        
        self.storage_btn = ActionButton("Informations stockage", 'pink', "💾")
        self.storage_btn.clicked.connect(self.show_storage_info)
        self.storage_btn.setEnabled(False)
        self.actions_grid.add_action_to_group("Infrastructure", self.storage_btn)
        
        layout.addWidget(self.actions_grid)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget

    def create_logs_section(self):
        """Section des logs avec contrôles - Layout amélioré"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # === TITRE PRINCIPAL ===
        title = SectionHeader("Logs en temps réel")
        layout.addWidget(title)
        
        # === CONTRÔLES EN LIGNE (Filtres à gauche, boutons à droite) ===
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 10, 0, 15)  # Plus d'espace autour
        
        # Panneau de contrôle des logs
        self.log_controls = LogControlPanel()
        
        # Connexion sécurisée des signaux
        try:
            if hasattr(self.log_controls, 'filter_changed'):
                self.log_controls.filter_changed.connect(self.on_log_filter_changed)
        except AttributeError:
            print("Signal filter_changed non disponible - filtres désactivés")
        
        self.log_controls.export_requested.connect(self.export_logs)
        self.log_controls.clear_requested.connect(self.clear_logs)
        
        controls_layout.addWidget(self.log_controls)
        layout.addLayout(controls_layout)
        
        # === ZONE D'AFFICHAGE DES LOGS ===
        self.tools_logs = LogDisplay("TOOLS")
        layout.addWidget(self.tools_logs)
        
        widget.setLayout(layout)
        return widget

    def create_import_tab(self):
        """Onglet Import IP Plan simplifié"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # En-tête avec version (UNE SEULE FOIS par onglet)
        header = SectionHeader("Import IP Plan", "📊", VersionLabel(self.VERSION, self.DEVELOPER))
        layout.addWidget(header)
        
        # Bouton d'import
        import_btn = ActionButton("Importer un plan d'adressage (.xlsx)", 'primary', "📁")
        import_btn.clicked.connect(self.import_ip_plan)
        layout.addWidget(import_btn)
        
        # Tableau des résultats
        from PyQt6.QtWidgets import QTableWidget
        self.ip_table = QTableWidget()
        layout.addWidget(self.ip_table)
        
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Import IP Plan")

    def add_external_tabs(self):
        """Ajoute les onglets externes (Network, Scanner)"""
        # Onglet Scanner
        try:
            from .tabs.network_scanner_tab import NetworkScannerTab
            scanner_tab = NetworkScannerTab(self, self.controller.proxmox_service)
            self.tabs.addTab(scanner_tab, "SCAN")
            log_debug("Onglet Scanner ajouté", "MainWindow")
        except ImportError as e:
            log_warning(f"Onglet Scanner non disponible: {e}", "MainWindow")
        
        # Onglet Network
        try:
            from .tabs.network_tab_refactored import NetworkTabRefactored as NetworkTab
            network_tab = NetworkTab(self)
            self.tabs.addTab(network_tab, "Network")
            log_debug("Onglet Network ajouté", "MainWindow")
        except ImportError as e:
            log_warning(f"Onglet Network non disponible: {e}", "MainWindow")

    def setup_logging(self):
        """Configure la redirection des logs"""
        qt_handler = toolbox_logger.get_qt_handler()
        qt_handler.log_message.connect(self.on_log_message)
        log_info("Système de logs refactorisé activé", "MainWindow")

    # === SLOTS DU CONTRÔLEUR ===
    
    def on_proxmox_connection_changed(self, connected):
        """Réagit aux changements de connexion Proxmox"""
        # Mettre à jour le statut
        if connected:
            info = self.controller.get_proxmox_info()
            if info:
                info_text = f"Proxmox VE {info['version']} • {info['nodes_count']} nœud(s)"
                self.connection_status.update_status(True, info_text)
                
                # Mettre à jour les métriques
                self.proxmox_metrics.clear_metrics()
                self.proxmox_metrics.add_metric("VMs Total", info['total_vms'], "🖥️", "#17a2b8")
                self.proxmox_metrics.add_metric("VMs Actives", info['running_vms'], "🟢", "#28a745")
                self.proxmox_metrics.add_metric("Nœuds", info['nodes_count'], "🏗️", "#6f42c1")
            else:
                self.connection_status.update_status(True, "Connecté")
        else:
            self.connection_status.update_status(False)
            self.proxmox_metrics.clear_metrics()
        
        # Activer/désactiver les actions
        self.actions_grid.enable_group("Gestion des VMs", connected)
        self.actions_grid.enable_group("Infrastructure", connected)

    def on_scripts_loaded(self, script_list):
        """Réagit au chargement des scripts"""
        self.scripts_list.clear()
        for script in script_list:
            self.scripts_list.addItem(script)

    def on_log_message(self, message):
        """Réagit aux nouveaux logs"""
        # Extraire le niveau du log
        level = "INFO"
        if "ERROR" in message:
            level = "ERROR"
        elif "SUCCESS" in message:
            level = "SUCCESS"
        elif "WARNING" in message:
            level = "WARNING"
        elif "DEBUG" in message:
            level = "DEBUG"
        
        self.tools_logs.add_log(message, level)

    def on_log_filter_changed(self, level, enabled):
        """Réagit aux changements de filtres - VERSION CORRIGÉE"""
        try:
            if hasattr(self, 'tools_logs') and hasattr(self.tools_logs, 'update_filter'):
                self.tools_logs.update_filter(level, enabled)
                print(f"Filtre {level} {'activé' if enabled else 'désactivé'}")
            else:
                print(f"Logs display non disponible pour filtre {level}")
        except Exception as e:
            print(f"Erreur lors du changement de filtre {level}: {e}")

    def configure_proxmox(self):
        """Configure Proxmox via le contrôleur"""
        dialog = ProxmoxConfigDialog(self)
        if dialog.exec():
            config = dialog.get_config()
            success, message = self.controller.configure_proxmox(config)
            
            if success:
                QMessageBox.information(self, "Connexion réussie", message)
            else:
                QMessageBox.critical(self, "Échec", message)

    def configure_gitlab_token(self):
        """Configure le token GitLab"""
        token, ok = QInputDialog.getText(
            self, "GitLab Token", 
            "Entrez votre token GitLab :", 
            QLineEdit.EchoMode.Password
        )
        
        if ok:
            success, message = self.controller.configure_gitlab_token(token)
            if success:
                QMessageBox.information(self, "Succès", message)

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
            if not success:
                QMessageBox.warning(self, "Erreur", message)
        else:
            QMessageBox.warning(self, "Sélection", "Aucun script sélectionné.")

    def open_qemu_agent_manager(self):
        """Ouvre le gestionnaire QEMU Agent"""
        dialog = QemuAgentManagerDialog(self, self.controller.proxmox_service)
        dialog.exec()

    def list_all_vms(self):
        """Liste toutes les VMs"""
        vms = self.controller.proxmox_service.list_vms()
        self.tools_logs.add_log(f"{len(vms)} VMs trouvées dans le cluster", "SUCCESS")
        for vm in vms:
            status = "RUNNING" if vm['status'] == 'running' else "STOPPED"
            self.tools_logs.add_log(f"VM: {vm['name']} (ID: {vm['vmid']}) on {vm['node']} - {status}", "INFO")

    def scan_linux_vms(self):
        """Scanne les VMs Linux"""
        linux_vms = self.controller.proxmox_service.get_linux_vms()
        self.tools_logs.add_log(f"{len(linux_vms)} VMs Linux actives trouvées", "SUCCESS")
        for vm in linux_vms:
            self.tools_logs.add_log(f"Linux VM: {vm['name']} - IP: {vm.get('ip', 'N/A')} on {vm['node']}", "INFO")

    def show_nodes_status(self):
        """Affiche le statut des nœuds"""
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

    def show_storage_info(self):
        """Affiche les informations de stockage"""
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

    def import_ip_plan(self):
        """Importe un plan d'adressage IP"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Sélectionner un fichier Excel", "", "Fichiers Excel (*.xlsx)"
        )
        
        if file_path:
            success, data, message = self.controller.import_ip_plan(file_path)
            
            if success:
                # Mettre à jour le tableau
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
                self.tools_logs.add_log(message, "SUCCESS")
            else:
                QMessageBox.critical(self, "Erreur", message)
                self.tools_logs.add_log(f"Erreur import: {message}", "ERROR")

    def export_logs(self):
        """Exporte les logs - VERSION AMÉLIORÉE"""
        try:
            from PyQt6.QtWidgets import QMessageBox, QFileDialog
            
            reply = QMessageBox.question(
                self,
                "Type d'export",
                "Quel type de logs voulez-vous exporter ?\n\n" +
                "• OUI = Logs actuellement affichés (filtrés)\n" +
                "• NON = Tous les logs (complets)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Cancel:
                return
            
            export_type = "filtered" if reply == QMessageBox.StandardButton.Yes else "complete"
            
            # Récupérer le contenu selon le type d'export
            if reply == QMessageBox.StandardButton.Yes:
                # Logs filtrés - utiliser la nouvelle méthode
                if hasattr(self.tools_logs, 'get_filtered_logs_text'):
                    logs_content = self.tools_logs.get_filtered_logs_text()
                else:
                    logs_content = self.tools_logs.toPlainText()
            else:
                # Tous les logs - utiliser la nouvelle méthode
                if hasattr(self.tools_logs, 'get_all_logs_text'):
                    logs_content = self.tools_logs.get_all_logs_text()
                else:
                    # Fallback - récupérer depuis la liste complète
                    logs_content = '\n'.join([f"[{level}] {msg}" for msg, level, _ in self.tools_logs.all_logs])
            
            success, export_content, filename = self.controller.export_logs(logs_content, export_type)
            
            if success:
                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Exporter les logs",
                    filename,
                    "Fichiers log (*.log);;Fichiers texte (*.txt);;Tous les fichiers (*.*)"
                )
                
                if file_path:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(export_content)
                    
                    QMessageBox.information(self, "Export réussi", f"Logs exportés vers:\n{file_path}")
                    self.tools_logs.add_log(f"Logs exportés vers: {os.path.basename(file_path)}", "SUCCESS")
            else:
                QMessageBox.critical(self, "Erreur", "Impossible d'exporter les logs")
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur d'export", f"Erreur lors de l'export:\n{str(e)}")
            self.tools_logs.add_log(f"Erreur export: {str(e)}", "ERROR")

    def clear_logs(self):
        """Efface les logs"""
        reply = QMessageBox.question(
            self,
            "Effacer les logs",
            "Êtes-vous sûr de vouloir effacer tous les logs ?\n\nCette action est irréversible.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.tools_logs.clear_logs()
            self.tools_logs.add_log("Logs effacés par l'utilisateur", "WARNING")
# src/ui/tabs/network_tab_refactored.py
"""
NetworkTab refactorisé utilisant les services SSH et les composants UI
Code réduit de 900+ lignes à ~300 lignes
"""

import os
import time
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QComboBox,
    QMessageBox, QFileDialog, QInputDialog
)

# Import des services et composants refactorisés
from ...services.ssh_service import NetworkService
from ..components.common_widgets import (
    VersionLabel, ConnectionStatusWidget, ActionButton, LogDisplay,
    LogControlPanel, SectionHeader, ConfigurationGroup, ActionGrid,
    WidgetFactory, StatusTable
)
from ..dialogs.network_config_dialog import NetworkConfigDialog

from ...core.logger import log_info, log_debug, log_error, log_success, log_warning


class NetworkTabRefactored(QWidget):
    """Onglet Network refactorisé - Version courte utilisant les services"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Service réseau centralisé
        self.network_service = NetworkService()
        
        # État interne
        self.current_device_type = "Cisco Switch/Router"
        self.active_thread = None
        
        self.init_ui()
        log_debug("NetworkTab refactorisé initialisé", "Network")

    def init_ui(self):
        """Interface utilisateur simplifiée"""
        main_layout = QVBoxLayout()
        
        # === SECTION CONFIGURATION (en haut) ===
        config_group = ConfigurationGroup("Configuration SSH Réseau", "🔐")
        config_layout = QHBoxLayout()
        
        # Boutons de configuration
        self.config_ssh_btn = WidgetFactory.create_config_button("Configurer SSH", 'primary', "⚙️")
        self.config_ssh_btn.clicked.connect(self.configure_ssh)
        config_layout.addWidget(self.config_ssh_btn)
        
        self.import_btn = WidgetFactory.create_config_button("Importer CSV", 'purple', "📁")
        self.import_btn.clicked.connect(self.import_devices_csv)
        config_layout.addWidget(self.import_btn)
        
        # Statut SSH
        self.ssh_status = ConnectionStatusWidget("SSH")
        config_layout.addWidget(self.ssh_status)
        
        # Info équipements
        self.devices_info = WidgetFactory.create_info_label("Aucun équipement chargé")
        config_layout.addWidget(self.devices_info)
        
        config_layout.addStretch()
        config_layout.addWidget(VersionLabel())
        
        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)
        
        # === SPLITTER PRINCIPAL ===
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Actions à gauche
        actions_widget = self.create_actions_section()
        main_splitter.addWidget(actions_widget)
        
        # Résultats à droite
        results_widget = self.create_results_section()
        main_splitter.addWidget(results_widget)
        
        # Répartition 30/70
        main_splitter.setStretchFactor(0, 30)
        main_splitter.setStretchFactor(1, 70)
        
        main_layout.addWidget(main_splitter)
        self.setLayout(main_layout)

    def create_actions_section(self):
        """Section des actions réseau"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        title = SectionHeader("Actions Réseau", "🌐")
        layout.addWidget(title)
        
        # === SÉLECTION TYPE D'ÉQUIPEMENT ===
        device_group = ConfigurationGroup("Type d'équipement", "🔧")
        device_layout = QVBoxLayout()
        
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
        device_layout.addWidget(self.device_type_combo)
        
        device_group.setLayout(device_layout)
        layout.addWidget(device_group)
        
        # === ACTIONS DYNAMIQUES ===
        self.actions_grid = ActionGrid()
        self.create_actions_for_device_type("cisco")  # Par défaut
        layout.addWidget(self.actions_grid)
        
        # === ÉQUIPEMENTS CHARGÉS ===
        devices_group = ConfigurationGroup("Équipements", "📡")
        devices_layout = QVBoxLayout()
        
        self.devices_table = StatusTable(["Hostname", "IP", "Type", "Description"])
        self.devices_table.setMaximumHeight(150)
        devices_layout.addWidget(self.devices_table)
        
        devices_group.setLayout(devices_layout)
        layout.addWidget(devices_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_results_section(self):
        """Section des résultats avec contrôles"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # En-tête avec contrôles
        header_layout = QHBoxLayout()
        title = SectionHeader("Résultats en temps réel", "📋")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Panneau de contrôle simplifié
        self.results_controls = LogControlPanel()
        self.results_controls.export_requested.connect(self.export_results)
        self.results_controls.clear_requested.connect(self.clear_results)
        header_layout.addWidget(self.results_controls)
        
        layout.addLayout(header_layout)
        
        # Zone d'affichage des résultats
        self.results_display = LogDisplay("NETWORK RESULTS")
        layout.addWidget(self.results_display)
        
        widget.setLayout(layout)
        return widget

    def create_actions_for_device_type(self, device_type_key):
        """Crée les actions dynamiquement selon le type d'équipement"""
        # Nettoyer les actions existantes
        self.actions_grid = ActionGrid()
        
        # Récupérer les commandes pour ce type
        commands = self.network_service.get_commands_for_device_type(device_type_key)
        
        # Couleurs par type d'équipement
        color_map = {
            'cisco': 'info',
            'fortinet': 'pink',
            'allied': 'orange',
            'stormshield': 'purple',
            'generic': 'success'
        }
        
        color = color_map.get(device_type_key, 'info')
        
        # Groupe d'actions pour ce type
        group_name = f"Actions {device_type_key.title()}"
        self.actions_grid.add_group(group_name, "📋")
        
        # Créer les boutons dynamiquement
        for action_name, cmd_list in commands.items():
            # Nom convivial pour l'action
            friendly_name = action_name.replace('_', ' ').title()
            
            btn = ActionButton(friendly_name, color, "📋")
            btn.clicked.connect(lambda checked, cmds=cmd_list: self.execute_commands(cmds))
            btn.setEnabled(False)  # Désactivé par défaut
            
            self.actions_grid.add_action_to_group(group_name, btn)
        
        # Action personnalisée
        custom_btn = ActionButton("Commande Personnalisée", 'secondary', "🔍")
        custom_btn.clicked.connect(self.execute_custom_command)
        custom_btn.setEnabled(False)
        self.actions_grid.add_action_to_group(group_name, custom_btn)

    # === ÉVÉNEMENTS ===
    
    def on_device_type_changed(self, device_type):
        """Change les actions selon le type d'équipement"""
        self.current_device_type = device_type
        
        # Mapper vers les clés internes
        type_mapping = {
            "Cisco Switch/Router": "cisco",
            "Allied Telesis Switch": "allied",
            "HP/Aruba Switch": "cisco",  # Utilise les commandes Cisco
            "Fortinet Firewall": "fortinet",
            "Stormshield Firewall": "stormshield",
            "pfSense Firewall": "generic",
            "Générique (Linux)": "generic"
        }
        
        device_key = type_mapping.get(device_type, "generic")
        
        log_info(f"Type d'équipement changé: {device_type}", "Network")
        self.create_actions_for_device_type(device_key)
        self.update_buttons_state()

    def configure_ssh(self):
        """Configure SSH avec dialogue simplifié"""
        dialog = NetworkConfigDialog(self)
        if dialog.exec():
            config = dialog.get_config()
            if config:
                success, message = self.network_service.configure_ssh(
                    config['username'], 
                    config['password']
                )
                
                if success:
                    self.ssh_status.update_status(True, f"Utilisateur: {config['username']}")
                    self.results_display.add_log(f"SSH configuré pour {config['username']}", "SUCCESS")
                    self.update_buttons_state()
                    
                    QMessageBox.information(self, "Configuration SSH", message)
                else:
                    QMessageBox.warning(self, "Erreur SSH", message)

    def import_devices_csv(self):
        """Importe les équipements depuis CSV"""
        # Dialogue d'aide pour le format CSV
        help_msg = QMessageBox(self)
        help_msg.setWindowTitle("Format CSV")
        help_msg.setText("Le fichier CSV doit contenir les colonnes: hostname, ip, type (optionnel), description (optionnel)")
        help_msg.setDetailedText("""Exemple de contenu CSV:
hostname,ip,type,description
SW-CORE-01,192.168.1.10,Cisco,Switch Core
FW-DMZ-01,192.168.1.1,Fortinet,Firewall DMZ
SW-ACCESS-02,192.168.1.20,Allied,Switch Access""")
        help_msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        help_msg.button(QMessageBox.StandardButton.Ok).setText("Continuer")
        
        if help_msg.exec() != QMessageBox.StandardButton.Ok:
            return
        
        # Sélection fichier
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Importer équipements réseau", "", "Fichiers CSV (*.csv)"
        )
        
        if file_path:
            success, devices, message = self.network_service.import_devices(file_path)
            
            if success:
                self.update_devices_table()
                self.update_devices_info()
                self.update_buttons_state()
                
                self.results_display.add_log(f"Import réussi: {len(devices)} équipements", "SUCCESS")
                QMessageBox.information(self, "Import réussi", message)
            else:
                self.results_display.add_log(f"Erreur import: {message}", "ERROR")
                QMessageBox.critical(self, "Erreur Import", message)

    def execute_commands(self, commands):
        """Exécute des commandes sur les équipements"""
        if not self.network_service.is_ssh_configured():
            QMessageBox.warning(self, "SSH requis", "Configurez d'abord SSH.")
            return
        
        devices = self.network_service.get_devices()
        if not devices:
            QMessageBox.warning(self, "Équipements requis", "Importez d'abord des équipements.")
            return
        
        # Confirmation
        reply = QMessageBox.question(
            self,
            "Confirmer l'exécution",
            f"Exécuter {len(commands)} commande(s) sur {len(devices)} équipements ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.results_display.add_log(f"Début exécution sur {len(devices)} équipements", "INFO")
            
            success, thread = self.network_service.execute_commands_on_devices(
                commands, self.current_device_type
            )
            
            if success:
                self.active_thread = thread
                # Connecter les signaux du thread
                thread.command_result.connect(self.on_command_success)
                thread.command_error.connect(self.on_command_error)
                thread.progress_update.connect(self.on_progress_update)
                thread.finished.connect(self.on_commands_finished)
                thread.start()
            else:
                QMessageBox.warning(self, "Erreur", thread)  # thread contient le message d'erreur

    def execute_custom_command(self):
        """Exécute une commande personnalisée"""
        command, ok = QInputDialog.getText(
            self, "Commande personnalisée", 
            "Entrez la commande à exécuter:"
        )
        
        if ok and command.strip():
            reply = QMessageBox.question(
                self, "Commande personnalisée",
                f"Exécuter '{command.strip()}' sur tous les équipements ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.execute_commands([command.strip()])

    def update_devices_table(self):
        """Met à jour le tableau des équipements"""
        devices = self.network_service.get_devices()
        
        self.devices_table.setRowCount(0)
        for device in devices:
            self.devices_table.add_status_row([
                device['hostname'],
                device['ip'],
                device['type'],
                device.get('description', '')
            ])

    def update_devices_info(self):
        """Met à jour les infos d'équipements"""
        devices = self.network_service.get_devices()
        type_summary = self.network_service.get_device_types_summary()
        
        if devices:
            total = len(devices)
            if len(type_summary) == 1:
                type_name = list(type_summary.keys())[0]
                info_text = f"{total} équipements ({type_name})"
            else:
                type_text = ", ".join([f"{count} {t}" for t, count in type_summary.items()])
                info_text = f"{total} équipements ({type_text})"
            
            self.devices_info.setText(info_text)
        else:
            self.devices_info.setText("Aucun équipement chargé")

    def update_buttons_state(self):
        """Met à jour l'état des boutons"""
        ssh_configured = self.network_service.is_ssh_configured()
        devices_loaded = bool(self.network_service.get_devices())
        
        # Activer les actions si SSH configuré ET équipements chargés
        enabled = ssh_configured and devices_loaded
        
        # Activer tous les groupes d'actions
        for group_name in self.actions_grid.groups.keys():
            self.actions_grid.enable_group(group_name, enabled)
        
        # Messages informatifs
        if devices_loaded and not ssh_configured:
            self.results_display.add_log("Équipements chargés. Configurez SSH pour activer les actions.", "INFO")
        elif ssh_configured and not devices_loaded:
            self.results_display.add_log("SSH configuré. Importez des équipements pour activer les actions.", "INFO")

    # === CALLBACKS DU THREAD ===
    
    def on_command_success(self, hostname, command, result):
        """Succès de commande"""
        self.results_display.add_log(f"✅ {hostname}: {command}", "SUCCESS")
        
        # Afficher un aperçu du résultat
        lines = result.strip().split('\n')
        preview = '\n'.join(lines[:10])  # Premiers 10 lignes
        if len(lines) > 10:
            preview += f"\n... ({len(lines)-10} lignes supplémentaires)"
        
        self.results_display.add_log(f"Résultat {hostname}:\n{preview}", "INFO")

    def on_command_error(self, hostname, command, error):
        """Erreur de commande"""
        self.results_display.add_log(f"❌ {hostname}: {command} - {error}", "ERROR")

    def on_progress_update(self, message):
        """Mise à jour progression"""
        self.results_display.add_log(message, "INFO")

    def on_commands_finished(self):
        """Fin des commandes"""
        self.results_display.add_log("🎯 Toutes les commandes terminées", "SUCCESS")
        self.active_thread = None

    # === EXPORT ET NETTOYAGE ===
    
    def export_results(self):
        """Exporte les résultats"""
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        filename = f"network_results_{timestamp}.txt"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exporter les résultats", filename,
            "Fichiers texte (*.txt);;Tous les fichiers (*.*)"
        )
        
        if file_path:
            try:
                content = self.results_display.toPlainText()
                
                # Métadonnées
                devices = self.network_service.get_devices()
                metadata = f"""
================================================================================
                    EXPORT RESULTATS NETWORK MANAGEMENT
================================================================================
Date d'export      : {time.strftime('%Y-%m-%d %H:%M:%S')}
Équipements        : {len(devices)}
Type d'équipement  : {self.current_device_type}
SSH configuré      : {'Oui' if self.network_service.is_ssh_configured() else 'Non'}
================================================================================

{content}
"""
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(metadata)
                
                self.results_display.add_log(f"Résultats exportés: {os.path.basename(file_path)}", "SUCCESS")
                QMessageBox.information(self, "Export réussi", f"Résultats exportés vers:\n{file_path}")
                
            except Exception as e:
                self.results_display.add_log(f"Erreur export: {str(e)}", "ERROR")
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export:\n{str(e)}")

    def clear_results(self):
        """Efface les résultats"""
        reply = QMessageBox.question(
            self, "Effacer les résultats",
            "Effacer tous les résultats affichés ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.results_display.clear_logs()

    def closeEvent(self, event):
        """Nettoyage à la fermeture"""
        if self.active_thread and self.active_thread.isRunning():
            self.active_thread.terminate()
            self.active_thread.wait()
        
        self.network_service.cleanup_threads()
        event.accept()


# Alias pour la compatibilité
NetworkTab = NetworkTabRefactored
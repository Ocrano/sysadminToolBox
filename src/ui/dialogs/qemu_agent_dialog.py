from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QProgressBar,
    QGroupBox, QInputDialog, QLineEdit, QMessageBox, QCheckBox,
    QFormLayout, QWidget
)
from PyQt6.QtGui import QIcon, QFont, QColor

# Import du système de logging
from ...core.logger import toolbox_logger, log_debug, log_info, log_error, log_success, log_step, log_vm

class SSHCredentialsDialog(QDialog):
    """Dialogue pour saisir les credentials SSH"""
    def __init__(self, parent=None, vm_info=None):
        super().__init__(parent)
        self.vm_info = vm_info
        self.credentials = {}
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Credentials SSH requis")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QVBoxLayout()
        
        # Header
        vm_name = self.vm_info.get('name', 'VM inconnue') if self.vm_info else 'VM'
        header_label = QLabel(f"🔐 Credentials SSH pour {vm_name}")
        header_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header_label)
        
        desc_label = QLabel("Entrez les informations de connexion SSH pour installer QEMU Agent :")
        desc_label.setStyleSheet("color: #6c757d; margin-bottom: 15px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Formulaire
        form_group = QGroupBox("Informations de connexion")
        form_layout = QFormLayout()
        
        # IP (pré-remplie si disponible)
        self.ip_input = QLineEdit()
        if self.vm_info and self.vm_info.get('ip') not in ['Non disponible', 'IP non disponible']:
            self.ip_input.setText(self.vm_info.get('ip', ''))
        self.ip_input.setPlaceholderText("Ex: 192.168.1.100")
        form_layout.addRow("🌐 Adresse IP:", self.ip_input)
        
        # Utilisateur
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Ex: root, admin, ubuntu...")
        form_layout.addRow("👤 Nom d'utilisateur:", self.username_input)
        
        # Mot de passe
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Mot de passe SSH")
        form_layout.addRow("🔑 Mot de passe:", self.password_input)
        
        # Checkbox pour afficher le mot de passe
        self.show_password_checkbox = QCheckBox("Afficher le mot de passe")
        self.show_password_checkbox.toggled.connect(self.toggle_password_visibility)
        form_layout.addRow("", self.show_password_checkbox)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Notes
        notes_group = QGroupBox("ℹ️ Informations")
        notes_layout = QVBoxLayout()
        notes_text = QLabel("""
• L'installation nécessite les privilèges sudo/root
• Les commandes suivantes seront exécutées :
  - Installation du package qemu-guest-agent
  - Activation et démarrage du service
• La connexion SSH doit être accessible depuis ce poste
• Un redémarrage complet de la VM sera effectué
• Les logs détaillés s'affichent dans l'onglet Export Projet
        """.strip())
        notes_text.setStyleSheet("font-size: 11px; color: #6c757d;")
        notes_text.setWordWrap(True)
        notes_layout.addWidget(notes_text)
        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group)
        
        # Boutons
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("❌ Annuler")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        button_layout.addStretch()
        
        self.ok_button = QPushButton("✅ Continuer l'installation")
        self.ok_button.clicked.connect(self.accept_credentials)
        self.ok_button.setDefault(True)
        self.ok_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Focus sur le premier champ vide
        if not self.ip_input.text():
            self.ip_input.setFocus()
        else:
            self.username_input.setFocus()

    def toggle_password_visibility(self, checked):
        """Bascule la visibilité du mot de passe"""
        if checked:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

    def accept_credentials(self):
        """Valide et accepte les credentials"""
        ip = self.ip_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        # Validation
        if not ip:
            QMessageBox.warning(self, "Champ requis", "L'adresse IP est requise")
            self.ip_input.setFocus()
            return
        
        if not username:
            QMessageBox.warning(self, "Champ requis", "Le nom d'utilisateur est requis")
            self.username_input.setFocus()
            return
        
        if not password:
            QMessageBox.warning(self, "Champ requis", "Le mot de passe est requis")
            self.password_input.setFocus()
            return
        
        # Validation de l'IP
        try:
            import ipaddress
            ipaddress.IPv4Address(ip)
        except Exception:
            QMessageBox.warning(self, "IP invalide", "L'adresse IP n'est pas valide")
            self.ip_input.setFocus()
            return
        
        # Stocker les credentials
        self.credentials = {
            'ip': ip,
            'username': username,
            'password': password
        }
        
        log_debug(f"Credentials SSH validés pour {username}@{ip}", "QemuAgent")
        self.accept()

    def get_credentials(self):
        """Retourne les credentials saisis"""
        return self.credentials

class QemuAgentInstallThread(QThread):
    """Thread pour installer QEMU Agent - Version avec logging complet"""
    progress_update = pyqtSignal(str)
    installation_complete = pyqtSignal(bool, str, dict)  # success, message, vm_info
    
    def __init__(self, proxmox_handler, vm_info, ssh_credentials=None, auto_restart=False):
        super().__init__()
        self.proxmox_handler = proxmox_handler
        self.vm_info = vm_info
        self.ssh_credentials = ssh_credentials
        self.auto_restart = auto_restart
        self.restart_confirmed = False
    
    def run(self):
        vm_name = self.vm_info.get('name', 'VM inconnue')
        log_vm("Début thread d'installation QEMU Agent", vm_name)
        
        try:
            if self.vm_info['os_type'] == 'linux':
                if not self.ssh_credentials:
                    log_error("Credentials SSH manquants", "Installation")
                    self.installation_complete.emit(False, "Credentials SSH requis pour Linux", self.vm_info)
                    return
                
                log_step(1, 5, "Démarrage installation QEMU Agent", "Installation")
                
                # Utiliser la version simplifiée sans dialogue dans le thread
                success, message = self.install_qemu_agent_simple_sequence(
                    self.vm_info, 
                    self.ssh_credentials
                )
                
                if success:
                    log_success(f"Installation terminée: {message}", "Installation")
                    self.installation_complete.emit(True, message, self.vm_info)
                else:
                    log_error(f"Installation échouée: {message}", "Installation")
                    self.installation_complete.emit(False, message, self.vm_info)
                    
            elif self.vm_info['os_type'] == 'windows':
                log_info("VM Windows détectée - installation manuelle requise", "Installation")
                success, message = self.proxmox_handler.install_qemu_agent_windows(self.vm_info)
                self.installation_complete.emit(False, message, self.vm_info)
            else:
                log_error(f"OS non supporté: {self.vm_info['os_type']}", "Installation")
                self.installation_complete.emit(False, f"OS non supporté pour {vm_name}", self.vm_info)
                
        except Exception as e:
            log_error(f"Erreur inattendue dans le thread: {str(e)}", "Installation")
            self.installation_complete.emit(False, f"Erreur inattendue: {str(e)}", self.vm_info)
    
    def install_qemu_agent_simple_sequence(self, vm_info, ssh_credentials):
        """Version simplifiée de l'installation sans dialogues PyQt avec logging détaillé"""
        vm_name = vm_info.get('name', 'VM inconnue')
        node_name = vm_info.get('node')
        vmid = vm_info.get('vmid')
        
        log_vm("Début séquence d'installation complète", vm_name)
        
        try:
            import time
            
            # ÉTAPE 1: Installation du package
            log_step(1, 5, "Installation du package qemu-guest-agent", "Installation")
            success, message = self.proxmox_handler.install_qemu_agent_package_only(vm_info, ssh_credentials)
            
            if not success:
                log_error(f"Échec installation package: {message}", "Installation")
                return False, f"Échec installation package: {message}"
            
            log_success("Package qemu-guest-agent installé", "Installation")
            
            # ÉTAPE 2: Activation dans Proxmox
            log_step(2, 5, "Activation QEMU Guest Agent dans Proxmox", "Installation")
            if not self.proxmox_handler.enable_qemu_agent_in_config(node_name, vmid):
                log_error("Impossible d'activer l'agent dans la configuration Proxmox", "Installation")
                return False, "Impossible d'activer l'agent dans la configuration Proxmox"
            
            log_success("Agent activé dans la config Proxmox", "Installation")
            
            # ÉTAPE 3: Redémarrage avec méthode robuste
            log_step(3, 5, "Redémarrage à froid de la VM", "Installation")
            log_info("⚠️ La VM sera temporairement indisponible", "Installation")
            
            restart_success, restart_message = self.restart_vm_robust(node_name, vmid, vm_name)
            
            if not restart_success:
                log_error(f"Échec redémarrage: {restart_message}", "Installation")
                return False, f"Échec redémarrage: {restart_message}"
            
            log_success("Redémarrage à froid réussi", "Installation")
            
            # ÉTAPE 4: Démarrage du service
            log_step(4, 5, "Démarrage du service qemu-guest-agent", "Installation")
            log_info("Attente stabilisation de la VM...", "Installation")
            time.sleep(10)  # Attendre que la VM soit stable
            
            service_success, service_message = self.proxmox_handler.start_qemu_agent_service(vm_info, ssh_credentials)
            
            if not service_success:
                log_error(f"Service non démarré: {service_message}", "Installation")
                return False, f"Service non démarré: {service_message}"
            
            log_success("Service qemu-guest-agent démarré", "Installation")
            
            # ÉTAPE 5: Vérification finale
            log_step(5, 5, "Vérification finale", "Installation")
            log_info("Test de l'agent QEMU...", "Installation")
            time.sleep(5)
            
            try:
                self.proxmox_handler.proxmox.nodes(node_name).qemu(vmid).agent.ping.post()
                log_success("Agent QEMU répond correctement", "Installation")
                log_vm("Installation QEMU Agent complètement réussie", vm_name)
                return True, f"Installation complète et agent fonctionnel sur {vm_name}"
            except Exception as e:
                log_info(f"Agent pas encore prêt: {str(e)}", "Installation")
                log_vm("Installation terminée, agent en cours d'initialisation", vm_name)
                return True, f"Installation terminée sur {vm_name}. L'agent devrait être fonctionnel (vérifiez dans quelques minutes)."
                
        except Exception as e:
            log_error(f"Erreur dans la séquence d'installation: {str(e)}", "Installation")
            return False, f"Erreur installation: {str(e)}"
    
    def restart_vm_robust(self, node_name, vmid, vm_name):
        """Redémarrage robuste avec gestion des erreurs et logging détaillé"""
        log_vm("Début redémarrage robuste", vm_name)
        
        try:
            import time
            
            # Tentative d'arrêt
            log_info(f"🔄 Arrêt de {vm_name}...", "Installation")
            
            shutdown_success, shutdown_message = self.proxmox_handler.shutdown_vm_robust(node_name, vmid, vm_name)
            if not shutdown_success:
                log_error(f"Échec arrêt: {shutdown_message}", "Installation")
                return False, shutdown_message
            
            log_success(f"✅ {vm_name} arrêtée", "Installation")
            
            # Petit délai pour s'assurer que l'arrêt est complet
            log_info("Pause sécurité avant redémarrage...", "Installation")
            time.sleep(3)
            
            # Redémarrage
            log_info(f"🚀 Démarrage de {vm_name}...", "Installation")
            
            start_success, start_message = self.proxmox_handler.start_vm_robust(node_name, vmid, vm_name)
            if not start_success:
                log_error(f"Échec démarrage: {start_message}", "Installation")
                return False, start_message
            
            log_success(f"✅ {vm_name} démarrée", "Installation")
            log_vm("Redémarrage à froid terminé avec succès", vm_name)
            return True, f"Redémarrage réussi"
            
        except Exception as e:
            log_error(f"Erreur redémarrage robuste: {str(e)}", "Installation")
            return False, f"Erreur redémarrage: {str(e)}"

class QemuAgentManagerDialog(QDialog):
    def __init__(self, parent=None, proxmox_handler=None):
        super().__init__(parent)
        self.proxmox_handler = proxmox_handler
        self.setWindowTitle("Gestionnaire QEMU Agent")
        self.resize(800, 500)  # Réduit car plus de zone de logs
        self.ssh_credentials = {}
        self.install_threads = []
        self.init_ui()
        self.load_vms_status()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # === HEADER ===
        header_label = QLabel("🔧 Gestionnaire QEMU Agent")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header_label.setFont(header_font)
        layout.addWidget(header_label)
        
        desc_label = QLabel("Gérez l'installation et l'activation de QEMU Agent sur vos VMs")
        desc_label.setStyleSheet("color: #6c757d; margin-bottom: 15px;")
        layout.addWidget(desc_label)
        
        # Info sur les logs
        logs_info = QLabel("📋 Les logs détaillés s'affichent en temps réel dans l'onglet 'Export Projet'")
        logs_info.setStyleSheet("""
            background-color: #e3f2fd;
            color: #1976d2;
            padding: 8px;
            border-radius: 4px;
            border-left: 4px solid #2196f3;
            margin-bottom: 15px;
        """)
        layout.addWidget(logs_info)
        
        # === TABLEAU DES VMs ===
        self.vm_table = QTableWidget()
        self.vm_table.setColumnCount(6)
        self.vm_table.setHorizontalHeaderLabels([
            "VM", "OS", "État", "Agent Activé", "Agent Fonctionne", "Actions"
        ])
        self.vm_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.vm_table)
        
        # === CONTRÔLES ===
        controls_group = QGroupBox("Actions")
        controls_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 Actualiser")
        self.refresh_btn.clicked.connect(self.load_vms_status)
        controls_layout.addWidget(self.refresh_btn)
        
        self.install_selected_btn = QPushButton("⚡ Installer sur sélectionnées")
        self.install_selected_btn.clicked.connect(self.install_on_selected)
        controls_layout.addWidget(self.install_selected_btn)
        
        self.auto_fix_btn = QPushButton("🚀 Auto-réparer tout")
        self.auto_fix_btn.clicked.connect(self.auto_fix_all)
        controls_layout.addWidget(self.auto_fix_btn)
        
        controls_layout.addStretch()
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # === PROGRESSION SIMPLIFIÉE ===
        progress_group = QGroupBox("Progression")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        # Message d'état simple
        self.status_label = QLabel("Prêt")
        self.status_label.setStyleSheet("color: #6c757d; font-style: italic;")
        progress_layout.addWidget(self.status_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # === BOUTONS ===
        button_layout = QHBoxLayout()
        
        self.close_btn = QPushButton("Fermer")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def load_vms_status(self):
        """Charge le statut de toutes les VMs"""
        if not self.proxmox_handler:
            log_error("Aucun handler Proxmox disponible", "QemuAgent")
            return
        
        self.status_label.setText("Analyse des VMs en cours...")
        log_step(1, 2, "Analyse des VMs et statut QEMU Agent", "QemuAgent")
        
        try:
            vms_detailed = self.proxmox_handler.get_all_vms_with_agent_status()
            log_debug(f"Récupération de {len(vms_detailed)} VMs depuis Proxmox", "QemuAgent")
            
            self.vm_table.setRowCount(len(vms_detailed))
            
            for row, vm in enumerate(vms_detailed):
                vm_name = vm['name']
                log_debug(f"Traitement VM {vm_name} - OS: {vm['os_type']}, Statut: {vm['status']}", "QemuAgent")
                
                # Nom de la VM
                name_item = QTableWidgetItem(vm_name)
                self.vm_table.setItem(row, 0, name_item)
                
                # OS
                os_text = vm['os_type'].title() if vm['os_type'] != 'unknown' else "❓ Inconnu"
                os_item = QTableWidgetItem(os_text)
                self.vm_table.setItem(row, 1, os_item)
                
                # État
                status_text = "🟢 Démarrée" if vm['status'] == 'running' else "🔴 Arrêtée"
                status_item = QTableWidgetItem(status_text)
                self.vm_table.setItem(row, 2, status_item)
                
                # Agent activé
                enabled_text = "✅ Oui" if vm['agent_enabled'] else "❌ Non"
                enabled_item = QTableWidgetItem(enabled_text)
                self.vm_table.setItem(row, 3, enabled_item)
                
                # Agent fonctionne
                if vm['status'] != 'running':
                    running_text = "⏸️ VM arrêtée"
                elif vm['agent_running']:
                    running_text = f"✅ Oui (IP: {vm['ip']})"
                    log_debug(f"VM {vm_name} - Agent fonctionnel sur IP {vm['ip']}", "QemuAgent")
                else:
                    running_text = "❌ Non"
                    log_debug(f"VM {vm_name} - Agent non fonctionnel", "QemuAgent")
                    
                running_item = QTableWidgetItem(running_text)
                self.vm_table.setItem(row, 4, running_item)
                
                # Bouton d'action
                if vm['can_install_agent'] and vm['status'] == 'running' and not vm['agent_running']:
                    action_btn = QPushButton("🔧 Installer + Redémarrer")
                    action_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #007bff;
                            color: white;
                            border: none;
                            padding: 5px 10px;
                            border-radius: 3px;
                            font-weight: bold;
                        }
                        QPushButton:hover {
                            background-color: #0056b3;
                        }
                    """)
                    action_btn.clicked.connect(lambda checked, v=vm: self.install_single_vm(v))
                    self.vm_table.setCellWidget(row, 5, action_btn)
                    log_debug(f"VM {vm_name} - Bouton d'installation disponible", "QemuAgent")
                else:
                    action_item = QTableWidgetItem("✅ OK" if vm['agent_running'] else "⚠️ Manuel")
                    self.vm_table.setItem(row, 5, action_item)
            
            self.vm_table.resizeColumnsToContents()
            self.status_label.setText(f"Analyse terminée - {len(vms_detailed)} VMs trouvées")
            log_step(2, 2, f"Analyse terminée - {len(vms_detailed)} VMs trouvées", "QemuAgent")
            
        except Exception as e:
            self.status_label.setText(f"Erreur: {str(e)}")
            log_error(f"Erreur lors du chargement des VMs: {str(e)}", "QemuAgent")

    def install_single_vm(self, vm_info):
        """Installe QEMU Agent sur une VM spécifique avec redémarrage automatique"""
        vm_name = vm_info.get('name', 'VM inconnue')
        log_vm(f"Début processus d'installation QEMU Agent", vm_name)
        
        # Pour Linux, demander les credentials SSH
        if vm_info['os_type'] == 'linux':
            log_debug("Demande des credentials SSH pour VM Linux", "QemuAgent")
            
            credentials_dialog = SSHCredentialsDialog(self, vm_info)
            if credentials_dialog.exec() != QDialog.DialogCode.Accepted:
                log_info(f"Installation annulée par l'utilisateur", "QemuAgent")
                return  # Utilisateur a annulé
            
            ssh_credentials = credentials_dialog.get_credentials()
            log_debug(f"Credentials SSH obtenus pour {ssh_credentials['username']}@{ssh_credentials['ip']}", "QemuAgent")
            
            # Demander confirmation pour le redémarrage AVANT de lancer le thread
            log_debug("Demande de confirmation pour le redémarrage", "QemuAgent")
            
            reply = QMessageBox.question(
                self, 
                "Confirmation installation", 
                f"""Installation complète de QEMU Agent sur {vm_name}

ÉTAPES QUI SERONT EFFECTUÉES :
1️⃣ Installation du package qemu-guest-agent
2️⃣ Activation de l'option dans Proxmox  
3️⃣ Redémarrage à froid de la VM (arrêt/démarrage)
4️⃣ Démarrage du service qemu-guest-agent
5️⃣ Vérification que l'agent fonctionne

⚠️ La VM sera temporairement indisponible pendant le redémarrage.
📋 Les logs détaillés s'afficheront dans l'onglet 'Export Projet'

Continuer l'installation ?""",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                log_info(f"Installation annulée par l'utilisateur après confirmation", "QemuAgent")
                return  # Utilisateur a annulé
            
            log_success(f"Installation confirmée par l'utilisateur", "QemuAgent")
        
        else:
            ssh_credentials = None
            log_debug("VM Windows détectée - pas de credentials SSH nécessaires", "QemuAgent")
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Mode indéterminé
        self.status_label.setText(f"Installation en cours sur {vm_name}...")
        
        # Désactiver tous les boutons pendant l'installation
        button_count = 0
        for row in range(self.vm_table.rowCount()):
            widget = self.vm_table.cellWidget(row, 5)
            if widget and isinstance(widget, QPushButton):
                widget.setEnabled(False)
                button_count += 1
        
        log_debug(f"Désactivation de {button_count} boutons pendant l'installation", "QemuAgent")
        
        # Lancer le thread avec auto_restart=True puisque confirmé
        log_info(f"Lancement du thread d'installation pour {vm_name}", "QemuAgent")
        thread = QemuAgentInstallThread(self.proxmox_handler, vm_info, ssh_credentials, auto_restart=True)
        thread.installation_complete.connect(self.on_installation_complete)
        self.install_threads.append(thread)
        thread.start()

    def install_on_selected(self):
        """Installe QEMU Agent sur les VMs sélectionnées"""
        selected_rows = self.vm_table.selectionModel().selectedRows()
        if not selected_rows:
            log_warning("Aucune VM sélectionnée pour installation groupée", "QemuAgent")
            QMessageBox.information(self, "Sélection", "Veuillez sélectionner au moins une VM")
            return
        
        log_info(f"{len(selected_rows)} VMs sélectionnées pour installation groupée", "QemuAgent")
        # TODO: Implémenter l'installation groupée avec redémarrage
        QMessageBox.information(self, "En développement", 
                              "Fonctionnalité en cours de développement.\nUtilisez l'installation individuelle en attendant.")

    def auto_fix_all(self):
        """Répare automatiquement toutes les VMs qui ont des problèmes d'agent"""
        log_info("Tentative de réparation automatique de toutes les VMs", "QemuAgent")
        # TODO: Implémenter la réparation automatique
        QMessageBox.information(self, "En développement", 
                              "Fonctionnalité en cours de développement.\nUtilisez l'installation individuelle en attendant.")

    def on_installation_complete(self, success, message, vm_info):
        """Appelé quand une installation se termine"""
        vm_name = vm_info.get('name', 'VM inconnue')
        
        self.progress_bar.setVisible(False)
        
        # Réactiver tous les boutons
        button_count = 0
        for row in range(self.vm_table.rowCount()):
            widget = self.vm_table.cellWidget(row, 5)
            if widget and isinstance(widget, QPushButton):
                widget.setEnabled(True)
                button_count += 1
        
        log_debug(f"Réactivation de {button_count} boutons après installation", "QemuAgent")
        
        if success:
            log_success(f"Installation terminée avec succès: {message}", "QemuAgent")
            log_vm("Installation QEMU Agent réussie", vm_name)
            self.status_label.setText(f"Installation réussie sur {vm_name}")
            
            # Actualiser le tableau pour refléter les changements
            log_debug("Actualisation du tableau des VMs", "QemuAgent")
            self.load_vms_status()
        else:
            log_error(f"Installation échouée: {message}", "QemuAgent")
            log_vm("Installation QEMU Agent échouée", vm_name)
            self.status_label.setText(f"Échec installation sur {vm_name}")
        
        # Message de notification
        if success:
            QMessageBox.information(self, "Installation réussie", message)
        else:
            QMessageBox.warning(self, "Installation échouée", message)

    def closeEvent(self, event):
        """Nettoie les threads lors de la fermeture"""
        log_info("Fermeture du gestionnaire QEMU Agent", "QemuAgent")
        
        active_threads = 0
        for thread in self.install_threads:
            if thread.isRunning():
                thread.terminate()
                thread.wait()
                active_threads += 1
        
        if active_threads > 0:
            log_debug(f"Arrêt de {active_threads} threads actifs", "QemuAgent")
        
        event.accept()
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QGroupBox, QComboBox,
    QMessageBox, QHeaderView, QSplitter
)
from PyQt6.QtGui import QColor

class IPAssignmentDialog(QDialog):
    def __init__(self, parent=None, discovered_hosts=None, proxmox_handler=None):
        super().__init__(parent)
        self.discovered_hosts = discovered_hosts or {}
        self.proxmox_handler = proxmox_handler
        self.vm_ip_assignments = {}  # {vmid: ip}
        
        self.setWindowTitle("Assignation IPs aux VMs")
        self.resize(1000, 600)
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # === HEADER ===
        header_label = QLabel("📋 Assignation d'IPs aux machines virtuelles")
        header_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header_label)
        
        desc_label = QLabel("Associez les IPs découvertes aux VMs Proxmox correspondantes")
        desc_label.setStyleSheet("color: #6c757d; margin-bottom: 15px;")
        layout.addWidget(desc_label)
        
        # === CONTENU PRINCIPAL ===
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # === COLONNE GAUCHE: VMs ===
        left_group = QGroupBox("🖥️ Machines virtuelles Proxmox")
        left_layout = QVBoxLayout()
        
        self.vms_table = QTableWidget()
        self.vms_table.setColumnCount(5)
        self.vms_table.setHorizontalHeaderLabels([
            "VM", "Statut", "IP Actuelle", "IP Assignée", "Actions"
        ])
        left_layout.addWidget(self.vms_table)
        
        left_group.setLayout(left_layout)
        main_splitter.addWidget(left_group)
        
        # === COLONNE DROITE: IPs découvertes ===
        right_group = QGroupBox("🔍 IPs découvertes")
        right_layout = QVBoxLayout()
        
        self.hosts_table = QTableWidget()
        self.hosts_table.setColumnCount(4)
        self.hosts_table.setHorizontalHeaderLabels([
            "IP", "Hostname", "OS", "Assignée à"
        ])
        right_layout.addWidget(self.hosts_table)
        
        right_group.setLayout(right_layout)
        main_splitter.addWidget(right_group)
        
        layout.addWidget(main_splitter)
        
        # === CONTRÔLES ===
        controls_layout = QHBoxLayout()
        
        self.auto_assign_button = QPushButton("🤖 Assignation automatique")
        self.auto_assign_button.clicked.connect(self.auto_assign)
        self.auto_assign_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        controls_layout.addWidget(self.auto_assign_button)
        
        self.clear_button = QPushButton("🗑️ Effacer assignations")
        self.clear_button.clicked.connect(self.clear_assignments)
        controls_layout.addWidget(self.clear_button)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # === BOUTONS ===
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        button_layout.addStretch()
        
        self.apply_button = QPushButton("Appliquer les assignations")
        self.apply_button.clicked.connect(self.apply_assignments)
        self.apply_button.setStyleSheet("""
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
        button_layout.addWidget(self.apply_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def load_data(self):
        """Charge les données des VMs et des hôtes découverts"""
        if not self.proxmox_handler:
            return
        
        # Charger les VMs
        vms = self.proxmox_handler.list_vms()
        self.vms_table.setRowCount(len(vms))
        
        for row, vm in enumerate(vms):
            vm_name = vm.get('name', f"VM-{vm['vmid']}")
            vm_status = vm.get('status', 'unknown')
            
            # Essayer de récupérer l'IP actuelle
            current_ip = "Non disponible"
            if vm_status == 'running':
                try:
                    current_ip = self.proxmox_handler.get_vm_ip(vm['node'], vm['vmid'])
                except:
                    pass
            
            # Nom VM
            self.vms_table.setItem(row, 0, QTableWidgetItem(vm_name))
            
            # Statut
            status_text = "🟢 Active" if vm_status == 'running' else "🔴 Arrêtée"
            self.vms_table.setItem(row, 1, QTableWidgetItem(status_text))
            
            # IP actuelle
            self.vms_table.setItem(row, 2, QTableWidgetItem(current_ip))
            
            # ComboBox pour assignation
            ip_combo = QComboBox()
            ip_combo.addItem("-- Sélectionner IP --")
            for ip in sorted(self.discovered_hosts.keys()):
                hostname = self.discovered_hosts[ip].get('hostname', '')
                display_text = f"{ip}" + (f" ({hostname})" if hostname and hostname != 'Unknown' else "")
                ip_combo.addItem(display_text, ip)
            
            ip_combo.currentTextChanged.connect(
                lambda text, vmid=vm['vmid'], combo=ip_combo: self.on_ip_assigned(vmid, combo)
            )
            self.vms_table.setCellWidget(row, 3, ip_combo)
            
            # Bouton manuel
            manual_button = QPushButton("✏️")
            manual_button.setToolTip("Saisie manuelle")
            manual_button.clicked.connect(
                lambda checked, vmid=vm['vmid'], row=row: self.manual_ip_entry(vmid, row)
            )
            self.vms_table.setCellWidget(row, 4, manual_button)
        
        # Charger les hôtes découverts
        self.hosts_table.setRowCount(len(self.discovered_hosts))
        
        for row, (ip, host_info) in enumerate(sorted(self.discovered_hosts.items())):
            self.hosts_table.setItem(row, 0, QTableWidgetItem(ip))
            self.hosts_table.setItem(row, 1, QTableWidgetItem(host_info.get('hostname', 'Unknown')))
            self.hosts_table.setItem(row, 2, QTableWidgetItem(host_info.get('os_guess', 'Unknown')))
            self.hosts_table.setItem(row, 3, QTableWidgetItem("Libre"))
        
        # Redimensionner les colonnes
        self.vms_table.resizeColumnsToContents()
        self.hosts_table.resizeColumnsToContents()

    def on_ip_assigned(self, vmid, combo):
        """Appelé quand une IP est assignée à une VM"""
        ip = combo.currentData()
        if ip and ip != "-- Sélectionner IP --":
            # Vérifier si l'IP n'est pas déjà assignée
            for other_vmid, other_ip in self.vm_ip_assignments.items():
                if other_vmid != vmid and other_ip == ip:
                    QMessageBox.warning(self, "IP déjà assignée", 
                                      f"L'IP {ip} est déjà assignée à une autre VM")
                    combo.setCurrentIndex(0)
                    return
            
            self.vm_ip_assignments[vmid] = ip
            self.update_hosts_table()
        else:
            # Retirer l'assignation
            if vmid in self.vm_ip_assignments:
                del self.vm_ip_assignments[vmid]
                self.update_hosts_table()

    def manual_ip_entry(self, vmid, row):
        """Permet la saisie manuelle d'une IP"""
        from PyQt6.QtWidgets import QInputDialog
        
        ip, ok = QInputDialog.getText(self, "Saisie manuelle", 
                                     "Entrez l'adresse IP pour cette VM:")
        if ok and ip:
            try:
                import ipaddress
                ipaddress.IPv4Address(ip)
                
                # Vérifier si l'IP n'est pas déjà assignée
                for other_vmid, other_ip in self.vm_ip_assignments.items():
                    if other_vmid != vmid and other_ip == ip:
                        QMessageBox.warning(self, "IP déjà assignée", 
                                          f"L'IP {ip} est déjà assignée à une autre VM")
                        return
                
                self.vm_ip_assignments[vmid] = ip
                
                # Mettre à jour l'affichage
                combo = self.vms_table.cellWidget(row, 3)
                
                # Ajouter l'IP au combo si elle n'existe pas
                found = False
                for i in range(combo.count()):
                    if combo.itemData(i) == ip:
                        combo.setCurrentIndex(i)
                        found = True
                        break
                
                if not found:
                    combo.addItem(f"{ip} (Manuel)", ip)
                    combo.setCurrentIndex(combo.count() - 1)
                
                self.update_hosts_table()
                
            except Exception as e:
                QMessageBox.warning(self, "IP invalide", f"Adresse IP invalide: {str(e)}")

    def update_hosts_table(self):
        """Met à jour le tableau des hôtes avec les assignations"""
        # Créer un mapping IP -> VM name
        ip_to_vm = {}
        for vmid, ip in self.vm_ip_assignments.items():
            # Trouver le nom de la VM
            for row in range(self.vms_table.rowCount()):
                vm_name_item = self.vms_table.item(row, 0)
                if vm_name_item:
                    ip_to_vm[ip] = vm_name_item.text()
                    break
        
        # Mettre à jour le tableau des hôtes
        for row in range(self.hosts_table.rowCount()):
            ip_item = self.hosts_table.item(row, 0)
            if ip_item:
                ip = ip_item.text()
                assigned_item = self.hosts_table.item(row, 3)
                if ip in ip_to_vm:
                    assigned_item.setText(f"➡️ {ip_to_vm[ip]}")
                    assigned_item.setForeground(QColor("#28a745"))  # Vert pour assigné
                else:
                    assigned_item.setText("Libre")
                    assigned_item.setForeground(QColor("#6c757d"))  # Gris pour libre

    def auto_assign(self):
        """Assignation automatique basée sur la correspondance des hostnames"""
        if not self.discovered_hosts:
            QMessageBox.information(self, "Auto-assignation", "Aucun hôte découvert")
            return
        
        assignments_made = 0
        
        # Parcourir toutes les VMs
        for row in range(self.vms_table.rowCount()):
            vm_name_item = self.vms_table.item(row, 0)
            if not vm_name_item:
                continue
                
            vm_name = vm_name_item.text().lower()
            
            # Chercher une correspondance dans les hôtes découverts
            best_match_ip = None
            best_match_score = 0
            
            for ip, host_info in self.discovered_hosts.items():
                hostname = host_info.get('hostname', '').lower()
                
                # Ignorer si déjà assigné
                if ip in self.vm_ip_assignments.values():
                    continue
                
                # Calcul de score de correspondance
                score = 0
                if hostname and hostname != 'unknown':
                    if vm_name in hostname or hostname in vm_name:
                        score = len(set(vm_name) & set(hostname))
                    
                    if score > best_match_score:
                        best_match_score = score
                        best_match_ip = ip
            
            # Assigner si un bon match est trouvé
            if best_match_ip and best_match_score > 2:
                # Récupérer le vmid (approximation basée sur le tableau)
                try:
                    # Cette partie devrait être améliorée avec une meilleure méthode
                    # pour récupérer le vmid
                    combo = self.vms_table.cellWidget(row, 3)
                    if combo:
                        for i in range(combo.count()):
                            if combo.itemData(i) == best_match_ip:
                                combo.setCurrentIndex(i)
                                assignments_made += 1
                                break
                except:
                    pass
        
        if assignments_made > 0:
            QMessageBox.information(self, "Auto-assignation", 
                                  f"{assignments_made} assignation(s) automatique(s) effectuée(s)")
        else:
            QMessageBox.information(self, "Auto-assignation", 
                                  "Aucune correspondance automatique trouvée")

    def clear_assignments(self):
        """Efface toutes les assignations"""
        self.vm_ip_assignments.clear()
        
        # Remettre tous les combos à la première option
        for row in range(self.vms_table.rowCount()):
            combo = self.vms_table.cellWidget(row, 3)
            if combo:
                combo.setCurrentIndex(0)
        
        self.update_hosts_table()

    def apply_assignments(self):
        """Applique les assignations en mettant à jour l'interface parent"""
        if not self.vm_ip_assignments:
            QMessageBox.information(self, "Assignations", "Aucune assignation à appliquer")
            return
        
        try:
            # Appliquer les assignations
            applied_count = 0
            
            for vmid, ip in self.vm_ip_assignments.items():
                # Ici, on pourrait mettre à jour une structure de données
                # ou déclencher des événements pour informer l'interface principale
                applied_count += 1
            
            QMessageBox.information(self, "Assignations appliquées", 
                                  f"{applied_count} assignation(s) appliquée(s) avec succès")
            
            # Signaler aux composants parents (si nécessaire)
            # self.assignments_applied.emit(self.vm_ip_assignments)
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", 
                               f"Erreur lors de l'application des assignations: {str(e)}")

    def get_assignments(self):
        """Retourne les assignations effectuées"""
        return self.vm_ip_assignments
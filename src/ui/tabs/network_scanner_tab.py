import subprocess
import ipaddress
import threading
import socket
from concurrent.futures import ThreadPoolExecutor
import time
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QProgressBar, QTextEdit,
    QGroupBox, QLineEdit, QCheckBox, QComboBox, QSpinBox,
    QFormLayout, QMessageBox, QSplitter
)
from PyQt6.QtGui import QColor

class NetworkScanThread(QThread):
    """Thread pour scanner le réseau en arrière-plan"""
    scan_progress = pyqtSignal(int, int)  # current, total
    host_found = pyqtSignal(dict)  # informations de l'hôte trouvé
    scan_complete = pyqtSignal()
    status_update = pyqtSignal(str)
    
    def __init__(self, subnets, check_ssh=True, check_rdp=False):
        super().__init__()
        self.subnets = subnets
        self.check_ssh = check_ssh
        self.check_rdp = check_rdp
        self.total_hosts = 0
        self.current_host = 0
    
    def ping_host(self, ip):
        """Ping une IP spécifique"""
        try:
            # Windows
            result = subprocess.run(['ping', '-n', '1', '-w', '1000', str(ip)], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                return True
        except:
            try:
                # Linux/Mac
                result = subprocess.run(['ping', '-c', '1', '-W', '1', str(ip)], 
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    return True
            except:
                pass
        return False
    
    def check_port(self, ip, port, timeout=2):
        """Vérifie si un port est ouvert"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def get_hostname(self, ip):
        """Tente de résoudre le nom d'hôte"""
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname
        except:
            return "Unknown"
    
    def scan_host(self, ip):
        """Scan complet d'un hôte"""
        if not self.ping_host(ip):
            return None
        
        # Hôte actif, collecter les infos
        host_info = {
            "ip": str(ip),
            "hostname": self.get_hostname(str(ip)),
            "ssh": False,
            "rdp": False,
            "web": False,
            "os_guess": "Unknown"
        }
        
        # Vérifier les services
        if self.check_ssh:
            host_info["ssh"] = self.check_port(str(ip), 22)
        
        if self.check_rdp:
            host_info["rdp"] = self.check_port(str(ip), 3389)
        
        # Vérifier HTTP/HTTPS
        host_info["web"] = self.check_port(str(ip), 80) or self.check_port(str(ip), 443)
        
        # Deviner l'OS basé sur les ports ouverts
        if host_info["ssh"] and not host_info["rdp"]:
            host_info["os_guess"] = "Linux"
        elif host_info["rdp"] and not host_info["ssh"]:
            host_info["os_guess"] = "Windows"
        elif host_info["ssh"] and host_info["rdp"]:
            host_info["os_guess"] = "Windows (SSH enabled)"
        
        return host_info
    
    def run(self):
        try:
            # Calculer le nombre total d'hôtes
            all_hosts = []
            for subnet in self.subnets:
                try:
                    network = ipaddress.IPv4Network(subnet, strict=False)
                    all_hosts.extend(list(network.hosts()))
                except Exception as e:
                    self.status_update.emit(f"Erreur subnet {subnet}: {e}")
                    continue
            
            self.total_hosts = len(all_hosts)
            self.status_update.emit(f"Scan de {self.total_hosts} adresses IP...")
            
            def scan_and_report(ip):
                host_info = self.scan_host(ip)
                self.current_host += 1
                self.scan_progress.emit(self.current_host, self.total_hosts)
                
                if host_info:
                    self.host_found.emit(host_info)
            
            # Scan parallèle pour plus de rapidité
            with ThreadPoolExecutor(max_workers=50) as executor:
                futures = [executor.submit(scan_and_report, ip) for ip in all_hosts]
                for future in futures:
                    future.result()
            
            self.scan_complete.emit()
            
        except Exception as e:
            self.status_update.emit(f"Erreur scan: {e}")

class NetworkScannerTab(QWidget):
    def __init__(self, parent=None, proxmox_handler=None):
        super().__init__(parent)
        self.proxmox_handler = proxmox_handler
        self.discovered_hosts = {}
        self.scan_thread = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # === HEADER ===
        header_label = QLabel("🔍 Scanner Réseau")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header_label)
        
        desc_label = QLabel("Découvrez les équipements actifs sur votre réseau")
        desc_label.setStyleSheet("color: #6c757d; margin-bottom: 15px;")
        layout.addWidget(desc_label)
        
        # === CONFIGURATION ===
        config_group = QGroupBox("Configuration du scan")
        config_layout = QFormLayout()
        
        # Sous-réseaux
        self.subnet_input = QLineEdit("192.168.1.0/24")
        self.subnet_input.setPlaceholderText("Ex: 192.168.1.0/24,10.0.0.0/24")
        config_layout.addRow("Sous-réseaux:", self.subnet_input)
        
        # Options de scan
        options_layout = QHBoxLayout()
        self.ssh_checkbox = QCheckBox("SSH (22)")
        self.ssh_checkbox.setChecked(True)
        options_layout.addWidget(self.ssh_checkbox)
        
        self.rdp_checkbox = QCheckBox("RDP (3389)")
        options_layout.addWidget(self.rdp_checkbox)
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "Réseaux courants",
            "Réseau local (192.168.x.x)",
            "Réseau privé (10.x.x.x)",
            "Réseau entreprise (172.16.x.x)"
        ])
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)
        options_layout.addWidget(QLabel("Preset:"))
        options_layout.addWidget(self.preset_combo)
        
        options_layout.addStretch()
        config_layout.addRow("Options:", options_layout)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # === CONTRÔLES ===
        controls_layout = QHBoxLayout()
        
        self.scan_button = QPushButton("🚀 Lancer le scan")
        self.scan_button.clicked.connect(self.start_scan)
        self.scan_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        controls_layout.addWidget(self.scan_button)
        
        self.stop_button = QPushButton("⏹️ Arrêter")
        self.stop_button.clicked.connect(self.stop_scan)
        self.stop_button.setEnabled(False)
        controls_layout.addWidget(self.stop_button)
        
        self.clear_button = QPushButton("🗑️ Effacer")
        self.clear_button.clicked.connect(self.clear_results)
        controls_layout.addWidget(self.clear_button)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # === PROGRESSION ===
        progress_group = QGroupBox("Progression")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Prêt à scanner")
        progress_layout.addWidget(self.status_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # === RÉSULTATS ===
        results_group = QGroupBox("Équipements découverts")
        results_layout = QVBoxLayout()
        
        # Statistiques
        stats_layout = QHBoxLayout()
        self.stats_label = QLabel("Aucun équipement trouvé")
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()
        
        self.assign_button = QPushButton("📋 Assigner aux VMs")
        self.assign_button.clicked.connect(self.assign_to_vms)
        self.assign_button.setEnabled(False)
        stats_layout.addWidget(self.assign_button)
        
        results_layout.addLayout(stats_layout)
        
        # Tableau des résultats
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "IP", "Hostname", "OS", "SSH", "RDP", "Web"
        ])
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSortingEnabled(True)
        results_layout.addWidget(self.results_table)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        self.setLayout(layout)

    def on_preset_changed(self, preset):
        """Change les sous-réseaux selon le preset sélectionné"""
        presets = {
            "Réseaux courants": "192.168.1.0/24,192.168.0.0/24,10.0.0.0/24",
            "Réseau local (192.168.x.x)": "192.168.1.0/24,192.168.0.0/24",
            "Réseau privé (10.x.x.x)": "10.0.0.0/24,10.0.1.0/24",
            "Réseau entreprise (172.16.x.x)": "172.16.0.0/24,172.16.1.0/24"
        }
        
        if preset in presets:
            self.subnet_input.setText(presets[preset])

    def start_scan(self):
        """Lance le scan réseau"""
        subnets_text = self.subnet_input.text().strip()
        if not subnets_text:
            QMessageBox.warning(self, "Configuration", "Veuillez spécifier au moins un sous-réseau")
            return
        
        subnets = [s.strip() for s in subnets_text.split(',') if s.strip()]
        
        # Valider les sous-réseaux
        for subnet in subnets:
            try:
                ipaddress.IPv4Network(subnet, strict=False)
            except Exception as e:
                QMessageBox.warning(self, "Sous-réseau invalide", f"'{subnet}' n'est pas valide: {e}")
                return
        
        # Démarrer le scan
        self.scan_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.assign_button.setEnabled(False)
        self.results_table.setRowCount(0)
        self.discovered_hosts.clear()
        
        self.scan_thread = NetworkScanThread(
            subnets, 
            self.ssh_checkbox.isChecked(), 
            self.rdp_checkbox.isChecked()
        )
        self.scan_thread.scan_progress.connect(self.update_progress)
        self.scan_thread.host_found.connect(self.add_discovered_host)
        self.scan_thread.scan_complete.connect(self.on_scan_complete)
        self.scan_thread.status_update.connect(self.status_label.setText)
        self.scan_thread.start()

    def stop_scan(self):
        """Arrête le scan en cours"""
        if self.scan_thread and self.scan_thread.isRunning():
            self.scan_thread.terminate()
            self.scan_thread.wait()
            self.on_scan_complete()

    def update_progress(self, current, total):
        """Met à jour la barre de progression"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(f"Scan en cours... {current}/{total}")

    def add_discovered_host(self, host_info):
        """Ajoute un hôte découvert au tableau"""
        ip = host_info['ip']
        self.discovered_hosts[ip] = host_info
        
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        
        # IP
        self.results_table.setItem(row, 0, QTableWidgetItem(ip))
        
        # Hostname
        hostname = host_info['hostname'] if host_info['hostname'] != 'Unknown' else ''
        self.results_table.setItem(row, 1, QTableWidgetItem(hostname))
        
        # OS
        os_item = QTableWidgetItem(host_info['os_guess'])
        if 'Linux' in host_info['os_guess']:
            os_item.setForeground(QColor("#28a745"))  # Vert pour Linux
        elif 'Windows' in host_info['os_guess']:
            os_item.setForeground(QColor("#0066cc"))  # Bleu pour Windows
        self.results_table.setItem(row, 2, os_item)
        
        # Services
        self.results_table.setItem(row, 3, QTableWidgetItem("✅" if host_info['ssh'] else "❌"))
        self.results_table.setItem(row, 4, QTableWidgetItem("✅" if host_info['rdp'] else "❌"))
        self.results_table.setItem(row, 5, QTableWidgetItem("✅" if host_info['web'] else "❌"))
        
        # Mettre à jour les stats
        total = len(self.discovered_hosts)
        linux_count = sum(1 for h in self.discovered_hosts.values() if 'Linux' in h['os_guess'])
        windows_count = sum(1 for h in self.discovered_hosts.values() if 'Windows' in h['os_guess'])
        
        self.stats_label.setText(f"🖥️ {total} équipements | 🐧 {linux_count} Linux | 🪟 {windows_count} Windows")
        
        self.results_table.resizeColumnsToContents()

    def on_scan_complete(self):
        """Appelé quand le scan est terminé"""
        self.scan_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.assign_button.setEnabled(len(self.discovered_hosts) > 0)
        
        total = len(self.discovered_hosts)
        self.status_label.setText(f"✅ Scan terminé - {total} équipements découverts")

    def clear_results(self):
        """Efface les résultats"""
        self.results_table.setRowCount(0)
        self.discovered_hosts.clear()
        self.stats_label.setText("Aucun équipement trouvé")
        self.assign_button.setEnabled(False)
        self.status_label.setText("Résultats effacés")

    def assign_to_vms(self):
        """Ouvre le dialog d'assignation aux VMs"""
        if not self.proxmox_handler or not self.proxmox_handler.is_connected():
            QMessageBox.warning(self, "Proxmox", "Connexion Proxmox requise")
            return
        
        from ..dialogs.ip_assignment_dialog import IPAssignmentDialog
        dialog = IPAssignmentDialog(self, self.discovered_hosts, self.proxmox_handler)
        dialog.exec()

    def get_discovered_hosts(self):
        """Retourne les hôtes découverts"""
        return self.discovered_hosts
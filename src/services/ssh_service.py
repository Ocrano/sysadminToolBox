# src/services/ssh_service.py
"""
Service SSH centralisé pour les équipements réseau
Gère les connexions, commandes et parseurs par type d'équipement
"""

import paramiko
import time
import csv
from PyQt6.QtCore import QThread, pyqtSignal

from ..core.logger import log_info, log_debug, log_error, log_success, log_warning


class SSHConnectionService:
    """Service de base pour les connexions SSH"""
    
    def __init__(self):
        self.config = {}
        self.is_configured = False
    
    def configure(self, username, password):
        """Configure les credentials SSH"""
        if not username or not password:
            return False, "Nom d'utilisateur et mot de passe requis"
        
        # Validation basique
        if not username.replace('.', '').replace('-', '').replace('_', '').isalnum():
            return False, "Nom d'utilisateur invalide"
        
        self.config = {
            'username': username,
            'password': password
        }
        self.is_configured = True
        log_success(f"SSH configuré pour utilisateur: {username}", "SSH")
        return True, f"Configuration SSH sauvegardée pour {username}"
    
    def test_connection(self, ip, timeout=10):
        """Test une connexion SSH"""
        if not self.is_configured:
            return False, "SSH non configuré"
        
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                ip,
                username=self.config['username'],
                password=self.config['password'],
                timeout=timeout
            )
            client.close()
            return True, "Connexion SSH réussie"
        except Exception as e:
            return False, f"Échec connexion SSH: {str(e)}"
    
    def execute_command(self, ip, command, timeout=30):
        """Exécute une commande SSH"""
        if not self.is_configured:
            return False, "SSH non configuré", ""
        
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                ip,
                username=self.config['username'],
                password=self.config['password'],
                timeout=10
            )
            
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
            
            # Attendre la completion
            start_time = time.time()
            while not stdout.channel.exit_status_ready():
                if time.time() - start_time > timeout:
                    break
                time.sleep(0.1)
            
            output = stdout.read().decode('utf-8', errors='ignore')
            error = stderr.read().decode('utf-8', errors='ignore')
            
            client.close()
            
            if error:
                return False, error, output
            else:
                return True, "Commande exécutée", output
                
        except Exception as e:
            return False, f"Erreur SSH: {str(e)}", ""


class DeviceCSVService:
    """Service de gestion des équipements via CSV"""
    
    def __init__(self):
        self.devices = []
    
    def import_from_csv(self, file_path):
        """Importe les équipements depuis un CSV"""
        try:
            devices = []
            imported_count = 0
            error_count = 0
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Vérifier colonnes obligatoires
                required_columns = ['hostname', 'ip']
                available_columns = [col.strip().lower() for col in reader.fieldnames]
                
                missing_columns = [col for col in required_columns if col not in available_columns]
                if missing_columns:
                    return False, [], f"Colonnes manquantes: {', '.join(missing_columns)}"
                
                for row_num, row in enumerate(reader, start=2):
                    # Nettoyer et valider
                    hostname = row.get('hostname', '').strip()
                    ip = row.get('ip', '').strip()
                    device_type = row.get('type', 'Generic').strip()
                    description = row.get('description', '').strip()
                    location = row.get('location', '').strip()
                    
                    # Validations
                    if not hostname:
                        log_warning(f"Ligne {row_num}: hostname vide", "CSV")
                        error_count += 1
                        continue
                    
                    if not ip:
                        log_warning(f"Ligne {row_num}: IP vide pour {hostname}", "CSV")
                        error_count += 1
                        continue
                    
                    # Validation IP
                    if not self._validate_ip(ip):
                        log_warning(f"Ligne {row_num}: IP invalide '{ip}' pour {hostname}", "CSV")
                        error_count += 1
                        continue
                    
                    # Vérifier doublons
                    if any(device['hostname'] == hostname for device in devices):
                        log_warning(f"Ligne {row_num}: hostname '{hostname}' en doublon", "CSV")
                        error_count += 1
                        continue
                    
                    if any(device['ip'] == ip for device in devices):
                        log_warning(f"Ligne {row_num}: IP '{ip}' en doublon", "CSV")
                        error_count += 1
                        continue
                    
                    # Ajouter équipement
                    device = {
                        'hostname': hostname,
                        'ip': ip,
                        'type': device_type or 'Generic',
                        'description': description,
                        'location': location
                    }
                    devices.append(device)
                    imported_count += 1
            
            self.devices = devices
            log_success(f"{imported_count} équipements importés depuis CSV", "CSV")
            return True, devices, f"{imported_count} équipements importés, {error_count} erreurs"
            
        except UnicodeDecodeError:
            return False, [], "Erreur d'encodage - utilisez UTF-8"
        except Exception as e:
            log_error(f"Erreur import CSV: {str(e)}", "CSV")
            return False, [], f"Erreur: {str(e)}"
    
    def _validate_ip(self, ip):
        """Valide une adresse IP"""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                if not part.isdigit() or not 0 <= int(part) <= 255:
                    return False
            return True
        except:
            return False
    
    def get_devices_by_type(self, device_type):
        """Filtre les équipements par type"""
        return [d for d in self.devices if device_type.lower() in d['type'].lower()]
    
    def get_device_types_summary(self):
        """Résumé des types d'équipements"""
        type_counts = {}
        for device in self.devices:
            device_type = device['type']
            type_counts[device_type] = type_counts.get(device_type, 0) + 1
        return type_counts


class NetworkCommandParser:
    """Parseur de commandes par type d'équipement"""
    
    @staticmethod
    def get_commands_for_device_type(device_type):
        """Retourne les commandes selon le type d'équipement"""
        commands_map = {
            'cisco': {
                'show_version': ['show version'],
                'show_config': ['show running-config'],
                'show_interfaces': ['show interfaces status', 'show ip interface brief'],
                'show_routes': ['show ip route'],
                'show_mac': ['show mac address-table'],
                'show_power': ['show power', 'show environment power'],
                'show_vlans': ['show vlan brief'],
                'show_cdp': ['show cdp neighbors detail']
            },
            'fortinet': {
                'system_status': ['get system status'],
                'show_config': ['show full-configuration'],
                'show_routes': ['get router info routing-table all'],
                'show_policies': ['show firewall policy'],
                'show_interfaces': ['get system interface'],
                'show_sessions': ['get system session list'],
                'show_performance': ['get system performance status']
            },
            'allied': {
                'show_system': ['show system'],
                'show_config': ['show running-config'],
                'show_interfaces': ['show interface'],
                'show_routes': ['show ip route'],
                'show_switch': ['show switch'],
                'show_vlans': ['show vlan all']
            },
            'stormshield': {
                'system_info': ['system info'],
                'show_config': ['config system global show'],
                'show_routes': ['network route list'],
                'show_rules': ['config firewall policy show'],
                'show_connections': ['monitor connection list'],
                'show_monitor': ['monitor system status']
            },
            'generic': {
                'system_info': ['uname -a', 'uptime', 'whoami'],
                'network_config': ['ip addr show', 'ip route show'],
                'interfaces': ['ifconfig -a', 'netstat -i'],
                'processes': ['ps aux', 'top -n 1'],
                'disk_usage': ['df -h', 'free -h']
            }
        }
        
        device_key = device_type.lower()
        for key in commands_map.keys():
            if key in device_key:
                return commands_map[key]
        
        return commands_map['generic']
    
    @staticmethod
    def parse_command_output(device_type, command, output):
        """Parse la sortie selon le type d'équipement"""
        # Pour l'instant, retourne la sortie brute
        # TODO: Implémenter des parseurs spécialisés
        return {
            'device_type': device_type,
            'command': command,
            'raw_output': output,
            'parsed': None  # À implémenter
        }


class NetworkCommandThread(QThread):
    """Thread pour exécuter des commandes sur multiple équipements"""
    
    command_result = pyqtSignal(str, str, str)  # hostname, command, result
    command_error = pyqtSignal(str, str, str)   # hostname, command, error
    progress_update = pyqtSignal(str)
    
    def __init__(self, ssh_service, devices, commands, device_type):
        super().__init__()
        self.ssh_service = ssh_service
        self.devices = devices
        self.commands = commands
        self.device_type = device_type
    
    def run(self):
        """Exécute les commandes sur tous les équipements"""
        total_devices = len(self.devices)
        
        for i, device in enumerate(self.devices, 1):
            hostname = device.get('hostname', 'Unknown')
            ip = device.get('ip', '')
            
            if not ip:
                self.command_error.emit(hostname, "Connection", "IP address missing")
                continue
            
            self.progress_update.emit(f"[{i}/{total_devices}] Connexion à {hostname} ({ip})...")
            
            # Test connexion
            success, message = self.ssh_service.test_connection(ip)
            if not success:
                self.command_error.emit(hostname, "SSH Connection", message)
                continue
            
            # Exécuter les commandes
            for command in self.commands:
                self.progress_update.emit(f"[{i}/{total_devices}] {hostname}: {command}")
                
                success, message, output = self.ssh_service.execute_command(ip, command)
                
                if success:
                    self.command_result.emit(hostname, command, output)
                else:
                    self.command_error.emit(hostname, command, message)
        
        self.progress_update.emit("Toutes les commandes terminées")


class NetworkService:
    """Service principal pour la gestion réseau"""
    
    def __init__(self):
        self.ssh = SSHConnectionService()
        self.csv = DeviceCSVService()
        self.parser = NetworkCommandParser()
        self.active_threads = []
        
        log_info("NetworkService initialisé", "Network")
    
    def configure_ssh(self, username, password):
        """Configure SSH"""
        return self.ssh.configure(username, password)
    
    def is_ssh_configured(self):
        """Vérifie si SSH est configuré"""
        return self.ssh.is_configured
    
    def import_devices(self, file_path):
        """Importe les équipements"""
        return self.csv.import_from_csv(file_path)
    
    def get_devices(self):
        """Récupère les équipements"""
        return self.csv.devices
    
    def get_device_types_summary(self):
        """Résumé des types"""
        return self.csv.get_device_types_summary()
    
    def get_commands_for_device_type(self, device_type):
        """Récupère les commandes pour un type"""
        return self.parser.get_commands_for_device_type(device_type)
    
    def execute_commands_on_devices(self, commands, device_type=None):
        """Exécute des commandes sur les équipements"""
        if not self.ssh.is_configured:
            return False, "SSH non configuré"
        
        if not self.csv.devices:
            return False, "Aucun équipement chargé"
        
        # Créer et lancer le thread
        thread = NetworkCommandThread(
            self.ssh, 
            self.csv.devices, 
            commands, 
            device_type or "generic"
        )
        
        self.active_threads.append(thread)
        return True, thread
    
    def cleanup_threads(self):
        """Nettoie les threads terminés"""
        active_count = 0
        for thread in self.active_threads:
            if thread.isRunning():
                thread.terminate()
                thread.wait()
                active_count += 1
        
        self.active_threads = []
        if active_count > 0:
            log_debug(f"Arrêt de {active_count} threads SSH", "Network")
# src/handlers/proxmox_handler.py
"""
Gestionnaire Proxmox avec support de la configuration persistante
pour le Connection Manager
"""

from proxmoxer import ProxmoxAPI
import requests
import json
import time
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

# Import du système de logging
try:
    from ..core.logger import log_info, log_debug, log_error, log_success, log_warning
except ImportError:
    # Fallback si le logger n'est pas disponible
    def log_info(msg, module="Proxmox"): print(f"INFO [{module}] {msg}")
    def log_debug(msg, module="Proxmox"): print(f"DEBUG [{module}] {msg}")
    def log_error(msg, module="Proxmox"): print(f"ERROR [{module}] {msg}")
    def log_success(msg, module="Proxmox"): print(f"SUCCESS [{module}] {msg}")
    def log_warning(msg, module="Proxmox"): print(f"WARNING [{module}] {msg}")

# Désactiver les warnings SSL pour les certificats auto-signés
disable_warnings(InsecureRequestWarning)


class ProxmoxConnectionService:
    """Service de connexion Proxmox avec gestion persistante de la configuration"""
    
    def __init__(self):
        self.proxmox = None
        self.connected = False
        self._last_config = None  # Configuration persistante
        self.connection_info = {}
        
        log_info("ProxmoxConnectionService initialisé", "Proxmox")
    
    def configure_connection(self, host, port, username, password, verify_ssl=False):
        """Configure les paramètres de connexion"""
        try:
            self._last_config = {
                'host': host,
                'port': port,
                'username': username,
                'password': password,
                'verify_ssl': verify_ssl
            }
            
            log_info(f"Configuration Proxmox: {username}@{host}:{port}", "Proxmox")
            return True
            
        except Exception as e:
            log_error(f"Erreur configuration Proxmox: {e}", "Proxmox")
            return False
    
    def test_connection(self):
        """Teste la connexion avec la configuration actuelle"""
        if not self._last_config:
            log_error("Aucune configuration disponible", "Proxmox")
            return False
        
        try:
            config = self._last_config
            
            # Créer l'instance ProxmoxAPI
            self.proxmox = ProxmoxAPI(
                config['host'],
                port=config['port'],
                user=config['username'],
                password=config['password'],
                verify_ssl=config['verify_ssl']
            )
            
            # Test simple : récupérer la version
            version_info = self.proxmox.version.get()
            
            if version_info:
                self.connected = True
                self.connection_info = {
                    'version': version_info.get('version', 'Unknown'),
                    'release': version_info.get('release', 'Unknown'),
                    'connected_at': time.time()
                }
                
                log_success(f"Connexion Proxmox réussie - Version: {self.connection_info['version']}", "Proxmox")
                return True
            else:
                log_error("Impossible de récupérer les informations de version", "Proxmox")
                return False
                
        except Exception as e:
            log_error(f"Échec connexion Proxmox: {e}", "Proxmox")
            self.connected = False
            self.proxmox = None
            return False
    
    def disconnect(self):
        """Déconnecte Proxmox"""
        self.connected = False
        self.proxmox = None
        self.connection_info = {}
        log_info("Proxmox déconnecté", "Proxmox")
    
    def is_connected(self):
        """Vérifie si la connexion est active"""
        return self.connected and self.proxmox is not None
    
    def get_connection_info(self):
        """Retourne les informations de connexion"""
        return self.connection_info.copy()
    
    # === API PROXMOX ===
    
    def get_cluster_status(self):
        """Récupère le statut du cluster"""
        if not self.is_connected():
            return None
        
        try:
            cluster_status = self.proxmox.cluster.status.get()
            return cluster_status
        except Exception as e:
            log_error(f"Erreur récupération statut cluster: {e}", "Proxmox")
            return None
    
    def get_nodes(self):
        """Récupère la liste des nœuds"""
        if not self.is_connected():
            return []
        
        try:
            nodes = self.proxmox.nodes.get()
            log_debug(f"{len(nodes)} nœud(s) trouvé(s)", "Proxmox")
            return nodes
        except Exception as e:
            log_error(f"Erreur récupération nœuds: {e}", "Proxmox")
            return []
    
    def list_vms(self):
        """Liste toutes les VMs du cluster"""
        if not self.is_connected():
            return []
        
        try:
            all_vms = []
            nodes = self.get_nodes()
            
            for node in nodes:
                node_name = node['node']
                
                # VMs QEMU
                try:
                    qemu_vms = self.proxmox.nodes(node_name).qemu.get()
                    for vm in qemu_vms:
                        vm['node'] = node_name
                        vm['type'] = 'qemu'
                        all_vms.append(vm)
                except Exception as e:
                    log_warning(f"Erreur VMs QEMU sur {node_name}: {e}", "Proxmox")
                
                # Conteneurs LXC
                try:
                    lxc_vms = self.proxmox.nodes(node_name).lxc.get()
                    for vm in lxc_vms:
                        vm['node'] = node_name
                        vm['type'] = 'lxc'
                        all_vms.append(vm)
                except Exception as e:
                    log_warning(f"Erreur conteneurs LXC sur {node_name}: {e}", "Proxmox")
            
            log_debug(f"{len(all_vms)} VM(s) trouvée(s) au total", "Proxmox")
            return all_vms
            
        except Exception as e:
            log_error(f"Erreur listage VMs: {e}", "Proxmox")
            return []
    
    def get_linux_vms(self):
        """Récupère les VMs Linux actives"""
        if not self.is_connected():
            return []
        
        try:
            all_vms = self.list_vms()
            linux_vms = []
            
            for vm in all_vms:
                if vm.get('status') == 'running':
                    # Essayer de récupérer l'IP via l'agent QEMU
                    try:
                        if vm.get('type') == 'qemu':
                            node_name = vm['node']
                            vmid = vm['vmid']
                            
                            # Récupérer les interfaces réseau
                            network_info = self.proxmox.nodes(node_name).qemu(vmid).agent('network-get-interfaces').get()
                            
                            # Extraire l'IP principale
                            ip_address = None
                            if 'result' in network_info:
                                for interface in network_info['result']:
                                    if interface.get('name') != 'lo' and 'ip-addresses' in interface:
                                        for ip_info in interface['ip-addresses']:
                                            if ip_info.get('ip-address-type') == 'ipv4':
                                                ip_address = ip_info.get('ip-address')
                                                break
                                    if ip_address:
                                        break
                            
                            if ip_address:
                                vm['ip'] = ip_address
                                linux_vms.append(vm)
                                
                    except Exception:
                        # Si l'agent n'est pas disponible, ajouter quand même la VM
                        vm['ip'] = 'N/A'
                        linux_vms.append(vm)
            
            log_debug(f"{len(linux_vms)} VM(s) Linux active(s) trouvée(s)", "Proxmox")
            return linux_vms
            
        except Exception as e:
            log_error(f"Erreur scan VMs Linux: {e}", "Proxmox")
            return []
    
    def get_node_status(self):
        """Récupère le statut détaillé des nœuds"""
        if not self.is_connected():
            return []
        
        try:
            nodes = self.get_nodes()
            detailed_status = []
            
            for node in nodes:
                node_name = node['node']
                
                try:
                    # Récupérer les statistiques du nœud
                    status = self.proxmox.nodes(node_name).status.get()
                    
                    detailed_status.append({
                        'node': node_name,
                        'status': node.get('status', 'unknown'),
                        'cpu': status.get('cpu', 0),
                        'mem_used': status.get('memory', {}).get('used', 0),
                        'mem_total': status.get('memory', {}).get('total', 0),
                        'uptime': status.get('uptime', 0),
                        'load': status.get('loadavg', [0, 0, 0])
                    })
                    
                except Exception as e:
                    log_warning(f"Erreur statut du nœud {node_name}: {e}", "Proxmox")
                    detailed_status.append({
                        'node': node_name,
                        'status': 'error',
                        'cpu': 0,
                        'mem_used': 0,
                        'mem_total': 0,
                        'uptime': 0,
                        'load': [0, 0, 0]
                    })
            
            log_debug(f"Statut de {len(detailed_status)} nœud(s) récupéré", "Proxmox")
            return detailed_status
            
        except Exception as e:
            log_error(f"Erreur récupération statut nœuds: {e}", "Proxmox")
            return []
    
    def get_storage_info(self):
        """Récupère les informations de stockage"""
        if not self.is_connected():
            return []
        
        try:
            nodes = self.get_nodes()
            storage_info = []
            
            for node in nodes:
                node_name = node['node']
                
                try:
                    # Récupérer les stockages du nœud
                    storages = self.proxmox.nodes(node_name).storage.get()
                    
                    for storage in storages:
                        storage_name = storage['storage']
                        
                        try:
                            # Récupérer les détails du stockage
                            storage_status = self.proxmox.nodes(node_name).storage(storage_name).status.get()
                            
                            storage_info.append({
                                'node': node_name,
                                'storage': storage_name,
                                'type': storage.get('type', 'unknown'),
                                'total': storage_status.get('total', 0),
                                'used': storage_status.get('used', 0),
                                'available': storage_status.get('avail', 0),
                                'active': storage.get('active', 0) == 1
                            })
                            
                        except Exception as e:
                            log_warning(f"Erreur détails stockage {storage_name} sur {node_name}: {e}", "Proxmox")
                            storage_info.append({
                                'node': node_name,
                                'storage': storage_name,
                                'type': storage.get('type', 'unknown'),
                                'total': 0,
                                'used': 0,
                                'available': 0,
                                'active': storage.get('active', 0) == 1
                            })
                            
                except Exception as e:
                    log_warning(f"Erreur stockages du nœud {node_name}: {e}", "Proxmox")
            
            log_debug(f"{len(storage_info)} stockage(s) analysé(s)", "Proxmox")
            return storage_info
            
        except Exception as e:
            log_error(f"Erreur récupération infos stockage: {e}", "Proxmox")
            return []
    
    def get_vm_details(self, node, vmid, vm_type='qemu'):
        """Récupère les détails d'une VM spécifique"""
        if not self.is_connected():
            return None
        
        try:
            if vm_type == 'qemu':
                vm_config = self.proxmox.nodes(node).qemu(vmid).config.get()
                vm_status = self.proxmox.nodes(node).qemu(vmid).status.current.get()
            else:  # lxc
                vm_config = self.proxmox.nodes(node).lxc(vmid).config.get()
                vm_status = self.proxmox.nodes(node).lxc(vmid).status.current.get()
            
            return {
                'config': vm_config,
                'status': vm_status
            }
            
        except Exception as e:
            log_error(f"Erreur détails VM {vmid} sur {node}: {e}", "Proxmox")
            return None
    
    def start_vm(self, node, vmid, vm_type='qemu'):
        """Démarre une VM"""
        if not self.is_connected():
            return False
        
        try:
            if vm_type == 'qemu':
                self.proxmox.nodes(node).qemu(vmid).status.start.post()
            else:  # lxc
                self.proxmox.nodes(node).lxc(vmid).status.start.post()
            
            log_success(f"VM {vmid} démarrée sur {node}", "Proxmox")
            return True
            
        except Exception as e:
            log_error(f"Erreur démarrage VM {vmid} sur {node}: {e}", "Proxmox")
            return False
    
    def stop_vm(self, node, vmid, vm_type='qemu'):
        """Arrête une VM"""
        if not self.is_connected():
            return False
        
        try:
            if vm_type == 'qemu':
                self.proxmox.nodes(node).qemu(vmid).status.stop.post()
            else:  # lxc
                self.proxmox.nodes(node).lxc(vmid).status.stop.post()
            
            log_success(f"VM {vmid} arrêtée sur {node}", "Proxmox")
            return True
            
        except Exception as e:
            log_error(f"Erreur arrêt VM {vmid} sur {node}: {e}", "Proxmox")
            return False
    
    def restart_vm(self, node, vmid, vm_type='qemu'):
        """Redémarre une VM"""
        if not self.is_connected():
            return False
        
        try:
            if vm_type == 'qemu':
                self.proxmox.nodes(node).qemu(vmid).status.reboot.post()
            else:  # lxc
                self.proxmox.nodes(node).lxc(vmid).status.reboot.post()
            
            log_success(f"VM {vmid} redémarrée sur {node}", "Proxmox")
            return True
            
        except Exception as e:
            log_error(f"Erreur redémarrage VM {vmid} sur {node}: {e}", "Proxmox")
            return False


class ProxmoxService:
    """Service principal Proxmox - Wrapper autour de ProxmoxConnectionService"""
    
    def __init__(self):
        self.connection_service = ProxmoxConnectionService()
        log_info("ProxmoxService principal initialisé", "Proxmox")
    
    # === MÉTHODES DE CONNEXION ===
    
    def configure_connection(self, host, port, username, password, verify_ssl=False):
        """Configure la connexion Proxmox"""
        return self.connection_service.configure_connection(host, port, username, password, verify_ssl)
    
    def test_connection(self):
        """Teste la connexion"""
        return self.connection_service.test_connection()
    
    def disconnect(self):
        """Déconnecte"""
        return self.connection_service.disconnect()
    
    def is_connected(self):
        """Vérifie si connecté"""
        return self.connection_service.is_connected()
    
    def get_connection_info(self):
        """Informations de connexion"""
        return self.connection_service.get_connection_info()
    
    # === DÉLÉGATION DES MÉTHODES API ===
    
    def get_cluster_status(self):
        """Statut du cluster"""
        return self.connection_service.get_cluster_status()
    
    def get_nodes(self):
        """Liste des nœuds"""
        return self.connection_service.get_nodes()
    
    def list_vms(self):
        """Liste des VMs"""
        return self.connection_service.list_vms()
    
    def get_linux_vms(self):
        """VMs Linux actives"""
        return self.connection_service.get_linux_vms()
    
    def get_node_status(self):
        """Statut détaillé des nœuds"""
        return self.connection_service.get_node_status()
    
    def get_storage_info(self):
        """Informations de stockage"""
        return self.connection_service.get_storage_info()
    
    def get_vm_details(self, node, vmid, vm_type='qemu'):
        """Détails d'une VM"""
        return self.connection_service.get_vm_details(node, vmid, vm_type)
    
    def start_vm(self, node, vmid, vm_type='qemu'):
        """Démarre une VM"""
        return self.connection_service.start_vm(node, vmid, vm_type)
    
    def stop_vm(self, node, vmid, vm_type='qemu'):
        """Arrête une VM"""
        return self.connection_service.stop_vm(node, vmid, vm_type)
    
    def restart_vm(self, node, vmid, vm_type='qemu'):
        """Redémarre une VM"""
        return self.connection_service.restart_vm(node, vmid, vm_type)
    
    # === PROPRIÉTÉS POUR COMPATIBILITÉ ===
    
    @property
    def _last_config(self):
        """Configuration persistante pour le contrôleur"""
        return self.connection_service._last_config
    
    @property
    def proxmox(self):
        """Accès direct à l'instance ProxmoxAPI"""
        return self.connection_service.proxmox
    
    # === MÉTHODES AVANCÉES (pour futures fonctionnalités) ===
    
    def get_cluster_resources(self):
        """Récupère toutes les ressources du cluster"""
        if not self.is_connected():
            return []
        
        try:
            resources = self.connection_service.proxmox.cluster.resources.get()
            log_debug(f"{len(resources)} ressource(s) cluster récupérée(s)", "Proxmox")
            return resources
        except Exception as e:
            log_error(f"Erreur ressources cluster: {e}", "Proxmox")
            return []
    
    def get_vm_snapshots(self, node, vmid, vm_type='qemu'):
        """Récupère les snapshots d'une VM"""
        if not self.is_connected():
            return []
        
        try:
            if vm_type == 'qemu':
                snapshots = self.connection_service.proxmox.nodes(node).qemu(vmid).snapshot.get()
            else:  # lxc
                snapshots = self.connection_service.proxmox.nodes(node).lxc(vmid).snapshot.get()
            
            log_debug(f"{len(snapshots)} snapshot(s) trouvé(s) pour VM {vmid}", "Proxmox")
            return snapshots
            
        except Exception as e:
            log_error(f"Erreur snapshots VM {vmid}: {e}", "Proxmox")
            return []
    
    def create_vm_snapshot(self, node, vmid, snapname, description="", vm_type='qemu'):
        """Crée un snapshot de VM"""
        if not self.is_connected():
            return False
        
        try:
            if vm_type == 'qemu':
                self.connection_service.proxmox.nodes(node).qemu(vmid).snapshot.post(
                    snapname=snapname,
                    description=description
                )
            else:  # lxc
                self.connection_service.proxmox.nodes(node).lxc(vmid).snapshot.post(
                    snapname=snapname,
                    description=description
                )
            
            log_success(f"Snapshot '{snapname}' créé pour VM {vmid}", "Proxmox")
            return True
            
        except Exception as e:
            log_error(f"Erreur création snapshot VM {vmid}: {e}", "Proxmox")
            return False
    
    def get_cluster_backup_schedule(self):
        """Récupère la planification des sauvegardes"""
        if not self.is_connected():
            return []
        
        try:
            backup_jobs = self.connection_service.proxmox.cluster.backup.get()
            log_debug(f"{len(backup_jobs)} tâche(s) de sauvegarde trouvée(s)", "Proxmox")
            return backup_jobs
        except Exception as e:
            log_error(f"Erreur planification sauvegardes: {e}", "Proxmox")
            return []
    
    def refresh_connection_info(self):
        """Actualise les informations de connexion"""
        if self.is_connected():
            try:
                # Récupérer les informations à jour
                version_info = self.connection_service.proxmox.version.get()
                if version_info:
                    self.connection_service.connection_info.update({
                        'version': version_info.get('version', 'Unknown'),
                        'release': version_info.get('release', 'Unknown'),
                        'last_refresh': time.time()
                    })
                    log_debug("Informations de connexion actualisées", "Proxmox")
                    return True
            except Exception as e:
                log_warning(f"Erreur actualisation infos connexion: {e}", "Proxmox")
        return False


# Export des classes principales
__all__ = ['ProxmoxService', 'ProxmoxConnectionService']
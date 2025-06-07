# src/services/proxmox_service.py
"""
Service Proxmox divisé en modules spécialisés
Sépare les responsabilités: connexion, VMs, infrastructure, QEMU Agent
VERSION CORRIGÉE COMPLÈTE avec toutes les méthodes manquantes
"""

from ..core.logger import log_debug, log_info, log_error, log_success, log_ssh, log_proxmox, log_vm


class ProxmoxConnectionService:
    """Service de gestion des connexions Proxmox"""
    
    def __init__(self):
        self.proxmox = None
        self.nodes = []
        self.connection_info = {}
        log_info("ProxmoxConnectionService initialisé", "Proxmox")
    
    def connect(self, config):
        """Établit la connexion à Proxmox"""
        from proxmoxer import ProxmoxAPI
        
        log_info(f"Connexion à Proxmox {config['ip']}", "Proxmox")
        try:
            self.proxmox = ProxmoxAPI(
                config['ip'],
                user=config['user'],
                password=config['password'],
                verify_ssl=False
            )
            self.nodes = [node['node'] for node in self.proxmox.nodes.get()]
            self.connection_info = config.copy()
            log_success(f"Proxmox connecté - {len(self.nodes)} nœud(s): {', '.join(self.nodes)}", "Proxmox")
            return True
        except Exception as e:
            log_error(f"Connexion échouée à {config['ip']}: {e}", "Proxmox")
            return False
    
    def disconnect(self):
        """Ferme la connexion Proxmox"""
        log_info("Déconnexion Proxmox", "Proxmox")
        self.proxmox = None
        self.nodes = []
        self.connection_info = {}
    
    def is_connected(self):
        """Vérifie si connecté"""
        return self.proxmox is not None
    
    def get_version(self):
        """Récupère la version Proxmox"""
        try:
            if not self.proxmox:
                return "Non connecté"
            version_info = self.proxmox.version.get()
            return version_info.get("version", "N/A")
        except Exception as e:
            log_error(f"Erreur version Proxmox: {e}", "Proxmox")
            return "N/A"


class ProxmoxVMService:
    """Service de gestion des VMs"""
    
    def __init__(self, connection_service):
        self.connection = connection_service
        self._last_vm_count = 0
        self._last_linux_count = 0
    
    def list_all_vms(self):
        """Récupère toutes les VMs"""
        try:
            if not self.connection.is_connected():
                return []
            
            vms = []
            for node in self.connection.proxmox.nodes.get():
                node_name = node['node']
                for vm in self.connection.proxmox.nodes(node_name).qemu.get():
                    vms.append({
                        "vmid": vm.get("vmid"),
                        "name": vm.get("name"),
                        "status": vm.get("status"),
                        "node": node_name
                    })
            
            # Log optimisé
            if len(vms) != self._last_vm_count:
                log_success(f"{len(vms)} VMs trouvées dans le cluster", "VMService")
                self._last_vm_count = len(vms)
            
            return vms
        except Exception as e:
            log_error(f"Erreur récupération VMs: {e}", "VMService")
            return []
    
    def get_linux_vms(self):
        """Récupère les VMs Linux actives avec IPs"""
        linux_vms = []
        if not self.connection.is_connected():
            return linux_vms
            
        try:
            for node_name in self.connection.nodes:
                vms = self.connection.proxmox.nodes(node_name).qemu.get()
                for vm in vms:
                    if vm.get('status') == 'running':
                        try:
                            info = self.connection.proxmox.nodes(node_name).qemu(vm['vmid']).agent.get('os-info')
                            os_name = info.get('name', '').lower()
                            if any(x in os_name for x in ['linux', 'ubuntu', 'debian', 'centos', 'rhel']):
                                vm_ip = self.get_vm_ip(node_name, vm['vmid'])
                                linux_vms.append({
                                    "vmid": vm['vmid'],
                                    "name": vm.get('name', f"VM-{vm['vmid']}"),
                                    "ip": vm_ip,
                                    "node": node_name
                                })
                        except:
                            continue
            
            # Log optimisé
            if len(linux_vms) != self._last_linux_count:
                log_success(f"{len(linux_vms)} VMs Linux actives trouvées", "VMService")
                self._last_linux_count = len(linux_vms)
            
        except Exception as e:
            log_error(f"Erreur scan VMs Linux: {e}", "VMService")
            
        return linux_vms
    
    def get_vm_ip(self, node_name, vmid):
        """Récupère l'IP d'une VM"""
        try:
            interfaces = self.connection.proxmox.nodes(node_name).qemu(vmid).agent.get("network-get-interfaces")
            for iface in interfaces.get('result', []):
                for addr in iface.get("ip-addresses", []):
                    ip = addr.get("ip-address")
                    if ip and not ip.startswith("127.") and not ip.startswith("::") and ":" not in ip:
                        return ip
        except:
            pass
        return "IP non disponible"
    
    def get_vm_status(self, node_name, vmid):
        """Récupère le statut d'une VM"""
        try:
            status = self.connection.proxmox.nodes(node_name).qemu(vmid).status.current.get()
            return status.get('status', 'unknown')
        except:
            return 'unknown'
    
    def start_vm(self, node_name, vmid, vm_name="VM"):
        """Démarre une VM"""
        try:
            self.connection.proxmox.nodes(node_name).qemu(vmid).status.start.post()
            log_info(f"Démarrage de {vm_name} en cours", "VMService")
            return True, f"Démarrage de {vm_name} initié"
        except Exception as e:
            log_error(f"Échec démarrage {vm_name}: {e}", "VMService")
            return False, f"Impossible de démarrer {vm_name}: {str(e)}"
    
    def stop_vm(self, node_name, vmid, vm_name="VM"):
        """Arrête une VM"""
        try:
            self.connection.proxmox.nodes(node_name).qemu(vmid).status.shutdown.post()
            log_info(f"Arrêt de {vm_name} en cours", "VMService")
            return True, f"Arrêt de {vm_name} initié"
        except Exception as e:
            try:
                # Fallback: arrêt forcé
                self.connection.proxmox.nodes(node_name).qemu(vmid).status.stop.post()
                log_info(f"Arrêt forcé de {vm_name}", "VMService")
                return True, f"Arrêt forcé de {vm_name}"
            except Exception as e2:
                log_error(f"Impossible d'arrêter {vm_name}: {str(e2)}", "VMService")
                return False, f"Impossible d'arrêter {vm_name}: {str(e2)}"


class ProxmoxInfrastructureService:
    """Service de gestion de l'infrastructure"""
    
    def __init__(self, connection_service):
        self.connection = connection_service
    
    def get_nodes_status(self):
        """Récupère le statut de tous les nœuds"""
        try:
            if not self.connection.is_connected():
                return []
                
            status_info = []
            for node in self.connection.proxmox.nodes.get():
                node_name = node['node']
                try:
                    status = self.connection.proxmox.nodes(node_name).status.get()
                    cpu = status.get("cpu", 0)
                    mem = status.get("memory", {})
                    mem_total = mem.get("total", 0)
                    mem_used = mem.get("used", 0)
                    uptime = status.get("uptime", 0)
                    
                    status_info.append({
                        "node": node_name,
                        "cpu": cpu,
                        "mem_total": mem_total,
                        "mem_used": mem_used,
                        "uptime": uptime,
                        "status": node.get("status", "unknown")
                    })
                except:
                    continue
            
            log_success(f"Statut de {len(status_info)} nœud(s) récupéré", "InfraService")
            return status_info
        except Exception as e:
            log_error(f"Erreur statut nœuds: {e}", "InfraService")
            return []
    
    def get_storage_info(self):
        """Récupère les informations de stockage"""
        try:
            if not self.connection.is_connected():
                return []
                
            storages_info = []
            for node in self.connection.proxmox.nodes.get():
                node_name = node['node']
                try:
                    storages = self.connection.proxmox.nodes(node_name).storage.get()
                    for storage in storages:
                        storage_detail = self.connection.proxmox.nodes(node_name).storage(storage['storage']).status.get()
                        storages_info.append({
                            "node": node_name,
                            "storage": storage.get("storage"),
                            "type": storage.get("type"),
                            "total": storage_detail.get("total", 0),
                            "used": storage_detail.get("used", 0),
                            "available": storage_detail.get("avail", 0),
                            "enabled": storage.get("shared", False)
                        })
                except:
                    continue
            
            log_success(f"{len(storages_info)} stockage(s) analysé(s)", "InfraService")
            return storages_info
        except Exception as e:
            log_error(f"Erreur stockage: {e}", "InfraService")
            return []


class ProxmoxQemuAgentService:
    """Service de gestion QEMU Agent"""
    
    def __init__(self, connection_service):
        self.connection = connection_service
    
    def get_vm_detailed_status(self, node_name, vmid):
        """Récupère le statut détaillé d'une VM incluant QEMU Agent"""
        try:
            # Configuration VM
            vm_config = self.connection.proxmox.nodes(node_name).qemu(vmid).config.get()
            vm_status = self.connection.proxmox.nodes(node_name).qemu(vmid).status.current.get()
            
            # Agent activé ?
            agent_enabled = vm_config.get('agent', 0) == 1
            
            vm_info = {
                "vmid": vmid,
                "name": vm_config.get('name', f"VM-{vmid}"),
                "status": vm_status.get('status', 'unknown'),
                "node": node_name,
                "agent_enabled": agent_enabled,
                "agent_running": False,
                "ip": "Non disponible",
                "os_type": "unknown",
                "can_install_agent": False
            }
            
            if vm_info["status"] == "running":
                # Test agent
                try:
                    self.connection.proxmox.nodes(node_name).qemu(vmid).agent.ping.post()
                    vm_info["agent_running"] = True
                    vm_info["ip"] = self._get_vm_ip(node_name, vmid)
                    
                    # Détecter OS
                    try:
                        os_info = self.connection.proxmox.nodes(node_name).qemu(vmid).agent.get('os-info')
                        os_name = os_info.get('name', '').lower()
                        if 'windows' in os_name:
                            vm_info["os_type"] = "windows"
                        elif any(x in os_name for x in ['linux', 'ubuntu', 'debian', 'centos', 'rhel']):
                            vm_info["os_type"] = "linux"
                        vm_info["can_install_agent"] = True
                    except:
                        pass
                        
                except:
                    # Agent ne répond pas
                    os_type = vm_config.get('ostype', '')
                    if os_type.startswith('win'):
                        vm_info["os_type"] = "windows"
                        vm_info["can_install_agent"] = True
                    elif os_type.startswith('l') or 'linux' in os_type:
                        vm_info["os_type"] = "linux"
                        vm_info["can_install_agent"] = True
            
            return vm_info
            
        except Exception as e:
            log_error(f"Erreur statut VM {vmid}: {e}", "QemuService")
            return None
    
    def get_all_vms_with_agent_status(self):
        """Récupère toutes les VMs avec statut QEMU Agent"""
        log_info("Analyse des VMs et statut QEMU Agent", "QemuService")
        vms_detailed = []
        
        try:
            for node_name in self.connection.nodes:
                vms = self.connection.proxmox.nodes(node_name).qemu.get()
                for vm in vms:
                    vm_detail = self.get_vm_detailed_status(node_name, vm['vmid'])
                    if vm_detail:
                        vms_detailed.append(vm_detail)
                        
            log_success(f"Analyse terminée - {len(vms_detailed)} VMs analysées", "QemuService")
                        
        except Exception as e:
            log_error(f"Erreur analyse VMs: {e}", "QemuService")
            
        return vms_detailed
    
    def enable_agent_in_config(self, node_name, vmid):
        """Active l'agent dans la config Proxmox"""
        try:
            self.connection.proxmox.nodes(node_name).qemu(vmid).config.put(agent=1)
            log_success(f"Agent QEMU activé pour VM {vmid}", "QemuService")
            return True
        except Exception as e:
            log_error(f"Échec activation agent VM {vmid}: {e}", "QemuService")
            return False
    
    def _get_vm_ip(self, node_name, vmid):
        """Récupère l'IP d'une VM (méthode privée)"""
        try:
            interfaces = self.connection.proxmox.nodes(node_name).qemu(vmid).agent.get("network-get-interfaces")
            for iface in interfaces.get('result', []):
                for addr in iface.get("ip-addresses", []):
                    ip = addr.get("ip-address")
                    if ip and not ip.startswith("127.") and not ip.startswith("::") and ":" not in ip:
                        return ip
        except:
            pass
        return "IP non disponible"
    
    # === NOUVELLES MÉTHODES POUR L'INSTALLATION QEMU AGENT ===
    
    def install_qemu_agent_package_only(self, vm_info, ssh_credentials):
        """Installe uniquement le package qemu-guest-agent via SSH"""
        vm_name = vm_info.get('name', 'VM inconnue')
        ip = ssh_credentials['ip']
        username = ssh_credentials['username']
        password = ssh_credentials['password']
        
        try:
            import paramiko
            
            log_info(f"Connexion SSH à {username}@{ip} pour {vm_name}", "QemuAgent")
            
            # Connexion SSH
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, username=username, password=password, timeout=30)
            
            # Détecter la distribution
            stdin, stdout, stderr = ssh.exec_command('cat /etc/os-release')
            os_release = stdout.read().decode()
            
            log_debug(f"Distribution détectée pour {vm_name}: {os_release[:100]}...", "QemuAgent")
            
            # Commandes d'installation selon la distribution
            if 'ubuntu' in os_release.lower() or 'debian' in os_release.lower():
                commands = [
                    'sudo apt-get update',
                    'sudo apt-get install -y qemu-guest-agent'
                ]
                log_info(f"Installation via APT pour {vm_name}", "QemuAgent")
            elif 'centos' in os_release.lower() or 'rhel' in os_release.lower() or 'rocky' in os_release.lower():
                commands = [
                    'sudo yum install -y qemu-guest-agent'
                ]
                log_info(f"Installation via YUM pour {vm_name}", "QemuAgent")
            elif 'fedora' in os_release.lower():
                commands = [
                    'sudo dnf install -y qemu-guest-agent'
                ]
                log_info(f"Installation via DNF pour {vm_name}", "QemuAgent")
            else:
                ssh.close()
                log_error(f"Distribution non supportée pour {vm_name}: {os_release[:50]}", "QemuAgent")
                return False, f"Distribution non supportée pour {vm_name}"
            
            # Exécuter les commandes
            for cmd in commands:
                log_debug(f"Exécution: {cmd} sur {vm_name}", "QemuAgent")
                stdin, stdout, stderr = ssh.exec_command(cmd)
                exit_status = stdout.channel.recv_exit_status()
                
                if exit_status != 0:
                    error = stderr.read().decode()
                    ssh.close()
                    log_error(f"Échec commande '{cmd}' sur {vm_name}: {error}", "QemuAgent")
                    return False, f"Erreur installation package: {error}"
                else:
                    output = stdout.read().decode()
                    log_debug(f"Commande réussie sur {vm_name}: {output[:200]}...", "QemuAgent")
            
            ssh.close()
            log_success(f"Package qemu-guest-agent installé sur {vm_name}", "QemuAgent")
            return True, f"Package installé sur {vm_name}"
            
        except Exception as e:
            log_error(f"Erreur SSH {vm_name}: {str(e)}", "QemuAgent")
            return False, f"Erreur SSH {vm_name}: {str(e)}"
    
    def start_qemu_agent_service(self, vm_info, ssh_credentials):
        """Démarre le service qemu-guest-agent via SSH"""
        vm_name = vm_info.get('name', 'VM inconnue')
        ip = ssh_credentials['ip']
        username = ssh_credentials['username']
        password = ssh_credentials['password']
        
        try:
            import paramiko
            
            log_info(f"Démarrage du service QEMU Agent sur {vm_name}", "QemuAgent")
            
            # Connexion SSH
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, username=username, password=password, timeout=30)
            
            # Commandes pour démarrer et activer le service
            commands = [
                'sudo systemctl enable qemu-guest-agent',
                'sudo systemctl start qemu-guest-agent',
                'sudo systemctl status qemu-guest-agent --no-pager'
            ]
            
            # Exécuter les commandes
            for i, cmd in enumerate(commands):
                log_debug(f"Exécution: {cmd} sur {vm_name}", "QemuAgent")
                stdin, stdout, stderr = ssh.exec_command(cmd)
                exit_status = stdout.channel.recv_exit_status()
                
                # Pour les deux premières commandes, l'exit status doit être 0
                if i < 2 and exit_status != 0:
                    error = stderr.read().decode()
                    ssh.close()
                    log_error(f"Échec commande '{cmd}' sur {vm_name}: {error}", "QemuAgent")
                    return False, f"Erreur service: {error}"
                else:
                    output = stdout.read().decode()
                    log_debug(f"Sortie commande sur {vm_name}: {output[:200]}...", "QemuAgent")
            
            ssh.close()
            log_success(f"Service qemu-guest-agent démarré sur {vm_name}", "QemuAgent")
            return True, f"Service démarré sur {vm_name}"
            
        except Exception as e:
            log_error(f"Erreur SSH service {vm_name}: {str(e)}", "QemuAgent")
            return False, f"Erreur SSH service {vm_name}: {str(e)}"
    
    def shutdown_vm_robust(self, node_name, vmid, vm_name):
        """Arrêt robuste d'une VM avec fallback"""
        try:
            log_info(f"Arrêt robuste de {vm_name} (ID: {vmid})", "QemuAgent")
            
            # Tentative d'arrêt gracieux
            self.connection.proxmox.nodes(node_name).qemu(vmid).status.shutdown.post()
            log_debug(f"Commande shutdown envoyée à {vm_name}", "QemuAgent")
            
            # Attendre l'arrêt (max 60 secondes)
            import time
            for i in range(12):  # 12 * 5 = 60 secondes
                time.sleep(5)
                status = self.connection.proxmox.nodes(node_name).qemu(vmid).status.current.get()
                current_status = status.get('status')
                log_debug(f"Statut {vm_name} après {(i+1)*5}s: {current_status}", "QemuAgent")
                
                if current_status == 'stopped':
                    log_success(f"Arrêt gracieux de {vm_name} réussi", "QemuAgent")
                    return True, f"Arrêt gracieux de {vm_name} réussi"
            
            # Si toujours en marche, arrêt forcé
            log_warning(f"Timeout arrêt gracieux pour {vm_name}, passage en arrêt forcé", "QemuAgent")
            self.connection.proxmox.nodes(node_name).qemu(vmid).status.stop.post()
            
            # Attendre l'arrêt forcé (max 30 secondes)
            for i in range(6):  # 6 * 5 = 30 secondes
                time.sleep(5)
                status = self.connection.proxmox.nodes(node_name).qemu(vmid).status.current.get()
                current_status = status.get('status')
                log_debug(f"Statut {vm_name} (forcé) après {(i+1)*5}s: {current_status}", "QemuAgent")
                
                if current_status == 'stopped':
                    log_success(f"Arrêt forcé de {vm_name} réussi", "QemuAgent")
                    return True, f"Arrêt forcé de {vm_name} réussi"
            
            log_error(f"Impossible d'arrêter {vm_name} même en mode forcé", "QemuAgent")
            return False, f"Impossible d'arrêter {vm_name}"
            
        except Exception as e:
            log_error(f"Erreur arrêt {vm_name}: {str(e)}", "QemuAgent")
            return False, f"Erreur arrêt {vm_name}: {str(e)}"
    
    def start_vm_robust(self, node_name, vmid, vm_name):
        """Démarrage robuste d'une VM"""
        try:
            log_info(f"Démarrage robuste de {vm_name} (ID: {vmid})", "QemuAgent")
            
            # Démarrer la VM
            self.connection.proxmox.nodes(node_name).qemu(vmid).status.start.post()
            log_debug(f"Commande start envoyée à {vm_name}", "QemuAgent")
            
            # Attendre le démarrage (max 120 secondes)
            import time
            for i in range(24):  # 24 * 5 = 120 secondes
                time.sleep(5)
                status = self.connection.proxmox.nodes(node_name).qemu(vmid).status.current.get()
                current_status = status.get('status')
                log_debug(f"Statut {vm_name} après {(i+1)*5}s: {current_status}", "QemuAgent")
                
                if current_status == 'running':
                    log_success(f"Démarrage de {vm_name} réussi", "QemuAgent")
                    return True, f"Démarrage de {vm_name} réussi"
            
            log_error(f"Timeout démarrage {vm_name} (120s)", "QemuAgent")
            return False, f"Timeout démarrage {vm_name}"
            
        except Exception as e:
            log_error(f"Erreur démarrage {vm_name}: {str(e)}", "QemuAgent")
            return False, f"Erreur démarrage {vm_name}: {str(e)}"


# Classe principale orchestrant tous les services
class ProxmoxService:
    """Service principal Proxmox orchestrant tous les sous-services"""
    
    def __init__(self):
        self.connection = ProxmoxConnectionService()
        self.vms = ProxmoxVMService(self.connection)
        self.infrastructure = ProxmoxInfrastructureService(self.connection)
        self.qemu_agent = ProxmoxQemuAgentService(self.connection)
        
        log_info("ProxmoxService principal initialisé", "Proxmox")
    
    # Méthodes de convenance pour garder la compatibilité
    def connect(self, config):
        return self.connection.connect(config)
    
    def disconnect(self):
        return self.connection.disconnect()
    
    def is_connected(self):
        return self.connection.is_connected()
    
    def get_version(self):
        return self.connection.get_version()
    
    @property
    def nodes(self):
        return self.connection.nodes
    
    # Délégations vers les services spécialisés
    def list_vms(self):
        return self.vms.list_all_vms()
    
    def get_linux_vms(self):
        return self.vms.get_linux_vms()
    
    def get_vm_ip(self, node_name, vmid):
        return self.vms.get_vm_ip(node_name, vmid)
    
    def get_node_status(self):
        return self.infrastructure.get_nodes_status()
    
    def get_storage_info(self):
        return self.infrastructure.get_storage_info()
    
    def get_all_vms_with_agent_status(self):
        return self.qemu_agent.get_all_vms_with_agent_status()
    
    def get_vm_detailed_status(self, node_name, vmid):
        return self.qemu_agent.get_vm_detailed_status(node_name, vmid)
    
    def enable_qemu_agent_in_config(self, node_name, vmid):
        return self.qemu_agent.enable_agent_in_config(node_name, vmid)
    
    # === NOUVELLES DÉLÉGATIONS POUR L'INSTALLATION QEMU AGENT ===
    
    def install_qemu_agent_package_only(self, vm_info, ssh_credentials):
        """Délégation vers le service QEMU Agent"""
        return self.qemu_agent.install_qemu_agent_package_only(vm_info, ssh_credentials)
    
    def start_qemu_agent_service(self, vm_info, ssh_credentials):
        """Délégation vers le service QEMU Agent"""
        return self.qemu_agent.start_qemu_agent_service(vm_info, ssh_credentials)
    
    def shutdown_vm_robust(self, node_name, vmid, vm_name):
        """Délégation vers le service QEMU Agent"""
        return self.qemu_agent.shutdown_vm_robust(node_name, vmid, vm_name)
    
    def start_vm_robust(self, node_name, vmid, vm_name):
        """Délégation vers le service QEMU Agent"""
        return self.qemu_agent.start_vm_robust(node_name, vmid, vm_name)
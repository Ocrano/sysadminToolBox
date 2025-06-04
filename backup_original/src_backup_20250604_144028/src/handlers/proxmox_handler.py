from proxmoxer import ProxmoxAPI
from ..core.logger import log_debug, log_info, log_error, log_success, log_ssh, log_proxmox, log_vm

class ProxmoxHandler:
    def __init__(self):
        self.proxmox = None
        self.nodes = []
        self._last_vm_count = 0  # Cache pour éviter les logs répétitifs
        self._last_linux_count = 0
        log_info("ProxmoxHandler initialisé", "Proxmox")

    def connect(self, config):
        log_info(f"Connexion à Proxmox {config['ip']}", "Proxmox")
        try:
            self.proxmox = ProxmoxAPI(
                config['ip'],
                user=config['user'],
                password=config['password'],
                verify_ssl=False
            )
            self.nodes = [node['node'] for node in self.proxmox.nodes.get()]
            log_success(f"Proxmox connecté - {len(self.nodes)} nœud(s): {', '.join(self.nodes)}", "Proxmox")
            return True
        except Exception as e:
            log_error(f"Connexion échouée à {config['ip']}: {e}", "Proxmox")
            return False

    def get_vm_detailed_status(self, node_name, vmid):
        """Récupère le statut détaillé d'une VM incluant QEMU Agent"""
        try:
            # Configuration de la VM
            vm_config = self.proxmox.nodes(node_name).qemu(vmid).config.get()
            
            # Statut actuel de la VM
            vm_status = self.proxmox.nodes(node_name).qemu(vmid).status.current.get()
            
            # Vérifier si l'agent est activé dans la config
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
                # Tester si l'agent répond
                try:
                    # Test ping de l'agent
                    ping_result = self.proxmox.nodes(node_name).qemu(vmid).agent.ping.post()
                    vm_info["agent_running"] = True
                    
                    # Récupérer l'IP si l'agent fonctionne
                    vm_info["ip"] = self.get_vm_ip(node_name, vmid)
                    
                    # Détecter l'OS
                    try:
                        os_info = self.proxmox.nodes(node_name).qemu(vmid).agent.get('os-info')
                        os_name = os_info.get('name', '').lower()
                        if 'windows' in os_name:
                            vm_info["os_type"] = "windows"
                        elif any(x in os_name for x in ['linux', 'ubuntu', 'debian', 'centos', 'rhel']):
                            vm_info["os_type"] = "linux"
                        vm_info["can_install_agent"] = True
                    except:
                        pass
                        
                except Exception as e:
                    # L'agent ne répond pas
                    vm_info["agent_running"] = False
                    
                    # Essayer de détecter l'OS via la config Proxmox
                    os_type = vm_config.get('ostype', '')
                    if os_type.startswith('win'):
                        vm_info["os_type"] = "windows"
                        vm_info["can_install_agent"] = True
                    elif os_type.startswith('l') or 'linux' in os_type:
                        vm_info["os_type"] = "linux"
                        vm_info["can_install_agent"] = True
            
            return vm_info
            
        except Exception as e:
            log_error(f"Erreur statut VM {vmid}: {e}", "Proxmox")
            return None

    def get_all_vms_with_agent_status(self):
        """Récupère toutes les VMs avec leur statut QEMU Agent"""
        log_info("Analyse des VMs et statut QEMU Agent", "Tools")
        vms_detailed = []
        
        try:
            for node_name in self.nodes:
                vms = self.proxmox.nodes(node_name).qemu.get()
                for vm in vms:
                    vm_detail = self.get_vm_detailed_status(node_name, vm['vmid'])
                    if vm_detail:
                        vms_detailed.append(vm_detail)
                        
            # Log consolidé
            log_success(f"Analyse terminée - {len(vms_detailed)} VMs analysées", "Tools")
                        
        except Exception as e:
            log_error(f"Erreur analyse VMs: {e}", "Tools")
            
        return vms_detailed

    def enable_qemu_agent_in_config(self, node_name, vmid):
        """Active l'agent QEMU dans la configuration de la VM"""
        try:
            # Mettre à jour la configuration pour activer l'agent
            self.proxmox.nodes(node_name).qemu(vmid).config.put(agent=1)
            log_success(f"Agent QEMU activé pour VM {vmid}", "Installation")
            return True
        except Exception as e:
            log_error(f"Échec activation agent VM {vmid}: {e}", "Installation")
            return False

    def shutdown_vm_robust(self, node_name, vmid, vm_name="VM"):
        """Arrêt robuste d'une VM avec fallback sur stop forcé"""
        try:
            import time
            
            # Tentative d'arrêt normal (graceful shutdown)
            try:
                self.proxmox.nodes(node_name).qemu(vmid).status.shutdown.post()
                log_info(f"Arrêt en cours de {vm_name}", "Installation")
            except Exception as e:
                # Si l'arrêt normal échoue, essayer l'arrêt forcé
                try:
                    self.proxmox.nodes(node_name).qemu(vmid).status.stop.post()
                    log_info(f"Arrêt forcé de {vm_name}", "Installation")
                except Exception as e2:
                    log_error(f"Impossible d'arrêter {vm_name}: {str(e2)}", "Installation")
                    return False, f"Impossible d'arrêter {vm_name}: {str(e2)}"
            
            # Attendre l'arrêt effectif avec polling
            max_wait_time = 120  # 2 minutes maximum
            check_interval = 5   # Vérifier toutes les 5 secondes
            elapsed_time = 0
            
            while elapsed_time < max_wait_time:
                try:
                    current_status = self.get_vm_status(node_name, vmid)
                    
                    if current_status == 'stopped':
                        log_success(f"{vm_name} arrêtée avec succès", "Installation")
                        return True, f"{vm_name} arrêtée avec succès"
                    
                    time.sleep(check_interval)
                    elapsed_time += check_interval
                    
                except Exception as e:
                    time.sleep(check_interval)
                    elapsed_time += check_interval
            
            # Si on arrive ici, timeout
            log_error(f"Timeout arrêt de {vm_name}", "Installation")
            return False, f"Timeout - {vm_name} ne s'arrête pas"
            
        except Exception as e:
            log_error(f"Erreur arrêt {vm_name}: {str(e)}", "Installation")
            return False, f"Erreur lors de l'arrêt de {vm_name}: {str(e)}"

    def start_vm_robust(self, node_name, vmid, vm_name="VM"):
        """Démarrage robuste d'une VM avec vérification"""
        try:
            import time
            
            try:
                self.proxmox.nodes(node_name).qemu(vmid).status.start.post()
                log_info(f"Démarrage de {vm_name} en cours", "Installation")
            except Exception as e:
                log_error(f"Échec démarrage {vm_name}: {e}", "Installation")
                return False, f"Impossible de démarrer {vm_name}: {str(e)}"
            
            # Attendre le démarrage effectif
            max_wait_time = 180  # 3 minutes maximum  
            check_interval = 5   # Vérifier toutes les 5 secondes
            elapsed_time = 0
            
            while elapsed_time < max_wait_time:
                try:
                    current_status = self.get_vm_status(node_name, vmid)
                    
                    if current_status == 'running':
                        log_success(f"{vm_name} démarrée avec succès", "Installation")
                        return True, f"{vm_name} démarrée avec succès"
                    
                    time.sleep(check_interval)
                    elapsed_time += check_interval
                    
                except Exception as e:
                    time.sleep(check_interval)
                    elapsed_time += check_interval
            
            # Si on arrive ici, timeout
            log_error(f"Timeout démarrage {vm_name}", "Installation")
            return False, f"Timeout - {vm_name} ne démarre pas"
            
        except Exception as e:
            log_error(f"Erreur démarrage {vm_name}: {str(e)}", "Installation")
            return False, f"Erreur lors du démarrage de {vm_name}: {str(e)}"

    def get_vm_status(self, node_name, vmid):
        """Récupère le statut actuel d'une VM"""
        try:
            status = self.proxmox.nodes(node_name).qemu(vmid).status.current.get()
            return status.get('status', 'unknown')
        except Exception as e:
            return 'unknown'

    def install_qemu_agent_package_only(self, vm_info, ssh_credentials):
        """Installe uniquement le package qemu-guest-agent sans démarrer le service"""
        vm_name = vm_info.get('name', 'VM inconnue')
        vm_ip = ssh_credentials.get('ip', vm_info.get('ip', 'IP non disponible'))
        
        try:
            import paramiko
            import time
            
            if vm_ip in ["Non disponible", "IP non disponible", None, ""]:
                log_error(f"IP non disponible pour {vm_name}", "Installation")
                return False, f"IP non disponible pour {vm_name}"
            
            log_info(f"Connexion SSH à {vm_name} ({vm_ip})", "Installation")
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                vm_ip, 
                username=ssh_credentials['username'], 
                password=ssh_credentials['password'], 
                timeout=15
            )
            
            # Détecter la distribution
            stdin, stdout, stderr = client.exec_command("cat /etc/os-release", timeout=10)
            os_release = stdout.read().decode('utf-8').lower()
            
            # Extraire le nom de la distribution pour le log
            distro_name = "Inconnue"
            if 'ubuntu' in os_release:
                distro_name = "Ubuntu"
            elif 'debian' in os_release:
                distro_name = "Debian"
            elif 'centos' in os_release:
                distro_name = "CentOS"
            elif 'rhel' in os_release:
                distro_name = "RHEL"
            elif 'fedora' in os_release:
                distro_name = "Fedora"
            
            log_info(f"Installation sur {distro_name}", "Installation")
            
            username = ssh_credentials['username'].lower()
            is_root = (username == 'root')
            
            # Commandes pour installer SEULEMENT le package
            commands = []
            
            if is_root:
                if 'ubuntu' in os_release or 'debian' in os_release:
                    commands = [
                        "export DEBIAN_FRONTEND=noninteractive",
                        "apt update",
                        "apt install -y qemu-guest-agent"
                    ]
                elif 'centos' in os_release or 'rhel' in os_release or 'rocky' in os_release or 'fedora' in os_release:
                    commands = [
                        "yum install -y qemu-guest-agent || dnf install -y qemu-guest-agent"
                    ]
            else:
                # Test sudo
                test_stdin, test_stdout, test_stderr = client.exec_command(
                    f"echo '{ssh_credentials['password']}' | sudo -S whoami", 
                    timeout=10
                )
                sudo_result = test_stdout.read().decode('utf-8', errors='ignore')
                
                if 'root' not in sudo_result:
                    log_error(f"Droits sudo insuffisants", "Installation")
                    client.close()
                    return False, f"Droits sudo insuffisants"
                
                if 'ubuntu' in os_release or 'debian' in os_release:
                    commands = [
                        f"echo '{ssh_credentials['password']}' | sudo -S sh -c 'export DEBIAN_FRONTEND=noninteractive && apt update'",
                        f"echo '{ssh_credentials['password']}' | sudo -S apt install -y qemu-guest-agent"
                    ]
                elif 'centos' in os_release or 'rhel' in os_release or 'rocky' in os_release or 'fedora' in os_release:
                    commands = [
                        f"echo '{ssh_credentials['password']}' | sudo -S sh -c 'yum install -y qemu-guest-agent || dnf install -y qemu-guest-agent'"
                    ]
            
            if not commands:
                log_error(f"Distribution {distro_name} non supportée", "Installation")
                client.close()
                return False, f"Distribution {distro_name} non supportée"
            
            # Exécuter les commandes d'installation
            for i, cmd in enumerate(commands):
                stdin, stdout, stderr = client.exec_command(cmd, timeout=120)
                
                start_time = time.time()
                while not stdout.channel.exit_status_ready():
                    if time.time() - start_time > 120:
                        break
                    time.sleep(0.5)
                
                exit_code = stdout.channel.recv_exit_status()
                output = stdout.read().decode('utf-8', errors='ignore')
                error = stderr.read().decode('utf-8', errors='ignore')
                
                if exit_code != 0:
                    if 'already' not in output.lower() and 'already' not in error.lower():
                        log_error(f"Échec installation: {error[:100] if error else 'Erreur inconnue'}", "Installation")
                        client.close()
                        return False, f"Échec installation: {error[:100] if error else 'Erreur inconnue'}"
            
            client.close()
            log_success(f"Package qemu-guest-agent installé sur {vm_name}", "Installation")
            return True, "Package qemu-guest-agent installé avec succès"
            
        except Exception as e:
            log_error(f"Erreur installation sur {vm_name}: {str(e)}", "Installation")
            return False, f"Erreur: {str(e)}"

    def start_qemu_agent_service(self, vm_info, ssh_credentials):
        """Démarre le service qemu-guest-agent après redémarrage"""
        vm_name = vm_info.get('name', 'VM inconnue')
        vm_ip = ssh_credentials.get('ip', vm_info.get('ip', 'IP non disponible'))
        
        try:
            import paramiko
            import time
            
            # Tentatives de reconnexion (la VM peut mettre du temps à être accessible)
            max_attempts = 5
            for attempt in range(max_attempts):
                try:
                    client = paramiko.SSHClient()
                    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    client.connect(
                        vm_ip, 
                        username=ssh_credentials['username'], 
                        password=ssh_credentials['password'], 
                        timeout=10
                    )
                    log_info(f"Reconnexion SSH réussie à {vm_name}", "Installation")
                    break
                except Exception as e:
                    if attempt == max_attempts - 1:
                        log_error(f"Impossible de se reconnecter à {vm_name}", "Installation")
                        return False, f"Impossible de se reconnecter à {vm_name} après redémarrage"
                    time.sleep(10)  # Attendre avant la prochaine tentative
            
            # Détecter la distribution pour les bonnes commandes
            stdin, stdout, stderr = client.exec_command("cat /etc/os-release", timeout=10)
            os_release = stdout.read().decode('utf-8').lower()
            
            username = ssh_credentials['username'].lower()
            is_root = (username == 'root')
            
            # Commandes pour activer et démarrer le service
            if is_root:
                if 'ubuntu' in os_release or 'debian' in os_release:
                    commands = [
                        "systemctl enable qemu-guest-agent",
                        "systemctl start qemu-guest-agent",
                        "systemctl is-active qemu-guest-agent"
                    ]
                elif 'centos' in os_release or 'rhel' in os_release or 'rocky' in os_release or 'fedora' in os_release:
                    commands = [
                        "systemctl enable qemu-guest-agent",
                        "systemctl start qemu-guest-agent", 
                        "systemctl is-active qemu-guest-agent"
                    ]
                else:
                    client.close()
                    log_error("Distribution non supportée pour service", "Installation")
                    return False, "Distribution non supportée pour démarrage service"
            else:
                if 'ubuntu' in os_release or 'debian' in os_release:
                    commands = [
                        f"echo '{ssh_credentials['password']}' | sudo -S systemctl enable qemu-guest-agent",
                        f"echo '{ssh_credentials['password']}' | sudo -S systemctl start qemu-guest-agent",
                        f"echo '{ssh_credentials['password']}' | sudo -S systemctl is-active qemu-guest-agent"
                    ]
                elif 'centos' in os_release or 'rhel' in os_release or 'rocky' in os_release or 'fedora' in os_release:
                    commands = [
                        f"echo '{ssh_credentials['password']}' | sudo -S systemctl enable qemu-guest-agent",
                        f"echo '{ssh_credentials['password']}' | sudo -S systemctl start qemu-guest-agent",
                        f"echo '{ssh_credentials['password']}' | sudo -S systemctl is-active qemu-guest-agent"
                    ]
                else:
                    client.close()
                    log_error("Distribution non supportée pour service", "Installation")
                    return False, "Distribution non supportée pour démarrage service"
            
            # Exécuter les commandes de service
            all_success = True
            
            for i, cmd in enumerate(commands):
                stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
                
                start_time = time.time()
                while not stdout.channel.exit_status_ready():
                    if time.time() - start_time > 30:
                        break
                    time.sleep(0.5)
                
                exit_code = stdout.channel.recv_exit_status()
                output = stdout.read().decode('utf-8', errors='ignore')
                
                # La dernière commande (is-active) doit retourner "active"
                if i == len(commands) - 1:
                    if 'active' in output.lower():
                        log_success(f"Service qemu-guest-agent actif sur {vm_name}", "Installation")
                    else:
                        all_success = False
                        log_error(f"Service pas encore actif sur {vm_name}", "Installation")
                elif exit_code != 0:
                    all_success = False
            
            client.close()
            
            if all_success:
                return True, "Service qemu-guest-agent démarré avec succès"
            else:
                return False, "Service installé mais peut nécessiter quelques minutes pour démarrer"
                
        except Exception as e:
            log_error(f"Erreur démarrage service sur {vm_name}: {str(e)}", "Installation")
            return False, f"Erreur démarrage service: {str(e)}"

    def install_qemu_agent_windows(self, vm_info):
        """Guide pour installer QEMU Agent sur Windows"""
        vm_name = vm_info.get('name', 'VM inconnue')
        log_info(f"Installation manuelle requise pour {vm_name} (Windows)", "Installation")
        # Pour Windows, c'est plus complexe car il faut les ISO tools
        return False, """
        Installation manuelle requise pour Windows:
        1. Télécharger les Virtio drivers depuis le site Proxmox
        2. Monter l'ISO dans la VM Windows
        3. Installer qemu-guest-agent.exe depuis l'ISO
        4. Redémarrer la VM
        
        Ou utiliser PowerShell avec WinRM activé.
        """

    # === MÉTHODES EXISTANTES OPTIMISÉES ===
    def list_vms(self):
        """Récupère la liste de toutes les VMs sur tous les nœuds"""
        try:
            vms = []
            for node in self.proxmox.nodes.get():
                node_name = node['node']
                for vm in self.proxmox.nodes(node_name).qemu.get():
                    vms.append({
                        "vmid": vm.get("vmid"),
                        "name": vm.get("name"),
                        "status": vm.get("status"),
                        "node": node_name
                    })
            
            # Log optimisé - seulement si le nombre a changé
            if len(vms) != self._last_vm_count:
                log_success(f"{len(vms)} VMs trouvées dans le cluster", "Tools")
                self._last_vm_count = len(vms)
            
            return vms
        except Exception as e:
            log_error(f"Erreur récupération VMs: {e}", "Tools")
            return []

    def get_linux_vms(self):
        """Récupère spécifiquement les VMs Linux en cours d'exécution avec leurs IPs"""
        linux_vms = []
        if not self.proxmox:
            log_error("Pas de connexion Proxmox", "Tools")
            return linux_vms
            
        try:
            for node_name in self.nodes:
                vms = self.proxmox.nodes(node_name).qemu.get()
                for vm in vms:
                    if vm.get('status') == 'running':
                        try:
                            info = self.proxmox.nodes(node_name).qemu(vm['vmid']).agent.get('os-info')
                            os_name = info.get('name', '').lower()
                            if 'linux' in os_name or 'ubuntu' in os_name or 'debian' in os_name or 'centos' in os_name or 'rhel' in os_name:
                                vm_ip = self.get_vm_ip(node_name, vm['vmid'])
                                linux_vms.append({
                                    "vmid": vm['vmid'],
                                    "name": vm.get('name', f"VM-{vm['vmid']}"),
                                    "ip": vm_ip,
                                    "node": node_name
                                })
                        except Exception as e:
                            continue
            
            # Log optimisé - seulement si le nombre a changé
            if len(linux_vms) != self._last_linux_count:
                log_success(f"{len(linux_vms)} VMs Linux actives trouvées", "Tools")
                self._last_linux_count = len(linux_vms)
            
        except Exception as e:
            log_error(f"Erreur scan VMs Linux: {e}", "Tools")
            
        return linux_vms

    def get_vm_ip(self, node_name, vmid):
        """Récupère l'adresse IP d'une VM spécifique"""
        try:
            interfaces = self.proxmox.nodes(node_name).qemu(vmid).agent.get("network-get-interfaces")
            for iface in interfaces.get('result', []):
                for addr in iface.get("ip-addresses", []):
                    ip = addr.get("ip-address")
                    if ip and not ip.startswith("127.") and not ip.startswith("::") and ":" not in ip:
                        return ip
        except Exception as e:
            pass
        return "IP non disponible"

    def get_version(self):
        """Récupère la version de Proxmox"""
        try:
            if not self.proxmox:
                return "Non connecté"
            version_info = self.proxmox.version.get()
            version = version_info.get("version", "N/A")
            return version
        except Exception as e:
            log_error(f"Erreur version Proxmox: {e}", "Proxmox")
            return "N/A"

    def get_storage_info(self):
        """Récupère les informations de stockage pour tous les nœuds"""
        try:
            if not self.proxmox:
                return []
                
            storages_info = []
            for node in self.proxmox.nodes.get():
                node_name = node['node']
                try:
                    storages = self.proxmox.nodes(node_name).storage.get()
                    for storage in storages:
                        storage_detail = self.proxmox.nodes(node_name).storage(storage['storage']).status.get()
                        storages_info.append({
                            "node": node_name,
                            "storage": storage.get("storage"),
                            "type": storage.get("type"),
                            "total": storage_detail.get("total", 0),
                            "used": storage_detail.get("used", 0),
                            "available": storage_detail.get("avail", 0),
                            "enabled": storage.get("shared", False)
                        })
                except Exception as e:
                    continue
            
            # Log consolidé
            log_success(f"{len(storages_info)} stockage(s) analysé(s)", "Tools")
            return storages_info
        except Exception as e:
            log_error(f"Erreur stockage: {e}", "Tools")
            return []

    def get_node_status(self):
        """Récupère le statut (CPU, RAM, uptime) de tous les nœuds"""
        try:
            if not self.proxmox:
                return []
                
            status_info = []
            for node in self.proxmox.nodes.get():
                node_name = node['node']
                try:
                    status = self.proxmox.nodes(node_name).status.get()
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
                    
                except Exception as e:
                    continue
            
            # Log consolidé
            log_success(f"Statut de {len(status_info)} nœud(s) récupéré", "Tools")
            return status_info
        except Exception as e:
            log_error(f"Erreur statut nœuds: {e}", "Tools")
            return []

    def is_connected(self):
        """Vérifie si la connexion à Proxmox est active"""
        connected = self.proxmox is not None
        return connected

    def disconnect(self):
        """Ferme la connexion à Proxmox"""
        log_info("Déconnexion Proxmox", "Proxmox")
        self.proxmox = None
        self.nodes = []
        self._last_vm_count = 0
        self._last_linux_count = 0
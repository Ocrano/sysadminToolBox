# src/ui/controllers/main_controller.py
"""
Contrôleur principal pour MainWindow
Gère les interactions entre l'UI et les services
"""

from PyQt6.QtCore import QObject, pyqtSignal
import time
import os

# Import du système de logging
try:
    from ...core.logger import log_info, log_debug, log_error, log_success, log_warning
except ImportError:
    # Fallback si le logger n'est pas disponible
    def log_info(msg, module="Controller"): print(f"INFO [{module}] {msg}")
    def log_debug(msg, module="Controller"): print(f"DEBUG [{module}] {msg}")
    def log_error(msg, module="Controller"): print(f"ERROR [{module}] {msg}")
    def log_success(msg, module="Controller"): print(f"SUCCESS [{module}] {msg}")
    def log_warning(msg, module="Controller"): print(f"WARNING [{module}] {msg}")


class MainController(QObject):
    """Contrôleur principal de l'application"""
    
    # Signaux pour notifier l'UI
    proxmox_connection_changed = pyqtSignal(bool)  # connected
    proxmox_info_updated = pyqtSignal(dict)  # info_dict
    scripts_loaded = pyqtSignal(list)  # script_list
    service_connection_changed = pyqtSignal(str, bool, dict)  # service, connected, info
    
    def __init__(self, git_manager, script_runner, proxmox_handler):
        super().__init__()
        
        # Services injectés
        self.git_manager = git_manager
        self.script_runner = script_runner
        self.proxmox_handler = proxmox_handler
        
        # État de connexion des services
        self.connected_services = {}
        
        log_info("MainController initialisé", "Controller")
    
    # === GESTION PROXMOX ===
    
    def configure_proxmox(self, config):
        """Configure et teste la connexion Proxmox"""
        try:
            log_info("Configuration Proxmox en cours...", "Controller")
            
            # CORRECTION: Utiliser les bonnes clés du dialog
            success = self.proxmox_handler.configure_connection(
                host=config['ip'],        # ← 'ip' au lieu de 'host'
                port=config['port'],
                username=config['user'],  # ← 'user' au lieu de 'username'
                password=config['password'],
                verify_ssl=config.get('verify_ssl', False)
            )
            
            if success:
                # Tester la connexion
                test_result = self.proxmox_handler.test_connection()
                if test_result:
                    log_success("Connexion Proxmox établie", "Controller")
                    
                    # Récupérer les informations
                    info = self.get_proxmox_info()
                    
                    # Marquer comme connecté
                    self.connected_services['Proxmox VE'] = {
                        'connected': True,
                        'info': info,
                        'last_update': time.time()
                    }
                    
                    # Émettre les signaux
                    self.proxmox_connection_changed.emit(True)
                    self.proxmox_info_updated.emit(info)
                    self.service_connection_changed.emit('Proxmox VE', True, info)
                    
                    return True, "Connexion Proxmox réussie"
                else:
                    log_error("Échec du test de connexion Proxmox", "Controller")
                    return False, "Impossible de se connecter à Proxmox. Vérifiez les paramètres."
            else:
                log_error("Échec de la configuration Proxmox", "Controller")
                return False, "Configuration Proxmox échouée"
                
        except Exception as e:
            log_error(f"Erreur configuration Proxmox: {e}", "Controller")
            return False, f"Erreur: {str(e)}"
    
    def disconnect_proxmox(self):
        """Déconnecte Proxmox"""
        try:
            # Marquer comme déconnecté
            if 'Proxmox VE' in self.connected_services:
                del self.connected_services['Proxmox VE']
            
            # Émettre les signaux
            self.proxmox_connection_changed.emit(False)
            self.service_connection_changed.emit('Proxmox VE', False, {})
            
            log_info("Proxmox déconnecté", "Controller")
            return True
            
        except Exception as e:
            log_error(f"Erreur déconnexion Proxmox: {e}", "Controller")
            return False
    
    def get_proxmox_info(self):
        """Récupère les informations Proxmox"""
        try:
            if not self.proxmox_handler.is_connected():
                return {}
            
            # Récupérer les informations du cluster
            cluster_info = self.proxmox_handler.get_cluster_status()
            nodes_info = self.proxmox_handler.get_nodes()
            vms_info = self.proxmox_handler.list_vms()
            
            # Calculer les statistiques
            nodes_count = len(nodes_info) if nodes_info else 0
            total_vms = len(vms_info) if vms_info else 0
            running_vms = len([vm for vm in vms_info if vm.get('status') == 'running']) if vms_info else 0
            
            # Version Proxmox (essayer de la récupérer de manière sécurisée)
            version = "N/A"
            try:
                if nodes_info and len(nodes_info) > 0:
                    first_node = nodes_info[0]
                    # Vérifier que first_node est bien un dictionnaire
                    if isinstance(first_node, dict):
                        version = first_node.get('version', 'N/A')
                    else:
                        log_debug(f"Type inattendu pour first_node: {type(first_node)}", "Controller")
                
                # Alternative: essayer de récupérer la version via connection_info
                if version == "N/A" and self.proxmox_handler.is_connected():
                    connection_info = self.proxmox_handler.get_connection_info()
                    if isinstance(connection_info, dict):
                        version = connection_info.get('version', 'N/A')
                        
            except Exception as version_error:
                log_warning(f"Impossible de récupérer la version: {version_error}", "Controller")
                version = "N/A"
            
            # Nom du cluster (gestion sécurisée)
            cluster_name = "Default"
            try:
                if cluster_info:
                    if isinstance(cluster_info, dict):
                        cluster_name = cluster_info.get('name', 'Default')
                    elif isinstance(cluster_info, list) and len(cluster_info) > 0:
                        # Si cluster_info est une liste, prendre le premier élément
                        first_cluster = cluster_info[0]
                        if isinstance(first_cluster, dict):
                            cluster_name = first_cluster.get('name', 'Default')
            except Exception as cluster_error:
                log_warning(f"Impossible de récupérer le nom du cluster: {cluster_error}", "Controller")
                cluster_name = "Default"
            
            info = {
                'nodes_count': nodes_count,
                'total_vms': total_vms,
                'running_vms': running_vms,
                'version': version,
                'cluster_name': cluster_name,
                'last_update': time.strftime("%H:%M:%S")
            }
            
            log_debug(f"Informations Proxmox récupérées: {info}", "Controller")
            return info
            
        except Exception as e:
            log_error(f"Erreur récupération infos Proxmox: {e}", "Controller")
            return {}
    
    def refresh_proxmox_info(self):
        """Actualise les informations Proxmox"""
        if self.is_proxmox_connected():
            info = self.get_proxmox_info()
            if info:
                # Mettre à jour le cache
                self.connected_services['Proxmox VE']['info'] = info
                self.connected_services['Proxmox VE']['last_update'] = time.time()
                
                # Émettre les signaux
                self.proxmox_info_updated.emit(info)
                self.service_connection_changed.emit('Proxmox VE', True, info)
                
                log_info("Informations Proxmox actualisées", "Controller")
                return True
        return False
    
    def is_proxmox_connected(self):
        """Vérifie si Proxmox est connecté"""
        return ('Proxmox VE' in self.connected_services and 
                self.connected_services['Proxmox VE'].get('connected', False) and
                self.proxmox_handler.is_connected())
    
    # === GESTION DES SERVICES GÉNÉRIQUES ===
    
    def handle_service_connection_request(self, service_name, connect=True):
        """Gère les demandes de connexion/déconnexion des services"""
        log_info(f"Demande de {'connexion' if connect else 'déconnexion'} pour {service_name}", "Controller")
        
        if service_name == "Proxmox VE":
            if connect:
                # Si déjà configuré, se reconnecter
                if hasattr(self.proxmox_handler, '_last_config') and self.proxmox_handler._last_config:
                    config = self.proxmox_handler._last_config
                    # CORRECTION: Adapter les clés pour le reconnexion automatique
                    normalized_config = {
                        'ip': config.get('host', config.get('ip', '')),
                        'port': config.get('port', 8006),
                        'user': config.get('username', config.get('user', '')),
                        'password': config.get('password', ''),
                        'verify_ssl': config.get('verify_ssl', False)
                    }
                    return self.configure_proxmox(normalized_config)
                else:
                    # Pas encore configuré, demander la configuration
                    self.service_connection_changed.emit(service_name, False, {'needs_config': True})
                    return False, "Configuration requise"
            else:
                return self.disconnect_proxmox(), "Déconnexion réussie"
        
        elif service_name == "VMware vSphere":
            if connect:
                # TODO: Implémenter la connexion vSphere
                log_warning("Connexion vSphere pas encore implémentée", "Controller")
                self.service_connection_changed.emit(service_name, False, {'error': 'Non implémenté'})
                return False, "vSphere pas encore supporté"
            else:
                # TODO: Déconnexion vSphere
                return True, "vSphere déconnecté"
        
        else:
            log_error(f"Service inconnu: {service_name}", "Controller")
            return False, f"Service {service_name} non supporté"
    
    def get_service_info(self, service_name):
        """Récupère les informations d'un service"""
        if service_name in self.connected_services:
            return self.connected_services[service_name].get('info', {})
        return {}
    
    def refresh_all_services(self):
        """Actualise tous les services connectés"""
        refreshed_count = 0
        
        for service_name in list(self.connected_services.keys()):
            if service_name == "Proxmox VE":
                if self.refresh_proxmox_info():
                    refreshed_count += 1
            # TODO: Ajouter d'autres services
        
        log_info(f"{refreshed_count} service(s) actualisé(s)", "Controller")
        return refreshed_count
    
    # === GESTION DES SCRIPTS ===
    
    def configure_gitlab_token(self, token):
        """Configure le token GitLab"""
        try:
            success = self.git_manager.configure_token(token)  # Méthode probable du GitLabManager
            if success:
                log_success("Token GitLab configuré", "Controller")
                return True, "Token GitLab enregistré avec succès"
            else:
                log_error("Échec configuration token GitLab", "Controller")
                return False, "Impossible de configurer le token GitLab"
                
        except Exception as e:
            log_error(f"Erreur configuration GitLab: {e}", "Controller")
            return False, f"Erreur: {str(e)}"
    
    def load_scripts_from_gitlab(self):
        """Charge les scripts depuis GitLab"""
        try:
            log_info("Chargement des scripts depuis GitLab...", "Controller")
            scripts = self.git_manager.list_scripts()  # Méthode probable du GitLabManager
            
            if scripts:
                log_success(f"{len(scripts)} script(s) récupéré(s)", "Controller")
                self.scripts_loaded.emit(scripts)
                return scripts
            else:
                log_warning("Aucun script trouvé sur GitLab", "Controller")
                return []
                
        except Exception as e:
            log_error(f"Erreur chargement scripts GitLab: {e}", "Controller")
            return []
    
    def load_local_scripts(self):
        """Charge les scripts locaux"""
        try:
            log_debug("Chargement des scripts locaux", "Controller")
            
            scripts_dir = "scripts"
            if not os.path.exists(scripts_dir):
                log_debug("Dossier scripts inexistant", "Controller")
                return []
            
            scripts = []
            for file in os.listdir(scripts_dir):
                if file.endswith('.ps1'):
                    scripts.append(file)
            
            if scripts:
                log_info(f"{len(scripts)} script(s) local(aux) trouvé(s)", "Controller")
                self.scripts_loaded.emit(scripts)
            else:
                log_debug("Aucun script local trouvé", "Controller")
            
            return scripts
            
        except Exception as e:
            log_error(f"Erreur chargement scripts locaux: {e}", "Controller")
            return []
    
    def run_script(self, script_name):
        """Exécute un script"""
        try:
            log_info(f"Exécution du script: {script_name}", "Controller")
            
            result = self.script_runner.execute_script(script_name)  # Méthode probable du ScriptRunner
            
            if result.get('success', False):
                log_success(f"Script {script_name} exécuté avec succès", "Controller")
                return True, f"Script exécuté:\n{result.get('output', '')}"
            else:
                log_error(f"Échec du script {script_name}: {result.get('error', 'Erreur inconnue')}", "Controller")
                return False, f"Erreur script:\n{result.get('error', 'Erreur inconnue')}"
                
        except Exception as e:
            log_error(f"Erreur exécution script {script_name}: {e}", "Controller")
            return False, f"Erreur: {str(e)}"
    
    # === IMPORT DE DONNÉES ===
    
    def import_ip_plan(self, file_path):
        """Importe un plan d'adressage IP"""
        try:
            log_info(f"Import du plan IP: {file_path}", "Controller")
            
            # Utiliser l'importeur IP
            from ...utils.ip_plan_importer import IPPlanImporter
            importer = IPPlanImporter()
            
            success, data, message = importer.import_from_excel(file_path)
            
            if success:
                log_success(f"Plan IP importé: {len(data)} entrées", "Controller")
                return True, data, message
            else:
                log_error(f"Échec import IP: {message}", "Controller")
                return False, [], message
                
        except Exception as e:
            log_error(f"Erreur import IP: {e}", "Controller")
            return False, [], f"Erreur: {str(e)}"
    
    # === EXPORT DE LOGS ===
    
    def export_logs(self, logs_content, export_type="complete"):
        """Exporte les logs"""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"toolbox_logs_{export_type}_{timestamp}.log"
            
            # En-tête du fichier
            header = f"""# Toolbox PyQt6 - Export des logs
# Type: {export_type}
# Date: {time.strftime("%Y-%m-%d %H:%M:%S")}
# ===================================

"""
            
            export_content = header + logs_content
            
            log_info(f"Logs préparés pour export: {filename}", "Controller")
            return True, export_content, filename
            
        except Exception as e:
            log_error(f"Erreur préparation export logs: {e}", "Controller")
            return False, "", ""
    
    # === PROPRIÉTÉS PUBLIQUES ===
    
    @property
    def proxmox_service(self):
        """Accès au service Proxmox pour compatibilité"""
        return self.proxmox_handler
    
    def get_connected_services_list(self):
        """Retourne la liste des services connectés"""
        return list(self.connected_services.keys())
    
    def get_service_last_update(self, service_name):
        """Retourne le timestamp de dernière mise à jour d'un service"""
        if service_name in self.connected_services:
            return self.connected_services[service_name].get('last_update', 0)
        return 0
# src/ui/controllers/main_controller.py
"""
Contrôleur principal pour la fenêtre MainWindow
Sépare la logique métier de l'interface utilisateur
"""

from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal

from ...core.logger import log_info, log_debug, log_error, log_success, log_warning


class MainController(QObject):
    """Contrôleur principal gérant la logique de la fenêtre principale"""
    
    # Signaux pour communication avec l'UI
    proxmox_connection_changed = pyqtSignal(bool)  # connected
    scripts_loaded = pyqtSignal(list)  # script_list
    logs_updated = pyqtSignal(str)  # log_message
    
    def __init__(self, git_manager, script_runner, proxmox_handler):
        super().__init__()
        self.git_manager = git_manager
        self.script_runner = script_runner
        self.proxmox_handler = proxmox_handler
        
        log_info("MainController initialisé", "Controller")
    
    # === GESTION PROXMOX ===
    def configure_proxmox(self, config):
        """Configure la connexion Proxmox"""
        log_info(f"Configuration Proxmox pour {config['ip']}", "Controller")
        
        connected = self.proxmox_handler.connect(config)
        if connected:
            log_success("Connexion Proxmox établie", "Controller")
            self.proxmox_connection_changed.emit(True)
            return True, "Connexion à Proxmox réussie."
        else:
            log_error("Échec connexion Proxmox", "Controller")
            self.proxmox_connection_changed.emit(False)
            return False, "Échec de la connexion à Proxmox."
    
    def get_proxmox_info(self):
        """Récupère les informations Proxmox pour l'affichage"""
        if not self.proxmox_handler.is_connected():
            return None
        
        try:
            version = self.proxmox_handler.get_version()
            nodes_count = len(self.proxmox_handler.nodes)
            
            # Statistiques VMs
            total_vms = len(self.proxmox_handler.list_vms())
            running_vms = len([vm for vm in self.proxmox_handler.list_vms() if vm['status'] == 'running'])
            
            return {
                'version': version,
                'nodes_count': nodes_count,
                'total_vms': total_vms,
                'running_vms': running_vms
            }
        except Exception as e:
            log_error(f"Erreur récupération info Proxmox: {e}", "Controller")
            return None
    
    # === GESTION SCRIPTS ===
    def configure_gitlab_token(self, token):
        """Configure le token GitLab"""
        if token:
            self.git_manager.set_token(token)
            log_success("Token GitLab configuré", "Controller")
            return True, "Token GitLab mis à jour."
        else:
            log_info("Configuration token GitLab annulée", "Controller")
            return False, "Configuration annulée."
    
    def load_scripts_from_gitlab(self):
        """Charge les scripts depuis GitLab"""
        log_info("Chargement des scripts depuis GitLab", "Controller")
        
        scripts = self.git_manager.fetch_and_download_scripts()
        if scripts:
            log_success(f"{len(scripts)} scripts récupérés depuis GitLab", "Controller")
            script_list = [f"{script} (Téléchargé)" for script in scripts]
        else:
            log_info("Aucun script trouvé sur GitLab", "Controller")
            script_list = ["Aucun script trouvé."]
        
        self.scripts_loaded.emit(script_list)
        return scripts
    
    def load_local_scripts(self):
        """Charge les scripts locaux"""
        import os
        
        log_debug("Chargement des scripts locaux", "Controller")
        
        if not os.path.exists("scripts"):
            log_debug("Dossier scripts inexistant", "Controller")
            return []
        
        local_scripts = []
        script_list = []
        
        for file in os.listdir("scripts"):
            if file.endswith(".ps1"):
                local_scripts.append(file)
                script_list.append(f"{file} (Local)")
                log_debug(f"Script local trouvé: {file}", "Controller")
        
        if local_scripts:
            log_success(f"{len(local_scripts)} scripts locaux chargés", "Controller")
        else:
            log_info("Aucun script local trouvé", "Controller")
        
        self.scripts_loaded.emit(script_list)
        return local_scripts
    
    def run_script(self, script_name):
        """Exécute un script sélectionné"""
        import os
        
        # Nettoyer le nom (retirer les annotations comme "(Local)")
        clean_name = script_name.split(' ')[0]
        script_path = os.path.join("scripts", clean_name)
        
        log_info(f"Exécution du script: {clean_name}", "Controller")
        
        if os.path.exists(script_path):
            self.script_runner.run_script(script_path)
            log_success(f"Script lancé: {clean_name}", "Controller")
            return True, f"Script {clean_name} lancé avec succès."
        else:
            log_error(f"Script non trouvé: {clean_name}", "Controller")
            return False, f"Le fichier {clean_name} n'existe pas."
    
    # === GESTION IMPORT IP ===
    def import_ip_plan(self, file_path):
        """Importe un plan d'adressage IP"""
        import pandas as pd
        
        log_info("Début import plan d'adressage IP", "Controller")
        log_debug(f"Fichier sélectionné: {file_path}", "Controller")
        
        try:
            df = pd.read_excel(file_path, sheet_name="Nommage HL-RL", header=None)
            log_debug("Fichier Excel lu avec succès", "Controller")

            col_h = df.iloc[:, 7].astype(str).tolist()
            col_k = df.iloc[:, 10].astype(str).tolist()
            col_p = df.iloc[:, 15].astype(str).tolist()
            col_u = df.iloc[:, 20].astype(str).tolist()

            clean_data = []
            for h, k, p, u in zip(col_h, col_k, col_p, col_u):
                h_str = h.strip().lower()
                k_str = k.strip().lower()
                p_str = p.strip().lower()
                u_str = u.strip().lower()

                if h_str == "hostname" or k_str == "prod ip" or p_str == "mgt ip" or u_str == "idrac ip":
                    continue

                h = '' if h_str == "nan" else h.strip()
                k = '' if k_str == "nan" else k.strip()
                p = '' if p_str == "nan" else p.strip()
                u = '' if u_str == "nan" else u.strip()

                if not any([h, k, p, u]):
                    continue

                clean_data.append((h, k, p, u))

            log_success(f"Import terminé - {len(clean_data)} entrées traitées", "Controller")
            return True, clean_data, f"Import réussi: {len(clean_data)} entrées"

        except Exception as e:
            log_error(f"Erreur import plan IP: {str(e)}", "Controller")
            return False, [], f"Erreur lors de l'import: {str(e)}"
    
    # === GESTION LOGS ===
    def export_logs(self, logs_content, export_type="complete"):
        """Exporte les logs vers un fichier"""
        import datetime
        from PyQt6.QtWidgets import QFileDialog
        
        try:
            default_filename = f"toolbox_logs_{export_type}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            
            # Cette méthode sera appelée depuis l'UI qui aura accès au parent
            # Pour l'instant, retourner les données formatées
            export_content = f"""
================================================================================
                        TOOLBOX PyQt6 - EXPORT DES LOGS
================================================================================
Version         : Alpha 0.0.6
Développeur     : ocrano
Date d'export   : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Type d'export   : {export_type}
================================================================================

{logs_content}

================================================================================
                            FIN DE L'EXPORT
================================================================================
""".strip()
            
            log_info(f"Export logs préparé ({export_type})", "Controller")
            return True, export_content, default_filename
            
        except Exception as e:
            log_error(f"Erreur préparation export logs: {str(e)}", "Controller")
            return False, "", ""
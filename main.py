# main.py
"""
Point d'entrée principal de l'application Toolbox PyQt6
Version simplifiée et compatible
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
    
print(f"Répertoire de travail: {os.getcwd()}")
print(f"Fichiers dans resources/icons/: {os.listdir('resources/icons/')}")
# Import des services existants (avec gestion d'erreur)
try:
    from src.handlers.git_manager import GitLabManager as GitManager
except ImportError:
    print("Warning: GitLabManager non trouvé, utilisation d'un stub")
    class GitManager:
        def __init__(self, gitlab_url="https://gitlab.com"): 
            self.gitlab_url = gitlab_url
        def configure_token(self, token): return True
        def list_scripts(self): return []

try:
    from src.handlers.script_runner import ScriptRunner
except ImportError:
    print("Warning: ScriptRunner non trouvé, utilisation d'un stub")
    class ScriptRunner:
        def __init__(self): pass
        def execute_script(self, name): return {'success': False, 'error': 'Non implémenté'}

try:
    from src.handlers.proxmox_handler import ProxmoxService
except ImportError:
    print("Warning: ProxmoxService non trouvé, utilisation d'un stub")
    class ProxmoxService:
        def __init__(self): pass
        def is_connected(self): return False

# Import de la fenêtre principale refactorisée
from src.ui.main_window_refactored import MainWindowRefactored

# Import du système de logging
from src.core.logger import log_info, log_error, log_success


def setup_application():
    """Configure l'application PyQt6"""
    app = QApplication(sys.argv)
    app.setApplicationName("Toolbox PyQt6")
    app.setApplicationVersion("0.0.7")
    app.setOrganizationName("ocrano")
    
    # Style sombre pour l'application
    app.setStyleSheet("""
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QTabWidget::pane {
            border: 1px solid #555;
            background-color: #2b2b2b;
        }
        QTabBar::tab {
            background-color: #3c3c3c;
            color: #ffffff;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        QTabBar::tab:selected {
            background-color: #007bff;
            color: #ffffff;
        }
        QTabBar::tab:hover {
            background-color: #495057;
        }
    """)
    
    return app


def initialize_services():
    """Initialise tous les services de l'application"""
    log_info("Initialisation des services...", "Main")
    
    # GitLab Manager (avec URL par défaut)
    git_manager = GitManager("https://gitlab.com")  # URL GitLab par défaut
    
    # Script Runner  
    script_runner = ScriptRunner()
    
    # Proxmox Service (nouveau)
    proxmox_service = ProxmoxService()
    
    log_success("Services initialisés avec succès", "Main")
    
    return git_manager, script_runner, proxmox_service


def main():
    """Fonction principale"""
    try:
        log_info("Démarrage Toolbox PyQt6 - Version Connection Manager", "Main")
        
        # Créer l'application
        app = setup_application()
        
        # Initialiser les services
        git_manager, script_runner, proxmox_service = initialize_services()
        
        # Créer la fenêtre principale refactorisée
        window = MainWindowRefactored(git_manager, script_runner, proxmox_service)
        window.show()
        
        log_success("Application démarrée avec succès", "Main")
        
        # Lancer l'application
        return app.exec()
        
    except Exception as e:
        log_error(f"Erreur fatale au démarrage: {e}", "Main")
        print(f"Erreur détaillée: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
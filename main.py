#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Toolbox PyQt6 - Connection Manager
Point d'entrée principal - VERSION SANS LOGGING POUR TEST
"""

import sys
import os
from PyQt6.QtWidgets import QApplication

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_application():
    """Configure l'application PyQt6"""
    app = QApplication(sys.argv)
    app.setApplicationName("Toolbox PyQt6")
    app.setApplicationVersion("0.0.7")
    app.setOrganizationName("ocrano")
    
    # Style sombre
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
            border: 1px solid #555;
        }
        QTabBar::tab:selected {
            background-color: #007acc;
            border-bottom: none;
        }
        QTabBar::tab:hover {
            background-color: #505050;
        }
    """)
    
    return app

def setup_services():
    """Configure les services de l'application"""
    try:
        # Import du service unifié
        from src.services.proxmox_service import ProxmoxService
        
        # Services factices
        class MockGitLabManager:
            def configure_token(self, token):
                print(f"Token GitLab configuré: {token[:10]}...")
                return True
            
            def list_scripts(self):
                return ["script1.ps1", "script2.ps1", "script3.ps1"]
        
        class MockScriptRunner:
            def execute_script(self, script_name):
                print(f"Exécution du script: {script_name}")
                return {
                    'success': True,
                    'output': f"Script {script_name} exécuté avec succès"
                }
        
        # Créer les services
        git_manager = MockGitLabManager()
        script_runner = MockScriptRunner()
        proxmox_service = ProxmoxService()
        
        return git_manager, script_runner, proxmox_service
        
    except ImportError as e:
        print(f"Erreur d'import des services: {e}")
        sys.exit(1)

def main():
    """Point d'entrée principal"""
    print("Démarrage de l'application Toolbox PyQt6...")
    
    # Configuration de l'application
    app = setup_application()
    print("✓ Application PyQt6 configurée")
    
    # Configuration des services
    git_manager, script_runner, proxmox_service = setup_services()
    print("✓ Services configurés")
    
    try:
        # Import de la MainWindow refactorisée
        from src.ui.main_window_refactored import MainWindowRefactored
        print("✓ Interface importée")
        
        # Créer et afficher la fenêtre principale
        window = MainWindowRefactored(git_manager, script_runner, proxmox_service)
        window.show()
        print("✓ Fenêtre principale créée et affichée")
        print("🚀 Application démarrée avec succès!")
        
        # Lancer l'application
        return app.exec()
        
    except ImportError as e:
        print(f"❌ Erreur d'import de l'interface: {e}")
        print("\nVérifiez que tous les fichiers sont présents:")
        print("- src/ui/main_window_refactored.py")
        print("- src/ui/controllers/main_controller.py") 
        print("- src/services/proxmox_service.py")
        print("- src/core/logger.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ Application interrompue par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"💥 Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
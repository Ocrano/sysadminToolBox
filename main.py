#!/usr/bin/env python3
"""
Point d'entrée principal - Version refactorisée
Utilise la nouvelle architecture MVC
"""

import sys
import os
from PyQt6.QtWidgets import QApplication

# Ajouter le chemin src au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.ui.main_window_refactored import MainWindowRefactored
from src.services.proxmox_service import ProxmoxService
from src.handlers.git_manager import GitLabManager
from src.handlers.script_runner import ScriptRunner
from src.core.logger import log_info, log_success

def main():
    app = QApplication(sys.argv)
    
    # Initialiser les services
    log_info("Démarrage Toolbox PyQt6 - Version Refactorisée", "Main")
    
    # Services métier
    proxmox_service = ProxmoxService()
    git_manager = GitLabManager("")  # 🔧 URL vide, configurée via interface
    script_runner = ScriptRunner()
    
    # Fenêtre principale refactorisée
    window = MainWindowRefactored(git_manager, script_runner, proxmox_service)
    window.show()
    
    log_success("Application démarrée avec succès", "Main")
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
ToolboxPyQt6 - Point d'entrée principal
"""
import sys
import os

# Ajouter le répertoire src au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.handlers.git_manager import GitLabManager
from src.handlers.script_runner import ScriptRunner
from src.handlers.proxmox_handler import ProxmoxHandler
from src.core.logger import log_info, log_success

def main():
    log_info("Démarrage de ToolboxPyQt6", "Main")
    
    app = QApplication(sys.argv)
    
    # Configuration
    GITLAB_URL = "https://git.gtd-international.com"
    
    # Initialisation
    git_manager = GitLabManager(GITLAB_URL)
    script_runner = ScriptRunner()
    proxmox_handler = ProxmoxHandler()
    
    # Fenêtre principale
    window = MainWindow(git_manager, script_runner, proxmox_handler)
    window.show()
    
    log_success("Application démarrée", "Main")
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())

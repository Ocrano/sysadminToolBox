import logging
import sys
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal

class QtLogHandler(logging.Handler, QObject):
    """Handler pour rediriger les logs vers l'interface PyQt"""
    log_message = pyqtSignal(str)
    
    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)
        
    def emit(self, record):
        """Émets un signal avec le message de log formaté"""
        try:
            msg = self.format(record)
            self.log_message.emit(msg)
        except Exception:
            self.handleError(record)

class ToolboxLogger:
    """Logger centralisé pour toute l'application - Version lisibilité améliorée"""
    
    def __init__(self):
        self.logger = logging.getLogger('ToolboxPyQt6')
        self.logger.setLevel(logging.DEBUG)
        
        # Éviter les doublons si déjà configuré
        if self.logger.handlers:
            return
            
        # Handler pour l'interface PyQt
        self.qt_handler = QtLogHandler()
        self.qt_handler.setLevel(logging.DEBUG)
        
        # Handler pour la console (optionnel, garde les logs dans le terminal aussi)
        self.console_handler = logging.StreamHandler(sys.stdout)
        self.console_handler.setLevel(logging.DEBUG)
        
        # Format des messages pour la console (avec emojis)
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Format simplifié et LISIBLE pour l'interface (SANS emojis)
        qt_formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)-7s [%(name)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        
        self.qt_handler.setFormatter(qt_formatter)
        self.console_handler.setFormatter(console_formatter)
        
        # Ajouter les handlers
        self.logger.addHandler(self.qt_handler)
        self.logger.addHandler(self.console_handler)
    
    def get_qt_handler(self):
        """Retourne le handler PyQt pour connecter les signaux"""
        return self.qt_handler
    
    def debug(self, message, component="General"):
        """Log de debug - SANS emoji"""
        self.logger.debug(f"[{component}] {message}")
    
    def info(self, message, component="General"):
        """Log d'information - SANS emoji"""
        self.logger.info(f"[{component}] {message}")
    
    def warning(self, message, component="General"):
        """Log d'avertissement - SANS emoji"""
        self.logger.warning(f"[{component}] {message}")
    
    def error(self, message, component="General"):
        """Log d'erreur - SANS emoji"""
        self.logger.error(f"[{component}] {message}")
    
    def success(self, message, component="General"):
        """Log de succès - Marqueur simple SANS emoji"""
        self.logger.info(f"[{component}] SUCCESS: {message}")
    
    def step(self, step_num, total_steps, message, component="General"):
        """Log d'étape dans un processus - SANS emoji"""
        self.logger.info(f"[{component}] STEP {step_num}/{total_steps}: {message}")
    
    def ssh_log(self, message, ip="Unknown"):
        """Log spécialisé pour SSH - SANS emoji"""
        self.logger.debug(f"[SSH-{ip}] {message}")
    
    def proxmox_log(self, message, node="Unknown"):
        """Log spécialisé pour Proxmox - SANS emoji"""
        self.logger.debug(f"[Proxmox-{node}] {message}")
    
    def vm_log(self, message, vm_name="Unknown"):
        """Log spécialisé pour les VMs - SANS emoji"""
        self.logger.info(f"[VM-{vm_name}] {message}")

# Instance globale du logger
toolbox_logger = ToolboxLogger()

# Fonctions de convenance pour l'import simple
def log_debug(message, component="General"):
    toolbox_logger.debug(message, component)

def log_info(message, component="General"):
    toolbox_logger.info(message, component)

def log_warning(message, component="General"):
    toolbox_logger.warning(message, component)

def log_error(message, component="General"):
    toolbox_logger.error(message, component)

def log_success(message, component="General"):
    toolbox_logger.success(message, component)

def log_step(step_num, total_steps, message, component="General"):
    toolbox_logger.step(step_num, total_steps, message, component)

def log_ssh(message, ip="Unknown"):
    toolbox_logger.ssh_log(message, ip)

def log_proxmox(message, node="Unknown"):
    toolbox_logger.proxmox_log(message, node)

def log_vm(message, vm_name="Unknown"):
    toolbox_logger.vm_log(message, vm_name)
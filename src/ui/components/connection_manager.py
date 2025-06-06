# src/ui/components/connection_manager.py
"""
Connection Manager - Gestionnaire centralisé des connexions
VERSION FINALE DÉFINITIVE: Icônes parfaites + espacement optimal
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QLabel, QComboBox, QProgressBar, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QPainter, QColor, QIcon
import time
import os
from pathlib import Path


class ConnectionStatusIndicator(QWidget):
    """Indicateur de statut moderne avec animation"""
    
    def __init__(self, size=12):
        super().__init__()
        self.size = size
        self.status = "disconnected"  # disconnected, connecting, connected, error
        self.setFixedSize(size, size)
        
        # Timer pour animation
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update)
        self.animation_frame = 0
    
    def set_status(self, status):
        """Met à jour le statut : disconnected, connecting, connected, error"""
        self.status = status
        
        if status == "connecting":
            self.animation_timer.start(200)  # Animation toutes les 200ms
        else:
            self.animation_timer.stop()
            self.animation_frame = 0
        
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Couleurs selon le statut
        colors = {
            "disconnected": "#6c757d",
            "connecting": "#ffc107",
            "connected": "#28a745",
            "error": "#dc3545"
        }
        
        color = QColor(colors.get(self.status, "#6c757d"))
        
        # Animation pour "connecting"
        if self.status == "connecting":
            self.animation_frame += 1
            opacity = 0.3 + 0.7 * (abs((self.animation_frame % 10) - 5) / 5)
            color.setAlphaF(opacity)
        
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, self.size, self.size)


class IconManager:
    """Gestionnaire d'icônes avec fallbacks automatiques"""
    
    @staticmethod
    def get_service_icon(service_name, icon_path=None):
        """
        Récupère l'icône d'un service avec fallback automatique
        
        Args:
            service_name (str): Nom du service
            icon_path (str): Chemin optionnel vers l'icône
            
        Returns:
            str: Emoji ou chemin vers l'icône
        """
        # Dictionnaire des icônes de fallback (emojis)
        fallback_icons = {
            'Proxmox VE': '🟠',
            'VMware vSphere': '🔵', 
            'Docker': '🐳',
            'Kubernetes': '☸️',
            'OpenStack': '☁️',
            'Hyper-V': '🏢',
            'XenServer': '🔷',
            'QEMU/KVM': '🐧'
        }
        
        # Si un chemin d'icône est fourni, vérifier s'il existe
        if icon_path and os.path.exists(icon_path):
            return icon_path
        
        # Sinon, utiliser l'emoji de fallback
        return fallback_icons.get(service_name, '🖥️')
    
    @staticmethod
    def find_icon_in_project(service_type):
        """
        Recherche une icône dans le projet pour un type de service
        
        Args:
            service_type (str): Type de service (proxmox, vsphere, etc.)
            
        Returns:
            str: Chemin vers l'icône ou None
        """
        # Déterminer le répertoire racine du projet
        current_file = Path(__file__)
        
        # Remonter depuis src/ui/components/ vers la racine
        project_root = current_file.parent.parent.parent.parent
        
        # Possibles emplacements d'icônes
        possible_locations = [
            project_root / "ressources" / "icons",  # Votre structure actuelle
            project_root / "resources" / "icons",   # Structure standard
            project_root / "assets" / "icons",      # Alternative commune
            project_root / "icons",                 # Directement à la racine
        ]
        
        # Extensions supportées
        extensions = ['.png', '.ico', '.svg', '.jpg', '.jpeg']
        
        for location in possible_locations:
            if location.exists():
                for ext in extensions:
                    icon_file = location / f"{service_type}{ext}"
                    if icon_file.exists():
                        return str(icon_file)
        
        return None
    
    @staticmethod
    def debug_icon_paths():
        """Debug: affiche tous les chemins testés"""
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent
        
        print("=== DEBUG ICON PATHS ===")
        print(f"Fichier actuel: {current_file}")
        print(f"Racine projet: {project_root}")
        
        # Vérifier chaque emplacement possible
        possible_locations = [
            "ressources/icons",
            "resources/icons", 
            "assets/icons",
            "icons"
        ]
        
        for loc in possible_locations:
            full_path = project_root / loc
            exists = full_path.exists()
            print(f"  {loc}: {'✅ EXISTS' if exists else '❌ NOT FOUND'} ({full_path})")
            
            if exists:
                try:
                    files = list(full_path.iterdir())
                    print(f"    Fichiers: {[f.name for f in files if f.is_file()]}")
                except:
                    print(f"    Erreur lecture dossier")
        
        print("========================")


class ConnectionCard(QWidget):
    """Carte de connexion pour chaque service - VERSION FINALE OPTIMISÉE"""
    
    connection_requested = pyqtSignal(str)  # service_name
    disconnection_requested = pyqtSignal(str)
    configuration_requested = pyqtSignal(str)
    
    def __init__(self, service_config):
        super().__init__()
        self.service_name = service_config['name']
        self.service_type = service_config['type']
        
        # CORRECTION: Utiliser le gestionnaire d'icônes
        specified_icon = service_config.get('icon')
        auto_found_icon = IconManager.find_icon_in_project(self.service_type)
        self.service_icon = IconManager.get_service_icon(self.service_name, specified_icon or auto_found_icon)
        
        self.service_description = service_config['description']
        
        self.is_connected = False
        self.connection_info = {}
        
        self.init_ui()
    
    def create_perfect_icon(self, icon_path_or_emoji, base_size=32):
        """
        Crée une icône parfaitement dimensionnée avec tailles spécifiques par service
        
        Args:
            icon_path_or_emoji: Chemin vers l'icône ou emoji
            base_size: Taille de base en pixels
        
        Returns:
            QLabel avec l'icône parfaitement dimensionnée
        """
        # TAILLES SPÉCIFIQUES PAR SERVICE
        service_sizes = {
            "vsphere": 40,    # vSphere plus grand
            "proxmox": 32,    # Proxmox taille normale
            "docker": 32,     # Docker normal
            "kubernetes": 32  # Kubernetes normal
        }
        
        # Déterminer la taille finale
        final_size = service_sizes.get(self.service_type, base_size)
        
        print(f"🎯 Service: {self.service_type} -> Taille: {final_size}px")
        
        icon_label = QLabel()
        
        if isinstance(icon_path_or_emoji, str) and icon_path_or_emoji.endswith(('.png', '.ico', '.svg', '.jpg', '.jpeg')):
            try:
                # Charger l'image originale
                original_pixmap = QPixmap(icon_path_or_emoji)
                
                if not original_pixmap.isNull():
                    original_width = original_pixmap.width()
                    original_height = original_pixmap.height()
                    
                    print(f"📏 Image originale: {original_width}x{original_height}")
                    
                    # Redimensionner directement à la taille finale
                    scaled_pixmap = original_pixmap.scaled(
                        final_size, final_size,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    
                    # Créer un canvas carré de la taille finale
                    canvas = QPixmap(final_size, final_size)
                    canvas.fill(QColor(0, 0, 0, 0))  # Transparent
                    
                    # Centrer l'image redimensionnée
                    painter = QPainter(canvas)
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                    
                    x = (final_size - scaled_pixmap.width()) // 2
                    y = (final_size - scaled_pixmap.height()) // 2
                    painter.drawPixmap(x, y, scaled_pixmap)
                    painter.end()
                    
                    icon_label.setPixmap(canvas)
                    
                    print(f"✅ Icône créée: {scaled_pixmap.width()}x{scaled_pixmap.height()} centrée dans {final_size}x{final_size}")
                    
                else:
                    print(f"❌ Pixmap null pour {icon_path_or_emoji}")
                    raise Exception("Pixmap null")
                    
            except Exception as e:
                print(f"❌ Erreur chargement icône {icon_path_or_emoji}: {e}")
                # Fallback vers emoji
                return self.create_emoji_icon("🖥️", final_size)
        else:
            # C'est un emoji ou texte
            print(f"😀 Emoji détecté: {icon_path_or_emoji}")
            return self.create_emoji_icon(icon_path_or_emoji, final_size)
        
        # Standardiser le conteneur à la taille finale
        icon_label.setFixedSize(final_size, final_size)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)
        
        return icon_label

    def create_emoji_icon(self, emoji_text, size=32):
        """Crée une icône emoji parfaitement dimensionnée"""
        label = QLabel(emoji_text)
        
        # Calculer la taille de police appropriée selon la taille
        font_size = max(12, int(size * 0.65))  # 65% de la taille du conteneur
        
        label.setStyleSheet(f"""
            QLabel {{
                font-size: {font_size}px;
                font-weight: bold;
                color: #ffffff;
                background-color: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }}
        """)
        
        label.setFixedSize(size, size)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        print(f"🎭 Emoji {emoji_text} créé avec taille {size}px, police {font_size}px")
        
        return label
    
    def init_ui(self):
        """Interface de la carte - HAUTEUR OPTIMISÉE"""
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # === EN-TÊTE DE LA CARTE ===
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        
        # Icône + Nom - MÉTHODE PARFAITE
        icon_label = self.create_perfect_icon(self.service_icon)
        header_layout.addWidget(icon_label)
        
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        
        name_label = QLabel(self.service_name)
        name_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        title_layout.addWidget(name_label)
        
        desc_label = QLabel(self.service_description)
        desc_label.setStyleSheet("font-size: 11px; color: #adb5bd;")
        title_layout.addWidget(desc_label)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # Indicateur de statut
        self.status_indicator = ConnectionStatusIndicator()
        header_layout.addWidget(self.status_indicator)
        
        layout.addLayout(header_layout)
        
        # === INFORMATIONS DE CONNEXION ===
        self.info_frame = QFrame()
        self.info_frame.setFixedHeight(0)  # Caché par défaut
        self.info_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                margin: 6px 2px;
            }
        """)
        
        self.info_layout = QVBoxLayout()
        self.info_layout.setContentsMargins(8, 8, 8, 8)
        self.info_layout.setSpacing(4)
        self.info_frame.setLayout(self.info_layout)
        
        layout.addWidget(self.info_frame)
        
        # === BOUTONS D'ACTION ===
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(6)
        
        # Bouton configurer
        self.config_btn = QPushButton("⚙️ Config")
        self.config_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                font-size: 10px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #5a6268; }
        """)
        self.config_btn.clicked.connect(lambda: self.configuration_requested.emit(self.service_name))
        buttons_layout.addWidget(self.config_btn)
        
        # Bouton connexion/déconnexion
        self.connection_btn = QPushButton("🔗 Connecter")
        self.connection_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                font-size: 10px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #0056b3; }
        """)
        self.connection_btn.clicked.connect(self.toggle_connection)
        buttons_layout.addWidget(self.connection_btn)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
        self.setFixedWidth(320)  # Largeur adaptée
        self.setMinimumHeight(150)  # Hauteur RÉDUITE pour optimiser l'espace
        self.setMaximumHeight(165)  # Hauteur max RÉDUITE
        
        # Appliquer le style par défaut
        self.apply_default_style()
    
    def apply_default_style(self):
        """Applique le style par défaut"""
        self.setStyleSheet("""
            ConnectionCard {
                background-color: #3a3d42;
                border: 2px solid #4a4d52;
                border-radius: 12px;
                margin: 8px;
                padding: 4px;
            }
            ConnectionCard:hover {
                border-color: #6c757d;
                background-color: #42464b;
                box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.4);
            }
        """)
    
    def toggle_connection(self):
        """Basculer entre connexion/déconnexion"""
        if self.is_connected:
            self.disconnection_requested.emit(self.service_name)
        else:
            self.connection_requested.emit(self.service_name)
    
    def set_connecting(self):
        """Indique que la connexion est en cours"""
        self.status_indicator.set_status("connecting")
        self.connection_btn.setText("⏳ Connexion...")
        self.connection_btn.setEnabled(False)
    
    def set_connected(self, info=None):
        """Marque comme connecté avec infos optionnelles"""
        self.is_connected = True
        self.connection_info = info or {}
        
        self.status_indicator.set_status("connected")
        self.connection_btn.setText("🔌 Déconnecter")
        self.connection_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 9px;
                font-weight: 600;
                min-width: 70px;
                max-width: 70px;
                min-height: 24px;
                max-height: 24px;
            }
            QPushButton:hover { background-color: #c82333; }
        """)
        self.connection_btn.setEnabled(True)
        
        # Afficher les infos de connexion
        self.update_connection_info()
    
    def set_disconnected(self, error_message=None):
        """Marque comme déconnecté"""
        self.is_connected = False
        self.connection_info = {}
        
        if error_message:
            self.status_indicator.set_status("error")
        else:
            self.status_indicator.set_status("disconnected")
        
        self.connection_btn.setText("🔗 Connecter")
        self.connection_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                font-size: 10px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #0056b3; }
        """)
        self.connection_btn.setEnabled(True)
        
        # Masquer les infos
        self.info_frame.setFixedHeight(0)
        self.clear_info_layout()
    
    def update_connection_info(self):
        """Met à jour l'affichage des informations de connexion"""
        self.clear_info_layout()
        
        if not self.connection_info:
            self.info_frame.setFixedHeight(0)
            return
        
        # Afficher les infos selon le type de service
        if self.service_type == "proxmox":
            self.add_info_line("🏗️", f"Nœuds: {self.connection_info.get('nodes_count', 'N/A')}")
            self.add_info_line("🖥️", f"VMs: {self.connection_info.get('total_vms', 'N/A')}")
            self.add_info_line("🟢", f"Actives: {self.connection_info.get('running_vms', 'N/A')}")
            if 'version' in self.connection_info:
                self.add_info_line("📋", f"Version: {self.connection_info['version']}")
            
        elif self.service_type == "vsphere":
            self.add_info_line("🏢", f"vCenter: {self.connection_info.get('vcenter_version', 'N/A')}")
            self.add_info_line("🖥️", f"ESXi: {self.connection_info.get('hosts_count', 'N/A')}")
            self.add_info_line("📊", f"Clusters: {self.connection_info.get('clusters_count', 'N/A')}")
        
        # Ajuster la hauteur
        self.info_frame.setFixedHeight(self.info_layout.sizeHint().height() + 16)
    
    def add_info_line(self, icon, text):
        """Ajoute une ligne d'information"""
        line_layout = QHBoxLayout()
        line_layout.setContentsMargins(0, 0, 0, 0)
        line_layout.setSpacing(6)
        
        icon_label = QLabel(icon)
        icon_label.setFixedWidth(16)
        line_layout.addWidget(icon_label)
        
        text_label = QLabel(text)
        text_label.setStyleSheet("font-size: 10px; color: #ffffff;")
        line_layout.addWidget(text_label)
        line_layout.addStretch()
        
        line_widget = QWidget()
        line_widget.setLayout(line_layout)
        self.info_layout.addWidget(line_widget)
    
    def clear_info_layout(self):
        """Nettoie le layout des infos"""
        while self.info_layout.count():
            child = self.info_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()


class ConnectionManager(QWidget):
    """Gestionnaire principal des connexions - VERSION FINALE DÉFINITIVE"""
    
    # Signaux pour communiquer avec MainWindow
    connection_status_changed = pyqtSignal(str, bool, dict)  # service, connected, info
    configuration_requested = pyqtSignal(str)  # service_name
    
    def __init__(self):
        super().__init__()
        self.service_cards = {}
        
        # DEBUG: Afficher les chemins testés
        IconManager.debug_icon_paths()
        
        self.init_ui()
        self.setup_services()
    
    def init_ui(self):
        """Interface principale - ESPACEMENT FINAL PARFAIT"""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 8, 10, 25)  # Marge bas MAXIMISÉE pour libérer l'espace
        layout.setSpacing(8)  # Espacement optimal
        
        # Titre compact
        title = QLabel("🔗 Gestionnaire de Connexions")
        title.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            color: #ffffff;
            margin-bottom: 6px;
        """)
        layout.addWidget(title)
        
        # Conteneur des cartes avec marges maximisées
        cards_container = QWidget()
        cards_container.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border: none;
            }
        """)
        
        self.cards_layout = QHBoxLayout()
        self.cards_layout.setContentsMargins(5, 10, 5, 18)  # Marge bas MAXIMISÉE
        self.cards_layout.setSpacing(20)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        cards_container.setLayout(self.cards_layout)
        
        layout.addWidget(cards_container)
        
        # Barre d'actions avec séparation MAXIMALE
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(6)
        actions_layout.setContentsMargins(0, 12, 0, 0)  # Marge haute AUGMENTÉE
        
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 10px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #138496; }
        """)
        refresh_btn.clicked.connect(self.refresh_all_connections)
        actions_layout.addWidget(refresh_btn)
        
        actions_layout.addStretch()
        
        # Indicateur global compact
        self.global_status = QLabel("💤 Aucune connexion active")
        self.global_status.setStyleSheet("font-size: 10px; color: #6c757d; font-style: italic;")
        actions_layout.addWidget(self.global_status)
        
        layout.addLayout(actions_layout)
        
        self.setLayout(layout)
        self.setMaximumHeight(250)  # Hauteur FINALE optimisée
        self.setMinimumHeight(250)  # Hauteur minimale fixée
    
    def setup_services(self):
        """Configure les services disponibles"""
        services = [
            {
                'name': 'Proxmox VE',
                'type': 'proxmox',
                'description': 'Gestionnaire de virtualisation'
            },
            {
                'name': 'VMware vSphere',
                'type': 'vsphere',
                'description': 'Infrastructure VMware'
            }
        ]
        
        for service_config in services:
            card = ConnectionCard(service_config)
            card.connection_requested.connect(self.handle_connection_request)
            card.disconnection_requested.connect(self.handle_disconnection_request)
            card.configuration_requested.connect(self.handle_configuration_request)
            
            self.service_cards[service_config['name']] = card
            self.cards_layout.addWidget(card)
        
        # Spacer pour aligner à gauche
        self.cards_layout.addStretch()
    
    def handle_connection_request(self, service_name):
        """Gère une demande de connexion"""
        card = self.service_cards.get(service_name)
        if card:
            card.set_connecting()
            self.connection_status_changed.emit(service_name, True, {})
    
    def handle_disconnection_request(self, service_name):
        """Gère une demande de déconnexion"""
        card = self.service_cards.get(service_name)
        if card:
            card.set_disconnected()
            self.connection_status_changed.emit(service_name, False, {})
            self.update_global_status()
    
    def handle_configuration_request(self, service_name):
        """Gère une demande de configuration"""
        self.configuration_requested.emit(service_name)
    
    # === API PUBLIQUE POUR MAINWINDOW ===
    
    def set_service_connected(self, service_name, info=None):
        """API publique pour marquer un service comme connecté"""
        card = self.service_cards.get(service_name)
        if card:
            card.set_connected(info)
            self.update_global_status()
    
    def set_service_disconnected(self, service_name, error=None):
        """API publique pour marquer un service comme déconnecté"""
        card = self.service_cards.get(service_name)
        if card:
            card.set_disconnected(error)
            self.update_global_status()
    
    def set_service_connecting(self, service_name):
        """API publique pour marquer un service en connexion"""
        card = self.service_cards.get(service_name)
        if card:
            card.set_connecting()
    
    def update_service_info(self, service_name, info):
        """Met à jour les informations d'un service connecté"""
        card = self.service_cards.get(service_name)
        if card and card.is_connected:
            card.connection_info.update(info)
            card.update_connection_info()
    
    def get_connected_services(self):
        """Retourne la liste des services connectés"""
        return [name for name, card in self.service_cards.items() if card.is_connected]
    
    def is_service_connected(self, service_name):
        """Vérifie si un service est connecté"""
        card = self.service_cards.get(service_name)
        return card.is_connected if card else False
    
    def update_global_status(self):
        """Met à jour le statut global"""
        connected_services = [name for name, card in self.service_cards.items() if card.is_connected]
        
        if not connected_services:
            self.global_status.setText("💤 Aucune connexion active")
            self.global_status.setStyleSheet("font-size: 11px; color: #6c757d; font-style: italic;")
        else:
            count = len(connected_services)
            services_text = ', '.join(connected_services)
            if len(services_text) > 50:
                services_text = f"{connected_services[0]} et {count-1} autre(s)"
            self.global_status.setText(f"✅ {count} service(s) connecté(s): {services_text}")
            self.global_status.setStyleSheet("font-size: 11px; color: #28a745; font-weight: 600;")
    
    def refresh_all_connections(self):
        """Actualise toutes les connexions actives"""
        connected_services = self.get_connected_services()
        if connected_services:
            for service_name in connected_services:
                self.connection_status_changed.emit(service_name, True, {'refresh': True})
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Actualisation", "Aucune connexion active à actualiser.")


# Export
__all__ = ['ConnectionManager', 'ConnectionCard', 'ConnectionStatusIndicator', 'IconManager']
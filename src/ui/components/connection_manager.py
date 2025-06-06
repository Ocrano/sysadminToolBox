# src/ui/components/connection_manager.py
"""
Connection Manager - Gestionnaire centralisé des connexions
VERSION FINALE SUBTILE: Cartes avec fonds colorés subtils et espacement
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
    """Carte de connexion pour chaque service - FOND SUBTIL ET ESPACEMENT"""
    
    connection_requested = pyqtSignal(str)  # service_name
    disconnection_requested = pyqtSignal(str)
    configuration_requested = pyqtSignal(str)
    
    def __init__(self, service_config):
        super().__init__()
        self.service_name = service_config['name']
        self.service_type = service_config['type']
        
        # COULEURS SUBTILES PAR SERVICE (pour les fonds uniquement)
         # COULEURS TRÈS VISIBLES (VERSION TEST)
        self.service_colors = {
            "proxmox": {
                "background": "#4a2c1a",        # Orange foncé TRÈS visible
                "border": "#ff6b35",            # Bordure orange vive
                "hover_bg": "#5a3422",          # Hover orange
                "hover_border": "#ff8f65"       # Bordure hover
            },
            "vsphere": {
                "background": "#1a2938",        # Bleu foncé TRÈS visible
                "border": "#1e88e5",            # Bordure bleue vive
                "hover_bg": "#243242",          # Hover bleu
                "hover_border": "#42a5f5"       # Bordure hover
            }
        }
        
        # Récupérer les couleurs du service (fallback vers couleurs neutres)
        self.colors = self.service_colors.get(self.service_type, {
            "background": "rgba(108, 117, 125, 0.08)",
            "border": "rgba(108, 117, 125, 0.2)",
            "hover_bg": "rgba(108, 117, 125, 0.12)",
            "hover_border": "rgba(108, 117, 125, 0.3)"
        })
        
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
        """Interface de la carte - FOND SUBTIL ET BOUTONS NORMAUX"""
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)  # Marges internes généreuses
        layout.setSpacing(10)
        
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
                background-color: rgba(255, 255, 255, 0.05);
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
        
        # === BOUTONS D'ACTION NORMAUX ===
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        
        # Bouton configurer - STYLE NORMAL
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
        
        # Bouton connexion/déconnexion - STYLE NORMAL
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
        self.setFixedWidth(340)  # Largeur légèrement augmentée pour les marges
        self.setMinimumHeight(155)  # Hauteur optimisée
        self.setMaximumHeight(170)  # Hauteur max
        
        # Appliquer le style avec fond subtil
        self.apply_subtle_style()
    
    def apply_subtle_style(self):
            """Style avec couleurs TRÈS visibles"""
            self.setStyleSheet(f"""
                ConnectionCard {{
                    background-color: {self.colors['background']} !important;
                    border: 3px solid {self.colors['border']} !important;
                    border-radius: 12px;
                    margin: 5px;
                    padding: 0px;
                }}
                ConnectionCard:hover {{
                    background-color: {self.colors['hover_bg']} !important;
                    border-color: {self.colors['hover_border']} !important;
                    box-shadow: 0px 6px 16px rgba(0, 0, 0, 0.4);
                }}
            """)
            
            print(f"🔥 Style RENFORCÉ appliqué pour {self.service_type}")
            print(f"   Fond: {self.colors['background']}")
            print(f"   Bordure: {self.colors['border']}")
            
            # Forcer la mise à jour
            self.setStyleSheet(self.styleSheet())
            self.update()
            self.repaint()
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
        """Marque comme connecté avec bouton rouge de déconnexion"""
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
        """Marque comme déconnecté avec style normal"""
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
    """Gestionnaire principal des connexions - AVEC ESPACEMENT DES CARTES"""
    
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
        """Interface principale - AVEC ESPACEMENT ENTRE CARTES"""
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 10, 15, 20)  # Marges externes généreuses
        layout.setSpacing(10)
        
        # Titre compact SANS EMOJI
        title = QLabel("Gestionnaire de Connexions")
        title.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            color: #ffffff;
            margin-bottom: 8px;
        """)
        layout.addWidget(title)
        
        # Conteneur des cartes avec espacement
        cards_container = QWidget()
        cards_container.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border: none;
            }
        """)
        
        self.cards_layout = QHBoxLayout()
        self.cards_layout.setContentsMargins(10, 10, 10, 15)  # Marges pour cartes
        self.cards_layout.setSpacing(25)  # ESPACEMENT ENTRE CARTES augmenté
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        cards_container.setLayout(self.cards_layout)
        
        layout.addWidget(cards_container)
        
        # Barre d'actions SIMPLIFIÉE
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(6)
        actions_layout.setContentsMargins(0, 10, 0, 0)
        
        actions_layout.addStretch()
        
        # Indicateur global compact
        self.global_status = QLabel("💤 Aucune connexion active")
        self.global_status.setStyleSheet("font-size: 10px; color: #6c757d; font-style: italic;")
        actions_layout.addWidget(self.global_status)
        
        layout.addLayout(actions_layout)
        
        # === SÉPARATEUR VISUEL ===
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("""
            QFrame {
                color: #4a4d52;
                background-color: #4a4d52;
                border: none;
                margin: 12px 0px;
            }
        """)
        layout.addWidget(separator)
        
        self.setLayout(layout)
        self.setMaximumHeight(290)  # Hauteur ajustée pour les nouvelles marges
        self.setMinimumHeight(290)
    
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


# Export
__all__ = ['ConnectionManager', 'ConnectionCard', 'ConnectionStatusIndicator', 'IconManager']
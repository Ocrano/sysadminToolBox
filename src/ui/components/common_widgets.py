# src/ui/components/common_widgets.py - VERSION CORRIGÉE AVEC FILTRES
"""
Composants UI réutilisables - Version avec filtres fonctionnels
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, 
    QLabel, QTextEdit, QCheckBox, QProgressBar, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QTextCharFormat, QColor
import time


class VersionLabel(QLabel):
    """Label de version standardisé"""
    
    def __init__(self, version="Alpha 0.0.6", developer="ocrano"):
        super().__init__(f"{version} • by {developer}")
        self.setStyleSheet("color: #6c757d; font-size: 10px; font-style: italic;")


class ConnectionStatusWidget(QWidget):
    """Widget de statut de connexion réutilisable"""
    
    def __init__(self, service_name="Service"):
        super().__init__()
        self.service_name = service_name
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_label = QLabel("❌ Non connecté")
        self.status_label.setFixedWidth(120)
        
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #495057; font-size: 12px; margin-left: 10px;")
        
        layout.addWidget(self.status_label)
        layout.addWidget(self.info_label)
        layout.addStretch()
        
        self.setLayout(layout)
        self.update_status(False)
    
    def update_status(self, connected, info_text=""):
        if connected:
            self.status_label.setText("✅ Connecté")
            self.status_label.setStyleSheet("""
                QLabel {
                    padding: 6px 10px;
                    border-radius: 4px;
                    background-color: #d4edda;
                    color: #155724;
                    font-weight: bold;
                    font-size: 12px;
                }
            """)
        else:
            self.status_label.setText("❌ Non connecté")
            self.status_label.setStyleSheet("""
                QLabel {
                    padding: 6px 10px;
                    border-radius: 4px;
                    background-color: #f8d7da;
                    color: #721c24;
                    font-weight: bold;
                    font-size: 12px;
                }
            """)
        
        self.info_label.setText(info_text)


class LogControlPanel(QWidget):
    """Panneau de contrôle pour les logs avec filtres fonctionnels"""
    
    export_requested = pyqtSignal()
    clear_requested = pyqtSignal()
    filter_changed = pyqtSignal(str, bool)  # level, enabled
    
    def __init__(self):
        super().__init__()
        self.filters = {
            'DEBUG': True,
            'INFO': True,
            'SUCCESS': True,
            'WARNING': True,
            'ERROR': True
        }
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)
        
        # === SECTION FILTRES ===
        filters_group = QFrame()
        filters_group.setFrameStyle(QFrame.Shape.StyledPanel)
        filters_group.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 2px;
            }
        """)
        
        filters_layout = QHBoxLayout()
        filters_layout.setContentsMargins(8, 4, 8, 4)
        filters_layout.setSpacing(8)
        
        filters_label = QLabel("Filtres:")
        filters_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #495057;")
        filters_layout.addWidget(filters_label)
        
        # Créer les checkboxes pour chaque niveau
        self.filter_checkboxes = {}
        
        filter_configs = [
            ('DEBUG', '🐛', '#868e96'),
            ('INFO', 'ℹ️', '#17a2b8'),
            ('SUCCESS', '✅', '#28a745'),
            ('WARNING', '⚠️', '#ffc107'),
            ('ERROR', '❌', '#dc3545')
        ]
        
        for level, icon, color in filter_configs:
            checkbox = QCheckBox(f"{icon} {level}")
            checkbox.setChecked(self.filters[level])
            checkbox.setStyleSheet(f"""
                QCheckBox {{
                    font-size: 11px;
                    font-weight: bold;
                    color: {color};
                    spacing: 2px;
                }}
                QCheckBox::indicator {{
                    width: 14px;
                    height: 14px;
                }}
                QCheckBox::indicator:checked {{
                    background-color: {color};
                    border: 1px solid {color};
                    border-radius: 2px;
                }}
                QCheckBox::indicator:unchecked {{
                    background-color: white;
                    border: 1px solid #ccc;
                    border-radius: 2px;
                }}
            """)
            
            # Connecter le signal avec une lambda qui capture la valeur de level
            checkbox.stateChanged.connect(lambda state, lvl=level: self.on_filter_changed(lvl, state == 2))
            
            self.filter_checkboxes[level] = checkbox
            filters_layout.addWidget(checkbox)
        
        filters_group.setLayout(filters_layout)
        layout.addWidget(filters_group)
        
        layout.addStretch()
        
        # === BOUTONS D'ACTION ===
        # Bouton tout sélectionner/désélectionner
        self.toggle_all_btn = QPushButton("🔄 Tout")
        self.toggle_all_btn.setToolTip("Sélectionner/Désélectionner tous les filtres")
        self.toggle_all_btn.clicked.connect(self.toggle_all_filters)
        self.toggle_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 6px 10px;
                border-radius: 3px;
                font-size: 11px;
                margin-right: 5px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        layout.addWidget(self.toggle_all_btn)
        
        # Bouton export
        self.export_btn = QPushButton("💾 Exporter")
        self.export_btn.clicked.connect(self.export_requested.emit)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                font-size: 12px;
                margin-right: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        layout.addWidget(self.export_btn)
        
        # Bouton clear
        self.clear_btn = QPushButton("🗑️ Effacer")
        self.clear_btn.clicked.connect(self.clear_requested.emit)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        layout.addWidget(self.clear_btn)
        
        self.setLayout(layout)
    
    def on_filter_changed(self, level, enabled):
        """Gère le changement d'état d'un filtre"""
        try:
            self.filters[level] = enabled
            print(f"Filtre {level} {'activé' if enabled else 'désactivé'}")
            self.filter_changed.emit(level, enabled)
        except Exception as e:
            print(f"Erreur changement filtre {level}: {e}")
    
    def toggle_all_filters(self):
        """Bascule tous les filtres"""
        # Si tous sont cochés, tout décocher, sinon tout cocher
        all_checked = all(self.filters.values())
        new_state = not all_checked
        
        for level, checkbox in self.filter_checkboxes.items():
            checkbox.setChecked(new_state)
            # Le signal stateChanged sera automatiquement émis
        
        self.toggle_all_btn.setText("🔄 Tout" if new_state else "🔄 Aucun")
    
    def get_active_filters(self):
        """Retourne la liste des filtres actifs"""
        return [level for level, enabled in self.filters.items() if enabled]


class LogDisplay(QTextEdit):
    """Zone d'affichage des logs avec filtrage par niveau"""
    
    def __init__(self, title="Logs"):
        super().__init__()
        self.title = title
        self.all_logs = []  # Stockage de tous les logs: [(message, level, timestamp), ...]
        self.active_filters = {'DEBUG', 'INFO', 'SUCCESS', 'WARNING', 'ERROR'}  # Tous actifs par défaut
        self.init_ui()
        self.add_welcome_message()
    
    def init_ui(self):
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 10))
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 15px;
                line-height: 1.4;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            }
        """)
    
    def add_welcome_message(self):
        """Ajoute le message d'accueil"""
        cursor = self.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        
        format_header = QTextCharFormat()
        format_header.setForeground(QColor("#74c0fc"))
        format_header.setFontWeight(QFont.Weight.Bold)
        cursor.setCharFormat(format_header)
        cursor.insertText("=" * 80 + "\n")
        cursor.insertText(f"                        {self.title.upper()} - SESSION STARTED\n")
        cursor.insertText("=" * 80 + "\n\n")
        
        format_system = QTextCharFormat()
        format_system.setForeground(QColor("#51cf66"))
        cursor.setCharFormat(format_system)
        cursor.insertText(f"SYSTEM: Welcome to {self.title}\n")
        cursor.insertText("SYSTEM: Filtres par niveau de criticité activés\n")
        cursor.insertText("SYSTEM: Utilisez les checkboxes pour filtrer les logs\n\n")
    
    def add_log(self, message, level="INFO"):
        """Ajoute un log et l'affiche si le filtre est actif"""
        try:
            timestamp = time.strftime("%H:%M:%S")
            
            # Stocker le log complet
            self.all_logs.append((message, level, timestamp))
            
            # Afficher seulement si le niveau est dans les filtres actifs
            if level in self.active_filters:
                self._append_log_to_display(message, level, timestamp)
            
        except Exception as e:
            print(f"Erreur ajout log: {e}")
    
    def _append_log_to_display(self, message, level, timestamp):
        """Ajoute un log à l'affichage avec formatage"""
        try:
            cursor = self.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            
            # Format selon le niveau
            format = QTextCharFormat()
            
            if level == "SUCCESS":
                format.setForeground(QColor("#51cf66"))
                format.setFontWeight(QFont.Weight.Bold)
            elif level == "ERROR":
                format.setForeground(QColor("#ff6b6b"))
                format.setFontWeight(QFont.Weight.Bold)
            elif level == "WARNING":
                format.setForeground(QColor("#ffd43b"))
            elif level == "DEBUG":
                format.setForeground(QColor("#868e96"))
            else:  # INFO
                format.setForeground(QColor("#74c0fc"))
            
            cursor.setCharFormat(format)
            cursor.insertText(f"[{timestamp}] {level} | {message}\n")
            
            # Auto-scroll vers le bas
            scrollbar = self.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
        except Exception as e:
            print(f"Erreur affichage log: {e}")
    
    def update_filter(self, level, enabled):
        """Met à jour les filtres et rafraîchit l'affichage"""
        try:
            if enabled:
                self.active_filters.add(level)
            else:
                self.active_filters.discard(level)
            
            # Rafraîchir l'affichage
            self._refresh_display()
            
            print(f"Filtre {level} {'activé' if enabled else 'désactivé'}. Filtres actifs: {self.active_filters}")
            
        except Exception as e:
            print(f"Erreur mise à jour filtre {level}: {e}")
    
    def _refresh_display(self):
        """Rafraîchit l'affichage complet avec les filtres actuels"""
        try:
            # Sauvegarder la position du scroll
            scrollbar = self.verticalScrollBar()
            scroll_position = scrollbar.value()
            was_at_bottom = scroll_position >= scrollbar.maximum() - 10
            
            # Effacer le contenu actuel
            self.clear()
            
            # Remettre le message d'accueil
            self.add_welcome_message()
            
            # Réafficher tous les logs filtrés
            for message, level, timestamp in self.all_logs:
                if level in self.active_filters:
                    self._append_log_to_display(message, level, timestamp)
            
            # Restaurer la position du scroll (ou aller en bas si on y était)
            if was_at_bottom:
                scrollbar.setValue(scrollbar.maximum())
            else:
                scrollbar.setValue(min(scroll_position, scrollbar.maximum()))
                
        except Exception as e:
            print(f"Erreur rafraîchissement affichage: {e}")
    
    def clear_logs(self):
        """Efface tous les logs"""
        try:
            self.clear()
            self.all_logs = []
            self.add_welcome_message()
            
            # Message de nettoyage
            cursor = self.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            format = QTextCharFormat()
            format.setForeground(QColor("#ffd43b"))
            cursor.setCharFormat(format)
            timestamp = time.strftime("%H:%M:%S")
            cursor.insertText(f"[{timestamp}] SYSTEM | Logs cleared by user\n\n")
            
        except Exception as e:
            print(f"Erreur clear logs: {e}")
    
    def get_filtered_logs_text(self):
        """Retourne le texte des logs actuellement affichés (filtrés)"""
        try:
            filtered_logs = []
            for message, level, timestamp in self.all_logs:
                if level in self.active_filters:
                    filtered_logs.append(f"[{timestamp}] {level} | {message}")
            return '\n'.join(filtered_logs)
        except Exception as e:
            print(f"Erreur récupération logs filtrés: {e}")
            return ""
    
    def get_all_logs_text(self):
        """Retourne le texte de tous les logs (non filtrés)"""
        try:
            all_logs_text = []
            for message, level, timestamp in self.all_logs:
                all_logs_text.append(f"[{timestamp}] {level} | {message}")
            return '\n'.join(all_logs_text)
        except Exception as e:
            print(f"Erreur récupération tous les logs: {e}")
            return ""


class ActionButton(QPushButton):
    """Bouton d'action stylisé avec couleurs par catégorie"""
    
    def __init__(self, text, color='primary', icon=""):
        super().__init__(f"{icon} {text}" if icon else text)
        self.color = color
        self.apply_style()
    
    def apply_style(self):
        """Applique le style selon la couleur"""
        colors = {
            'primary': '#007bff',
            'success': '#28a745',
            'info': '#17a2b8',
            'warning': '#ffc107',
            'danger': '#dc3545',
            'secondary': '#6c757d',
            'purple': '#6f42c1',
            'orange': '#fd7e14',
            'pink': '#e83e8c'
        }
        
        base_color = colors.get(self.color, '#007bff')
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {base_color};
                color: white;
                border: none;
                padding: 12px;
                border-radius: 5px;
                font-weight: bold;
                text-align: left;
                font-size: 13px;
            }}
            QPushButton:hover {{
                opacity: 0.8;
            }}
            QPushButton:disabled {{
                background-color: #6c757d;
            }}
        """)


class SectionHeader(QWidget):
    """En-tête de section avec titre et version"""
    
    def __init__(self, title, icon="", version_widget=None):
        super().__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 10)
        
        title_text = f"{icon} {title}" if icon else title
        title_label = QLabel(title_text)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        if version_widget is None:
            version_widget = VersionLabel()
        layout.addWidget(version_widget)
        
        self.setLayout(layout)


class ConfigurationGroup(QGroupBox):
    """Groupe de configuration standardisé"""
    
    def __init__(self, title, icon="🔗"):
        super().__init__(f"{icon} {title}")
        self.setMaximumHeight(80)
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 12px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
                color: #495057;
            }
        """)


class ActionGrid(QWidget):
    """Grille d'actions organisée par groupes"""
    
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.groups = {}
        self.setLayout(self.layout)
    
    def add_group(self, group_name, icon="🛠️"):
        """Ajoute un groupe d'actions"""
        group = QGroupBox(f"{icon} {group_name}")
        group_layout = QVBoxLayout()
        group.setLayout(group_layout)
        
        self.groups[group_name] = group_layout
        self.layout.addWidget(group)
        
        return group_layout
    
    def add_action_to_group(self, group_name, button):
        """Ajoute un bouton à un groupe"""
        if group_name in self.groups:
            self.groups[group_name].addWidget(button)
    
    def enable_group(self, group_name, enabled=True):
        """Active/désactive tous les boutons d'un groupe"""
        if group_name in self.groups:
            layout = self.groups[group_name]
            for i in range(layout.count()):
                widget = layout.itemAt(i).widget()
                if isinstance(widget, QPushButton):
                    widget.setEnabled(enabled)


class WidgetFactory:
    """Factory pour créer des widgets standardisés"""
    
    @staticmethod
    def create_config_button(text, color='primary', icon="⚙️"):
        """Crée un bouton de configuration"""
        btn = ActionButton(text, color, icon)
        btn.setFixedWidth(140)
        return btn
    
    @staticmethod
    def create_info_label(text=""):
        """Crée un label d'information"""
        label = QLabel(text)
        label.setStyleSheet("color: #495057; font-size: 12px; margin-left: 10px;")
        return label


class MetricsDisplay(QWidget):
    """Affichage de métriques avec icônes et couleurs"""
    
    def __init__(self):
        super().__init__()
        self.metrics = {}
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
    
    def add_metric(self, name, value, icon="📊", color="#17a2b8"):
        """Ajoute une métrique"""
        metric_widget = QWidget()
        metric_layout = QVBoxLayout()
        metric_layout.setContentsMargins(10, 5, 10, 5)
        
        # Icône + valeur
        value_label = QLabel(f"{icon} {value}")
        value_label.setStyleSheet(f"""
            font-size: 18px; 
            font-weight: bold; 
            color: {color};
            text-align: center;
        """)
        
        # Nom de la métrique
        name_label = QLabel(name)
        name_label.setStyleSheet("""
            font-size: 12px; 
            color: #6c757d;
            text-align: center;
        """)
        
        metric_layout.addWidget(value_label)
        metric_layout.addWidget(name_label)
        metric_widget.setLayout(metric_layout)
        
        # Style de la carte
        metric_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin: 2px;
            }
        """)
        
        self.metrics[name] = value_label
        self.layout.addWidget(metric_widget)
    
    def update_metric(self, name, value, icon="📊"):
        """Met à jour une métrique"""
        if name in self.metrics:
            self.metrics[name].setText(f"{icon} {value}")
    
    def clear_metrics(self):
        """Efface toutes les métriques"""
        for i in reversed(range(self.layout.count())):
            child = self.layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        self.metrics.clear()


class StatusTable(QTableWidget):
    """Tableau de statut standardisé"""
    
    def __init__(self, headers):
        super().__init__()
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
        # Style du tableau
        self.setStyleSheet("""
            QTableWidget {
                gridline-color: #dee2e6;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }
            QHeaderView::section {
                background-color: #e9ecef;
                padding: 6px;
                font-weight: bold;
                border: 1px solid #dee2e6;
            }
        """)
        
        # Configuration
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    
    def add_status_row(self, data):
        """Ajoute une ligne de données"""
        row_position = self.rowCount()
        self.insertRow(row_position)
        
        for column, value in enumerate(data):
            item = QTableWidgetItem(str(value))
            self.setItem(row_position, column, item)


# Export des composants principaux
__all__ = [
    'VersionLabel',
    'ConnectionStatusWidget', 
    'ActionButton',
    'LogDisplay',
    'LogControlPanel',
    'SectionHeader',
    'ConfigurationGroup',
    'ActionGrid',
    'WidgetFactory',
    'MetricsDisplay',
    'StatusTable'
]
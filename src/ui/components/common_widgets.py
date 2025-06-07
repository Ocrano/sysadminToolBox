# src/ui/components/common_widgets.py - VERSION FINITIONS PARFAITES
"""
Composants UI réutilisables - Finitions et espacement parfait
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
    """Widget de statut de connexion - Ultra-compact"""
    
    def __init__(self, service_name="Service"):
        super().__init__()
        self.service_name = service_name
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        self.status_label = QLabel("❌ Non connecté")
        self.status_label.setFixedWidth(120)
        self.status_label.setFixedHeight(32)  # MÊME HAUTEUR que le bouton
        
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #ffffff; font-size: 12px; margin-left: 5px;")
        
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
                    border-radius: 3px;
                    border: 1px solid #28a745;
                    color: #28a745;
                    font-weight: bold;
                    font-size: 11px;
                    background-color: transparent;
                }
            """)
        else:
            self.status_label.setText("❌ Non connecté")
            self.status_label.setStyleSheet("""
                QLabel {
                    padding: 6px 10px;
                    border-radius: 3px;
                    border: 1px solid #dc3545;
                    color: #dc3545;
                    font-weight: bold;
                    font-size: 11px;
                    background-color: transparent;
                }
            """)
        
        self.info_label.setText(info_text)


class LogControlPanel(QWidget):
    """Panneau de contrôle pour les logs - Ultra-compact"""
    
    export_requested = pyqtSignal()
    clear_requested = pyqtSignal()
    filter_changed = pyqtSignal(str, bool)
    
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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # === SECTION FILTRES À GAUCHE ===
        filters_container = QWidget()
        filters_layout = QHBoxLayout()
        filters_layout.setContentsMargins(0, 0, 0, 0)
        filters_layout.setSpacing(8)
        
        # Label filtres
        filters_label = QLabel("Filtres:")
        filters_label.setStyleSheet("""
            QLabel {
                font-weight: bold; 
                font-size: 11px; 
                color: #ffffff;
                margin-right: 6px;
            }
        """)
        filters_layout.addWidget(filters_label)
        
        # Checkboxes filtres
        self.filter_checkboxes = {}
        
        filter_configs = [
            ('DEBUG', '#6c757d'),
            ('INFO', '#17a2b8'),
            ('SUCCESS', '#28a745'),
            ('WARNING', '#ffc107'),
            ('ERROR', '#dc3545')
        ]
        
        for level, color in filter_configs:
            checkbox = QCheckBox(level)
            checkbox.setChecked(self.filters[level])
            checkbox.setStyleSheet(f"""
                QCheckBox {{
                    font-size: 10px;
                    font-weight: 600;
                    color: {color};
                    spacing: 4px;
                    margin-right: 4px;
                }}
                QCheckBox::indicator {{
                    width: 14px;
                    height: 14px;
                    border-radius: 2px;
                }}
                QCheckBox::indicator:checked {{
                    background-color: {color};
                    border: 1px solid {color};
                }}
                QCheckBox::indicator:unchecked {{
                    background-color: transparent;
                    border: 1px solid #dee2e6;
                }}
                QCheckBox::indicator:hover {{
                    border: 1px solid {color};
                }}
            """)
            
            checkbox.stateChanged.connect(lambda state, lvl=level: self.on_filter_changed(lvl, state == 2))
            
            self.filter_checkboxes[level] = checkbox
            filters_layout.addWidget(checkbox)
        
        filters_container.setLayout(filters_layout)
        layout.addWidget(filters_container)
        
        layout.addStretch()
        
        # === BOUTONS À DROITE ===
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(5)
        
        # Bouton tout/aucun
        self.toggle_all_btn = QPushButton("Tout")
        self.toggle_all_btn.setToolTip("Sélectionner/Désélectionner tous les filtres")
        self.toggle_all_btn.clicked.connect(self.toggle_all_filters)
        self.toggle_all_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #6c757d;
                color: #6c757d;
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 10px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #6c757d;
                color: white;
            }
        """)
        buttons_layout.addWidget(self.toggle_all_btn)
        
        # Bouton export
        self.export_btn = QPushButton("Exporter")
        self.export_btn.clicked.connect(self.export_requested.emit)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #28a745;
                color: #28a745;
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 10px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #28a745;
                color: white;
            }
        """)
        buttons_layout.addWidget(self.export_btn)
        
        # Bouton clear
        self.clear_btn = QPushButton("Effacer")
        self.clear_btn.clicked.connect(self.clear_requested.emit)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #dc3545;
                color: #dc3545;
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 10px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #dc3545;
                color: white;
            }
        """)
        buttons_layout.addWidget(self.clear_btn)
        
        buttons_container.setLayout(buttons_layout)
        layout.addWidget(buttons_container)
        
        self.setLayout(layout)
        
        # Style du conteneur principal - AUCUN padding
        self.setStyleSheet("""
            LogControlPanel {
                background-color: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
        """)
    
    def on_filter_changed(self, level, enabled):
        try:
            self.filters[level] = enabled
            print(f"Filtre {level} {'activé' if enabled else 'désactivé'}")
            self.filter_changed.emit(level, enabled)
        except Exception as e:
            print(f"Erreur changement filtre {level}: {e}")
    
    def toggle_all_filters(self):
        all_checked = all(self.filters.values())
        new_state = not all_checked
        
        for level, checkbox in self.filter_checkboxes.items():
            checkbox.setChecked(new_state)
        
        self.toggle_all_btn.setText("Aucun" if new_state else "Tout")
    
    def get_active_filters(self):
        return [level for level, enabled in self.filters.items() if enabled]


class LogDisplay(QTextEdit):
    """Zone d'affichage des logs avec filtrage par niveau"""
    
    def __init__(self, title="Logs"):
        super().__init__()
        self.title = title
        self.all_logs = []
        self.active_filters = {'DEBUG', 'INFO', 'SUCCESS', 'WARNING', 'ERROR'}
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
                border-radius: 4px;
                padding: 10px;
                line-height: 1.4;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            }
        """)
    
    def add_welcome_message(self):
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
        try:
            timestamp = time.strftime("%H:%M:%S")
            self.all_logs.append((message, level, timestamp))
            
            if level in self.active_filters:
                self._append_log_to_display(message, level, timestamp)
            
        except Exception as e:
            print(f"Erreur ajout log: {e}")
    
    def _append_log_to_display(self, message, level, timestamp):
        try:
            cursor = self.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            
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
            
            scrollbar = self.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
        except Exception as e:
            print(f"Erreur affichage log: {e}")
    
    def update_filter(self, level, enabled):
        try:
            if enabled:
                self.active_filters.add(level)
            else:
                self.active_filters.discard(level)
            
            self._refresh_display()
            print(f"Filtre {level} {'activé' if enabled else 'désactivé'}. Filtres actifs: {self.active_filters}")
            
        except Exception as e:
            print(f"Erreur mise à jour filtre {level}: {e}")
    
    def _refresh_display(self):
        try:
            scrollbar = self.verticalScrollBar()
            scroll_position = scrollbar.value()
            was_at_bottom = scroll_position >= scrollbar.maximum() - 10
            
            self.clear()
            self.add_welcome_message()
            
            for message, level, timestamp in self.all_logs:
                if level in self.active_filters:
                    self._append_log_to_display(message, level, timestamp)
            
            if was_at_bottom:
                scrollbar.setValue(scrollbar.maximum())
            else:
                scrollbar.setValue(min(scroll_position, scrollbar.maximum()))
                
        except Exception as e:
            print(f"Erreur rafraîchissement affichage: {e}")
    
    def clear_logs(self):
        try:
            self.clear()
            self.all_logs = []
            self.add_welcome_message()
            
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
        try:
            all_logs_text = []
            for message, level, timestamp in self.all_logs:
                all_logs_text.append(f"[{timestamp}] {level} | {message}")
            return '\n'.join(all_logs_text)
        except Exception as e:
            print(f"Erreur récupération tous les logs: {e}")
            return ""


class ActionButton(QPushButton):
    """Bouton d'action stylisé - PADDING CORRIGÉ"""
    
    def __init__(self, text, color='primary', icon=""):
        super().__init__(f"{icon} {text}" if icon else text)
        self.color = color
        self.apply_style()
    
    def apply_style(self):
        colors = {
            'primary': '#007bff',
            'success': '#28a745',
            'info': '#17a2b8',
            'warning': '#ffc107',
            'danger': '#dc3545',
            'secondary': '#6c757d',
        }
        
        base_color = colors.get(self.color, '#007bff')
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {base_color};
                color: white;
                border: none;
                padding: 12px 10px;
                border-radius: 4px;
                text-align: center;
                font-size: 12px;
                min-height: 20px;
            }}
            QPushButton:hover {{
                opacity: 0.8;
            }}
            QPushButton:disabled {{
                background-color: #6c757d;
            }}
        """)


class SectionHeader(QWidget):
    """En-tête de section ultra-compact"""
    
    def __init__(self, title, icon="", version_widget=None):
        super().__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 2)
        layout.setSpacing(0)
        
        title_text = f"{icon} {title}" if icon else title
        title_label = QLabel(title_text)
        title_label.setStyleSheet("""
            font-size: 13px; 
            font-weight: bold; 
            color: #ffffff;
            padding: 2px 0px;
        """)
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        if version_widget is not None:
            layout.addWidget(version_widget)
        
        self.setLayout(layout)


class ConfigurationGroup(QGroupBox):
    """Groupe de configuration - ESPACEMENT AMÉLIORÉ"""
    
    def __init__(self, title, icon=""):
        display_title = f"{icon} {title}" if icon else title
        super().__init__(display_title)
        self.setMaximumHeight(70)
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11px;
                border: 1px solid #555;
                border-radius: 4px;
                margin-top: 10px;
                margin-bottom: 8px;
                padding-top: 12px;
                background-color: transparent;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
                color: #ffffff;
                font-size: 11px;
                font-weight: bold;
                background-color: transparent;
            }
        """)


class ActionGrid(QWidget):
    """Grille d'actions - ESPACEMENT ENTRE GROUPES AUGMENTÉ"""
    
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(15)  # ESPACEMENT AUGMENTÉ entre les groupes !
        self.groups = {}
        self.setLayout(self.layout)
    
    def add_group(self, group_name, icon=""):
        display_title = f"{icon} {group_name}" if icon else group_name
        group = QGroupBox(display_title)
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(8, 8, 8, 8)
        group_layout.setSpacing(10)
        group.setLayout(group_layout)
        
        # Style avec titre BIEN POSITIONNÉ et PLUS D'ESPACE
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #555;
                border-radius: 4px;
                margin-top: 15px;
                margin-bottom: 10px;
                padding-top: 10px;
                background-color: transparent;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                top: 10px;
                padding: 0 6px 0 6px;
                color: #ffffff;
                font-size: 12px;
                font-weight: bold;
                background-color: #2b2b2b;
                text-align: center;
            }
        """)
        
        self.groups[group_name] = group_layout
        self.layout.addWidget(group)
        
        return group_layout
    
    def add_action_to_group(self, group_name, button):
        if group_name in self.groups:
            self.groups[group_name].addWidget(button)
    
    def enable_group(self, group_name, enabled=True):
        if group_name in self.groups:
            layout = self.groups[group_name]
            for i in range(layout.count()):
                widget = layout.itemAt(i).widget()
                if isinstance(widget, QPushButton):
                    widget.setEnabled(enabled)


class WidgetFactory:
    """Factory pour créer des widgets standardisés"""
    
    @staticmethod
    def create_config_button(text, color='primary', icon=""):
        """Bouton de configuration CLEAN et ALIGNÉ avec le statut"""
        btn = QPushButton(f"{icon} {text}" if icon else text)
        
        # Style CLEAN et compact
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #007bff;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                font-weight: 600;
                font-size: 11px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: #0056b3;
            }}
        """)
        
        # MÊME TAILLE que le statut de connexion
        btn.setFixedWidth(120)  # Même largeur
        btn.setFixedHeight(32)  # Même hauteur
        
        return btn
    
    @staticmethod
    def create_info_label(text=""):
        label = QLabel(text)
        label.setStyleSheet("color: #ffffff; font-size: 11px; margin-left: 5px;")
        return label


class MetricsDisplay(QWidget):
    """Affichage de métriques ultra-compact"""
    
    def __init__(self):
        super().__init__()
        self.metrics = {}
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)
        self.setLayout(self.layout)
    
    def add_metric(self, name, value, icon="", color="#17a2b8"):
        metric_widget = QWidget()
        metric_layout = QVBoxLayout()
        metric_layout.setContentsMargins(8, 4, 8, 4)
        metric_layout.setSpacing(1)
        
        display_text = f"{icon} {value}" if icon else str(value)
        value_label = QLabel(display_text)
        value_label.setStyleSheet(f"""
            font-size: 14px; 
            font-weight: bold; 
            color: {color};
            text-align: center;
        """)
        
        name_label = QLabel(name)
        name_label.setStyleSheet("""
            font-size: 10px; 
            color: #ffffff;
            text-align: center;
            font-weight: 500;
        """)
        
        metric_layout.addWidget(value_label)
        metric_layout.addWidget(name_label)
        metric_widget.setLayout(metric_layout)
        
        metric_widget.setStyleSheet(f"""
            QWidget {{
                background-color: transparent;
                border: 1px solid {color};
                border-radius: 4px;
                margin: 1px;
            }}
        """)
        
        self.metrics[name] = value_label
        self.layout.addWidget(metric_widget)
    
    def update_metric(self, name, value, icon=""):
        if name in self.metrics:
            display_text = f"{icon} {value}" if icon else str(value)
            self.metrics[name].setText(display_text)
    
    def clear_metrics(self):
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
        
        self.setStyleSheet("""
            QTableWidget {
                gridline-color: #dee2e6;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }
            QHeaderView::section {
                background-color: #e9ecef;
                padding: 4px;
                font-weight: bold;
                border: 1px solid #dee2e6;
            }
        """)
        
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    
    def add_status_row(self, data):
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
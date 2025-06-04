#!/usr/bin/env python3
"""
Script d'analyse et de refactorisation automatique ToolboxPyQt6
Analyse les fichiers volumineux et propose/effectue une refactorisation
"""

import ast
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class ClassInfo:
    """Information sur une classe"""
    name: str
    line_start: int
    line_end: int
    methods: List[str]
    imports_used: Set[str]
    responsibilities: List[str]


@dataclass
class FunctionInfo:
    """Information sur une fonction"""
    name: str
    line_start: int
    line_end: int
    imports_used: Set[str]
    complexity: int


@dataclass
class FileAnalysis:
    """Analyse complète d'un fichier"""
    path: Path
    total_lines: int
    classes: List[ClassInfo]
    functions: List[FunctionInfo]
    imports: List[str]
    complexity_score: int
    refactoring_suggestions: List[str]


class CodeAnalyzer(ast.NodeVisitor):
    """Analyseur de code Python basé sur AST"""
    
    def __init__(self, source_code: str):
        self.source_lines = source_code.split('\n')
        self.imports = []
        self.classes = []
        self.functions = []
        self.current_class = None
        
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(f"import {alias.name}")
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        module = node.module or ""
        names = [alias.name for alias in node.names]
        self.imports.append(f"from {module} import {', '.join(names)}")
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        class_info = ClassInfo(
            name=node.name,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            methods=[],
            imports_used=set(),
            responsibilities=[]
        )
        
        self.current_class = class_info
        self.classes.append(class_info)
        
        # Analyser les méthodes
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                class_info.methods.append(item.name)
                
                # Analyser les responsabilités basées sur les noms de méthodes
                responsibilities = self._analyze_method_responsibilities(item.name)
                class_info.responsibilities.extend(responsibilities)
        
        self.generic_visit(node)
        self.current_class = None
    
    def visit_FunctionDef(self, node):
        if self.current_class is None:  # Fonction standalone
            func_info = FunctionInfo(
                name=node.name,
                line_start=node.lineno,
                line_end=node.end_lineno or node.lineno,
                imports_used=set(),
                complexity=self._calculate_complexity(node)
            )
            self.functions.append(func_info)
        
        self.generic_visit(node)
    
    def _analyze_method_responsibilities(self, method_name: str) -> List[str]:
        """Analyse les responsabilités basées sur le nom de la méthode"""
        responsibilities = []
        
        # Responsabilités UI
        ui_keywords = ['init_ui', 'setup_', 'create_', 'update_', 'on_', 'show_', 'hide_', 'display_']
        if any(keyword in method_name.lower() for keyword in ui_keywords):
            responsibilities.append("UI")
        
        # Responsabilités réseau
        network_keywords = ['ssh_', 'connect_', 'execute_', 'command_', 'network_', 'scan_']
        if any(keyword in method_name.lower() for keyword in network_keywords):
            responsibilities.append("Network")
        
        # Responsabilités données
        data_keywords = ['load_', 'save_', 'import_', 'export_', 'parse_', 'format_']
        if any(keyword in method_name.lower() for keyword in data_keywords):
            responsibilities.append("Data")
        
        # Responsabilités Proxmox
        proxmox_keywords = ['proxmox_', 'vm_', 'qemu_', 'agent_', 'install_']
        if any(keyword in method_name.lower() for keyword in proxmox_keywords):
            responsibilities.append("Proxmox")
        
        return responsibilities
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calcule la complexité cyclomatique approximative"""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity


def analyze_file(file_path: Path) -> FileAnalysis:
    """Analyse un fichier Python"""
    try:
        content = file_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        # Parser AST
        tree = ast.parse(content)
        analyzer = CodeAnalyzer(content)
        analyzer.visit(tree)
        
        # Calculer la complexité globale
        total_complexity = sum(func.complexity for func in analyzer.functions)
        for cls in analyzer.classes:
            total_complexity += len(cls.methods) * 2  # Approximation
        
        # Générer des suggestions
        suggestions = generate_refactoring_suggestions(
            len(lines), analyzer.classes, analyzer.functions
        )
        
        return FileAnalysis(
            path=file_path,
            total_lines=len(lines),
            classes=analyzer.classes,
            functions=analyzer.functions,
            imports=analyzer.imports,
            complexity_score=total_complexity,
            refactoring_suggestions=suggestions
        )
        
    except Exception as e:
        print(f"❌ Erreur analyse {file_path}: {e}")
        return None


def generate_refactoring_suggestions(total_lines: int, classes: List[ClassInfo], functions: List[FunctionInfo]) -> List[str]:
    """Génère des suggestions de refactorisation"""
    suggestions = []
    
    # Suggestions basées sur la taille
    if total_lines > 500:
        suggestions.append(f"🚨 Fichier très volumineux ({total_lines} lignes) - Refactorisation recommandée")
    elif total_lines > 300:
        suggestions.append(f"⚠️ Fichier volumineux ({total_lines} lignes) - Envisager une refactorisation")
    
    # Suggestions basées sur les classes
    for cls in classes:
        class_lines = cls.line_end - cls.line_start
        if class_lines > 200:
            suggestions.append(f"🔧 Classe '{cls.name}' trop volumineuse ({class_lines} lignes)")
        
        if len(cls.methods) > 15:
            suggestions.append(f"📦 Classe '{cls.name}' a trop de méthodes ({len(cls.methods)})")
        
        # Analyser les responsabilités multiples
        unique_responsibilities = set(cls.responsibilities)
        if len(unique_responsibilities) > 2:
            suggestions.append(f"🎯 Classe '{cls.name}' a plusieurs responsabilités: {', '.join(unique_responsibilities)}")
    
    # Suggestions basées sur les fonctions
    complex_functions = [f for f in functions if f.complexity > 10]
    if complex_functions:
        suggestions.append(f"🔀 {len(complex_functions)} fonctions très complexes à simplifier")
    
    return suggestions


def print_analysis_results(analyses: List[FileAnalysis]):
    """Affiche les résultats d'analyse"""
    print("📊 RÉSULTATS D'ANALYSE")
    print("=" * 60)
    
    # Tri par nombre de lignes (desc)
    analyses.sort(key=lambda x: x.total_lines, reverse=True)
    
    print(f"\n📋 Top fichiers volumineux:")
    for i, analysis in enumerate(analyses[:10], 1):
        status = "🚨" if analysis.total_lines > 500 else "⚠️" if analysis.total_lines > 300 else "✅"
        print(f"{i:2d}. {status} {analysis.path.name:<30} {analysis.total_lines:4d} lignes")
    
    print(f"\n🔍 Analyse détaillée:")
    for analysis in analyses:
        if analysis.total_lines > 200:  # Seulement les gros fichiers
            print(f"\n📄 {analysis.path}")
            print(f"   Lignes: {analysis.total_lines}")
            print(f"   Classes: {len(analysis.classes)}")
            print(f"   Fonctions: {len(analysis.functions)}")
            print(f"   Complexité: {analysis.complexity_score}")
            
            if analysis.refactoring_suggestions:
                print("   Suggestions:")
                for suggestion in analysis.refactoring_suggestions:
                    print(f"     • {suggestion}")


def create_refactoring_structure(analysis: FileAnalysis) -> Dict[str, str]:
    """Crée la structure de refactorisation pour un fichier"""
    suggestions = {}
    
    if "main_window" in analysis.path.name:
        suggestions = {
            "src/ui/components/connection_panel.py": "Panneau de connexion Proxmox",
            "src/ui/components/log_display.py": "Affichage des logs avec filtres", 
            "src/ui/components/tab_manager.py": "Gestionnaire d'onglets",
            "src/ui/controllers/main_controller.py": "Logique principale",
            "src/ui/controllers/proxmox_controller.py": "Contrôleur Proxmox",
            "src/ui/models/app_state.py": "État global de l'application"
        }
    
    elif "network_tab" in analysis.path.name:
        suggestions = {
            "src/ui/tabs/network/network_ui.py": "Interface réseau",
            "src/ui/tabs/network/device_table.py": "Tableau des équipements",
            "src/ui/tabs/network/command_panel.py": "Panneau de commandes",
            "src/network/device_manager.py": "Gestion des équipements",
            "src/network/ssh_client.py": "Client SSH réutilisable",
            "src/network/command_executor.py": "Exécuteur de commandes"
        }
    
    elif "proxmox_handler" in analysis.path.name:
        suggestions = {
            "src/handlers/proxmox/proxmox_client.py": "Client API Proxmox",
            "src/handlers/proxmox/vm_manager.py": "Gestion des VMs",
            "src/handlers/proxmox/node_manager.py": "Gestion des nœuds",
            "src/handlers/proxmox/storage_manager.py": "Gestion du stockage",
            "src/handlers/proxmox/qemu_agent/agent_installer.py": "Installation QEMU Agent"
        }
    
    elif "qemu_agent_dialog" in analysis.path.name:
        suggestions = {
            "src/ui/dialogs/qemu_agent/qemu_agent_dialog.py": "Interface principale",
            "src/ui/dialogs/qemu_agent/ssh_credentials_dialog.py": "Dialogue credentials",
            "src/ui/dialogs/qemu_agent/vm_table_widget.py": "Tableau des VMs",
            "src/services/qemu_agent_service.py": "Service d'installation",
            "src/services/installation_thread.py": "Thread d'installation"
        }
    
    return suggestions


def extract_class_from_file(file_path: Path, class_name: str, output_path: Path) -> bool:
    """Extrait une classe vers un nouveau fichier"""
    try:
        content = file_path.read_text(encoding='utf-8')
        tree = ast.parse(content)
        
        # Trouver la classe
        class_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                class_node = node
                break
        
        if not class_node:
            print(f"❌ Classe '{class_name}' non trouvée dans {file_path}")
            return False
        
        # Extraire le code de la classe
        lines = content.split('\n')
        class_lines = lines[class_node.lineno-1:class_node.end_lineno]
        
        # Analyser les imports nécessaires
        imports_needed = extract_imports_for_class(content, class_lines)
        
        # Créer le nouveau fichier
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        new_content = []
        new_content.extend(imports_needed)
        new_content.append("")
        new_content.extend(class_lines)
        
        output_path.write_text('\n'.join(new_content), encoding='utf-8')
        print(f"✅ Classe '{class_name}' extraite vers {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur extraction {class_name}: {e}")
        return False


def extract_imports_for_class(full_content: str, class_lines: List[str]) -> List[str]:
    """Détermine les imports nécessaires pour une classe"""
    # Analyse simple basée sur les mots-clés trouvés
    class_content = '\n'.join(class_lines)
    needed_imports = []
    
    # Imports PyQt6 communs
    pyqt_widgets = ['QWidget', 'QVBoxLayout', 'QHBoxLayout', 'QLabel', 'QPushButton', 'QTableWidget', 'QMessageBox']
    pyqt_core = ['Qt', 'QThread', 'pyqtSignal']
    
    if any(widget in class_content for widget in pyqt_widgets):
        needed_imports.append("from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton")
    
    if any(core in class_content for core in pyqt_core):
        needed_imports.append("from PyQt6.QtCore import Qt, QThread, pyqtSignal")
    
    # Autres imports spécifiques trouvés dans le fichier original
    original_imports = []
    for line in full_content.split('\n'):
        if line.strip().startswith(('import ', 'from ')) and 'PyQt6' not in line:
            original_imports.append(line.strip())
    
    # Ajouter les imports qui semblent nécessaires
    for imp in original_imports:
        if any(word in class_content for word in imp.split()):
            needed_imports.append(imp)
    
    return needed_imports


def create_refactored_files(analysis: FileAnalysis) -> bool:
    """Crée les fichiers refactorisés pour un fichier analysé"""
    print(f"\n🔧 Refactorisation de {analysis.path.name}")
    
    structure = create_refactoring_structure(analysis)
    if not structure:
        print(f"⚠️ Pas de structure de refactorisation définie pour {analysis.path.name}")
        return False
    
    print("📁 Structure proposée:")
    for path, description in structure.items():
        print(f"   • {path:<50} - {description}")
    
    confirm = input(f"\n❓ Créer cette structure? (o/N): ").lower()
    if confirm not in ['o', 'oui', 'y', 'yes']:
        return False
    
    # Créer les dossiers
    created_files = []
    for file_path in structure.keys():
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Créer un fichier de base avec la structure
        if not path.exists():
            content = create_base_file_content(path, structure[file_path])
            path.write_text(content, encoding='utf-8')
            created_files.append(path)
            print(f"✅ Créé: {path}")
        
        # Créer __init__.py si nécessaire
        init_file = path.parent / "__init__.py"
        if not init_file.exists():
            init_file.write_text('"""Module init file"""', encoding='utf-8')
    
    print(f"\n🎉 {len(created_files)} fichiers créés!")
    print("📋 Prochaines étapes:")
    print("   1. Déplacer le code approprié dans chaque fichier")
    print("   2. Mettre à jour les imports")
    print("   3. Tester la refactorisation")
    
    return True


def create_base_file_content(file_path: Path, description: str) -> str:
    """Crée le contenu de base pour un nouveau fichier"""
    class_name = file_path.stem.title().replace('_', '')
    
    if 'dialog' in file_path.name:
        template = f'''"""
{description}
"""
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

class {class_name}(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("{description}")
        self.init_ui()
    
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        layout = QVBoxLayout()
        
        # TODO: Ajouter les composants UI
        label = QLabel("{description}")
        layout.addWidget(label)
        
        self.setLayout(layout)
'''
    
    elif 'widget' in file_path.name or 'panel' in file_path.name:
        template = f'''"""
{description}
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class {class_name}(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        layout = QVBoxLayout()
        
        # TODO: Ajouter les composants UI
        label = QLabel("{description}")
        layout.addWidget(label)
        
        self.setLayout(layout)
'''
    
    elif 'controller' in file_path.name:
        template = f'''"""
{description}
"""
from PyQt6.QtCore import QObject, pyqtSignal

class {class_name}(QObject):
    # Signaux
    status_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup()
    
    def setup(self):
        """Configuration initiale"""
        # TODO: Initialisation du contrôleur
        pass
'''
    
    elif 'manager' in file_path.name or 'service' in file_path.name:
        template = f'''"""
{description}
"""
from PyQt6.QtCore import QObject, pyqtSignal

class {class_name}(QObject):
    # Signaux
    operation_completed = pyqtSignal(bool, str)  # success, message
    
    def __init__(self):
        super().__init__()
        self.setup()
    
    def setup(self):
        """Configuration initiale"""
        # TODO: Initialisation du service
        pass
'''
    
    else:
        template = f'''"""
{description}
"""

class {class_name}:
    def __init__(self):
        """Initialisation de {class_name}"""
        # TODO: Implémentation
        pass
'''
    
    return template


def main():
    """Fonction principale"""
    print("🔍 ANALYSEUR ET REFACTORISATION AUTOMATIQUE")
    print("=" * 50)
    
    # Trouver tous les fichiers Python
    src_path = Path("src")
    if not src_path.exists():
        print("❌ Dossier 'src' non trouvé. Exécutez d'abord la migration.")
        return
    
    python_files = list(src_path.rglob("*.py"))
    if Path("main.py").exists():
        python_files.append(Path("main.py"))
    
    print(f"📄 {len(python_files)} fichiers Python trouvés")
    
    # Analyser les fichiers
    analyses = []
    for file_path in python_files:
        if file_path.name != "__init__.py":
            print(f"🔍 Analyse: {file_path}")
            analysis = analyze_file(file_path)
            if analysis:
                analyses.append(analysis)
    
    # Afficher les résultats
    print_analysis_results(analyses)
    
    # Proposer la refactorisation des gros fichiers
    big_files = [a for a in analyses if a.total_lines > 300]
    if big_files:
        print(f"\n🚨 {len(big_files)} fichiers nécessitent une refactorisation")
        
        for analysis in big_files:
            print(f"\n" + "="*60)
            print(f"📄 {analysis.path.name} ({analysis.total_lines} lignes)")
            
            if analysis.refactoring_suggestions:
                print("💡 Suggestions:")
                for suggestion in analysis.refactoring_suggestions:
                    print(f"   • {suggestion}")
            
            refactor = input(f"\n❓ Refactoriser {analysis.path.name}? (o/N): ").lower()
            if refactor in ['o', 'oui', 'y', 'yes']:
                create_refactored_files(analysis)
    
    print(f"\n✨ Analyse terminée!")
    print(f"📊 Résumé:")
    print(f"   • {len(analyses)} fichiers analysés")
    print(f"   • {len(big_files)} fichiers volumineux détectés") 
    print(f"   • Ligne moyenne: {sum(a.total_lines for a in analyses) // len(analyses)}")


if __name__ == "__main__":
    main()
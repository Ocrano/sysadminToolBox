#!/usr/bin/env python3
"""
Script de migration automatique pour la refactorisation Toolbox PyQt6
Crée la nouvelle structure de dossiers et sauvegarde l'ancien code
"""

import os
import shutil
import datetime
from pathlib import Path

class ToolboxRefactorSetup:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root).resolve()
        self.src_path = self.project_root / "src"
        self.backup_path = self.project_root / "backup_original"
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print(f"🔧 Setup de refactorisation Toolbox PyQt6")
        print(f"📁 Dossier projet: {self.project_root}")
        print(f"⏰ Timestamp: {self.timestamp}")
        print("=" * 60)
    
    def backup_original_files(self):
        """Sauvegarde les fichiers originaux"""
        print("💾 Sauvegarde des fichiers originaux...")
        
        # Créer le dossier de backup
        self.backup_path.mkdir(exist_ok=True)
        backup_src = self.backup_path / f"src_backup_{self.timestamp}"
        backup_src.mkdir(exist_ok=True)
        
        # Fichiers à sauvegarder
        files_to_backup = [
            "main.py",
            "src/ui/main_window.py",
            "src/ui/tabs/network_tab.py", 
            "src/handlers/proxmox_handler.py"
        ]
        
        for file_path in files_to_backup:
            source = self.project_root / file_path
            if source.exists():
                # Créer la structure de dossiers dans le backup
                backup_file = backup_src / file_path
                backup_file.parent.mkdir(parents=True, exist_ok=True)
                
                shutil.copy2(source, backup_file)
                print(f"  ✅ Sauvegardé: {file_path}")
            else:
                print(f"  ⚠️  Non trouvé: {file_path}")
        
        print(f"📦 Backup créé dans: {backup_src}")
        return True
    
    def create_new_structure(self):
        """Crée la nouvelle structure de dossiers"""
        print("\n🏗️  Création de la nouvelle structure...")
        
        # Nouvelle structure
        new_dirs = [
            "src/ui/controllers",
            "src/ui/components", 
            "src/services",
            "src/models",
            "src/network",  # Pour futures extensions
            "config",       # Pour configurations
            "resources",    # Pour ressources
            "tests",        # Pour tests futurs
            "docs"          # Pour documentation
        ]
        
        for dir_path in new_dirs:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  📁 Créé: {dir_path}")
        
        return True
    
    def create_init_files(self):
        """Crée les fichiers __init__.py nécessaires"""
        print("\n📝 Création des fichiers __init__.py...")
        
        init_files = [
            "src/ui/controllers/__init__.py",
            "src/ui/components/__init__.py",
            "src/services/__init__.py", 
            "src/models/__init__.py",
            "src/network/__init__.py"
        ]
        
        init_content = {
            "src/ui/controllers/__init__.py": '"""Contrôleurs MVC pour l\'interface utilisateur"""\n',
            "src/ui/components/__init__.py": '"""Composants UI réutilisables"""\n',
            "src/services/__init__.py": '"""Services métier de l\'application"""\n',
            "src/models/__init__.py": '"""Modèles de données"""\n',
            "src/network/__init__.py": '"""Extensions réseau"""\n'
        }
        
        for init_file in init_files:
            full_path = self.project_root / init_file
            content = init_content.get(init_file, '"""Module package"""\n')
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"  ✅ Créé: {init_file}")
        
        return True
    
    def create_readme_files(self):
        """Crée des fichiers README pour documenter chaque dossier"""
        print("\n📖 Création des fichiers README...")
        
        readme_content = {
            "src/ui/controllers/README.md": """# Contrôleurs MVC

Ce dossier contient les contrôleurs qui gèrent la logique métier séparée de l'interface utilisateur.

## Fichiers à placer ici:
- `main_controller.py` : Contrôleur principal de MainWindow

## Pattern MVC:
- **Model** : Services (src/services/)  
- **View** : Interface UI (src/ui/)
- **Controller** : Logique métier (ici)
""",
            
            "src/ui/components/README.md": """# Composants UI Réutilisables

Ce dossier contient les widgets et composants UI standardisés.

## Fichiers à placer ici:
- `common_widgets.py` : Widgets réutilisables (ActionButton, LogDisplay, etc.)

## Avantages:
- Consistance visuelle
- Réutilisabilité
- Maintenance centralisée
""",
            
            "src/services/README.md": """# Services Métier

Ce dossier contient les services qui gèrent la logique métier de l'application.

## Fichiers à placer ici:
- `proxmox_service.py` : Service Proxmox modulaire
- `ssh_service.py` : Service SSH centralisé

## Principes:
- Séparation des responsabilités
- Services indépendants
- Facilité de test
""",
            
            "src/models/README.md": """# Modèles de Données

Ce dossier contiendra les modèles de données de l'application (futur).

## Exemples futurs:
- `device.py` : Modèle pour équipements réseau
- `vm.py` : Modèle pour machines virtuelles  
- `node.py` : Modèle pour nœuds Proxmox
""",
            
            "config/README.md": """# Configuration

Ce dossier contiendra les fichiers de configuration par défaut.

## Fichiers futurs:
- `default_config.json` : Configuration par défaut
- `settings.yaml` : Paramètres utilisateur
""",
            
            "tests/README.md": """# Tests

Ce dossier contiendra les tests unitaires et d'intégration.

## Structure future:
- `test_services/` : Tests des services
- `test_ui/` : Tests de l'interface
- `test_integration/` : Tests d'intégration
"""
        }
        
        for readme_path, content in readme_content.items():
            full_path = self.project_root / readme_path
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  📄 Créé: {readme_path}")
        
        return True
    
    def create_placeholder_files(self):
        """Crée des fichiers de placeholder pour maintenir la structure Git"""
        print("\n🎯 Création de placeholders...")
        
        placeholder_dirs = [
            "resources/icons",
            "resources/styles", 
            "resources/templates",
            "logs"
        ]
        
        for dir_path in placeholder_dirs:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            
            # Créer un fichier .gitkeep
            gitkeep = full_path / ".gitkeep"
            with open(gitkeep, 'w') as f:
                f.write(f"# Placeholder pour maintenir {dir_path} dans Git\n")
            
            print(f"  📌 Créé: {dir_path}/.gitkeep")
        
        return True
    
    def create_migration_guide(self):
        """Crée un guide de migration détaillé"""
        print("\n📋 Création du guide de migration...")
        
        guide_content = f"""# Guide de Migration - Toolbox PyQt6 Refactorisé

## 🎯 Objectif
Migration vers une architecture MVC avec réduction de 61% du code.

## 📅 Migration créée le: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 📁 Nouvelle Structure Créée

```
src/
├── ui/
│   ├── controllers/          # 🆕 Contrôleurs MVC
│   ├── components/           # 🆕 Composants réutilisables
│   ├── dialogs/              # ✅ Existant (à optimiser)
│   └── tabs/                 # ✅ Existant
├── services/                 # 🆕 Services métier  
├── models/                   # 🆕 Modèles de données (futur)
└── network/                  # 🆕 Extensions réseau (futur)
```

## 📦 Fichiers Sauvegardés
Les fichiers originaux sont dans: `backup_original/src_backup_{self.timestamp}/`

## 🔄 Prochaines Étapes

### 1. Placer les Nouveaux Fichiers
Copiez les fichiers générés par Claude dans ces emplacements:

```
📁 src/ui/controllers/
  └── main_controller.py              # 🆕 Contrôleur principal

📁 src/ui/components/  
  └── common_widgets.py               # 🆕 Composants UI

📁 src/services/
  ├── proxmox_service.py              # 🆕 Service Proxmox modulaire
  └── ssh_service.py                  # 🆕 Service SSH centralisé

📁 src/ui/
  ├── main_window_refactored.py       # 🆕 MainWindow refactorisée
  └── tabs/
      └── network_tab_refactored.py   # 🆕 NetworkTab refactorisé
```

### 2. Modifier main.py
Remplacez le contenu de `main.py` par la version refactorisée fournie.

### 3. Tests
1. Testez la connexion Proxmox
2. Testez les scripts PowerShell  
3. Testez l'onglet Network
4. Testez l'import IP Plan

### 4. Migration Progressive (Recommandé)
- Gardez l'ancien code en parallèle
- Testez chaque fonctionnalité
- Validez avant de supprimer l'ancien code

## 🐛 Debugging
- Vérifiez les imports
- Consultez les logs dans l'onglet Tools
- Les README dans chaque dossier expliquent l'organisation

## 📞 Support
En cas de problème, vérifiez:
1. Structure des dossiers créée correctement
2. Tous les __init__.py présents  
3. Imports relatifs corrects
4. Fichiers placés aux bons endroits
"""
        
        guide_path = self.project_root / "MIGRATION_GUIDE.md"
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(guide_content)
        
        print(f"  📖 Guide créé: MIGRATION_GUIDE.md")
        return True
    
    def show_file_placement_instructions(self):
        """Affiche les instructions détaillées de placement des fichiers"""
        print("\n" + "="*80)
        print("🎯 INSTRUCTIONS DE PLACEMENT DES FICHIERS")
        print("="*80)
        
        instructions = [
            ("📁 src/ui/controllers/main_controller.py", 
             "Contrôleur principal - Logique métier de MainWindow"),
            
            ("📁 src/ui/components/common_widgets.py", 
             "Composants UI réutilisables - ActionButton, LogDisplay, etc."),
            
            ("📁 src/services/proxmox_service.py", 
             "Service Proxmox modulaire - Remplace proxmox_handler.py"),
            
            ("📁 src/services/ssh_service.py", 
             "Service SSH centralisé - Gestion équipements réseau"),
            
            ("📁 src/ui/main_window_refactored.py", 
             "MainWindow refactorisée - 300 lignes vs 800"),
            
            ("📁 src/ui/tabs/network_tab_refactored.py", 
             "NetworkTab refactorisé - 300 lignes vs 900"),
            
            ("📁 main.py (remplacer le contenu)", 
             "Point d'entrée modifié pour utiliser les nouveaux services")
        ]
        
        for i, (path, description) in enumerate(instructions, 1):
            print(f"{i}. {path}")
            print(f"   💡 {description}")
            print()
        
        print("⚠️  IMPORTANT:")
        print("   - Copiez les fichiers générés par Claude aux emplacements ci-dessus")
        print("   - Ne supprimez PAS les anciens fichiers pour l'instant")
        print("   - Testez la nouvelle version avant de nettoyer")
        print()
        print("📖 Consultez MIGRATION_GUIDE.md pour plus de détails")
        
        return True
    
    def run_setup(self):
        """Exécute le setup complet"""
        try:
            print("🚀 Démarrage du setup de refactorisation...\n")
            
            # Étapes du setup
            steps = [
                ("Sauvegarde des fichiers originaux", self.backup_original_files),
                ("Création de la nouvelle structure", self.create_new_structure),
                ("Création des fichiers __init__.py", self.create_init_files),
                ("Création des fichiers README", self.create_readme_files),
                ("Création des placeholders", self.create_placeholder_files),
                ("Création du guide de migration", self.create_migration_guide),
                ("Instructions de placement", self.show_file_placement_instructions)
            ]
            
            for step_name, step_func in steps:
                try:
                    step_func()
                except Exception as e:
                    print(f"❌ Erreur dans {step_name}: {e}")
                    return False
            
            print("\n" + "="*80)
            print("🎉 SETUP TERMINÉ AVEC SUCCÈS!")
            print("="*80)
            print("✅ Structure créée")
            print("✅ Fichiers sauvegardés") 
            print("✅ Guide de migration créé")
            print("✅ Instructions de placement affichées")
            print()
            print("🔄 Prochaine étape: Copiez les fichiers générés par Claude")
            print("📖 Consultez MIGRATION_GUIDE.md pour les détails")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur générale du setup: {e}")
            return False

def main():
    """Point d'entrée principal"""
    import sys
    
    # Déterminer le dossier racine du projet
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = "."
    
    # Vérifier que nous sommes dans le bon dossier
    project_path = Path(project_root).resolve()
    
    if not (project_path / "src").exists():
        print("❌ Erreur: Dossier 'src' non trouvé!")
        print("💡 Exécutez ce script depuis la racine de votre projet Toolbox")
        print("   ou spécifiez le chemin: python setup_refactor.py /chemin/vers/projet")
        return False
    
    # Lancer le setup
    setup = ToolboxRefactorSetup(project_root)
    return setup.run_setup()

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
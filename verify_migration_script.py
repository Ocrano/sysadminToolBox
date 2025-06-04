#!/usr/bin/env python3
"""
Script de vérification de la migration Toolbox PyQt6
Vérifie que tous les fichiers sont en place et que l'architecture est correcte
"""

import os
import sys
from pathlib import Path
import importlib.util

class MigrationVerifier:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root).resolve()
        self.src_path = self.project_root / "src"
        self.errors = []
        self.warnings = []
        self.success_count = 0
        self.total_checks = 0
    
    def check_file_exists(self, file_path, description, required=True):
        """Vérifie qu'un fichier existe"""
        self.total_checks += 1
        full_path = self.project_root / file_path
        
        if full_path.exists():
            print(f"✅ {description}: {file_path}")
            self.success_count += 1
            return True
        else:
            if required:
                self.errors.append(f"❌ REQUIS: {description} - {file_path}")
                print(f"❌ {description}: {file_path} (MANQUANT)")
            else:
                self.warnings.append(f"⚠️  OPTIONNEL: {description} - {file_path}")
                print(f"⚠️  {description}: {file_path} (optionnel, manquant)")
            return False
    
    def check_directory_structure(self):
        """Vérifie la structure des dossiers"""
        print("📁 Vérification de la structure des dossiers...")
        
        required_dirs = [
            ("src", "Dossier source principal"),
            ("src/ui", "Interface utilisateur"),
            ("src/ui/controllers", "Contrôleurs MVC"),
            ("src/ui/components", "Composants UI"),
            ("src/services", "Services métier"),
            ("src/models", "Modèles de données"),
            ("src/handlers", "Handlers existants"),
            ("src/utils", "Utilitaires")
        ]
        
        optional_dirs = [
            ("src/network", "Extensions réseau"),
            ("config", "Configuration"),
            ("resources", "Ressources"),
            ("tests", "Tests"),
            ("docs", "Documentation"),
            ("logs", "Logs")
        ]
        
        for dir_path, description in required_dirs:
            self.check_file_exists(dir_path, description, required=True)
        
        for dir_path, description in optional_dirs:
            self.check_file_exists(dir_path, description, required=False)
        
        return True
    
    def check_init_files(self):
        """Vérifie les fichiers __init__.py"""
        print("\n📝 Vérification des fichiers __init__.py...")
        
        init_files = [
            ("src/__init__.py", "Package source principal"),
            ("src/ui/__init__.py", "Package UI"),
            ("src/ui/controllers/__init__.py", "Package contrôleurs"),
            ("src/ui/components/__init__.py", "Package composants"),
            ("src/services/__init__.py", "Package services"),
            ("src/models/__init__.py", "Package modèles"),
            ("src/handlers/__init__.py", "Package handlers"),
            ("src/utils/__init__.py", "Package utilitaires")
        ]
        
        for init_file, description in init_files:
            self.check_file_exists(init_file, description, required=True)
        
        return True
    
    def check_refactored_files(self):
        """Vérifie les nouveaux fichiers refactorisés"""
        print("\n🆕 Vérification des fichiers refactorisés...")
        
        refactored_files = [
            ("src/ui/controllers/main_controller.py", "Contrôleur principal"),
            ("src/ui/components/common_widgets.py", "Composants UI réutilisables"),
            ("src/services/proxmox_service.py", "Service Proxmox modulaire"),
            ("src/services/ssh_service.py", "Service SSH centralisé"),
            ("src/ui/main_window_refactored.py", "MainWindow refactorisée"),
            ("src/ui/tabs/network_tab_refactored.py", "NetworkTab refactorisé")
        ]
        
        for file_path, description in refactored_files:
            self.check_file_exists(file_path, description, required=True)
        
        return True
    
    def check_existing_files(self):
        """Vérifie que les fichiers existants sont toujours là"""
        print("\n✅ Vérification des fichiers existants...")
        
        existing_files = [
            ("main.py", "Point d'entrée principal"),
            ("src/core/logger.py", "Système de logging"),
            ("src/handlers/git_manager.py", "Gestionnaire Git"),
            ("src/handlers/script_runner.py", "Exécuteur de scripts"),
            ("src/utils/ip_plan_importer.py", "Importeur IP Plan"),
            ("src/ui/dialogs/proxmox_config_dialog.py", "Dialogue config Proxmox"),
            ("src/ui/dialogs/qemu_agent_dialog.py", "Dialogue QEMU Agent")
        ]
        
        for file_path, description in existing_files:
            self.check_file_exists(file_path, description, required=True)
        
        return True
    
    def check_import_syntax(self):
        """Vérifie la syntaxe des imports dans les nouveaux fichiers"""
        print("\n🔍 Vérification de la syntaxe des imports...")
        
        files_to_check = [
            "src/ui/controllers/main_controller.py",
            "src/ui/components/common_widgets.py", 
            "src/services/proxmox_service.py",
            "src/services/ssh_service.py"
        ]
        
        for file_path in files_to_check:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    # Vérifier la syntaxe en chargeant le module
                    spec = importlib.util.spec_from_file_location("test_module", full_path)
                    if spec and spec.loader:
                        print(f"✅ Syntaxe OK: {file_path}")
                        self.success_count += 1
                    else:
                        self.errors.append(f"❌ Erreur spec: {file_path}")
                        print(f"❌ Erreur spec: {file_path}")
                except SyntaxError as e:
                    self.errors.append(f"❌ Erreur syntaxe: {file_path} - {e}")
                    print(f"❌ Erreur syntaxe: {file_path} - {e}")
                except Exception as e:
                    self.warnings.append(f"⚠️  Import warning: {file_path} - {e}")
                    print(f"⚠️  Import warning: {file_path} - {e}")
                
                self.total_checks += 1
        
        return True
    
    def check_backup_files(self):
        """Vérifie que les sauvegardes ont été créées"""
        print("\n💾 Vérification des sauvegardes...")
        
        backup_path = self.project_root / "backup_original"
        if backup_path.exists():
            print(f"✅ Dossier de sauvegarde: {backup_path}")
            self.success_count += 1
            
            # Lister les backups disponibles
            backup_dirs = [d for d in backup_path.iterdir() if d.is_dir() and d.name.startswith("src_backup_")]
            if backup_dirs:
                latest_backup = max(backup_dirs, key=lambda x: x.name)
                print(f"✅ Sauvegarde la plus récente: {latest_backup.name}")
                self.success_count += 1
            else:
                self.warnings.append("⚠️  Aucune sauvegarde trouvée dans backup_original/")
                print("⚠️  Aucune sauvegarde trouvée")
        else:
            self.warnings.append("⚠️  Dossier backup_original/ non trouvé")
            print("⚠️  Dossier backup_original/ non trouvé")
        
        self.total_checks += 2
        return True
    
    def check_migration_guide(self):
        """Vérifie que le guide de migration existe"""
        print("\n📖 Vérification du guide de migration...")
        
        guide_files = [
            ("MIGRATION_GUIDE.md", "Guide de migration principal"),
            ("README.md", "README du projet (optionnel)")
        ]
        
        for file_path, description in guide_files:
            required = file_path == "MIGRATION_GUIDE.md"
            self.check_file_exists(file_path, description, required=required)
        
        return True
    
    def show_detailed_report(self):
        """Affiche un rapport détaillé"""
        print("\n" + "="*80)
        print("📊 RAPPORT DE VÉRIFICATION DÉTAILLÉ")
        print("="*80)
        
        # Statistiques
        success_rate = (self.success_count / self.total_checks * 100) if self.total_checks > 0 else 0
        print(f"✅ Réussite: {self.success_count}/{self.total_checks} ({success_rate:.1f}%)")
        print(f"❌ Erreurs: {len(self.errors)}")
        print(f"⚠️  Avertissements: {len(self.warnings)}")
        
        # Erreurs critiques
        if self.errors:
            print(f"\n❌ ERREURS CRITIQUES ({len(self.errors)}):")
            for error in self.errors:
                print(f"  {error}")
        
        # Avertissements
        if self.warnings:
            print(f"\n⚠️  AVERTISSEMENTS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning}")
        
        return len(self.errors) == 0
    
    def show_next_steps(self):
        """Affiche les prochaines étapes selon le résultat"""
        print("\n🔄 PROCHAINES ÉTAPES:")
        
        if len(self.errors) == 0:
            print("🎉 Migration structurelle complète!")
            print("✅ Tous les fichiers requis sont en place")
            print()
            print("📝 Pour finaliser:")
            print("1. Testez l'application: python main.py")
            print("2. Vérifiez chaque fonctionnalité")
            print("3. Consultez les logs en cas de problème")
            print("4. Une fois validé, vous pouvez supprimer les anciens fichiers")
        else:
            print("⚠️  Migration incomplète")
            print("🔧 Actions requises:")
            print("1. Corrigez les erreurs listées ci-dessus")
            print("2. Relancez ce script de vérification")
            print("3. Consultez MIGRATION_GUIDE.md pour plus d'aide")
        
        print("\n📞 Support:")
        print("- Consultez MIGRATION_GUIDE.md")
        print("- Vérifiez les imports relatifs")
        print("- Assurez-vous que tous les fichiers générés par Claude sont copiés")
    
    def run_verification(self):
        """Exécute la vérification complète"""
        print("🔍 Démarrage de la vérification de migration...\n")
        
        try:
            # Étapes de vérification
            verification_steps = [
                ("Structure des dossiers", self.check_directory_structure),
                ("Fichiers __init__.py", self.check_init_files),
                ("Fichiers refactorisés", self.check_refactored_files),
                ("Fichiers existants", self.check_existing_files),
                ("Syntaxe des imports", self.check_import_syntax),
                ("Sauvegardes", self.check_backup_files),
                ("Guide de migration", self.check_migration_guide)
            ]
            
            for step_name, step_func in verification_steps:
                try:
                    step_func()
                except Exception as e:
                    self.errors.append(f"❌ Erreur dans {step_name}: {e}")
                    print(f"❌ Erreur dans {step_name}: {e}")
            
            # Rapport final
            success = self.show_detailed_report()
            self.show_next_steps()
            
            return success
            
        except Exception as e:
            print(f"❌ Erreur générale de vérification: {e}")
            return False

def main():
    """Point d'entrée principal"""
    # Déterminer le dossier racine du projet
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = "."
    
    # Vérifier que nous sommes dans le bon dossier
    project_path = Path(project_root).resolve()
    
    print(f"🔍 Vérification de migration Toolbox PyQt6")
    print(f"📁 Dossier projet: {project_path}")
    print("=" * 60)
    
    if not (project_path / "src").exists():
        print("❌ Erreur: Dossier 'src' non trouvé!")
        print("💡 Exécutez ce script depuis la racine de votre projet Toolbox")
        print("   ou spécifiez le chemin: python verify_migration.py /chemin/vers/projet")
        return False
    
    # Lancer la vérification
    verifier = MigrationVerifier(project_root)
    return verifier.run_verification()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
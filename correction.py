#!/usr/bin/env python3
"""
Script de correction rapide des imports problématiques
Corrige les références à l'ancien proxmox_handler
"""

import os
import re
from pathlib import Path

class ImportsFixer:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root).resolve()
        print("🔧 Correction des imports problématiques")
        print("=" * 40)
    
    def fix_imports_in_file(self, file_path, fixes):
        """Applique les corrections d'imports dans un fichier"""
        full_path = self.project_root / file_path
        
        if not full_path.exists():
            print(f"⚠️  Fichier non trouvé: {file_path}")
            return False
        
        try:
            # Lire le fichier
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            modified = False
            
            # Appliquer chaque correction
            for old_pattern, new_replacement in fixes.items():
                if old_pattern in content:
                    content = content.replace(old_pattern, new_replacement)
                    modified = True
                    print(f"  ✅ Corrigé: {old_pattern} → {new_replacement}")
            
            # Sauvegarder si modifié
            if modified:
                # Créer une sauvegarde
                backup_path = full_path.with_suffix(full_path.suffix + '.backup')
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                
                # Écrire le fichier corrigé
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"✅ Fichier corrigé: {file_path}")
                print(f"💾 Sauvegarde: {backup_path}")
                return True
            else:
                print(f"ℹ️  Aucune correction nécessaire: {file_path}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur traitement {file_path}: {e}")
            return False
    
    def fix_all_import_issues(self):
        """Corrige tous les problèmes d'imports identifiés"""
        
        # Corrections à appliquer par fichier
        files_to_fix = {
            
            # main_window_refactored.py - Remplacer references à proxmox_handler
            "src/ui/main_window_refactored.py": {
                "self.controller.proxmox_handler": "self.controller.proxmox_service",
                "proxmox_handler": "proxmox_service",
                "from ..handlers.proxmox_handler import": "# Removed old import",
            },
            
            # qemu_agent_dialog.py - Corriger si nécessaire
            "src/ui/dialogs/qemu_agent_dialog.py": {
                "from ...handlers.proxmox_handler import": "# Import removed - using service passed as parameter",
                "ProxmoxHandler": "ProxmoxService",
            },
            
            # main_controller.py - Vérifier les références
            "src/ui/controllers/main_controller.py": {
                "proxmox_handler": "proxmox_service",
            },
            
            # network_tab_refactored.py - Vérifier les références  
            "src/ui/tabs/network_tab_refactored.py": {
                "proxmox_handler": "proxmox_service",
            }
        }
        
        fixed_files = 0
        
        for file_path, fixes in files_to_fix.items():
            print(f"\n📝 Traitement: {file_path}")
            if self.fix_imports_in_file(file_path, fixes):
                fixed_files += 1
        
        return fixed_files
    
    def scan_for_problematic_imports(self):
        """Scanne tous les fichiers Python pour détecter les imports problématiques"""
        print("\n🔍 Scan des imports problématiques...")
        
        problematic_patterns = [
            r'from\s+.*proxmox_handler\s+import',
            r'import\s+.*proxmox_handler',
            r'from\s+.*main_window\s+import',
            r'import\s+.*main_window(?!_refactored)',
            r'from\s+.*network_tab\s+import',
            r'import\s+.*network_tab(?!_refactored)',
        ]
        
        python_files = list(self.project_root.rglob("*.py"))
        issues_found = []
        
        for py_file in python_files:
            # Ignorer les fichiers de backup et les anciens fichiers
            if any(skip in str(py_file) for skip in ['.backup', 'backup_', '_old', 'main_window.py', 'network_tab.py', 'proxmox_handler.py']):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for line_num, line in enumerate(content.split('\n'), 1):
                    for pattern in problematic_patterns:
                        if re.search(pattern, line):
                            relative_path = py_file.relative_to(self.project_root)
                            issues_found.append({
                                'file': relative_path,
                                'line': line_num,
                                'content': line.strip(),
                                'pattern': pattern
                            })
                            
            except Exception as e:
                print(f"⚠️  Erreur lecture {py_file}: {e}")
        
        if issues_found:
            print(f"\n❌ {len(issues_found)} imports problématiques trouvés:")
            for issue in issues_found:
                print(f"  📄 {issue['file']}:{issue['line']}")
                print(f"     {issue['content']}")
        else:
            print("✅ Aucun import problématique détecté")
        
        return issues_found
    
    def run_complete_fix(self):
        """Exécute la correction complète"""
        try:
            print("🚀 Correction complète des imports...\n")
            
            # Étape 1: Scanner les problèmes
            issues = self.scan_for_problematic_imports()
            
            # Étape 2: Appliquer les corrections
            fixed_files = self.fix_all_import_issues()
            
            # Étape 3: Re-scanner pour vérifier
            print("\n🔍 Vérification post-correction...")
            remaining_issues = self.scan_for_problematic_imports()
            
            # Résumé
            print("\n" + "="*50)
            print("📊 RÉSUMÉ DE LA CORRECTION")
            print("="*50)
            print(f"📝 Fichiers corrigés: {fixed_files}")
            print(f"❌ Problèmes initiaux: {len(issues)}")
            print(f"⚠️  Problèmes restants: {len(remaining_issues)}")
            
            if len(remaining_issues) == 0:
                print("\n🎉 TOUS LES IMPORTS CORRIGÉS!")
                print("🚀 Testez maintenant: python main.py")
                return True
            else:
                print("\n⚠️  Corrections manuelles nécessaires:")
                for issue in remaining_issues:
                    print(f"  📄 {issue['file']}:{issue['line']} - {issue['content']}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur générale: {e}")
            return False

def main():
    """Point d'entrée principal"""
    import sys
    
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = "."
    
    fixer = ImportsFixer(project_root)
    success = fixer.run_complete_fix()
    
    if success:
        print("\n✅ Correction terminée avec succès!")
        print("🔄 Relancez maintenant: python main.py")
    else:
        print("\n⚠️  Correction partielle - vérifiez les problèmes restants")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
#!/usr/bin/env python3
"""
Correction de l'import NetworkTab
Deux solutions possibles selon le nom de classe dans le fichier
"""

from pathlib import Path
import re

def fix_network_import():
    """Corrige l'import de NetworkTab"""
    project_root = Path(".")
    
    print("🔧 Correction de l'import NetworkTab...")
    
    # 1. Vérifier le nom de la classe dans network_tab_refactored.py
    network_file = project_root / "src/ui/tabs/network_tab_refactored.py"
    main_window_file = project_root / "src/ui/main_window_refactored.py"
    
    if not network_file.exists():
        print("❌ Fichier network_tab_refactored.py manquant!")
        print("💡 Copiez l'artifact 'network_tab_refactored' dans:")
        print(f"   {network_file}")
        return False
    
    # Lire le fichier network_tab_refactored.py pour trouver le nom de classe
    try:
        with open(network_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Chercher le nom de la classe
        class_matches = re.findall(r'class\s+(\w+)\s*\(', content)
        main_class = None
        
        for class_name in class_matches:
            if 'Network' in class_name and 'Tab' in class_name:
                main_class = class_name
                break
        
        if not main_class:
            print("❌ Aucune classe NetworkTab* trouvée dans network_tab_refactored.py")
            return False
        
        print(f"✅ Classe trouvée: {main_class}")
        
        # 2. Corriger l'import dans main_window_refactored.py
        if not main_window_file.exists():
            print("❌ main_window_refactored.py manquant!")
            return False
        
        with open(main_window_file, 'r', encoding='utf-8') as f:
            main_content = f.read()
        
        # Backup
        with open(main_window_file.with_suffix('.py.backup2'), 'w', encoding='utf-8') as f:
            f.write(main_content)
        
        # Corriger l'import selon le nom de classe trouvé
        old_import = "from .tabs.network_tab_refactored import NetworkTabRefactored"
        new_import = f"from .tabs.network_tab_refactored import {main_class}"
        
        if old_import in main_content:
            main_content = main_content.replace(old_import, new_import)
            print(f"✅ Import corrigé: {old_import} → {new_import}")
        
        # Corriger l'instanciation
        old_instance = "network_tab = NetworkTabRefactored(self)"
        new_instance = f"network_tab = {main_class}(self)"
        
        if old_instance in main_content:
            main_content = main_content.replace(old_instance, new_instance)
            print(f"✅ Instanciation corrigée: {old_instance} → {new_instance}")
        
        # Sauvegarder
        with open(main_window_file, 'w', encoding='utf-8') as f:
            f.write(main_content)
        
        print("✅ Correction terminée!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def alternative_fix():
    """Solution alternative: renommer la classe dans network_tab_refactored.py"""
    project_root = Path(".")
    network_file = project_root / "src/ui/tabs/network_tab_refactored.py"
    
    if not network_file.exists():
        print("❌ Fichier network_tab_refactored.py manquant!")
        return False
    
    try:
        with open(network_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Backup
        with open(network_file.with_suffix('.py.backup'), 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Trouver et renommer la classe principale
        if 'class NetworkTab(' in content:
            content = content.replace('class NetworkTab(', 'class NetworkTabRefactored(')
            print("✅ Classe renommée: NetworkTab → NetworkTabRefactored")
        elif 'class NetworkTabRefactored(' in content:
            print("✅ Classe déjà nommée NetworkTabRefactored")
        else:
            print("❌ Aucune classe NetworkTab trouvée")
            return False
        
        # Ajouter alias à la fin du fichier si pas déjà présent
        if "# Alias pour la compatibilité" not in content:
            content += "\n\n# Alias pour la compatibilité\nNetworkTab = NetworkTabRefactored\n"
            print("✅ Alias ajouté pour compatibilité")
        
        # Sauvegarder
        with open(network_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Fichier network_tab_refactored.py corrigé!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    """Essaie les deux solutions"""
    print("🚀 Correction de l'import NetworkTab...\n")
    
    print("--- Solution 1: Corriger l'import ---")
    if fix_network_import():
        print("\n🎉 Solution 1 réussie!")
        print("🚀 Testez: python main.py")
        return
    
    print("\n--- Solution 2: Renommer la classe ---")
    if alternative_fix():
        print("\n🎉 Solution 2 réussie!")
        print("🚀 Testez: python main.py")
        return
    
    print("\n❌ Aucune solution automatique n'a fonctionné")
    print("\n🔧 SOLUTION MANUELLE:")
    print("1. Ouvrez src/ui/tabs/network_tab_refactored.py")
    print("2. Vérifiez le nom de la classe (ligne qui commence par 'class')")
    print("3. Dans main_window_refactored.py, ajustez l'import:")
    print("   from .tabs.network_tab_refactored import [NomDeVotreClasse]")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Script simple pour redimensionner les icônes Proxmox et vSphere
"""

import sys
import os
from pathlib import Path

def resize_with_pil():
    """Utilise PIL/Pillow pour redimensionner (plus fiable)"""
    try:
        from PIL import Image
        print("✅ Utilisation de PIL/Pillow")
        return True
    except ImportError:
        print("❌ PIL/Pillow non installé. Installez avec: pip install Pillow")
        return False

def resize_with_pyqt():
    """Utilise PyQt6 pour redimensionner"""
    try:
        import sys
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QPixmap
        from PyQt6.QtCore import Qt
        
        # Créer l'application Qt OBLIGATOIRE
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        print("✅ Utilisation de PyQt6")
        return True, QPixmap, Qt
    except ImportError:
        print("❌ PyQt6 non disponible")
        return False, None, None

def resize_image_pil(input_path, output_path, size=(24, 24)):
    """Redimensionne avec PIL"""
    try:
        from PIL import Image
        
        with Image.open(input_path) as img:
            # Convertir en RGBA si nécessaire (pour transparence)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Redimensionner en gardant l'aspect ratio
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Créer une nouvelle image avec fond transparent
            new_img = Image.new('RGBA', size, (0, 0, 0, 0))
            
            # Centrer l'image redimensionnée
            x = (size[0] - img.width) // 2
            y = (size[1] - img.height) // 2
            new_img.paste(img, (x, y), img)
            
            # Sauvegarder
            new_img.save(output_path, 'PNG')
            return True
            
    except Exception as e:
        print(f"❌ Erreur PIL: {e}")
        return False

def resize_image_pyqt(input_path, output_path, size=24):
    """Redimensionne avec PyQt6"""
    try:
        success, QPixmap, Qt = resize_with_pyqt()
        if not success:
            return False
        
        pixmap = QPixmap(str(input_path))
        if pixmap.isNull():
            print(f"❌ Impossible de charger: {input_path}")
            return False
        
        # Redimensionner
        scaled = pixmap.scaled(
            size, size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Sauvegarder
        success = scaled.save(str(output_path), 'PNG')
        return success
        
    except Exception as e:
        print(f"❌ Erreur PyQt6: {e}")
        return False

def find_icons():
    """Trouve les icônes dans le projet"""
    base_path = Path.cwd()
    
    # Chemins possibles
    possible_dirs = [
        base_path / "ressources" / "icons",
        base_path / "resources" / "icons"
    ]
    
    icons_found = {}
    
    for dir_path in possible_dirs:
        if dir_path.exists():
            print(f"📁 Vérification: {dir_path}")
            
            # Chercher proxmox.png
            proxmox_file = dir_path / "proxmox.png"
            if proxmox_file.exists():
                icons_found['proxmox'] = proxmox_file
                print(f"   ✅ Trouvé: proxmox.png")
            
            # Chercher vsphere.png
            vsphere_file = dir_path / "vsphere.png"
            if vsphere_file.exists():
                icons_found['vsphere'] = vsphere_file
                print(f"   ✅ Trouvé: vsphere.png")
    
    return icons_found

def get_image_info(file_path):
    """Obtient les informations d'une image"""
    try:
        # Essayer avec PIL d'abord
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                return f"{img.width}x{img.height}"
        except ImportError:
            pass
        
        # Essayer avec PyQt6
        success, QPixmap, Qt = resize_with_pyqt()
        if success:
            pixmap = QPixmap(str(file_path))
            if not pixmap.isNull():
                return f"{pixmap.width()}x{pixmap.height()}"
        
        return "Inconnu"
        
    except Exception as e:
        return f"Erreur: {e}"

def main():
    """Fonction principale"""
    print("🖼️  REDIMENSIONNEUR SIMPLE D'ICÔNES")
    print("=" * 50)
    
    # Trouver les icônes
    icons = find_icons()
    
    if not icons:
        print("❌ Aucune icône trouvée!")
        print("Vérifiez que proxmox.png et vsphere.png sont dans:")
        print("  - ressources/icons/ ")
        print("  - resources/icons/")
        return 1
    
    print(f"\n📊 ICÔNES TROUVÉES:")
    for name, path in icons.items():
        size_info = get_image_info(path)
        print(f"   {name}.png: {size_info}")
    
    # Choisir la méthode de redimensionnement
    print(f"\n🔧 MÉTHODES DISPONIBLES:")
    method = None
    
    if resize_with_pil():
        method = 'pil'
        print("   Utilisation de PIL/Pillow (recommandé)")
    elif resize_with_pyqt()[0]:
        method = 'pyqt'
        print("   Utilisation de PyQt6")
    else:
        print("❌ Aucune méthode disponible!")
        print("Installez PIL: pip install Pillow")
        return 1
    
    # Demander confirmation
    print(f"\n📏 REDIMENSIONNEMENT:")
    size = input("Taille souhaitée (défaut 24): ").strip()
    target_size = int(size) if size.isdigit() else 24
    
    backup = input("Créer des sauvegardes? (o/n, défaut: o): ").strip().lower()
    create_backup = backup != 'n'
    
    print(f"\n🔄 TRAITEMENT:")
    
    for name, original_path in icons.items():
        print(f"\n   📁 {name}.png:")
        
        # Créer sauvegarde si demandé
        if create_backup:
            backup_path = original_path.with_suffix('.backup.png')
            try:
                import shutil
                if not backup_path.exists():
                    shutil.copy2(original_path, backup_path)
                    print(f"      💾 Sauvegarde: {backup_path.name}")
                else:
                    print(f"      💾 Sauvegarde existe déjà")
            except Exception as e:
                print(f"      ⚠️  Échec sauvegarde: {e}")
        
        # Redimensionner
        original_size = get_image_info(original_path)
        print(f"      📏 Taille originale: {original_size}")
        
        success = False
        if method == 'pil':
            success = resize_image_pil(original_path, original_path, (target_size, target_size))
        elif method == 'pyqt':
            success = resize_image_pyqt(original_path, original_path, target_size)
        
        if success:
            new_size = get_image_info(original_path)
            print(f"      ✅ Nouvelle taille: {new_size}")
        else:
            print(f"      ❌ Échec redimensionnement")
    
    print(f"\n✅ TERMINÉ!")
    print(f"Relancez votre application pour voir les icônes redimensionnées.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
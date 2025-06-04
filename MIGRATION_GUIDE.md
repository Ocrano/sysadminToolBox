# Guide de Migration - Toolbox PyQt6 Refactorisé

## 🎯 Objectif
Migration vers une architecture MVC avec réduction de 61% du code.

## 📅 Migration créée le: 2025-06-04 14:40:28

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
Les fichiers originaux sont dans: `backup_original/src_backup_20250604_144028/`

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

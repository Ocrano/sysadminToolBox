# ToolboxPyQt6

Toolbox de gestion infrastructure avec PyQt6 pour l'administration de serveurs Proxmox VE et d'équipements réseau.

## Description

Application desktop développée en Python avec PyQt6 permettant la gestion centralisée d'infrastructures IT :
- Gestion des machines virtuelles Proxmox VE
- Administration d'équipements réseau (Cisco, Fortinet, Allied Telesis, etc.)
- Scanner réseau pour découverte d'équipements
- Installation automatisée de QEMU Guest Agent
- Exécution de scripts PowerShell
- Import de plans d'adressage IP

## Installation

### Prérequis
- Python 3.8 ou supérieur
- Windows 10/11 (pour les scripts PowerShell)

### Installation des dépendances
```bash
pip install -r requirements.txt
```

### Configuration
1. Configurer la connexion Proxmox dans l'interface
2. Définir les credentials SSH pour les équipements réseau
3. Optionnel : Configurer le token GitLab pour les scripts

## Utilisation

### Lancement de l'application
```bash
python main.py
```

### Fonctionnalités principales
- **Onglet Scripts** : Gestion et exécution de scripts PowerShell
- **Onglet Tools** : Actions Proxmox (VMs, QEMU Agent, infrastructure)
- **Onglet Network** : Gestion d'équipements réseau via SSH
- **Onglet Scanner** : Découverte d'équipements sur le réseau
- **Onglet Import IP** : Import de plans d'adressage depuis Excel

## Structure du projet

### Racine
```
ToolboxPyQt6/
├── main.py                    # Point d'entrée principal de l'application
├── requirements.txt           # Dépendances Python requises
├── pyproject.toml            # Configuration moderne du projet
├── README.md                 # Documentation (ce fichier)
├── .gitignore               # Exclusions Git
└── __init__.py              # Package principal (version 0.0.6)
```

### Code source (src/)
```
src/
├── __init__.py              # Package source principal
│
├── core/                    # Composants centraux
│   ├── __init__.py
│   └── logger.py           # Système de logging avec couleurs et déduplication
│
├── ui/                     # Interface utilisateur
│   ├── __init__.py
│   ├── main_window.py      # Fenêtre principale (800+ lignes - nécessite refactorisation)
│   │
│   ├── dialogs/            # Boîtes de dialogue
│   │   ├── __init__.py
│   │   ├── proxmox_config_dialog.py    # Configuration connexion Proxmox
│   │   ├── qemu_agent_dialog.py        # Gestionnaire QEMU Agent (600+ lignes)
│   │   ├── network_config_dialog.py    # Configuration SSH réseau (obsolète)
│   │   └── ip_assignment_dialog.py     # Assignation IPs aux VMs
│   │
│   └── tabs/               # Onglets de l'interface
│       ├── __init__.py
│       ├── network_tab.py           # Gestion équipements réseau (900+ lignes)
│       └── network_scanner_tab.py   # Scanner réseau
│
├── handlers/               # Gestionnaires de services
│   ├── __init__.py
│   ├── proxmox_handler.py  # API Proxmox VE (600+ lignes - nécessite refactorisation)
│   ├── git_manager.py      # Intégration GitLab pour scripts
│   └── script_runner.py    # Exécution scripts PowerShell et SSH
│
├── network/                # Fonctionnalités réseau (VIDE - futur)
│   └── __init__.py
│
└── utils/                  # Utilitaires
    ├── __init__.py
    └── ip_plan_importer.py # Import plans IP depuis Excel
```

### Ressources et outils
```
resources/                  # Ressources application (VIDE - futur)
├── icons/                 # Icônes interface
├── styles/                # Feuilles de style QSS
└── templates/             # Modèles documents

config/                    # Configuration (VIDE - futur)
└── default_config.json    # Configuration par défaut

scripts/                   # Scripts PowerShell
└── README.md             # Documentation scripts

build/                     # Outils de build
└── build_exe.py          # Création exécutable PyInstaller

tests/                     # Tests unitaires (VIDE - futur)
├── __init__.py
└── test_*.py             # Tests à développer

docs/                      # Documentation (VIDE - futur)

logs/                      # Fichiers de logs (VIDE - auto-créé)
└── .gitkeep
```

## Statut des composants

### Composants actifs (utilisés)
- **main.py** : Point d'entrée fonctionnel
- **src/core/logger.py** : Système de logging complet
- **src/ui/main_window.py** : Interface principale (volumineux)
- **src/ui/dialogs/** : Tous les dialogues sont fonctionnels
- **src/ui/tabs/** : Onglets réseau actifs
- **src/handlers/** : Tous les gestionnaires sont opérationnels
- **src/utils/ip_plan_importer.py** : Import Excel fonctionnel
- **build/build_exe.py** : Script de build opérationnel

### Composants en attente (structure créée, vides)
- **resources/** : Dossiers créés mais vides
- **config/** : Prévu pour configurations futures
- **src/network/** : Futur refactorisation du code réseau
- **tests/** : Tests à développer
- **docs/** : Documentation technique à rédiger
- **logs/** : Auto-créé lors de l'exécution

### Fichiers obsolètes identifiés
- **main.py.backup** : Ancienne version (peut être supprimé)
- **build_exe.py.backup** : Ancienne version (peut être supprimé)
- **proxmox_vm_viewer.py** : Non intégré (à supprimer ou intégrer)
- **src/ui/dialogs/network_config_dialog.py** : Doublon avec logique dans network_tab.py

## Problèmes identifiés nécessitant refactorisation

### Fichiers volumineux (>500 lignes)
1. **src/ui/main_window.py** (800+ lignes)
   - Responsabilités multiples : UI + logique Proxmox + logs
   - Doit être séparé en composants + contrôleurs

2. **src/ui/tabs/network_tab.py** (900+ lignes)
   - Mélange interface + SSH + commandes réseau
   - Doit être séparé en modules spécialisés

3. **src/handlers/proxmox_handler.py** (600+ lignes)
   - API + installation QEMU + gestion VMs
   - Doit être séparé par responsabilité

4. **src/ui/dialogs/qemu_agent_dialog.py** (600+ lignes)
   - Interface + logique installation + threads
   - Doit être simplifié et séparé

### Améliorations recommandées
- Créer des composants UI réutilisables
- Séparer la logique métier de l'interface
- Implémenter des services spécialisés (SSH, validation)
- Ajouter des tests unitaires
- Documenter l'API interne

## Build exécutable

### Création d'un .exe autonome
```bash
cd build
python build_exe.py
```

L'exécutable sera créé dans `build/dist/ToolboxPyQt6.exe` et contiendra toutes les dépendances.

### Prérequis build
- PyInstaller installé
- Tous les modules Python présents
- Optionnel : icon.ico pour l'icône

## Développement

### Architecture cible (refactorisation future)
```
src/
├── ui/components/          # Composants UI réutilisables
├── ui/controllers/         # Contrôleurs MVC
├── services/              # Services métier (SSH, validation)
├── models/                # Modèles de données
├── network/parsers/       # Parseurs par équipement
└── handlers/proxmox/      # Modules Proxmox spécialisés
```

### Contribution
1. Analyser les fichiers volumineux avec l'analyseur de code
2. Refactoriser par modules de responsabilité
3. Ajouter des tests pour chaque composant
4. Maintenir la compatibilité avec l'interface existante

## Licence

MIT License - Voir LICENSE pour plus de détails.

## Auteur

Développé par ocrano - Version 0.0.6

## Notes techniques

- Framework : PyQt6
- API Proxmox : proxmoxer
- SSH : paramiko  
- Excel : pandas + openpyxl
- Build : PyInstaller
- Minimum Python : 3.8
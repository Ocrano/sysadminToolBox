import os
import requests
from PyQt6.QtWidgets import QMessageBox
from urllib.parse import quote_plus

class GitLabManager:
    def __init__(self, gitlab_url):
        self.gitlab_url = gitlab_url
        self.token = None  # Token stocké en mémoire

    def set_token(self, token):
        """ Définit le token GitLab """
        self.token = token

    def fetch_and_download_scripts(self):
        """ Récupère et télécharge les scripts PowerShell depuis GitLab dans le dossier 'scripts' """
        if not self.token:
            QMessageBox.warning(None, "Erreur", "Aucun token GitLab fourni.")
            return []

        headers = {"PRIVATE-TOKEN": self.token}
        url = f"{self.gitlab_url}/api/v4/projects/200/repository/tree?ref=jsirufo&path=IVVQ/modulesnew"

        try:
            # Récupérer la liste des fichiers dans le répertoire GitLab
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            # Extraire les fichiers .ps1 depuis la réponse JSON
            scripts = [file['name'] for file in response.json() if file['name'].endswith('.ps1')]

            # Crée le dossier 'scripts' si nécessaire
            if not os.path.exists('scripts'):
                os.makedirs('scripts')

            # Téléchargement de chaque script dans le dossier 'scripts'
            for script_name in scripts:
                self.download_script(script_name)

            # Retourne la liste des scripts locaux dans le dossier 'scripts'
            return os.listdir('scripts')  # Liste tous les fichiers dans le dossier 'scripts'

        except requests.exceptions.RequestException as e:
            QMessageBox.critical(None, "Erreur", f"Erreur GitLab : {e}")
            return []

    def download_script(self, script_name):
        """ Télécharge un script spécifique depuis GitLab dans le dossier 'scripts' """
        if not self.token:
            QMessageBox.warning(None, "Erreur", "Aucun token GitLab fourni.")
            return None

        headers = {"PRIVATE-TOKEN": self.token}
        # Encode correctement le chemin du fichier pour l'URL
        encoded_path = quote_plus(f"IVVQ/modulesnew/{script_name}")
        
        # URL pour télécharger un script spécifique
        url = f"{self.gitlab_url}/api/v4/projects/200/repository/files/{encoded_path}/raw?ref=jsirufo"

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            script_path = os.path.join("scripts", script_name)
            # Enregistre le script localement dans le dossier 'scripts'
            with open(script_path, "wb") as f:
                f.write(response.content)
            return script_path
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(None, "Erreur", f"Erreur de téléchargement du script : {e}")
            return None

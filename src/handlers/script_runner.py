import subprocess
import os
import platform
import paramiko
from PyQt6.QtWidgets import QMessageBox, QInputDialog, QLineEdit
import threading
import time

class ScriptRunner:
    def __init__(self):
        self.ssh_credentials = {}  # Cache des credentials SSH

    def run_script(self, script_path):
        """Exécute un script PowerShell dans une nouvelle fenêtre"""
        if platform.system() == "Windows":
            abs_path = os.path.abspath(script_path)
            try:
                subprocess.Popen(
                    ["powershell.exe", "-NoExit", "-ExecutionPolicy", "Bypass", "-File", abs_path],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                print(f"Script lancé: {abs_path}")
            except Exception as e:
                print(f"Erreur lors de l'exécution du script : {e}")
                QMessageBox.critical(None, "Erreur", f"Erreur lors de l'exécution du script : {e}")
        else:
            print("L'exécution de scripts PowerShell n'est supportée que sous Windows.")
            QMessageBox.information(None, "Information", 
                                  "L'exécution de scripts PowerShell n'est supportée que sous Windows.")

    def execute_on_linux_vms(self, vms_list, script_content=None, command=None):
        """Exécute une commande ou un script sur plusieurs VMs Linux"""
        if not vms_list:
            QMessageBox.information(None, "Aucune VM", "Aucune VM sélectionnée.")
            return

        # Demander les credentials SSH si pas déjà en cache
        if not self.ssh_credentials:
            username, ok1 = QInputDialog.getText(None, "Credentials SSH", "Nom d'utilisateur SSH:")
            if not ok1 or not username:
                return
            
            password, ok2 = QInputDialog.getText(None, "Credentials SSH", "Mot de passe SSH:", 
                                               QLineEdit.EchoMode.Password)
            if not ok2 or not password:
                return
            
            self.ssh_credentials = {'username': username, 'password': password}

        # Si aucune commande spécifiée, demander à l'utilisateur
        if not command and not script_content:
            command, ok = QInputDialog.getText(None, "Commande à exécuter", 
                                             "Entrez la commande à exécuter sur les VMs:")
            if not ok or not command:
                return

        # Exécuter sur chaque VM dans un thread séparé pour éviter le blocage
        results = {}
        threads = []

        def execute_on_single_vm(vm):
            vm_name = vm.get('name', 'VM inconnue')
            vm_ip = vm.get('ip', '')
            
            if vm_ip == "IP non disponible" or not vm_ip:
                results[vm_name] = "❌ IP non disponible"
                return
            
            try:
                if script_content:
                    # Exécuter un script complet
                    result = self.execute_ssh_script(vm_ip, self.ssh_credentials['username'], 
                                                   self.ssh_credentials['password'], script_content)
                else:
                    # Exécuter une commande simple
                    result = self.execute_ssh_command(vm_ip, self.ssh_credentials['username'], 
                                                    self.ssh_credentials['password'], command)
                
                results[vm_name] = f"✅ Succès:\n{result}"
            except Exception as e:
                results[vm_name] = f"❌ Erreur: {str(e)}"

        # Lancer les threads pour chaque VM
        for vm in vms_list:
            thread = threading.Thread(target=execute_on_single_vm, args=(vm,))
            threads.append(thread)
            thread.start()

        # Attendre que tous les threads se terminent
        for thread in threads:
            thread.join()

        # Afficher les résultats
        self.show_execution_results(results)

    def execute_ssh_command(self, ip, username, password, command):
        """Exécute une commande SSH sur une machine distante"""
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(ip, username=username, password=password, timeout=10)
            
            stdin, stdout, stderr = client.exec_command(command)
            
            # Lire la sortie
            output = stdout.read().decode('utf-8', errors='ignore')
            error = stderr.read().decode('utf-8', errors='ignore')
            
            client.close()
            
            result = ""
            if output:
                result += f"Sortie:\n{output}\n"
            if error:
                result += f"Erreurs:\n{error}\n"
            
            return result if result else "Commande exécutée avec succès (pas de sortie)"
            
        except Exception as e:
            raise Exception(f"Erreur SSH sur {ip} : {str(e)}")

    def execute_ssh_script(self, ip, username, password, script_content):
        """Exécute un script complet via SSH"""
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(ip, username=username, password=password, timeout=10)
            
            # Créer un fichier temporaire sur la machine distante
            temp_script_path = f"/tmp/temp_script_{int(time.time())}.sh"
            
            # Écrire le script sur la machine distante
            stdin, stdout, stderr = client.exec_command(f"cat > {temp_script_path}")
            stdin.write(script_content)
            stdin.close()
            
            # Rendre le script exécutable
            client.exec_command(f"chmod +x {temp_script_path}")
            
            # Exécuter le script
            stdin, stdout, stderr = client.exec_command(f"bash {temp_script_path}")
            
            # Lire la sortie
            output = stdout.read().decode('utf-8', errors='ignore')
            error = stderr.read().decode('utf-8', errors='ignore')
            
            # Nettoyer le fichier temporaire
            client.exec_command(f"rm -f {temp_script_path}")
            
            client.close()
            
            result = ""
            if output:
                result += f"Sortie:\n{output}\n"
            if error:
                result += f"Erreurs:\n{error}\n"
            
            return result if result else "Script exécuté avec succès (pas de sortie)"
            
        except Exception as e:
            raise Exception(f"Erreur SSH sur {ip} : {str(e)}")

    def show_execution_results(self, results):
        """Affiche les résultats d'exécution dans une boîte de dialogue"""
        if not results:
            QMessageBox.information(None, "Résultats", "Aucun résultat à afficher.")
            return
        
        result_text = "=== Résultats d'exécution ===\n\n"
        
        for vm_name, result in results.items():
            result_text += f"🖥️  {vm_name}:\n{result}\n"
            result_text += "-" * 50 + "\n"
        
        # Créer une boîte de dialogue avec un texte scrollable
        msg = QMessageBox()
        msg.setWindowTitle("Résultats d'exécution")
        msg.setText("Exécution terminée sur toutes les VMs sélectionnées")
        msg.setDetailedText(result_text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    def clear_ssh_credentials(self):
        """Efface les credentials SSH du cache"""
        self.ssh_credentials = {}

    def run_command_on_vm(self, vm_info, command):
        """Exécute une commande simple sur une VM spécifique"""
        try:
            if not self.ssh_credentials:
                # Demander les credentials si pas en cache
                self.execute_on_linux_vms([vm_info], command=command)
            else:
                vm_name = vm_info.get('name', 'VM inconnue')
                vm_ip = vm_info.get('ip', '')
                
                if vm_ip == "IP non disponible" or not vm_ip:
                    QMessageBox.warning(None, "Erreur", f"IP non disponible pour {vm_name}")
                    return
                
                result = self.execute_ssh_command(vm_ip, self.ssh_credentials['username'], 
                                                self.ssh_credentials['password'], command)
                
                QMessageBox.information(None, f"Résultat - {vm_name}", result)
                
        except Exception as e:
            QMessageBox.critical(None, "Erreur", f"Erreur lors de l'exécution : {str(e)}")


# Fonction standalone pour compatibilité
def execute_ssh_command(ip, username, password, command):
    """Fonction standalone pour l'exécution de commandes SSH (compatibilité)"""
    runner = ScriptRunner()
    try:
        return runner.execute_ssh_command(ip, username, password, command)
    except Exception as e:
        return f"Erreur SSH sur {ip} : {str(e)}"
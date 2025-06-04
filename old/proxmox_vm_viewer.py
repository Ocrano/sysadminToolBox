from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QTabWidget, QWidget, QFormLayout, QProgressBar, QGroupBox, QHBoxLayout
)
from PyQt6.QtCore import Qt
import datetime

class ProxmoxVMViewer(QDialog):
    def __init__(self, proxmox_handler, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Vue des VMs et Infos Proxmox")
        self.resize(700, 500)
        self.proxmox_handler = proxmox_handler
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.tabs = QTabWidget()

        # Onglet VMs
        self.vm_tab = QWidget()
        self.init_vm_tab()
        self.tabs.addTab(self.vm_tab, "Machines Virtuelles")

        # Onglet Infos Serveur
        self.info_tab = QWidget()
        self.init_info_tab()
        self.tabs.addTab(self.info_tab, "Infos Serveur")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def init_vm_tab(self):
        layout = QVBoxLayout()
        self.label = QLabel("Liste des machines virtuelles et statut du noeud")
        layout.addWidget(self.label)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Nom VM", "Statut", "Node"])
        layout.addWidget(self.table)

        self.vm_tab.setLayout(layout)
        self.populate_vm_table()

    def populate_vm_table(self):
        vms = self.proxmox_handler.list_vms()
        self.table.setRowCount(len(vms))
        for row, vm in enumerate(vms):
            self.table.setItem(row, 0, QTableWidgetItem(vm.get("name", "N/A")))
            self.table.setItem(row, 1, QTableWidgetItem(vm.get("status", "unknown")))
            self.table.setItem(row, 2, QTableWidgetItem(vm.get("node", "unknown")))

    def init_info_tab(self):
        layout = QVBoxLayout()

        # Version Proxmox
        version = self.proxmox_handler.get_version()
        version_label = QLabel(f"<b>Version Proxmox:</b> {version}")
        layout.addWidget(version_label)

        # Datastores
        storages = self.proxmox_handler.get_storage_info()
        if storages:
            for node in set(s["node"] for s in storages):
                node_group = QGroupBox(f"Node: {node}")
                node_layout = QVBoxLayout()

                for storage in filter(lambda s: s["node"] == node, storages):
                    storage_name = storage["storage"]
                    storage_type = storage["type"]
                    total = storage.get("total", 0)
                    used = storage.get("used", 0)
                    avail = storage.get("available", 0)

                    # Convertir octets en Go pour affichage plus lisible
                    total_gb = total / (1024**3)
                    used_gb = used / (1024**3)
                    avail_gb = avail / (1024**3)

                    percent_used = (used / total * 100) if total > 0 else 0

                    storage_layout = QFormLayout()
                    storage_label = QLabel(f"{storage_name} ({storage_type})")
                    storage_progress = QProgressBar()
                    storage_progress.setValue(int(percent_used))
                    storage_progress.setFormat(f"{used_gb:.1f} Go / {total_gb:.1f} Go ({percent_used:.1f}%)")

                    storage_layout.addRow(storage_label, storage_progress)
                    node_layout.addLayout(storage_layout)

                node_group.setLayout(node_layout)
                layout.addWidget(node_group)
        else:
            layout.addWidget(QLabel("Aucune information sur les stockages."))

        # Statut noeuds (CPU, RAM, uptime)
        statuses = self.proxmox_handler.get_node_status()
        if statuses:
            for status in statuses:
                node_group = QGroupBox(f"Statut Node: {status['node']}")
                node_layout = QFormLayout()

                cpu_percent = status["cpu"] * 100  # cpu est entre 0 et 1
                mem_total_gb = status["mem_total"] / (1024**3)
                mem_used_gb = status["mem_used"] / (1024**3)
                mem_percent = (status["mem_used"] / status["mem_total"] * 100) if status["mem_total"] > 0 else 0
                uptime_seconds = status["uptime"]
                uptime_str = str(datetime.timedelta(seconds=uptime_seconds))

                cpu_bar = QProgressBar()
                cpu_bar.setValue(int(cpu_percent))
                cpu_bar.setFormat(f"CPU : {cpu_percent:.1f}%")

                mem_bar = QProgressBar()
                mem_bar.setValue(int(mem_percent))
                mem_bar.setFormat(f"RAM : {mem_used_gb:.1f} Go / {mem_total_gb:.1f} Go ({mem_percent:.1f}%)")

                node_layout.addRow(cpu_bar)
                node_layout.addRow(mem_bar)
                node_layout.addRow(QLabel(f"Uptime: {uptime_str}"))

                node_group.setLayout(node_layout)
                layout.addWidget(node_group)
        else:
            layout.addWidget(QLabel("Aucune information sur le statut des noeuds."))

        self.info_tab.setLayout(layout)

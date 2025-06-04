import pandas as pd
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

class IPPlanImporter:
    def __init__(self):
        pass

    def get_column_h(self, file_path, sheet_name="Nommage HL-RL"):
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
            col_index = 7  # colonne H (0-based)
            if col_index >= df.shape[1]:
                raise ValueError(f"La feuille '{sheet_name}' ne contient pas de colonne H.")
            col_values = df.iloc[:, col_index].dropna().astype(str).tolist()
            return col_values
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la lecture du fichier : {e}")

    def get_column_k(self, file_path, sheet_name="Nommage HL-RL"):
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
            col_index = 10  # colonne K (0-based)
            if col_index >= df.shape[1]:
                raise ValueError(f"La feuille '{sheet_name}' ne contient pas de colonne K.")
            col_values = df.iloc[:, col_index].dropna().astype(str).tolist()
            return col_values
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la lecture du fichier : {e}")

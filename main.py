import sys
import os

project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

from config import VAULT_PATH, DECOY_COUNT
from src.services.key_manager import KeyManager
from src.services.crypto_service import CryptoService
from src.ui.main_window import MainWindow

def main():
    print("Starte Cryptyko...")

    key_manager = KeyManager(vault_dir=VAULT_PATH, decoy_count=DECOY_COUNT)

    crypto_service = CryptoService()

    try:
        app = MainWindow(key_manager=key_manager, crypto_service=crypto_service)
        
        app.mainloop()
    except Exception as e:
        print(f"Ein kritischer Fehler beim Starten des UIs ist aufgetreten: {e}")

if __name__ == "__main__":
    main()
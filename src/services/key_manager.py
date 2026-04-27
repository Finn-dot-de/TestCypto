import os
import hashlib
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

class KeyManager:
    def __init__(self, vault_dir: str, decoy_count: int = 5):
        self.vault_dir = vault_dir
        self.decoy_count = decoy_count
        self.current_private_key = None

    def _ensure_vault_exists(self):
        if not os.path.exists(self.vault_dir):
            try:
                os.makedirs(self.vault_dir)
                if os.name == 'nt':
                    os.system(f'attrib +h "{self.vault_dir}"')
            except PermissionError:
                raise PermissionError(f"Keine Schreibrechte für '{self.vault_dir}'. Bitte die Anwendung als Administrator ausführen.")

    def _get_key_filename(self, password: str) -> str:
        pass_bytes = password.encode('utf-8')
        file_hash = hashlib.sha256(pass_bytes).hexdigest()[:16]
        return f"key_{file_hash}.pem"

    def setup_vault(self, password: str):
        self._ensure_vault_exists()
        real_key_filename = self._get_key_filename(password)
        real_key_path = os.path.join(self.vault_dir, real_key_filename)
        
        if os.path.exists(real_key_path):
            return

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self._save_key(private_key, real_key_path, password.encode('utf-8'))

        for _ in range(self.decoy_count):
            decoy_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            random_hash = hashlib.md5(os.urandom(16)).hexdigest()[:16]
            decoy_path = os.path.join(self.vault_dir, f"key_{random_hash}.pem")
            self._save_key(decoy_key, decoy_path, os.urandom(16))

    def _save_key(self, private_key, filepath: str, password_bytes: bytes):
        with open(filepath, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.BestAvailableEncryption(password_bytes)
            ))

    def load_private_key(self, password: str):
        real_key_filename = self._get_key_filename(password)
        real_key_path = os.path.join(self.vault_dir, real_key_filename)

        if not os.path.exists(real_key_path):
            raise FileNotFoundError("Der Schlüssel für dieses Passwort wurde nicht gefunden.")

        with open(real_key_path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=password.encode('utf-8')
            )
        self.current_private_key = private_key
        return private_key
    
    def get_contacts_dir(self):
        path = os.path.join(self.vault_dir, "contacts")
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    def import_contact_key(self, name: str, source_path: str):
        contacts_dir = self.get_contacts_dir()
        dest_path = os.path.join(contacts_dir, f"{name}.pub")
        
        with open(source_path, "rb") as f:
            key_data = f.read()
            serialization.load_pem_public_key(key_data) 
            
        with open(dest_path, "wb") as f:
            f.write(key_data)

    def list_contacts(self) -> list:
        contacts_dir = self.get_contacts_dir()
        return [f.replace(".pub", "") for f in os.listdir(contacts_dir) if f.endswith(".pub")]

    def get_public_key_for_contact(self, name: str):
        if name == "Mein Tresor (Ich selbst)":
            return self.current_private_key.public_key()

        contacts_dir = self.get_contacts_dir()
        path = os.path.join(contacts_dir, f"{name}.pub")
        with open(path, "rb") as f:
            return serialization.load_pem_public_key(f.read())
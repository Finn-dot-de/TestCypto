import struct
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet

class CryptoService:
    """
    Kapselt die reine kryptografische Logik.
    Nimmt Bytes entgegen und gibt Bytes zurück. Keine Datei-Operationen.
    """

    @staticmethod
    def encrypt_payload(data: bytes, public_key: rsa.RSAPublicKey) -> bytes:
        """
        Verschlüsselt die Daten hybrid und packt alles in ein kompaktes Byte-Array.
        Aufbau: [4 Bytes Key-Länge] + [Verschlüsselter Fernet-Key] + [Verschlüsselte Daten]
        """
        fernet_key = Fernet.generate_key()
        fernet = Fernet(fernet_key)
        
        encrypted_data = fernet.encrypt(data)
        
        encrypted_fernet_key = public_key.encrypt(
            fernet_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
    
        key_length_bytes = struct.pack('>I', len(encrypted_fernet_key))
        
        final_payload = key_length_bytes + encrypted_fernet_key + encrypted_data
        
        return final_payload

    @staticmethod
    def decrypt_payload(payload: bytes, private_key: rsa.RSAPrivateKey) -> bytes:
        """
        Zerlegt den Payload, entschlüsselt den Fernet-Key mit RSA und danach die Daten.
        """
        key_length = struct.unpack('>I', payload[:4])[0]
        
        encrypted_fernet_key = payload[4 : 4 + key_length]
        encrypted_data = payload[4 + key_length :]
        
        try:
            decrypted_fernet_key = private_key.decrypt(
                encrypted_fernet_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
        except ValueError:
            raise ValueError("Entschlüsselung fehlgeschlagen. Falscher Private Key oder defekte Daten.")
        
        fernet = Fernet(decrypted_fernet_key)
        decrypted_data = fernet.decrypt(encrypted_data)
        
        return decrypted_data
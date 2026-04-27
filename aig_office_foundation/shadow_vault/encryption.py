import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class VaultEncryption:
    """
    AES-256 GCM File Encryption.
    """
    @staticmethod
    def generate_key() -> bytes:
        return AESGCM.generate_key(bit_length=256)

    @staticmethod
    def encrypt(data: bytes, key: bytes) -> bytes:
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, data, None)
        return base64.b64encode(nonce + ciphertext)

    @staticmethod
    def decrypt(encrypted_data_b64: bytes, key: bytes) -> bytes:
        data = base64.b64decode(encrypted_data_b64)
        nonce = data[:12]
        ciphertext = data[12:]
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None)

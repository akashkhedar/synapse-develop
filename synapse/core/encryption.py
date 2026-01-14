"""
Encryption Service for Data Security

Provides AES-256 encryption for sensitive data at rest.
Used for encrypting database fields and file content.
"""

import base64
import hashlib
import logging
import os
import secrets
from typing import Optional, Union

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    AES-256 encryption service for sensitive data.

    Usage:
        # Encrypt/decrypt strings
        encrypted = EncryptionService.encrypt_field("sensitive data")
        decrypted = EncryptionService.decrypt_field(encrypted)

        # Encrypt/decrypt JSON
        encrypted = EncryptionService.encrypt_json({"key": "value"})
        decrypted = EncryptionService.decrypt_json(encrypted)
    """

    # Key derivation settings
    SALT_LENGTH = 16
    KEY_LENGTH = 32  # 256 bits
    ITERATIONS = 100000

    # Get encryption key from settings or environment
    _master_key: Optional[bytes] = None
    _fernet: Optional[Fernet] = None

    @classmethod
    def _get_master_key(cls) -> bytes:
        """Get or derive the master encryption key"""
        if cls._master_key is not None:
            return cls._master_key

        # Try to get key from settings/environment
        key_source = getattr(settings, "ENCRYPTION_KEY", None)
        if key_source is None:
            key_source = os.environ.get("SYNAPSE_ENCRYPTION_KEY")

        if key_source is None:
            # Generate a deterministic key from Django's SECRET_KEY
            # This is less secure but provides backwards compatibility
            logger.warning(
                "No ENCRYPTION_KEY set. Using derived key from SECRET_KEY. "
                "Set SYNAPSE_ENCRYPTION_KEY environment variable for production."
            )
            key_source = settings.SECRET_KEY

        # Derive a proper encryption key
        if isinstance(key_source, str):
            key_source = key_source.encode("utf-8")

        # Use SHA-256 to get a consistent 32-byte key
        cls._master_key = hashlib.sha256(key_source).digest()
        return cls._master_key

    @classmethod
    def _get_fernet(cls) -> Fernet:
        """Get Fernet instance for symmetric encryption"""
        if cls._fernet is not None:
            return cls._fernet

        key = cls._get_master_key()
        # Fernet requires URL-safe base64 encoded 32-byte key
        fernet_key = base64.urlsafe_b64encode(key)
        cls._fernet = Fernet(fernet_key)
        return cls._fernet

    @classmethod
    def encrypt_field(cls, data: Union[str, bytes]) -> str:
        """
        Encrypt a string field using Fernet (AES-128-CBC with HMAC).

        Args:
            data: String or bytes to encrypt

        Returns:
            Base64-encoded encrypted string
        """
        if data is None:
            return None

        if isinstance(data, str):
            data = data.encode("utf-8")

        fernet = cls._get_fernet()
        encrypted = fernet.encrypt(data)
        return encrypted.decode("utf-8")

    @classmethod
    def decrypt_field(cls, encrypted_data: str) -> str:
        """
        Decrypt a Fernet-encrypted string.

        Args:
            encrypted_data: Base64-encoded encrypted string

        Returns:
            Decrypted string
        """
        if encrypted_data is None:
            return None

        if isinstance(encrypted_data, str):
            encrypted_data = encrypted_data.encode("utf-8")

        fernet = cls._get_fernet()
        try:
            decrypted = fernet.decrypt(encrypted_data)
            return decrypted.decode("utf-8")
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Failed to decrypt data") from e

    @classmethod
    def encrypt_json(cls, data: dict) -> str:
        """
        Encrypt a JSON-serializable dictionary.

        Args:
            data: Dictionary to encrypt

        Returns:
            Base64-encoded encrypted string
        """
        import json

        json_str = json.dumps(data, separators=(",", ":"))
        return cls.encrypt_field(json_str)

    @classmethod
    def decrypt_json(cls, encrypted_data: str) -> dict:
        """
        Decrypt to a JSON dictionary.

        Args:
            encrypted_data: Base64-encoded encrypted string

        Returns:
            Decrypted dictionary
        """
        import json

        decrypted_str = cls.decrypt_field(encrypted_data)
        return json.loads(decrypted_str)

    @classmethod
    def encrypt_file_content(cls, content: bytes) -> bytes:
        """
        Encrypt file content using AES-256-GCM.
        More efficient for larger data.

        Args:
            content: File content to encrypt

        Returns:
            Encrypted bytes (nonce + ciphertext + tag)
        """
        key = cls._get_master_key()
        nonce = secrets.token_bytes(12)  # 96-bit nonce for GCM

        cipher = Cipher(
            algorithms.AES(key), modes.GCM(nonce), backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(content) + encryptor.finalize()

        # Return nonce + ciphertext + tag
        return nonce + ciphertext + encryptor.tag

    @classmethod
    def decrypt_file_content(cls, encrypted_content: bytes) -> bytes:
        """
        Decrypt AES-256-GCM encrypted file content.

        Args:
            encrypted_content: Encrypted bytes (nonce + ciphertext + tag)

        Returns:
            Decrypted file content
        """
        key = cls._get_master_key()

        # Extract nonce, ciphertext, and tag
        nonce = encrypted_content[:12]
        tag = encrypted_content[-16:]
        ciphertext = encrypted_content[12:-16]

        cipher = Cipher(
            algorithms.AES(key), modes.GCM(nonce, tag), backend=default_backend()
        )
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()

    @classmethod
    def generate_key(cls) -> str:
        """
        Generate a new random encryption key.

        Returns:
            Base64-encoded 256-bit key
        """
        key = secrets.token_bytes(32)
        return base64.b64encode(key).decode("utf-8")

    @classmethod
    def hash_for_lookup(cls, data: str) -> str:
        """
        Create a deterministic hash for lookup purposes.
        Useful for searching encrypted fields.

        Args:
            data: Data to hash

        Returns:
            Hex-encoded hash
        """
        key = cls._get_master_key()
        hmac_key = hashlib.sha256(key + b"lookup").digest()

        import hmac as hmac_module

        h = hmac_module.new(hmac_key, data.encode("utf-8"), hashlib.sha256)
        return h.hexdigest()

"""
Encrypted Django Model Fields

Provides transparent field-level encryption for sensitive data at rest.
Data is automatically encrypted before saving and decrypted when loaded.

Usage:
    from core.fields import EncryptedTextField, EncryptedJSONField

    class Annotation(models.Model):
        # Automatically encrypted at rest
        result = EncryptedJSONField(...)
        notes = EncryptedTextField(...)

Security:
    - Uses AES-256 encryption via Fernet
    - Key derived from SYNAPSE_ENCRYPTION_KEY or SECRET_KEY
    - Keys MUST be stored in environment variables, never in database
"""

import json
import logging
from typing import Any, Optional

from django.conf import settings
from django.db import models

from core.encryption import EncryptionService

logger = logging.getLogger(__name__)


class EncryptedFieldMixin:
    """
    Mixin providing encryption/decryption for Django model fields.

    Handles:
    - Automatic encryption on save (from_db_value → to database)
    - Automatic decryption on load (get_prep_value → from database)
    - Graceful handling of unencrypted legacy data
    """

    # Prefix to identify encrypted values
    ENCRYPTED_PREFIX = "enc::"

    def _is_encrypted(self, value: str) -> bool:
        """Check if value is already encrypted"""
        if not isinstance(value, str):
            return False
        return value.startswith(self.ENCRYPTED_PREFIX)

    def _encrypt(self, value: str) -> str:
        """Encrypt a string value"""
        if value is None or value == "":
            return value
        if self._is_encrypted(value):
            return value  # Already encrypted
        try:
            encrypted = EncryptionService.encrypt_field(value)
            return f"{self.ENCRYPTED_PREFIX}{encrypted}"
        except Exception as e:
            logger.error(f"Failed to encrypt field: {e}")
            # In production, you might want to raise here
            return value

    def _decrypt(self, value: str) -> str:
        """Decrypt a string value"""
        if value is None or value == "":
            return value
        if not self._is_encrypted(value):
            return value  # Not encrypted (legacy data)
        try:
            encrypted_data = value[len(self.ENCRYPTED_PREFIX) :]
            return EncryptionService.decrypt_field(encrypted_data)
        except Exception as e:
            logger.error(f"Failed to decrypt field: {e}")
            # Return the raw value if decryption fails
            # This handles cases where data might be corrupted
            return value


class EncryptedTextField(EncryptedFieldMixin, models.TextField):
    """
    A TextField that automatically encrypts data at rest.

    Usage:
        class MyModel(models.Model):
            sensitive_notes = EncryptedTextField(blank=True, default="")

    The data is stored encrypted in the database:
        DB value: "enc::gAAAAB8H3k2L..."
        Python value: "Patient has condition X"
    """

    def get_prep_value(self, value: Optional[str]) -> Optional[str]:
        """Called when saving to database - encrypt the value"""
        value = super().get_prep_value(value)
        if value is None:
            return None
        return self._encrypt(str(value))

    def from_db_value(
        self, value: Optional[str], expression, connection
    ) -> Optional[str]:
        """Called when loading from database - decrypt the value"""
        if value is None:
            return None
        return self._decrypt(value)

    def to_python(self, value: Optional[str]) -> Optional[str]:
        """Called during form validation and deserialization"""
        if value is None:
            return None
        if isinstance(value, str) and self._is_encrypted(value):
            return self._decrypt(value)
        return value


class EncryptedCharField(EncryptedFieldMixin, models.CharField):
    """
    A CharField that automatically encrypts data at rest.

    Note: Encrypted values are longer than original, so set max_length accordingly.
    A 100-char original might become 200+ chars when encrypted.
    """

    def get_prep_value(self, value: Optional[str]) -> Optional[str]:
        """Called when saving to database - encrypt the value"""
        value = super().get_prep_value(value)
        if value is None:
            return None
        return self._encrypt(str(value))

    def from_db_value(
        self, value: Optional[str], expression, connection
    ) -> Optional[str]:
        """Called when loading from database - decrypt the value"""
        if value is None:
            return None
        return self._decrypt(value)

    def to_python(self, value: Optional[str]) -> Optional[str]:
        """Called during form validation and deserialization"""
        if value is None:
            return None
        if isinstance(value, str) and self._is_encrypted(value):
            return self._decrypt(value)
        return value


class EncryptedJSONField(EncryptedFieldMixin, models.TextField):
    """
    A field that stores JSON data encrypted at rest.

    Usage:
        class Annotation(models.Model):
            result = EncryptedJSONField(default=dict)

    In Python: {"label": "cat", "bbox": [10, 20, 100, 200]}
    In Database: "enc::gAAAAB8H3k2L..." (encrypted JSON string)

    Note: This extends TextField (not JSONField) because we need to store
    the encrypted string, not let PostgreSQL parse it as JSON.
    """

    def get_prep_value(self, value: Any) -> Optional[str]:
        """Called when saving to database - serialize and encrypt"""
        if value is None:
            return None

        # Serialize to JSON string
        if isinstance(value, str):
            # Already a string, might be JSON or encrypted
            if self._is_encrypted(value):
                return value
            json_str = value
        else:
            # Convert to JSON string
            try:
                json_str = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
            except (TypeError, ValueError) as e:
                logger.error(f"Failed to serialize JSON: {e}")
                json_str = str(value)

        return self._encrypt(json_str)

    def from_db_value(self, value: Optional[str], expression, connection) -> Any:
        """Called when loading from database - decrypt and deserialize"""
        if value is None:
            return None

        # Decrypt
        decrypted = self._decrypt(value)

        # Parse JSON
        try:
            return json.loads(decrypted)
        except (json.JSONDecodeError, TypeError):
            # Not valid JSON, return as-is (legacy data or error)
            return decrypted

    def to_python(self, value: Any) -> Any:
        """Called during form validation and deserialization"""
        if value is None:
            return None
        if isinstance(value, str):
            if self._is_encrypted(value):
                value = self._decrypt(value)
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        return value

    def value_to_string(self, obj) -> str:
        """Serialization for dumpdata/loaddata"""
        value = self.value_from_object(obj)
        return json.dumps(value) if value is not None else ""


class EncryptedEmailField(EncryptedFieldMixin, models.EmailField):
    """
    An EmailField that encrypts email addresses at rest.

    Note: Searching by email will not work on encrypted data!
    You may need to store a hash for lookups.
    """

    def get_prep_value(self, value: Optional[str]) -> Optional[str]:
        value = super().get_prep_value(value)
        if value is None:
            return None
        return self._encrypt(str(value))

    def from_db_value(
        self, value: Optional[str], expression, connection
    ) -> Optional[str]:
        if value is None:
            return None
        return self._decrypt(value)

    def to_python(self, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str) and self._is_encrypted(value):
            return self._decrypt(value)
        return value


# For easy importing
__all__ = [
    "EncryptedTextField",
    "EncryptedCharField",
    "EncryptedJSONField",
    "EncryptedEmailField",
]

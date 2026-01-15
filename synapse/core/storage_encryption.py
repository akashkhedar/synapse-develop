"""
Cloud Storage Encryption Configuration Helpers

Provides utilities for configuring server-side encryption (SSE)
for cloud storage providers (S3, GCS, Azure).

File uploads → Cloud Storage (encrypted at rest using SSE-KMS)

Usage:
    # For S3
    from core.storage_encryption import get_s3_encryption_config
    extra_args = get_s3_encryption_config()
    s3_client.upload_file(file, bucket, key, ExtraArgs=extra_args)
"""

import logging
from typing import Dict, Any, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


def get_s3_encryption_config(kms_key_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get S3 server-side encryption configuration.

    Args:
        kms_key_id: Optional KMS key ID. If not provided, uses AWS managed keys (SSE-S3).

    Returns:
        Dict with ExtraArgs for boto3 upload/put operations

    Example:
        >>> config = get_s3_encryption_config()
        >>> s3.upload_file('file.txt', 'bucket', 'key', ExtraArgs=config)
    """
    # Get KMS key from settings if not provided
    kms_key_id = kms_key_id or getattr(settings, "AWS_SSE_KMS_KEY_ID", None)

    if kms_key_id:
        # Use customer-managed KMS key (SSE-KMS)
        return {
            "ServerSideEncryption": "aws:kms",
            "SSEKMSKeyId": kms_key_id,
        }
    else:
        # Use AWS managed keys (SSE-S3) - still encrypted, just AWS-managed key
        return {
            "ServerSideEncryption": "AES256",
        }


def get_gcs_encryption_config(kms_key_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Get GCS encryption configuration for Customer-Managed Encryption Keys (CMEK).

    Args:
        kms_key_name: Full resource name of the Cloud KMS key.
                     Format: projects/{project}/locations/{location}/keyRings/{keyRing}/cryptoKeys/{key}

    Returns:
        Dict with encryption configuration for GCS client
    """
    kms_key_name = kms_key_name or getattr(settings, "GCS_KMS_KEY_NAME", None)

    if kms_key_name:
        return {
            "kms_key_name": kms_key_name,
        }
    else:
        # GCS uses Google-managed encryption by default
        return {}


def get_azure_encryption_config(key_vault_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Get Azure Blob Storage encryption configuration.

    Note: Azure Storage Service Encryption (SSE) is enabled by default.
    For customer-managed keys, configure at the storage account level.

    Args:
        key_vault_key: Azure Key Vault key identifier for customer-managed encryption.

    Returns:
        Dict with encryption configuration
    """
    key_vault_key = key_vault_key or getattr(settings, "AZURE_KEY_VAULT_KEY", None)

    if key_vault_key:
        return {
            "encryption_key": key_vault_key,
        }
    else:
        # Azure uses Microsoft-managed encryption by default
        return {}


def log_encryption_status():
    """
    Log the current encryption configuration status.
    Useful for debugging and verification.
    """
    logger.info("=" * 50)
    logger.info("ENCRYPTION CONFIGURATION STATUS")
    logger.info("=" * 50)

    # Database encryption
    encryption_key = getattr(settings, "SYNAPSE_ENCRYPTION_KEY", None)
    if encryption_key:
        logger.info("✓ Field-level encryption: CONFIGURED (custom key)")
    else:
        logger.info(
            "⚠ Field-level encryption: Using derived key (set SYNAPSE_ENCRYPTION_KEY in production)"
        )

    # S3 encryption
    s3_kms = getattr(settings, "AWS_SSE_KMS_KEY_ID", None)
    if s3_kms:
        logger.info(f"✓ S3 SSE-KMS: CONFIGURED (key: {s3_kms[:20]}...)")
    else:
        logger.info("⚠ S3 SSE-KMS: Not configured (using SSE-S3 with AWS-managed keys)")

    # GCS encryption
    gcs_kms = getattr(settings, "GCS_KMS_KEY_NAME", None)
    if gcs_kms:
        logger.info(f"✓ GCS CMEK: CONFIGURED")
    else:
        logger.info("⚠ GCS CMEK: Not configured (using Google-managed encryption)")

    # Azure encryption
    azure_key = getattr(settings, "AZURE_KEY_VAULT_KEY", None)
    if azure_key:
        logger.info(f"✓ Azure Key Vault: CONFIGURED")
    else:
        logger.info("⚠ Azure: Using Microsoft-managed encryption (default)")

    logger.info("=" * 50)


# Environment variable documentation
ENCRYPTION_ENV_VARS = """
# ============================================================================
# ENCRYPTION ENVIRONMENT VARIABLES
# ============================================================================

# --- Database Field Encryption ---
# Master key for encrypting sensitive database fields (AES-256)
# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
SYNAPSE_ENCRYPTION_KEY=your-base64-encoded-key-here

# --- AWS S3 SSE-KMS ---
# KMS key ID for server-side encryption of S3 objects
# Format: arn:aws:kms:region:account-id:key/key-id
AWS_SSE_KMS_KEY_ID=arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012

# --- GCS CMEK ---
# Cloud KMS key for customer-managed encryption in GCS
# Format: projects/{project}/locations/{location}/keyRings/{ring}/cryptoKeys/{key}
GCS_KMS_KEY_NAME=projects/my-project/locations/us-central1/keyRings/my-ring/cryptoKeys/my-key

# --- Azure Key Vault ---
# Key Vault key identifier for customer-managed encryption
# Configure CMK at storage account level in Azure Portal
AZURE_KEY_VAULT_KEY=https://myvault.vault.azure.net/keys/mykey/version
"""

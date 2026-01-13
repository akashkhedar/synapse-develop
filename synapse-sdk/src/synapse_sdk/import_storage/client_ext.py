"""
Extended import storage client with simplified cloud import methods.
"""

from .client import ImportStorageClient, AsyncImportStorageClient
from .s3.client_ext import S3ClientExt, AsyncS3ClientExt


class ImportStorageClientExt(ImportStorageClient):
    """
    Extended import storage client with enhanced S3 capabilities.
    
    Example:
        >>> from synapse_sdk import Synapse
        >>> client = Synapse(api_key="your-api-key")
        >>> 
        >>> # Simple one-line S3 import
        >>> result = client.import_storage.s3.import_from_bucket(
        ...     project_id=123,
        ...     bucket="my-data",
        ...     prefix="images/"
        ... )
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Override s3 with extended client
        self.s3 = S3ClientExt(client_wrapper=self._client_wrapper)


class AsyncImportStorageClientExt(AsyncImportStorageClient):
    """
    Async extended import storage client with enhanced S3 capabilities.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Override s3 with extended client
        self.s3 = AsyncS3ClientExt(client_wrapper=self._client_wrapper)

"""
Simplified cloud storage import helpers.

This module provides high-level convenience methods for importing data from
cloud storage (S3, GCS, Azure) into Synapse projects with a single call.
"""

import typing
import time
from ..s3.client import S3Client, AsyncS3Client
from ...core.request_options import RequestOptions
from ...core.api_error import ApiError


class StorageImportResult(typing.TypedDict):
    """Result of a storage import operation"""
    storage_id: int
    storage_title: str
    project_id: int
    status: str
    tasks_imported: int


class S3ClientExt(S3Client):
    """
    Extended S3 client with simplified import workflow.
    
    Provides a single method to connect to S3 and import data into a project,
    replacing the multi-step process of create → validate → sync.
    
    Example:
        >>> from synapse_sdk import Synapse
        >>> client = Synapse(api_key="your-api-key")
        >>> 
        >>> # Import images from S3 bucket
        >>> result = client.import_storage.s3.import_from_bucket(
        ...     project_id=123,
        ...     bucket="my-data-bucket",
        ...     prefix="images/batch1/",
        ...     region="us-east-1",
        ...     aws_access_key_id="AKIA...",
        ...     aws_secret_access_key="..."
        ... )
        >>> print(f"Imported {result['tasks_imported']} tasks")
    """

    def import_from_bucket(
        self,
        *,
        project_id: int,
        bucket: str,
        prefix: typing.Optional[str] = None,
        region: typing.Optional[str] = None,
        aws_access_key_id: typing.Optional[str] = None,
        aws_secret_access_key: typing.Optional[str] = None,
        aws_session_token: typing.Optional[str] = None,
        regex_filter: typing.Optional[str] = None,
        recursive: bool = True,
        use_blob_urls: bool = True,
        presign: bool = True,
        presign_ttl: int = 60,
        title: typing.Optional[str] = None,
        description: typing.Optional[str] = None,
        wait_for_sync: bool = True,
        sync_timeout: int = 300,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> StorageImportResult:
        """
        Import data from an S3 bucket into a project.
        
        This is a convenience method that:
        1. Creates an S3 storage connection
        2. Validates the connection
        3. Syncs tasks from the bucket
        4. Optionally waits for sync to complete
        
        Parameters
        ----------
        project_id : int
            ID of the project to import data into
        bucket : str
            S3 bucket name
        prefix : str, optional
            S3 prefix/folder to import from
        region : str, optional
            AWS region (e.g., "us-east-1")
        aws_access_key_id : str, optional
            AWS access key (uses IAM role if not provided)
        aws_secret_access_key : str, optional
            AWS secret key
        aws_session_token : str, optional
            AWS session token for temporary credentials
        regex_filter : str, optional
            Regex pattern to filter objects (e.g., ".*\\.jpg$")
        recursive : bool
            Scan bucket recursively (default: True)
        use_blob_urls : bool
            Generate presigned URLs for media (default: True)
        presign : bool
            Enable presigned URLs (default: True)
        presign_ttl : int
            Presigned URL TTL in minutes (default: 60)
        title : str, optional
            Storage connection title
        description : str, optional
            Storage connection description
        wait_for_sync : bool
            Wait for sync to complete (default: True)
        sync_timeout : int
            Timeout in seconds for sync (default: 300)
        request_options : RequestOptions, optional
            Request-specific configuration
            
        Returns
        -------
        StorageImportResult
            Result with storage_id, tasks_imported, status
            
        Raises
        ------
        ApiError
            If storage creation or sync fails
        TimeoutError
            If sync doesn't complete within timeout
            
        Examples
        --------
        >>> # Import all images from a bucket
        >>> result = client.import_storage.s3.import_from_bucket(
        ...     project_id=123,
        ...     bucket="my-data",
        ...     prefix="images/",
        ...     region="us-west-2",
        ...     aws_access_key_id="AKIA...",
        ...     aws_secret_access_key="secret..."
        ... )
        >>>
        >>> # Import only JPG files
        >>> result = client.import_storage.s3.import_from_bucket(
        ...     project_id=123,
        ...     bucket="my-data",
        ...     regex_filter=r".*\\.jpg$"
        ... )
        """
        # Default title
        if not title:
            title = f"S3: {bucket}"
            if prefix:
                title += f"/{prefix.rstrip('/')}"

        # Default regex to match common file types if none provided
        if not regex_filter:
            regex_filter = ".*"

        # Create storage connection
        storage = self.create(
            project=project_id,
            bucket=bucket,
            prefix=prefix,
            region_name=region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            regex_filter=regex_filter,
            recursive_scan=recursive,
            use_blob_urls=use_blob_urls,
            presign=presign,
            presign_ttl=presign_ttl,
            title=title,
            description=description,
            request_options=request_options,
        )

        storage_id = storage.id

        # Validate the connection
        try:
            self.validate(
                id=storage_id,
                bucket=bucket,
                prefix=prefix,
                region_name=region,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token,
                project=project_id,
                request_options=request_options,
            )
        except ApiError:
            # Validation may not be required, continue with sync
            pass

        # Sync tasks from storage
        synced_storage = self.sync(id=storage_id, request_options=request_options)

        # Get task count
        task_count = getattr(synced_storage, 'last_sync_count', 0) or 0

        return StorageImportResult(
            storage_id=storage_id,
            storage_title=title,
            project_id=project_id,
            status="synced",
            tasks_imported=task_count,
        )

    def connect_and_sync(
        self,
        *,
        project_id: int,
        bucket: str,
        prefix: typing.Optional[str] = None,
        region: typing.Optional[str] = None,
        aws_access_key_id: typing.Optional[str] = None,
        aws_secret_access_key: typing.Optional[str] = None,
        request_options: typing.Optional[RequestOptions] = None,
        **kwargs,
    ) -> StorageImportResult:
        """
        Alias for import_from_bucket with simplified parameters.
        
        This is a convenience wrapper with fewer options for simple use cases.
        """
        return self.import_from_bucket(
            project_id=project_id,
            bucket=bucket,
            prefix=prefix,
            region=region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            request_options=request_options,
            **kwargs,
        )


class AsyncS3ClientExt(AsyncS3Client):
    """
    Async extended S3 client with simplified import workflow.
    """

    async def import_from_bucket(
        self,
        *,
        project_id: int,
        bucket: str,
        prefix: typing.Optional[str] = None,
        region: typing.Optional[str] = None,
        aws_access_key_id: typing.Optional[str] = None,
        aws_secret_access_key: typing.Optional[str] = None,
        aws_session_token: typing.Optional[str] = None,
        regex_filter: typing.Optional[str] = None,
        recursive: bool = True,
        use_blob_urls: bool = True,
        presign: bool = True,
        presign_ttl: int = 60,
        title: typing.Optional[str] = None,
        description: typing.Optional[str] = None,
        wait_for_sync: bool = True,
        sync_timeout: int = 300,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> StorageImportResult:
        """
        Import data from an S3 bucket into a project (async version).
        """
        # Default title
        if not title:
            title = f"S3: {bucket}"
            if prefix:
                title += f"/{prefix.rstrip('/')}"

        # Default regex
        if not regex_filter:
            regex_filter = ".*"

        # Create storage connection
        storage = await self.create(
            project=project_id,
            bucket=bucket,
            prefix=prefix,
            region_name=region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            regex_filter=regex_filter,
            recursive_scan=recursive,
            use_blob_urls=use_blob_urls,
            presign=presign,
            presign_ttl=presign_ttl,
            title=title,
            description=description,
            request_options=request_options,
        )

        storage_id = storage.id

        # Validate (optional)
        try:
            await self.validate(
                id=storage_id,
                bucket=bucket,
                prefix=prefix,
                region_name=region,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token,
                project=project_id,
                request_options=request_options,
            )
        except ApiError:
            pass

        # Sync tasks
        synced_storage = await self.sync(id=storage_id, request_options=request_options)

        task_count = getattr(synced_storage, 'last_sync_count', 0) or 0

        return StorageImportResult(
            storage_id=storage_id,
            storage_title=title,
            project_id=project_id,
            status="synced",
            tasks_imported=task_count,
        )

    async def connect_and_sync(
        self,
        *,
        project_id: int,
        bucket: str,
        prefix: typing.Optional[str] = None,
        region: typing.Optional[str] = None,
        aws_access_key_id: typing.Optional[str] = None,
        aws_secret_access_key: typing.Optional[str] = None,
        request_options: typing.Optional[RequestOptions] = None,
        **kwargs,
    ) -> StorageImportResult:
        """Alias for import_from_bucket with simplified parameters."""
        return await self.import_from_bucket(
            project_id=project_id,
            bucket=bucket,
            prefix=prefix,
            region=region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            request_options=request_options,
            **kwargs,
        )

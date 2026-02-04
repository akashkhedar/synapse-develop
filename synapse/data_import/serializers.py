"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license.
"""
import os
import zipfile
import tempfile
import shutil
from collections import Counter

from rest_framework import serializers
from django.core.files.storage import default_storage
from tasks.models import Task
from tasks.serializers import AnnotationSerializer, PredictionSerializer, TaskSerializer, TaskSerializerBulk

from .models import FileUpload


# File extension to type mapping
EXTENSION_TYPE_MAP = {
    # Images
    '.jpg': 'image', '.jpeg': 'image', '.png': 'image', '.gif': 'image',
    '.bmp': 'image', '.svg': 'image', '.webp': 'image', '.tiff': 'image', '.tif': 'image',
    # Audio
    '.wav': 'audio', '.mp3': 'audio', '.flac': 'audio', '.m4a': 'audio', '.ogg': 'audio',
    # Video
    '.mp4': 'video', '.webm': 'video', '.mov': 'video', '.avi': 'video', '.mkv': 'video',
    # Text
    '.txt': 'text',
    # Structured data
    '.csv': 'csv', '.tsv': 'tsv', '.json': 'json',
    # HTML/XML
    '.html': 'html', '.htm': 'html', '.xml': 'xml',
    # PDF
    '.pdf': 'pdf',
    # Medical/DICOM
    '.dcm': 'dicom', '.dicom': 'dicom', '.ima': 'dicom',
}


def analyze_zip_contents(file_path):
    """
    Analyze the contents of a ZIP file and return detected file types.
    
    Returns:
        dict: {
            'dominant_type': str,  # Most common file type
            'file_types': dict,    # Count of each file type
            'total_files': int,    # Total file count
            'sample_files': list,  # Sample of file names
            'has_dicom': bool,     # Whether DICOM files were detected
        }
    """
    file_types = Counter()
    sample_files = []
    has_dicom = False
    total_files = 0
    
    try:
        # For cloud storage or local files, we need to download to temp first
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
                tmp_path = tmp.name
                with default_storage.open(file_path, 'rb') as f:
                    shutil.copyfileobj(f, tmp)
            
            # Analyze without extracting - just read the file list
            with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                for name in zip_ref.namelist():
                    # Skip directories and hidden files
                    if name.endswith('/') or '/__MACOSX/' in name or name.startswith('__MACOSX/'):
                        continue
                    if os.path.basename(name).startswith('.'):
                        continue
                    
                    total_files += 1
                    ext = os.path.splitext(name.lower())[1]
                    
                    # Check extension
                    if ext in EXTENSION_TYPE_MAP:
                        file_type = EXTENSION_TYPE_MAP[ext]
                        file_types[file_type] += 1
                        if file_type == 'dicom':
                            has_dicom = True
                    elif ext == '' and '.' not in os.path.basename(name):
                        # No extension - could be DICOM (they often don't have extensions)
                        file_types['dicom'] += 1
                        has_dicom = True
                    else:
                        file_types['unknown'] += 1
                    
                    # Collect sample files (first 10)
                    if len(sample_files) < 10:
                        sample_files.append(os.path.basename(name))
                        
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    except zipfile.BadZipFile:
        return {
            'error': 'Invalid ZIP file',
            'dominant_type': None,
            'file_types': {},
            'total_files': 0,
            'sample_files': [],
            'has_dicom': False,
        }
    except Exception as e:
        return {
            'error': str(e),
            'dominant_type': None,
            'file_types': {},
            'total_files': 0,
            'sample_files': [],
            'has_dicom': False,
        }
    
    # Determine dominant type
    dominant_type = None
    if file_types:
        # Get the most common type, excluding 'unknown'
        valid_types = {k: v for k, v in file_types.items() if k != 'unknown'}
        if valid_types:
            dominant_type = max(valid_types, key=valid_types.get)
    
    return {
        'dominant_type': dominant_type,
        'file_types': dict(file_types),
        'total_files': total_files,
        'sample_files': sample_files,
        'has_dicom': has_dicom,
    }


class ImportApiSerializer(TaskSerializer):
    """Tasks serializer for Import API (TaskBulkCreateAPI)"""

    annotations = AnnotationSerializer(many=True, default=[])
    predictions = PredictionSerializer(many=True, default=[])

    class Meta:
        model = Task
        list_serializer_class = TaskSerializerBulk
        exclude = ('is_labeled', 'project')


class FileUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField(use_url=False)
    size = serializers.SerializerMethodField()
    content_type = serializers.SerializerMethodField()
    zip_analysis = serializers.SerializerMethodField()

    class Meta:
        model = FileUpload
        fields = ['id', 'file', 'size', 'content_type', 'zip_analysis']

    def get_size(self, obj) -> int | None:
        try:
            return obj.file.size
        except (ValueError, OSError):
            return None

    def get_content_type(self, obj) -> str | None:
        """Return the detected content type based on file extension."""
        try:
            ext = os.path.splitext(obj.file.name.lower())[1]
            return EXTENSION_TYPE_MAP.get(ext, 'unknown')
        except:
            return None

    def get_zip_analysis(self, obj) -> dict | None:
        """
        For ZIP files, analyze contents and return detected types.
        This helps the frontend choose the appropriate template.
        """
        try:
            ext = os.path.splitext(obj.file.name.lower())[1]
            if ext != '.zip':
                return None
            
            # Analyze ZIP contents
            return analyze_zip_contents(obj.file.name)
        except Exception as e:
            return {'error': str(e)}






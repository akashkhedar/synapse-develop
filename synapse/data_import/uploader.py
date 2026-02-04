"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license.
"""
import csv
import io
import logging
import mimetypes
import os

try:
    import ujson as json
except:  # noqa: E722
    import json

from core.utils.common import timeit
from core.utils.io import ssrf_safe_get
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.exceptions import ValidationError

from .models import FileUpload

logger = logging.getLogger(__name__)
csv.field_size_limit(131072 * 10)


def is_binary(f):
    return isinstance(f, (io.RawIOBase, io.BufferedIOBase))


def csv_generate_header(file):
    """Generate column names for headless csv file"""
    file.seek(0)
    names = []
    line = file.readline()

    num_columns = len(line.split(b',' if isinstance(line, bytes) else ','))
    for i in range(num_columns):
        names.append('column' + str(i + 1))
    file.seek(0)
    return names


def check_max_task_number(tasks):
    # max tasks
    if len(tasks) > settings.TASKS_MAX_NUMBER:
        raise ValidationError(
            f'Maximum task number is {settings.TASKS_MAX_NUMBER}, ' f'current task number is {len(tasks)}'
        )


def check_tasks_max_file_size(value):
    if value >= settings.TASKS_MAX_FILE_SIZE:
        raise ValidationError(
            f'Maximum total size of all files is {settings.TASKS_MAX_FILE_SIZE} bytes, '
            f'current size is {value} bytes'
        )


def check_extensions(files):
    for filename, file_obj in files.items():
        _, ext = os.path.splitext(file_obj.name)
        if ext.lower() not in settings.SUPPORTED_EXTENSIONS:
            raise ValidationError(f'{ext} extension is not supported')


def check_request_files_size(files):
    total = sum([file.size for _, file in files.items()])

    check_tasks_max_file_size(total)


def check_storage_limit(project, new_files_size):
    """
    Check if uploading new files would exceed organization's storage limit.
    Considers free storage from subscription plan and charges for overage.
    
    Args:
        project: Project instance
        new_files_size: Size of new files to upload (in bytes)
        
    Returns:
        dict: Overage details if storage exceeds free tier, None otherwise
        
    Raises:
        ValidationError: If storage limit would be exceeded without credits
    """
    from billing.models import OrganizationBilling
    from billing.storage_service import StorageCalculationService
    from decimal import Decimal
    
    organization = project.organization
    
    # Get current storage usage
    try:
        org_billing = OrganizationBilling.objects.get(organization=organization)
        current_storage_gb = org_billing.storage_used_gb or Decimal('0')
    except OrganizationBilling.DoesNotExist:
        current_storage_gb = Decimal('0')
        org_billing = None
    
    # Calculate new total storage
    new_files_gb = Decimal(str(new_files_size)) / Decimal(str(1024 ** 3))
    new_total_storage_gb = current_storage_gb + new_files_gb
    
    # Get free storage from active subscription
    free_storage_gb = Decimal('5')  # Default PAYG
    if org_billing and org_billing.active_subscription:
        subscription = org_billing.active_subscription
        if subscription.plan:
            free_storage_gb = Decimal(str(subscription.plan.storage_gb))
    
    # Calculate overage
    overage_gb = max(Decimal('0'), new_total_storage_gb - free_storage_gb)
    
    if overage_gb > 0:
        # Calculate overage cost
        storage_rate = Decimal('25.00')  # Default rate
        if org_billing and org_billing.active_subscription:
            subscription = org_billing.active_subscription
            if subscription.plan and hasattr(subscription.plan, 'extra_storage_rate_per_gb'):
                storage_rate = subscription.plan.extra_storage_rate_per_gb
        
        overage_cost = overage_gb * storage_rate
        
        # Check if organization has enough credits
        available_credits = org_billing.available_credits if org_billing else Decimal('0')
        
        if available_credits < overage_cost:
            raise ValidationError(
                f'Insufficient credits for storage overage. '
                f'Uploading these files will use {float(new_files_gb):.2f} GB, '
                f'bringing total to {float(new_total_storage_gb):.2f} GB. '
                f'Your plan includes {float(free_storage_gb)} GB free. '
                f'Overage: {float(overage_gb):.2f} GB × ₹{float(storage_rate)}/GB = ₹{float(overage_cost):.2f} credits. '
                f'Available credits: {float(available_credits):.2f}. '
                f'Please purchase more credits or upgrade your plan.'
            )
        
        logger.info(
            f"Storage overage for {organization.title}: "
            f"{float(overage_gb):.2f} GB will cost {float(overage_cost):.2f} credits"
        )
        
        return {
            'overage_gb': float(overage_gb),
            'overage_cost': float(overage_cost),
            'storage_rate': float(storage_rate),
            'new_total_gb': float(new_total_storage_gb),
            'free_storage_gb': float(free_storage_gb),
        }
    
    return None


def create_file_upload(user, project, file):
    instance = FileUpload(user=user, project=project, file=file)
    if settings.SVG_SECURITY_CLEANUP:
        content_type, encoding = mimetypes.guess_type(str(instance.file.name))
        if content_type in ['image/svg+xml']:
            clean_xml = allowlist_svg(instance.file.read().decode())
            instance.file.seek(0)
            instance.file.write(clean_xml.encode())
            instance.file.truncate()
    instance.save()
    return instance


def allowlist_svg(dirty_xml):
    """Filter out malicious/harmful content from SVG files
    by defining allowed tags
    """
    from lxml.html import clean

    allow_tags = [
        'xml',
        'svg',
        'circle',
        'ellipse',
        'line',
        'path',
        'polygon',
        'vector',
        'rect',
    ]

    cleaner = clean.Cleaner(
        allow_tags=allow_tags,
        style=True,
        links=True,
        add_nofollow=False,
        page_structure=True,
        safe_attrs_only=False,
        remove_unknown_tags=False,
    )

    clean_xml = cleaner.clean_html(dirty_xml)
    return clean_xml


def str_to_json(data):
    try:
        json_acceptable_string = data.replace("'", '"')
        return json.loads(json_acceptable_string)
    except ValueError:
        return None


def tasks_from_url(file_upload_ids, project, user, url, could_be_tasks_list):
    """Download file using URL and read tasks from it"""
    # process URL with tasks
    try:
        filename = url.rsplit('/', 1)[-1]

        response = ssrf_safe_get(
            url, verify=project.organization.should_verify_ssl_certs(), stream=True, headers={'Accept-Encoding': None}
        )

        # Try to get filename from resolved URL after redirects
        resolved_url = response.url if hasattr(response, 'url') else url
        if resolved_url != url:
            # Parse filename from the resolved URL after redirect
            from urllib.parse import unquote, urlparse

            parsed_url = urlparse(resolved_url)
            path = unquote(parsed_url.path)
            resolved_filename = path.rsplit('/', 1)[-1]
            # Remove query parameters
            if '?' in resolved_filename:
                resolved_filename = resolved_filename.split('?')[0]
            _, resolved_ext = os.path.splitext(resolved_filename)
            filename = resolved_filename

        # Check file extension
        _, ext = os.path.splitext(filename)
        if ext and ext.lower() not in settings.SUPPORTED_EXTENSIONS:
            raise ValidationError(f'{ext} extension is not supported')

        # Check file size before downloading
        content_length = response.headers.get('content-length')
        if content_length:
            check_tasks_max_file_size(int(content_length))

        file_content = response.content
        file_upload = create_file_upload(user, project, SimpleUploadedFile(filename, file_content))
        if file_upload.format_could_be_tasks_list:
            could_be_tasks_list = True
        file_upload_ids.append(file_upload.id)
        tasks, found_formats, data_keys = FileUpload.load_tasks_from_uploaded_files(project, file_upload_ids)

    except ValidationError as e:
        raise e
    except Exception as e:
        raise ValidationError(str(e))
    return data_keys, found_formats, tasks, file_upload_ids, could_be_tasks_list


@timeit
def create_file_uploads(user, project, FILES):
    could_be_tasks_list = False
    file_upload_ids = []
    check_request_files_size(FILES)
    check_extensions(FILES)
    
    # Check storage limits before uploading
    total_size = sum([file.size for _, file in FILES.items()])
    overage_details = check_storage_limit(project, total_size)
    
    # Upload files
    for _, file in FILES.items():
        file_upload = create_file_upload(user, project, file)
        if file_upload.format_could_be_tasks_list:
            could_be_tasks_list = True
        file_upload_ids.append(file_upload.id)
    
    # Charge for storage overage if needed
    if overage_details and overage_details['overage_gb'] > 0:
        from billing.storage_service import StorageCalculationService
        StorageCalculationService.charge_storage_overage(
            organization=project.organization,
            overage_gb=overage_details['overage_gb'],
            overage_cost=overage_details['overage_cost']
        )
        logger.info(
            f"Charged storage overage: {overage_details['overage_gb']:.2f} GB "
            f"= ₹{overage_details['overage_cost']:.2f}"
        )

    logger.debug(f'created file uploads: {file_upload_ids} could_be_tasks_list: {could_be_tasks_list}')
    return file_upload_ids, could_be_tasks_list


def load_tasks_for_async_import(project_import, user):
    """Load tasks from different types of request.data / request.files saved in project_import model"""
    file_upload_ids, found_formats, data_keys = [], [], set()

    if project_import.file_upload_ids:
        file_upload_ids = project_import.file_upload_ids
        tasks, found_formats, data_keys = FileUpload.load_tasks_from_uploaded_files(
            project_import.project, file_upload_ids
        )

    # take tasks from url address
    elif project_import.url:
        url = project_import.url
        # try to load json with task or tasks from url as string
        json_data = str_to_json(url)
        if json_data:
            file_upload = create_file_upload(
                user,
                project_import.project,
                SimpleUploadedFile('inplace.json', url.encode()),
            )
            file_upload_ids.append(file_upload.id)
            tasks, found_formats, data_keys = FileUpload.load_tasks_from_uploaded_files(
                project_import.project, file_upload_ids
            )

        # download file using url and read tasks from it
        else:
            could_be_tasks_list = False
            (
                data_keys,
                found_formats,
                tasks,
                file_upload_ids,
                could_be_tasks_list,
            ) = tasks_from_url(file_upload_ids, project_import.project, user, url, could_be_tasks_list)
            if could_be_tasks_list:
                project_import.could_be_tasks_list = True
                project_import.save(update_fields=['could_be_tasks_list'])

    elif project_import.tasks:
        tasks = project_import.tasks

    # check is data root is list
    if not isinstance(tasks, list):
        raise ValidationError('load_tasks: Data root must be list')

    # empty tasks error
    if not tasks:
        raise ValidationError('load_tasks: No tasks added')

    check_max_task_number(tasks)
    return tasks, file_upload_ids, found_formats, list(data_keys)


def load_tasks_for_async_import_streaming(project_import, user, batch_size=1000):
    """Load tasks from different types of request.data / request.files saved in project_import model,
    yielding tasks in batches to reduce memory usage"""
    from django.conf import settings

    if not batch_size:
        batch_size = settings.IMPORT_BATCH_SIZE

    all_file_upload_ids = []
    all_found_formats = {}
    all_data_keys = set()

    if project_import.file_upload_ids:
        file_upload_ids = project_import.file_upload_ids
        all_file_upload_ids = file_upload_ids.copy()

        for batch_tasks, batch_formats, batch_data_keys in FileUpload.load_tasks_from_uploaded_files_streaming(
            project_import.project, file_upload_ids, batch_size=batch_size
        ):
            all_found_formats.update(batch_formats)
            all_data_keys.update(batch_data_keys)

            # Validate each batch
            if not isinstance(batch_tasks, list):
                raise ValidationError('load_tasks: Data root must be list')
            if not batch_tasks:
                continue  # Skip empty batches

            check_max_task_number(batch_tasks)
            yield batch_tasks, file_upload_ids, batch_formats, list(batch_data_keys)

    elif project_import.url:
        # For URL imports, we still need to load everything at once
        # since we don't have streaming support for URL-based imports yet
        url = project_import.url
        file_upload_ids, found_formats, data_keys = [], [], set()

        # try to load json with task or tasks from url as string
        json_data = str_to_json(url)
        if json_data:
            file_upload = create_file_upload(
                user,
                project_import.project,
                SimpleUploadedFile('inplace.json', url.encode()),
            )
            file_upload_ids.append(file_upload.id)
            tasks, found_formats, data_keys = FileUpload.load_tasks_from_uploaded_files(
                project_import.project, file_upload_ids
            )
        else:
            could_be_tasks_list = False
            (
                data_keys,
                found_formats,
                tasks,
                file_upload_ids,
                could_be_tasks_list,
            ) = tasks_from_url(file_upload_ids, project_import.project, user, url, could_be_tasks_list)
            if could_be_tasks_list:
                project_import.could_be_tasks_list = True
                project_import.save(update_fields=['could_be_tasks_list'])

        if not isinstance(tasks, list):
            raise ValidationError('load_tasks: Data root must be list')
        if not tasks:
            raise ValidationError('load_tasks: No tasks added')

        check_max_task_number(tasks)

        all_file_upload_ids = file_upload_ids.copy()
        all_found_formats = found_formats.copy()
        all_data_keys = data_keys.copy()

        for i in range(0, len(tasks), batch_size):
            batch_tasks = tasks[i : i + batch_size]
            yield batch_tasks, file_upload_ids, found_formats, list(data_keys)

    elif project_import.tasks:
        tasks = project_import.tasks

        if not isinstance(tasks, list):
            raise ValidationError('load_tasks: Data root must be list')
        if not tasks:
            raise ValidationError('load_tasks: No tasks added')

        check_max_task_number(tasks)

        for i in range(0, len(tasks), batch_size):
            batch_tasks = tasks[i : i + batch_size]
            yield batch_tasks, [], {}, []

    else:
        raise ValidationError('load_tasks: No tasks added')

    return all_file_upload_ids, all_found_formats, list(all_data_keys)


def load_tasks(request, project):
    """Load tasks from different types of request.data / request.files"""
    file_upload_ids, found_formats, data_keys = [], [], set()
    could_be_tasks_list = False

    # Check content type first to determine how to handle the request
    content_type = request.content_type or ''
    
    logger.debug(f"load_tasks: content_type={content_type}")
    
    # For multipart/form-data, handle file uploads
    if 'multipart/form-data' in content_type:
        # Try to get files - use request.FILES which DRF provides
        # The middleware fix should have prevented the stream from being consumed
        try:
            files = request.FILES
            logger.debug(f"load_tasks: Found {len(files)} files in request.FILES")
        except Exception as e:
            logger.error(f"load_tasks: Error accessing request.FILES: {e}")
            files = None
        
        if files:
            check_request_files_size(files)
            check_extensions(files)
            for filename, file in files.items():
                file_upload = create_file_upload(request.user, project, file)
                if file_upload.format_could_be_tasks_list:
                    could_be_tasks_list = True
                file_upload_ids.append(file_upload.id)
            tasks, found_formats, data_keys = FileUpload.load_tasks_from_uploaded_files(project, file_upload_ids)
        else:
            # Fallback: try the underlying Django request
            django_request = getattr(request, '_request', request)
            files = getattr(django_request, 'FILES', None)
            logger.debug(f"load_tasks: Fallback - found {len(files) if files else 0} files in django_request.FILES")
            
            if files:
                check_request_files_size(files)
                check_extensions(files)
                for filename, file in files.items():
                    file_upload = create_file_upload(request.user, project, file)
                    if file_upload.format_could_be_tasks_list:
                        could_be_tasks_list = True
                    file_upload_ids.append(file_upload.id)
                tasks, found_formats, data_keys = FileUpload.load_tasks_from_uploaded_files(project, file_upload_ids)
            else:
                raise ValidationError('load_tasks: No files found in multipart request. Please ensure files are attached correctly.')

    # take tasks from url address
    elif 'application/x-www-form-urlencoded' in content_type:
        # empty url
        url = request.data.get('url')
        if not url:
            raise ValidationError('"url" is not found in request data')

        # try to load json with task or tasks from url as string
        json_data = str_to_json(url)
        if json_data:
            file_upload = create_file_upload(request.user, project, SimpleUploadedFile('inplace.json', url.encode()))
            file_upload_ids.append(file_upload.id)
            tasks, found_formats, data_keys = FileUpload.load_tasks_from_uploaded_files(project, file_upload_ids)

        # download file using url and read tasks from it
        else:
            (
                data_keys,
                found_formats,
                tasks,
                file_upload_ids,
                could_be_tasks_list,
            ) = tasks_from_url(file_upload_ids, project, request.user, url, could_be_tasks_list)

    # take one task from request DATA
    elif 'application/json' in content_type and isinstance(request.data, dict):
        tasks = [request.data]

    # take many tasks from request DATA
    elif 'application/json' in content_type and isinstance(request.data, list):
        tasks = request.data

    # Fallback: try to access request.FILES (for backwards compatibility)
    elif len(request.FILES):
        check_request_files_size(request.FILES)
        check_extensions(request.FILES)
        for filename, file in request.FILES.items():
            file_upload = create_file_upload(request.user, project, file)
            if file_upload.format_could_be_tasks_list:
                could_be_tasks_list = True
            file_upload_ids.append(file_upload.id)
        tasks, found_formats, data_keys = FileUpload.load_tasks_from_uploaded_files(project, file_upload_ids)

    # incorrect data source
    else:
        raise ValidationError('load_tasks: No data found in DATA or in FILES')

    # check is data root is list
    if not isinstance(tasks, list):
        raise ValidationError('load_tasks: Data root must be list')

    # empty tasks error
    if not tasks:
        raise ValidationError('load_tasks: No tasks added')

    check_max_task_number(tasks)
    return tasks, file_upload_ids, could_be_tasks_list, found_formats, list(data_keys)






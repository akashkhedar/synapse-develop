from core.utils.exceptions import SynapseAPIException
from rest_framework import status


class AnnotationDuplicateError(SynapseAPIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Annotation with this unique id already exists'






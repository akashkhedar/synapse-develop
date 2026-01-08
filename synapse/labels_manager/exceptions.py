from core.utils.exceptions import SynapseAPIException
from rest_framework import status


class LabelBulkUpdateError(SynapseAPIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY






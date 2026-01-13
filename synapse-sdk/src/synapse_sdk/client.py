from .base_client import SynapseBase, AsyncSynapseBase
from .tasks.client_ext import TasksClientExt, AsyncTasksClientExt
from .projects.client_ext import ProjectsClientExt, AsyncProjectsClientExt
from .billing.client_ext import BillingClientExt, AsyncBillingClientExt
from .import_storage.client_ext import ImportStorageClientExt, AsyncImportStorageClientExt
from .core.api_error import ApiError


class Synapse(SynapseBase):
    """"""
    __doc__ += SynapseBase.__doc__

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.tasks = TasksClientExt(client_wrapper=self._client_wrapper)
        self.projects = ProjectsClientExt(client_wrapper=self._client_wrapper)
        self.billing = BillingClientExt(client_wrapper=self._client_wrapper)
        self.import_storage = ImportStorageClientExt(client_wrapper=self._client_wrapper)


class AsyncSynapse(AsyncSynapseBase):
    """"""
    __doc__ += AsyncSynapseBase.__doc__

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.tasks = AsyncTasksClientExt(client_wrapper=self._client_wrapper)
        self.projects = AsyncProjectsClientExt(client_wrapper=self._client_wrapper)
        self.billing = AsyncBillingClientExt(client_wrapper=self._client_wrapper)
        self.import_storage = AsyncImportStorageClientExt(client_wrapper=self._client_wrapper)








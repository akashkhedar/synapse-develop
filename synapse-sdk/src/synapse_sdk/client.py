from .base_client import SynapseBase, AsyncSynapseBase
from .tasks.client_ext import TasksClientExt, AsyncTasksClientExt
from .projects.client_ext import ProjectsClientExt, AsyncProjectsClientExt
from .core.api_error import ApiError


class Synapse(SynapseBase):
    """"""
    __doc__ += SynapseBase.__doc__

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.tasks = TasksClientExt(client_wrapper=self._client_wrapper)
        self.projects = ProjectsClientExt(client_wrapper=self._client_wrapper)


class AsyncSynapse(AsyncSynapseBase):
    """"""
    __doc__ += AsyncSynapseBase.__doc__

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.tasks = AsyncTasksClientExt(client_wrapper=self._client_wrapper)
        self.projects = AsyncProjectsClientExt(client_wrapper=self._client_wrapper)








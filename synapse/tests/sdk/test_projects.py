import pytest

from synapse.tests.sdk.common import LABEL_CONFIG_AND_TASKS

pytestmark = pytest.mark.django_db
from synapse_sdk.client import Synapse


def test_start_and_get_project(django_live_url, business_client):
    client = Synapse(base_url=django_live_url, api_key=business_client.api_key)
    p = client.projects.create(title='New Project', label_config=LABEL_CONFIG_AND_TASKS['label_config'])

    project = client.projects.get(id=p.id)
    assert project
    assert project.title == 'New Project'

    client.projects.update(id=project.id, title='Updated Project')
    project = client.projects.get(id=p.id)
    assert project.title == 'Updated Project'


def test_delete_project(django_live_url, business_client):
    client = Synapse(base_url=django_live_url, api_key=business_client.api_key)
    p = client.projects.create(title='New Project', label_config=LABEL_CONFIG_AND_TASKS['label_config'])

    project = client.projects.get(id=p.id)
    client.projects.delete(id=project.id)

    any_project_found = False
    for project in client.projects.list():
        any_project_found = True

    assert not any_project_found


def test_list_projects_with_params(django_live_url, business_client):

    client = Synapse(base_url=django_live_url, api_key=business_client.api_key)
    client.projects.create(title='Project 1', label_config=LABEL_CONFIG_AND_TASKS['label_config'])
    client.projects.create(title='Project 2', label_config=LABEL_CONFIG_AND_TASKS['label_config'])

    projects = list(client.projects.list())
    assert len(projects) == 2
    assert projects[0].title == 'Project 2'
    assert projects[1].title == 'Project 1'

    projects = list(client.projects.list(filter='pinned_only'))
    assert not projects

    projects = list(client.projects.list(include='id,title,pinned_at,created_at,created_by'))
    assert projects[0].pinned_at is None
    assert projects[0].created_at is not None
    assert projects[0].created_by.email == business_client.user.email






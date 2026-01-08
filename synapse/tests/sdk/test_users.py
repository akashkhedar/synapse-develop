import pytest

from synapse.tests.sdk.common import LABEL_CONFIG_AND_TASKS

pytestmark = pytest.mark.django_db

from synapse_sdk.client import Synapse


def test_add_user(django_live_url, business_client):
    client = Synapse(base_url=django_live_url, api_key=business_client.api_key)
    client.projects.create(title='New Project', label_config=LABEL_CONFIG_AND_TASKS['label_config'])

    test_member_email = 'test_member@example.com'
    u = client.users.create(
        **{
            'email': test_member_email,
            'username': test_member_email,
            'first_name': 'Test',
            'last_name': 'Member',
        }
    )

    assert u.id in [u.id for u in client.users.list()]






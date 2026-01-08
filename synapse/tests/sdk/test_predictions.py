import pytest

from synapse.tests.sdk.common import LABEL_CONFIG_AND_TASKS

pytestmark = pytest.mark.django_db
from synapse_sdk.client import Synapse
from synapse_sdk.synapse_interface import LabelInterface
from synapse_sdk.synapse_interface.objects import PredictionValue, TaskValue


def test_predictions_CRUD(django_live_url, business_client):
    client = Synapse(base_url=django_live_url, api_key=business_client.api_key)
    li = LabelInterface(LABEL_CONFIG_AND_TASKS['label_config'])
    p = client.projects.create(title='New Project', label_config=li.config)

    task = ls.tasks.create(project=p.id, data={'my_text': 'Test task'})

    # create a prediction
    pv = PredictionValue(
        result=[li.get_control('sentiment_class').label(['Positive'])],
        score=0.9,
        model_version='1.0.0',
    )
    prediction = ls.predictions.create(
        task=task.id,
        **pv.model_dump(),
    )

    # get a prediction
    prediction = ls.predictions.get(id=prediction.id)
    assert prediction.result[0]['value']['choices'] == ['Positive']
    assert prediction.score == 0.9
    assert prediction.model_version == '1.0.0'

    # create another prediction
    pv = PredictionValue(
        result=[
            li.get_control('sentiment_class').label(['Neutral']),
            li.get_control('sentiment_class').label(['Negative']),
        ],
        score=0.8,
        model_version='1.0.1',
    )

    another_prediction = ls.predictions.create(task=task.id, **pv.model_dump())

    # check that there are two predictions
    predictions = ls.predictions.list(task=task.id)
    assert len(predictions) == 2

    # delete one prediction
    ls.predictions.delete(id=prediction.id)
    predictions = ls.predictions.list(task=task.id)
    assert len(predictions) == 1
    assert predictions[0].id == another_prediction.id


def test_create_predictions_with_import(django_live_url, business_client):
    client = Synapse(base_url=django_live_url, api_key=business_client.api_key)
    li = LabelInterface(LABEL_CONFIG_AND_TASKS['label_config'])
    p = client.projects.create(title='New Project', label_config=li.config)

    # import tasks with predictions
    client.projects.import_tasks(
        id=p.id,
        request=[
            {'my_text': 'Hello world', 'sentiment_class': 'Positive'},
            {'my_text': 'Goodbye Synapse', 'sentiment_class': 'Negative'},
            {'my_text': 'What a beautiful day', 'sentiment_class': 'Positive'},
        ],
        preannotated_from_fields=['sentiment_class'],
    )

    # check predictions for each class
    task_ids = []
    for task in ls.tasks.list(project=p.id):
        assert len(ls.predictions.list(task=task.id)) == 1
        task_ids.append(task.id)
    assert len(task_ids) == 3

    # import more tasks in extended format
    task1 = TaskValue(
        data={'my_text': 'Hello world'},
        predictions=[
            PredictionValue(
                result=[li.get_control('sentiment_class').label(['Positive'])],
                score=0.95,
                model_version='3.4.5',
            )
        ],
    )
    task2 = TaskValue(
        data={'my_text': 'Goodbye Synapse'},
        predictions=[
            PredictionValue(
                result=[li.get_control('sentiment_class').label(['Negative'])],
                score=0.85,
                model_version='3.4.5',
            )
        ],
    )

    client.projects.import_tasks(
        id=p.id,
        request=[task1.model_dump(), task2.model_dump()],
    )

    # check for new predictions
    for task in ls.tasks.list(project=p.id):
        predictions = ls.predictions.list(task=task.id)
        assert len(predictions) == 1
        if task.id not in task_ids:
            assert predictions[0].model_version == '3.4.5'
            task_ids.append(task.id)

    assert len(task_ids) == 5

    # update project with model_version (RND-113)
    assert p.model_version == ''
    client.projects.update(id=p.id, model_version='3.4.5')
    project = client.projects.get(id=p.id)
    assert project.model_version == '3.4.5'

    # assert it raises synapse_sdk.core.api_error.ApiError with validation_errors': {'model_version': ["Model version doesn't exist..." ]}
    from synapse_sdk.core.api_error import ApiError

    with pytest.raises(ApiError) as e:
        client.projects.update(id=p.id, model_version='3.4.6')
    assert e.value.status_code == 400
    assert e.value.body['validation_errors']['model_version'][0].startswith("Model version doesn't exist")


def test_projects_import_predictions(django_live_url, business_client):
    """Import multiple predictions via projects.import_predictions

    Purpose:
    - Verify that the bulk predictions import endpoint creates predictions for a project

    Setup:
    - Create a project with a simple text classification config
    - Create one task in the project

    Actions:
    - Call client.projects.import_predictions with three predictions for the same task

    Validations:
    - API returns created == 3
    - Listing predictions for the task returns exactly three items with expected model versions
    """

    client = Synapse(base_url=django_live_url, api_key=business_client.api_key)
    li = LabelInterface(LABEL_CONFIG_AND_TASKS['label_config'])
    project = client.projects.create(title='Predictions Import Project', label_config=li.config)

    task = ls.tasks.create(project=project.id, data={'my_text': 'Classify this sentence'})

    model_versions = ['humor__gpt-5-mini', 'humor__gpt-4.1-mini', 'humor__gpt-4o-mini']
    choices = [['Positive'], ['Neutral'], ['Negative']]

    predictions_payload = []
    for mv, ch in zip(model_versions, choices):
        predictions_payload.append(
            {
                'result': [
                    {
                        'from_name': 'sentiment_class',
                        'to_name': 'message',
                        'type': 'choices',
                        'value': {'choices': ch},
                    }
                ],
                'model_version': mv,
                'score': 1,
                'task': task.id,
            }
        )

    response = client.projects.import_predictions(id=project.id, request=predictions_payload)
    assert response.created == 3

    preds = ls.predictions.list(task=task.id)
    assert len(preds) == 3
    returned_versions = sorted([p.model_version for p in preds])
    assert returned_versions == sorted(model_versions)






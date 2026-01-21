"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license."""

import logging

import ujson as json
from core.current_request import CurrentContext, get_current_request
from core.feature_flags import flag_set
from core.label_config import replace_task_data_undefined_with_config_field
from core.utils.common import load_func, retry_database_locked
from core.utils.db import fast_first
from django.conf import settings
from django.db import IntegrityError, transaction
from drf_spectacular.utils import extend_schema_field
from fsm.serializer_fields import FSMStateField
from fsm.state_manager import get_state_manager
from fsm.utils import is_fsm_enabled
from synapse_sdk.synapse_interface import LabelInterface
from projects.models import Project
from rest_flex_fields import FlexFieldsModelSerializer
from rest_framework import generics, serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SkipField
from rest_framework.serializers import ModelSerializer
from rest_framework.settings import api_settings
from tasks.exceptions import AnnotationDuplicateError
from tasks.models import Annotation, AnnotationDraft, Prediction, PredictionMeta, Task
from tasks.validation import TaskValidator
from users.models import User
from users.serializers import UserSerializer

logger = logging.getLogger(__name__)


class PredictionQuerySerializer(serializers.Serializer):
    task = serializers.IntegerField(
        required=False, help_text="Task ID to filter predictions"
    )
    project = serializers.IntegerField(
        required=False, help_text="Project ID to filter predictions"
    )


@extend_schema_field(
    {
        "type": "array",
        "title": "Prediction result list",
        "description": "List of prediction results for the task",
        "items": {
            "type": "object",
            "title": "Prediction result items (regions)",
            "description": "List of predicted regions for the task",
        },
    }
)
class PredictionResultField(serializers.JSONField):
    pass


@extend_schema_field(
    {
        "type": "array",
        "title": "Annotation result list",
        "description": "List of annotation results for the task",
        "items": {
            "type": "object",
            "title": "Annotation result items (regions)",
            "description": "List of annotated regions for the task",
        },
    }
)
class AnnotationResultField(serializers.JSONField):
    pass


class PredictionSerializer(ModelSerializer):
    result = PredictionResultField()
    model_version = serializers.CharField(
        allow_blank=True,
        required=False,
        help_text="Model version - tag for predictions that can be used to filter tasks in Data Manager, as well as "
        "select specific model version for showing preannotations in the labeling interface",
    )
    created_ago = serializers.CharField(
        default="", read_only=True, help_text="Delta time from creation time"
    )

    def validate(self, data):
        """Validate prediction using LabelInterface against project configuration"""
        project = None
        if "task" in data:
            project = data["task"].project
        elif "project" in data:
            project = data["project"]
        ff_user = project.organization.created_by if project else "auto"

        if not flag_set(
            "fflag_feat_utc_210_prediction_validation_15082025", user=ff_user
        ):
            # Skip validation if feature flag is not set
            logger.info(
                f"Skipping prediction validation in PredictionSerializer for user {ff_user}"
            )
            return super().validate(data)

        # Only validate if we're updating the result field
        if "result" not in data:
            return data

        if not project:
            raise ValidationError("Project is required for prediction validation")

        # Validate prediction using LabelInterface
        li = LabelInterface(project.label_config)
        validation_errors = li.validate_prediction(data, return_errors=True)

        if validation_errors:
            raise ValidationError(f"Error validating prediction: {validation_errors}")

        return data

    class Meta:
        model = Prediction
        fields = "__all__"


class ListAnnotationSerializer(serializers.ListSerializer):
    pass


class CompletedByDMSerializer(UserSerializer):
    def _is_deleted(self, instance):
        """Override to never mark users as deleted in annotation context.

        We always want to show who completed an annotation, regardless of
        their current organization membership status.
        """
        return False

    def to_representation(self, instance):
        """Override to ensure proper context is passed"""
        # Ensure we have proper request context
        if "request" not in self.context and "view" in self.context:
            request = getattr(self.context["view"], "request", None)
            if request:
                self.context["request"] = request

        return super().to_representation(instance)

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "avatar", "email", "initials"]


class AnnotationSerializer(FlexFieldsModelSerializer):
    """
    Annotation Serializer with FSM state support.

    Note: The 'state' field will be populated from the queryset annotation
    if present, preventing N+1 queries. Use .with_state() on your queryset.
    """

    state = FSMStateField(
        read_only=True
    )  # FSM state - automatically uses annotation if present
    """"""

    result = AnnotationResultField(required=False)
    created_username = serializers.SerializerMethodField(
        default="", read_only=True, help_text="Username string"
    )
    created_ago = serializers.CharField(
        default="", read_only=True, help_text="Time delta from creation time"
    )
    completed_by = serializers.PrimaryKeyRelatedField(
        required=False, queryset=User.objects.all()
    )
    unique_id = serializers.CharField(required=False, write_only=True)

    def create(self, *args, **kwargs):
        try:
            return super().create(*args, **kwargs)
        except IntegrityError as e:
            errors = [
                "UNIQUE constraint failed: task_completion.unique_id",
                'duplicate key value violates unique constraint "task_completion_unique_id_key"',
            ]
            if any([error in str(e) for error in errors]):
                raise AnnotationDuplicateError()
            raise

    def validate_result(self, value):
        data = value
        # convert from str to json if need
        if isinstance(value, str):
            try:
                data = json.loads(value)
            except:  # noqa: E722
                raise ValueError('annotation "result" can\'t be parse from str to JSON')

        # check result is list
        if not isinstance(data, list):
            raise ValidationError(
                'annotation "result" field in annotation must be list'
            )

        return data

    def get_created_username(self, annotation) -> str:
        user = annotation.completed_by
        if not user:
            return ""

        name = user.first_name
        if len(user.last_name):
            name = name + " " + user.last_name

        name += f" {user.email}, {user.id}"
        return name

    def to_representation(self, obj):
        """Remove state field if feature flags are disabled"""
        ret = super().to_representation(obj)
        user = CurrentContext.get_user()
        if not (
            flag_set("fflag_feat_fit_568_finite_state_management", user=user)
            and flag_set("fflag_feat_fit_710_fsm_state_fields", user=user)
        ):
            ret.pop("state", None)

        # =====================================================================
        # HIDE ANNOTATOR INFO FROM OTHER ANNOTATORS AND CLIENTS
        # =====================================================================
        # Annotators should not see other annotators' identity
        # Clients should not see annotator details until review is complete
        try:
            from annotators.annotation_workflow import AnnotationWorkflowService
            from annotators.models import AnnotatorProfile, TaskConsensus

            if user and user.is_authenticated:
                is_annotator = hasattr(user, "annotator_profile")
                is_expert = getattr(user, "is_expert", False)
                is_admin = user.is_superuser
                is_own_annotation = obj.completed_by_id == user.id

                # Check if task is finalized
                task_finalized = False
                try:
                    consensus = obj.task.consensus
                    task_finalized = consensus.status == "finalized"
                except TaskConsensus.DoesNotExist:
                    pass

                # For annotators: only show completed_by for their own annotations
                # For clients: only show completed_by after task is finalized
                # Experts and admins can always see
                should_hide_identity = False

                if is_annotator and not is_expert and not is_admin:
                    # Annotators can only see their own identity
                    if not is_own_annotation:
                        should_hide_identity = True
                elif not is_expert and not is_admin:
                    # Clients - only see after finalization
                    if not task_finalized:
                        should_hide_identity = True

                if should_hide_identity:
                    # Replace completed_by with anonymous info
                    ret["completed_by"] = None
                    if "created_username" in ret:
                        ret["created_username"] = "Annotator"
        except Exception as e:
            import logging

            logging.getLogger(__name__).warning(f"Error hiding annotator info: {e}")

        return ret

    class Meta:
        model = Annotation
        exclude = ["prediction", "result_count"]
        expandable_fields = {"completed_by": (CompletedByDMSerializer,)}


class TaskSimpleSerializer(ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Don't pre-set annotations field - we'll handle it in to_representation
        if "annotations" not in self._declared_fields:
            self.fields["annotations"] = AnnotationSerializer(
                many=True, default=[], context=self.context, read_only=True
            )
        self.fields["predictions"] = PredictionSerializer(
            many=True, default=[], context=self.context, read_only=True
        )

    def to_representation(self, instance):
        # Check for consolidated annotation BEFORE parent serialization
        request = self.context.get("request")
        should_use_consolidated = False

        if request and hasattr(request, "user") and request.user.is_authenticated:
            try:
                from annotators.annotation_workflow import AnnotationWorkflowService
                from annotators.models import TaskConsensus

                user = request.user
                is_expert = hasattr(user, "expert_profile")

                # Check if expert and consolidated result exists
                if is_expert:
                    try:
                        consensus = instance.consensus
                        if consensus.consolidated_result and consensus.status in [
                            "review_required",
                            "consensus_reached",
                        ]:
                            should_use_consolidated = True
                            # Store consolidated info for later use
                            instance._consolidated_info = {
                                "result": consensus.consolidated_result,
                                "method": consensus.consolidation_method,
                                "agreement": float(consensus.average_agreement or 0),
                                "updated_at": consensus.updated_at,
                            }
                    except TaskConsensus.DoesNotExist:
                        pass
            except Exception as e:
                import logging

                logging.getLogger(__name__).warning(f"Error checking consolidated: {e}")

        project = instance.project
        if project:
            # resolve $undefined$ key in task data
            data = instance.data
            replace_task_data_undefined_with_config_field(data, project)

        ret = super().to_representation(instance)

        # =====================================================================
        # FILTER ANNOTATIONS BASED ON USER ROLE (ANNOTATION ISOLATION)
        # =====================================================================
        # Annotators can only see their own annotations
        # Experts see consolidated annotation if available, otherwise all annotations
        # Clients can only see after expert review is complete
        try:
            # Check if we should show consolidated annotation for expert
            if hasattr(instance, "_consolidated_info"):
                consolidated_info = instance._consolidated_info
                # Replace all annotations with consolidated annotation
                consolidated_ann = {
                    "id": "consolidated",  # String ID to identify as consolidated
                    "result": consolidated_info["result"],
                    "was_cancelled": False,
                    "ground_truth": False,
                    "created_at": (
                        consolidated_info["updated_at"].isoformat()
                        if consolidated_info["updated_at"]
                        else None
                    ),
                    "updated_at": (
                        consolidated_info["updated_at"].isoformat()
                        if consolidated_info["updated_at"]
                        else None
                    ),
                    "lead_time": 0,
                    "task": instance.id,
                    "completed_by": None,
                    # Add consolidation metadata
                    "_is_consolidated": True,
                    "_consolidation_method": consolidated_info["method"],
                    "_average_agreement": consolidated_info["agreement"],
                }
                ret["annotations"] = [consolidated_ann]
            else:
                # Normal annotation filtering for non-expert users
                from annotators.annotation_workflow import AnnotationWorkflowService

                request = self.context.get("request")
                if (
                    request
                    and hasattr(request, "user")
                    and request.user.is_authenticated
                ):
                    user = request.user
                    visible_annotations = (
                        AnnotationWorkflowService.get_visible_annotations(
                            user, instance, include_own=True
                        )
                    )
                    # Re-serialize only visible annotations
                    visible_ids = set(visible_annotations.values_list("id", flat=True))
                    if "annotations" in ret and ret["annotations"]:
                        ret["annotations"] = [
                            ann
                            for ann in ret["annotations"]
                            if ann.get("id") in visible_ids
                        ]
        except ImportError:
            pass  # Module not available
        except Exception as e:
            import logging

            logging.getLogger(__name__).warning(f"Error filtering annotations: {e}")

        # Add rework information for annotators
        try:
            from annotators.models import TaskAssignment, AnnotatorProfile

            request = self.context.get("request")
            if request and hasattr(request, "user") and request.user.is_authenticated:
                user = request.user
                if hasattr(user, "annotator_profile"):
                    profile = user.annotator_profile
                    assignment = TaskAssignment.objects.filter(
                        task=instance, annotator=profile
                    ).first()

                    if assignment and assignment.flagged_for_review:
                        ret["needs_rework"] = True
                        ret["rework_reason"] = assignment.flag_reason
                    else:
                        ret["needs_rework"] = False
        except Exception as e:
            import logging

            logging.getLogger(__name__).debug(f"Could not add rework info: {e}")

        return ret

    class Meta:
        model = Task
        exclude = ("precomputed_agreement",)


class BaseTaskSerializer(FlexFieldsModelSerializer):
    """Task Serializer with project scheme configs validation"""

    def project(self, task=None):
        """Take the project from context"""
        if "project" in self.context:
            project = self.context["project"]
        elif "view" in self.context and "project_id" in self.context["view"].kwargs:
            kwargs = self.context["view"].kwargs
            project = generics.get_object_or_404(Project, kwargs["project_id"])
        elif task:
            project = task.project
        else:
            project = None
        return project

    def validate(self, task):
        instance = self.instance if hasattr(self, "instance") else None

        project = self.project(task=instance)

        current_request = get_current_request()
        if current_request and current_request.method == "POST" and not project:
            # raise ValidationError for the project field with standard DRF message
            try:
                self.fields["project"].fail("required")
            except ValidationError as exc:
                raise ValidationError(
                    {
                        "project": exc.detail,
                    }
                )

        validator = TaskValidator(
            project,
            instance=instance if "data" not in task else None,
        )
        return validator.validate(task)

    def to_representation(self, instance):
        project = self.project(instance)
        if project:
            # resolve uri for storage (s3/gcs/etc)
            if self.context.get("resolve_uri", False):
                instance.data = instance.resolve_uri(instance.data, project)

            # resolve $undefined$ key in task data
            data = instance.data
            replace_task_data_undefined_with_config_field(data, project)

        ret = super().to_representation(instance)
        # Ensure allow_skip is always present in the response, even if None
        # This is important for frontend logic that checks allow_skip !== false
        if "allow_skip" not in ret:
            ret["allow_skip"] = instance.allow_skip

        # Include consensus information for expert review interface detection
        if hasattr(instance, "consensus") and instance.consensus:
            ret["consensus"] = {
                "id": instance.consensus.id,
                "status": instance.consensus.status,
                "average_agreement": (
                    float(instance.consensus.average_agreement)
                    if instance.consensus.average_agreement
                    else None
                ),
            }

        return ret

    class Meta:
        model = Task
        exclude = ("precomputed_agreement",)


class BaseTaskSerializerBulk(serializers.ListSerializer):
    """Serialize task with annotation from source json data"""

    annotations = AnnotationSerializer(many=True, default=[], read_only=True)
    predictions = PredictionSerializer(many=True, default=[], read_only=True)

    @property
    def project(self):
        return self.context.get("project")

    @staticmethod
    def format_error(i, detail, item):
        if len(detail) == 1:
            code = f" {detail[0].code}" if detail[0].code != "invalid" else ""
            return f"Error{code} at item {i}: {detail[0]} :: {item}"
        else:
            errors = ", ".join(detail)
            codes = [d.code for d in detail]
            return f"Errors {codes} at item {i}: {errors} :: {item}"

    def to_internal_value(self, data):
        """Body of run_validation for all data items"""
        if data is None:
            raise ValidationError("All tasks are empty (None)")

        if not isinstance(data, list):
            raise ValidationError(
                {api_settings.NON_FIELD_ERRORS_KEY: "not a list"}, code="not_a_list"
            )

        if not self.allow_empty and len(data) == 0:
            if self.parent and self.partial:
                raise SkipField()
            raise ValidationError(
                {api_settings.NON_FIELD_ERRORS_KEY: "empty"}, code="empty"
            )

        ret, errors = [], []
        self.annotation_count, self.prediction_count = 0, 0
        for i, item in enumerate(data):
            try:
                validated = self.child.validate(item)
            except ValidationError as exc:
                error = self.format_error(i, exc.detail, item)
                errors.append(error)
                # do not print to user too many errors
                if len(errors) >= 100:
                    errors[99] = "..."
                    break
            else:
                ret.append(validated)
                errors.append({})

                if "annotations" in item:
                    self.annotation_count += len(item["annotations"])
                if "predictions" in item:
                    self.prediction_count += len(item["predictions"])

        if any(errors):
            logger.warning("Can't deserialize tasks due to " + str(errors))
            raise ValidationError(errors)

        return ret

    @staticmethod
    def _insert_valid_completed_by(
        annotations, members_email_to_id, members_ids, default_user
    ):
        """Insert the correct id for completed_by by email in annotations"""
        for annotation in annotations:
            completed_by = annotation.get("completed_by")
            # no completed_by info found - just skip it, will be assigned to the user who imports
            if completed_by is None:
                annotation["completed_by_id"] = default_user.id

            # resolve annotators by email
            elif isinstance(completed_by, dict):
                if "email" not in completed_by:
                    raise ValidationError(
                        "It's expected to have 'email' field in 'completed_by' data in annotations"
                    )

                email = completed_by["email"]
                if email not in members_email_to_id:
                    if settings.ALLOW_IMPORT_TASKS_WITH_UNKNOWN_EMAILS:
                        annotation["completed_by_id"] = default_user.id
                    else:
                        raise ValidationError(f"Unknown annotator's email {email}")
                else:
                    # overwrite an actual member ID
                    annotation["completed_by_id"] = members_email_to_id[email]

            # old style annotators specification - try to find them by ID
            elif isinstance(completed_by, int) and completed_by in members_ids:
                if completed_by not in members_ids:
                    raise ValidationError(f"Unknown annotator's ID {completed_by}")
                annotation["completed_by_id"] = completed_by

            # in any other cases - import validation error
            else:
                raise ValidationError(
                    f"Import data contains completed_by={completed_by} which is not a valid annotator's email or ID"
                )
            annotation.pop("completed_by", None)

    @staticmethod
    def _insert_valid_user_reviews(dicts, members_email_to_id, default_user):
        """Insert correct user id by email from snapshot

        :param dicts: draft or review dicts from snapshot
        :param members_email_to_id: mapping from emails to current Synapse instance user IDs
        :param default_user: if email is not found in membr_email_to_id, this user will be used
        :return:
        """
        for obj in dicts:
            created_by = obj.get("created_by", {})
            email = created_by.get("email") if isinstance(created_by, dict) else None

            # user default user
            if email not in members_email_to_id:
                obj["created_by_id"] = default_user.id
                logger.warning(
                    "Email not found in members_email_to_id, default user used instead"
                )

            # resolve annotators by email
            else:
                obj["created_by_id"] = members_email_to_id[email]

            obj.pop("created_by", None)

    @staticmethod
    def _insert_valid_user_drafts(dicts, members_email_to_id, default_user):
        """Insert correct user id by email from snapshot

        :param dicts: draft or review dicts from snapshot
        :param members_email_to_id: mapping from emails to current Synapse instance user IDs
        :param default_user: if email is not found in membr_email_to_id, this user will be used
        :return:
        """
        for obj in dicts:
            email = obj.get("user")

            # user default user
            if email not in members_email_to_id:
                obj["user_id"] = default_user.id
                logger.warning(
                    "Email not found in members_email_to_id, default user used instead"
                )

            # resolve annotators by email
            else:
                obj["user_id"] = members_email_to_id[email]

            obj.pop("user", None)

    @retry_database_locked()
    def create(self, validated_data):
        """Create Tasks, Annotations, etc in bulk"""
        validated_tasks = validated_data
        logging.info(
            f"Try to serialize tasks with annotations, data len = {len(validated_data)}"
        )
        user = self.context.get("user", None)
        default_user = user or self.project.created_by
        ff_user = self.project.organization.created_by

        # get members from project, we need them to restore annotation.completed_by etc
        organization = self.project.organization
        members_email_to_id = dict(
            organization.members.values_list("user__email", "user__id")
        )
        members_ids = set(members_email_to_id.values())
        logger.debug(
            f"{len(members_email_to_id)} members found in organization {organization}"
        )

        # to be sure we add tasks with annotations at the same time
        with transaction.atomic():

            # extract annotations, predictions, drafts, reviews, etc
            # all these lists will be grouped by tasks, e.g.:
            # task_annotations = [ [a1, a2], [a3, a4, a5], ... ]
            task_annotations, task_predictions = [], []
            task_drafts, task_reviews = [], []
            for task in validated_tasks:
                # extract annotations from snapshot
                annotations = task.pop("annotations", [])
                self._insert_valid_completed_by(
                    annotations, members_email_to_id, members_ids, default_user
                )
                task_annotations.append(annotations)

                # extract predictions from snapshot
                predictions = task.pop("predictions", [])
                task_predictions.append(predictions)

                if flag_set(
                    "fflag_feat_back_lsdv_5307_import_reviews_drafts_29062023_short",
                    user=ff_user,
                ):
                    # extract drafts from snapshot
                    drafts = task.pop("drafts", [])
                    self._insert_valid_user_drafts(
                        drafts, members_email_to_id, default_user
                    )
                    task_drafts.append(drafts)

                    # extract reviews from snapshot annotations
                    for annotation in annotations:
                        reviews = annotation.get("reviews", [])
                        self._insert_valid_user_reviews(
                            reviews, members_email_to_id, default_user
                        )
                        task_reviews.append(reviews)

            db_tasks = self.add_tasks(
                task_annotations, task_predictions, validated_tasks
            )
            db_annotations = self.add_annotations(task_annotations, user)
            prediction_errors = self.add_predictions(task_predictions)

            raise_prediction_errors = True
            if not flag_set(
                "fflag_feat_utc_210_prediction_validation_15082025", user=ff_user
            ):
                raise_prediction_errors = False

            # If there are prediction validation errors, raise them
            if prediction_errors and raise_prediction_errors:
                raise ValidationError({"predictions": prediction_errors})

        self.post_process_annotations(user, db_annotations, "imported")
        self.post_process_tasks(self.project.id, [t.id for t in self.db_tasks])
        self.post_process_custom_callback(self.project.id, user)

        if flag_set(
            "fflag_feat_back_lsdv_5307_import_reviews_drafts_29062023_short",
            user=ff_user,
        ):
            with transaction.atomic():
                # build mapping between new and old ids in annotations,
                # we need it because annotation ids will be known only after saving to db
                annotation_mapping = {v.import_id: v.id for v in db_annotations}
                annotation_mapping[None] = None
                # the sequence of add_ functions is very important because of references to ids
                self.add_drafts(task_drafts, db_tasks, annotation_mapping, self.project)
                self.add_reviews(task_reviews, annotation_mapping, self.project)

        return db_tasks

    def add_predictions(self, task_predictions):
        """Save predictions to DB and set the latest model version in the project"""
        db_predictions = []
        validation_errors = []

        should_validate = self.project.label_config_is_not_default and flag_set(
            "fflag_feat_utc_210_prediction_validation_15082025",
            user=self.project.organization.created_by,
        )

        # add predictions
        last_model_version = None
        for i, predictions in enumerate(task_predictions):
            for j, prediction in enumerate(predictions):
                if not isinstance(prediction, dict):
                    validation_errors.append(
                        f"Task {i}, prediction {j}: Prediction must be a dictionary"
                    )
                    continue

                # Validate prediction only when project label config is not default
                if should_validate:
                    try:
                        li = (
                            LabelInterface(self.project.label_config)
                            if should_validate
                            else None
                        )
                        validation_errors_list = li.validate_prediction(
                            prediction, return_errors=True
                        )

                        if validation_errors_list:
                            # Format errors for better readability
                            for error in validation_errors_list:
                                validation_errors.append(
                                    f"Task {i}, prediction {j}: {error}"
                                )
                            continue

                    except Exception as e:
                        validation_errors.append(
                            f"Task {i}, prediction {j}: Error validating prediction - {str(e)}"
                        )
                        continue

                try:
                    # we need to call result normalizer here since "bulk_create" doesn't call save() method
                    result = Prediction.prepare_prediction_result(
                        prediction["result"], self.project
                    )
                    prediction_score = prediction.get("score")
                    if prediction_score is not None:
                        try:
                            prediction_score = float(prediction_score)
                        except ValueError:
                            logger.error(
                                "Can't upload prediction score: should be in float format."
                                "Fallback to score=None"
                            )
                            prediction_score = None

                    last_model_version = prediction.get("model_version", "undefined")
                    db_predictions.append(
                        Prediction(
                            task=self.db_tasks[i],
                            project=self.db_tasks[i].project,
                            result=result,
                            score=prediction_score,
                            model_version=last_model_version,
                        )
                    )
                except Exception as e:
                    validation_errors.append(
                        f"Task {i}, prediction {j}: Failed to create prediction - {str(e)}"
                    )
                    continue

        # Return validation errors if they exist
        if validation_errors:
            return validation_errors

        # predictions: DB bulk create
        self.db_predictions = Prediction.objects.bulk_create(
            db_predictions, batch_size=settings.BATCH_SIZE
        )
        logging.info(
            f"Predictions serialization success, len = {len(self.db_predictions)}"
        )



        return None  # No errors

    def add_reviews(self, task_reviews, annotation_mapping, project):
        """Save task reviews to DB"""
        return []

    def add_drafts(self, task_drafts, db_tasks, annotation_mapping, project):
        """Save task drafts to DB"""
        db_drafts = []

        # add drafts
        for i, drafts in enumerate(task_drafts):
            for draft in drafts:
                if not isinstance(draft, dict):
                    continue

                draft.update(
                    {
                        "task_id": db_tasks[i].id,
                        "annotation_id": annotation_mapping[draft.get("annotation")],
                        "project": self.project,
                        "import_id": draft.get("id"),
                    }
                )
                # remove redundant fields
                [
                    draft.pop(field, None)
                    for field in [
                        "id",
                        "task",
                        "annotation",
                        "project",
                        "created_username",
                        "created_ago",
                    ]
                ]
                db_drafts.append(AnnotationDraft(**draft))

        self.db_drafts = AnnotationDraft.objects.bulk_create(
            db_drafts, batch_size=settings.BATCH_SIZE
        )
        logging.info(f"drafts serialization success, len = {len(self.db_drafts)}")

        return self.db_drafts

    def add_annotations(self, task_annotations, user):
        """Save task annotations to DB"""
        db_annotations = []

        # add annotations
        for i, annotations in enumerate(task_annotations):
            for annotation in annotations:
                if not isinstance(annotation, dict):
                    continue

                ground_truth = annotation.pop("ground_truth", True)
                was_cancelled = annotation.pop("was_cancelled", False)
                lead_time = annotation.pop("lead_time", None)

                body = {
                    "task": self.db_tasks[i],
                    "project": self.project,
                    "ground_truth": ground_truth,
                    "was_cancelled": was_cancelled,
                    "completed_by_id": annotation["completed_by_id"],
                    "result": annotation["result"],
                    "lead_time": lead_time,
                    "import_id": annotation.get("id"),
                }
                db_annotations.append(Annotation(**body))

        # annotations: DB bulk create
        if settings.DJANGO_DB == settings.DJANGO_DB_SQLITE:
            self.db_annotations = []
            try:
                last_annotation = Annotation.objects.latest("id")
                current_id = last_annotation.id + 1
            except Annotation.DoesNotExist:
                current_id = 1

            for annotation in db_annotations:
                annotation.id = current_id
                current_id += 1
            self.db_annotations = Annotation.objects.bulk_create(
                db_annotations, batch_size=settings.BATCH_SIZE
            )
        else:
            self.db_annotations = Annotation.objects.bulk_create(
                db_annotations, batch_size=settings.BATCH_SIZE
            )
        logging.info(
            f"Annotations serialization success, len = {len(self.db_annotations)}"
        )

        return self.db_annotations

    def add_tasks(self, task_annotations, task_predictions, validated_tasks):
        """Extract tasks from validated_tasks and store them in DB"""
        db_tasks = []
        # Use required_overlap for consensus workflow (minimum 3)
        max_overlap = max(3, getattr(self.project, "required_overlap", 3))

        # Acquire a lock on the project to ensure atomicity when calculating inner_id
        project = Project.objects.select_for_update().get(id=self.project.id)

        last_task = fast_first(
            Task.objects.filter(project=project).order_by("-inner_id")
        )
        prev_inner_id = last_task.inner_id if last_task else 0
        max_inner_id = (prev_inner_id + 1) if prev_inner_id else 1

        calculate_is_labeled_with_distinct_annotators = flag_set(
            "fflag_fix_fit_1082_overlap_use_distinct_annotators", user="auto"
        )

        for i, task in enumerate(validated_tasks):
            cancelled_annotations = len(
                [ann for ann in task_annotations[i] if ann.get("was_cancelled", False)]
            )
            total_annotations = len(task_annotations[i]) - cancelled_annotations
            if calculate_is_labeled_with_distinct_annotators:
                current_overlap = len(
                    set([ann.get("completed_by_id") for ann in task_annotations[i]])
                )
            else:
                current_overlap = len(task_annotations[i])
            t = Task(
                project=self.project,
                data=task["data"],
                meta=task.get("meta", {}),
                overlap=max_overlap,
                target_assignment_count=max_overlap,  # Set target to match overlap for consensus
                is_labeled=current_overlap >= max_overlap,
                file_upload_id=task.get("file_upload_id"),
                inner_id=None if prev_inner_id is None else max_inner_id + i,
                total_predictions=len(task_predictions[i]),
                total_annotations=total_annotations,
                cancelled_annotations=cancelled_annotations,
                allow_skip=task.get(
                    "allow_skip", True
                ),  # Default to True for backward compatibility
            )
            db_tasks.append(t)

        # get task ids
        if settings.DJANGO_DB == settings.DJANGO_DB_SQLITE:
            self.db_tasks = []
            try:
                last_task = Task.objects.latest("id")
                current_id = last_task.id + 1
            except Task.DoesNotExist:
                current_id = 1

            for task in db_tasks:
                task.id = current_id
                current_id += 1
            self.db_tasks = Task.objects.bulk_create(
                db_tasks, batch_size=settings.BATCH_SIZE
            )
        else:
            self.db_tasks = Task.objects.bulk_create(
                db_tasks, batch_size=settings.BATCH_SIZE
            )

        logging.info(f"Tasks serialization success, len = {len(self.db_tasks)}")

        # Backfill FSM states for bulk-created tasks
        # bulk_create() bypasses save() so FSM transitions don't fire automatically
        self._backfill_fsm_states(self.db_tasks)

        return db_tasks

    def _backfill_fsm_states(self, tasks):
        """
        Backfill FSM states for tasks created via bulk_create().

        bulk_create() bypasses the model's save() method, so FSM transitions
        don't fire automatically. This sets initial CREATED state for newly imported tasks.
        """
        if not tasks or not is_fsm_enabled(user=None):
            return

        StateManager = get_state_manager()
        for task in tasks:
            StateManager.execute_transition(
                entity=task, transition_name="task_created", user=None
            )

    @staticmethod
    def post_process_annotations(user, db_annotations, action):
        pass

    @staticmethod
    def post_process_tasks(user, db_tasks):
        pass

    @staticmethod
    def add_annotation_fields(body, user, action):
        return body

    @staticmethod
    def post_process_custom_callback(project_id, user):
        pass

    class Meta:
        model = Task
        fields = "__all__"


TaskSerializer = load_func(settings.TASK_SERIALIZER)


class TaskWithAnnotationsSerializer(TaskSerializer):
    """ """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["annotations"] = AnnotationSerializer(
            many=True, default=[], context=self.context
        )

    class Meta:
        model = Task
        list_serializer_class = load_func(settings.TASK_SERIALIZER_BULK)

        exclude = ()


class AnnotationDraftSerializer(ModelSerializer):
    """
    AnnotationDraft Serializer with FSM state support.

    Note: The 'state' field will be populated from the queryset annotation
    if present, preventing N+1 queries. Use .with_state() on your queryset.
    """

    state = FSMStateField(
        read_only=True
    )  # FSM state - automatically uses annotation if present
    user = serializers.CharField(default=serializers.CurrentUserDefault())
    created_username = serializers.SerializerMethodField(
        default="", read_only=True, help_text="User name string"
    )
    created_ago = serializers.CharField(
        default="", read_only=True, help_text="Delta time from creation time"
    )

    def get_created_username(self, draft):
        user = draft.user
        if not user:
            return ""

        name = user.first_name
        last_name = user.last_name
        if len(last_name):
            name = name + " " + last_name
        name += (" " if name else "") + f"{user.email}, {user.id}"
        return name

    def to_representation(self, obj):
        """Remove state field if feature flags are disabled"""
        ret = super().to_representation(obj)
        user = CurrentContext.get_user()
        if not (
            flag_set("fflag_feat_fit_568_finite_state_management", user=user)
            and flag_set("fflag_feat_fit_710_fsm_state_fields", user=user)
        ):
            ret.pop("state", None)
        return ret

    class Meta:
        model = AnnotationDraft
        fields = "__all__"


class TaskWithAnnotationsAndPredictionsAndDraftsSerializer(TaskSerializer):

    predictions = serializers.SerializerMethodField(default=[], read_only=True)
    annotations = serializers.SerializerMethodField(default=[], read_only=True)
    drafts = serializers.SerializerMethodField(default=[], read_only=True)
    annotators = serializers.SerializerMethodField(default=[], read_only=True)
    updated_by = serializers.SerializerMethodField(default=[], read_only=True)

    def get_annotators(self, task):
        """Return annotators with full user data for frontend compatibility"""
        from users.models import User

        # Get unique user IDs from completed annotations
        user_ids = list(
            task.annotations.filter(was_cancelled=False)
            .values_list("completed_by", flat=True)
            .distinct()
        )

        if not user_ids:
            return []

        # Fetch user data
        users = User.objects.filter(id__in=user_ids).values(
            "id", "first_name", "last_name", "email", "username", "avatar"
        )
        user_map = {u["id"]: u for u in users}

        # Build annotator list with full user data (camelCase for frontend)
        result = []
        for user_id in user_ids:
            if user_id and user_id in user_map:
                user_data = user_map[user_id]
                result.append(
                    {
                        "user_id": user_id,
                        "id": user_data["id"],
                        "firstName": user_data["first_name"] or "",
                        "lastName": user_data["last_name"] or "",
                        "email": user_data["email"],
                        "username": user_data["username"],
                        "avatar": user_data["avatar"],
                        "annotated": True,
                        "review": None,
                        "reviewed": False,
                    }
                )
        return result

    def get_updated_by(self, task):
        """Return updated_by with full user details to avoid frontend reference errors"""
        if not task.updated_by_id:
            return []

        try:
            from users.models import User

            user = (
                User.objects.filter(id=task.updated_by_id)
                .values("id", "first_name", "last_name", "email", "username", "avatar")
                .first()
            )

            if user:
                return [
                    {
                        "user_id": user["id"],
                        "id": user["id"],
                        "firstName": user["first_name"] or "",
                        "lastName": user["last_name"] or "",
                        "email": user["email"],
                        "username": user["username"] or user["email"].split("@")[0],
                        "avatar": user["avatar"] or "",
                    }
                ]
        except Exception:
            pass

        return [{"user_id": task.updated_by_id}]

    def _get_user(self):
        if "request" in self.context and hasattr(self.context["request"], "user"):
            return self.context["request"].user

    def get_predictions(self, task):
        predictions = task.predictions
        return PredictionSerializer(
            predictions, many=True, read_only=True, default=[], context=self.context
        ).data

    def get_annotations(self, task):
        """Return annotations only for the current user"""
        from django.db.models import Prefetch
        from organizations.models import OrganizationMember

        annotations = task.annotations

        user = self._get_user()
        if user and user.is_annotator:
            annotations = annotations.filter(completed_by=user)

        # Prefetch organization members to avoid N+1 queries and prevent
        # 'Deleted User' issue when serializing completed_by field
        annotations = annotations.select_related("completed_by").prefetch_related(
            Prefetch(
                "completed_by__om_through",
                queryset=OrganizationMember.objects.select_related("organization"),
            )
        )

        return AnnotationSerializer(
            annotations, many=True, read_only=True, default=[], context=self.context
        ).data

    def get_drafts(self, task):
        """Return drafts only for the current user"""
        # it's for swagger documentation
        if not isinstance(task, Task):
            return AnnotationDraftSerializer(many=True)

        drafts = task.drafts
        if "request" in self.context and hasattr(self.context["request"], "user"):
            user = self.context["request"].user
            drafts = drafts.filter(user=user)

        return AnnotationDraftSerializer(
            drafts, many=True, read_only=True, default=[], context=self.context
        ).data


class NextTaskSerializer(TaskWithAnnotationsAndPredictionsAndDraftsSerializer):
    unique_lock_id = serializers.SerializerMethodField()

    def get_unique_lock_id(self, task):
        user = self.context["request"].user
        lock = task.locks.filter(user=user).first()
        if lock:
            return lock.unique_id

    def get_predictions(self, task):
        predictions = task.get_predictions_for_prelabeling()
        return PredictionSerializer(
            predictions, many=True, read_only=True, default=[], context=self.context
        ).data

    def get_annotations(self, task):
        result = []
        if self.context.get("annotations", False):
            annotations = super().get_annotations(task)
            user = self.context["request"].user
            for annotation in annotations:
                if annotation.get("completed_by") == user.id:
                    result.append(annotation)
        return result


class TaskIDWithAnnotationsAndPredictionsSerializer(ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["annotations"] = AnnotationSerializer(
            many=True, default=[], context=self.context
        )
        self.fields["predictions"] = PredictionSerializer(
            many=True, default=[], context=self.context
        )

    class Meta:
        model = Task
        fields = ["id", "annotations", "predictions"]


class TaskIDOnlySerializer(ModelSerializer):
    class Meta:
        model = Task
        fields = ["id"]


class PredictionMetaSerializer(ModelSerializer):
    """Serializer for PredictionMeta model"""

    class Meta:
        model = PredictionMeta
        fields = "__all__"
        read_only_fields = ["prediction", "failed_prediction"]


# LSE inherits this serializer
TaskSerializerBulk = load_func(settings.TASK_SERIALIZER_BULK)






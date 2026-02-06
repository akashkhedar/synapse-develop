"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license.
"""
import logging
import bleach
from constants import SAFE_HTML_ATTRIBUTES, SAFE_HTML_TAGS
from django.db.models import Q
from fsm.serializer_fields import FSMStateField

logger = logging.getLogger(__name__)
from synapse_sdk.synapse_interface import LabelInterface
from synapse_sdk.synapse_interface.control_tags import (
    BrushLabelsTag,
    BrushTag,
    ChoicesTag,
    DateTimeTag,
    EllipseLabelsTag,
    EllipseTag,
    HyperTextLabelsTag,
    KeyPointLabelsTag,
    KeyPointTag,
    LabelsTag,
    NumberTag,
    ParagraphLabelsTag,
    PolygonLabelsTag,
    PolygonTag,
    RatingTag,
    RectangleLabelsTag,
    RectangleTag,
    TaxonomyTag,
    TextAreaTag,
    TimeSeriesLabelsTag,
    VideoRectangleTag,
)
from projects.models import Project, ProjectImport, ProjectOnboarding, ProjectReimport, ProjectSummary
from rest_flex_fields import FlexFieldsModelSerializer
from rest_framework import serializers
from rest_framework.serializers import SerializerMethodField
from tasks.models import Task
from users.serializers import UserSimpleSerializer


class CreatedByFromContext:
    requires_context = True

    def __call__(self, serializer_field):
        return serializer_field.context.get('created_by')


class ProjectSerializer(FlexFieldsModelSerializer):
    """Serializer get numbers from project queryset annotation,
    make sure, that you use correct one(Project.objects.with_counts())
    """

    task_number = serializers.IntegerField(default=None, read_only=True, help_text='Total task number in project')
    total_annotations_number = serializers.IntegerField(
        default=None,
        read_only=True,
        help_text='Total annotations number in project including '
        'skipped_annotations_number and ground_truth_number.',
    )
    total_predictions_number = serializers.IntegerField(
        default=None,
        read_only=True,
        help_text='Total predictions number in project including '
        'skipped_annotations_number, ground_truth_number, and '
        'useful_annotation_number.',
    )
    useful_annotation_number = serializers.IntegerField(
        default=None,
        read_only=True,
        help_text='Useful annotation number in project not including '
        'skipped_annotations_number and ground_truth_number. '
        'Total annotations = annotation_number + '
        'skipped_annotations_number + ground_truth_number',
    )
    ground_truth_number = serializers.IntegerField(
        default=None, read_only=True, help_text='Honeypot annotation number in project'
    )
    skipped_annotations_number = serializers.IntegerField(
        default=None, read_only=True, help_text='Skipped by collaborators annotation number in project'
    )
    num_tasks_with_annotations = serializers.IntegerField(
        default=None, read_only=True, help_text='Tasks with annotations count'
    )

    created_by = UserSimpleSerializer(default=CreatedByFromContext(), help_text='Project owner')

    parsed_label_config = serializers.JSONField(
        default=None, read_only=True, help_text='JSON-formatted labeling configuration'
    )
    config_has_control_tags = SerializerMethodField(
        default=None, read_only=True, help_text='Flag to detect is project ready for labeling'
    )
    config_suitable_for_bulk_annotation = serializers.SerializerMethodField(
        default=None, read_only=True, help_text='Flag to detect is project ready for bulk annotation'
    )
    finished_task_number = serializers.IntegerField(default=None, read_only=True, help_text='Finished tasks')

    queue_total = serializers.SerializerMethodField()
    queue_done = serializers.SerializerMethodField()
    state = FSMStateField(read_only=True)  # FSM state - automatically uses annotation if present
    
    _annotator_assigned_tasks = SerializerMethodField(help_text='Number of tasks assigned to current annotator')
    _annotator_completed_tasks = SerializerMethodField(help_text='Number of tasks completed by current annotator')

    @property
    def user_id(self):
        try:
            return self.context['request'].user.id
        except KeyError:
            return next(iter(self.context['user_cache']))

    @staticmethod
    def get_config_has_control_tags(project) -> bool:
        return len(project.get_parsed_config()) > 0

    @staticmethod
    def get_config_suitable_for_bulk_annotation(project) -> bool:
        li = LabelInterface(project.label_config)

        # List of tags that should not be present
        disallowed_tags = [
            LabelsTag,
            BrushTag,
            BrushLabelsTag,
            EllipseTag,
            EllipseLabelsTag,
            KeyPointTag,
            KeyPointLabelsTag,
            PolygonTag,
            PolygonLabelsTag,
            RectangleTag,
            RectangleLabelsTag,
            HyperTextLabelsTag,
            ParagraphLabelsTag,
            TimeSeriesLabelsTag,
            VideoRectangleTag,
        ]

        # Return False if any disallowed tag is present
        for tag_class in disallowed_tags:
            if li.find_tags_by_class(tag_class):
                return False

        # Check perRegion/perItem for expanded list of tags, plus value="no" for Choices/Taxonomy
        allowed_tags_for_checks = [ChoicesTag, TaxonomyTag, DateTimeTag, NumberTag, RatingTag, TextAreaTag]
        for tag_class in allowed_tags_for_checks:
            tags = li.find_tags_by_class(tag_class)
            for tag in tags:
                per_region = tag.attr.get('perRegion', 'false').lower() == 'true'
                per_item = tag.attr.get('perItem', 'false').lower() == 'true'
                if per_region or per_item:
                    return False
                # For ChoicesTag and TaxonomyTag, the value attribute must not be set at all
                if tag_class in [ChoicesTag, TaxonomyTag]:
                    if 'value' in tag.attr:
                        return False

        # For TaxonomyTag, check labeling and apiUrl
        taxonomy_tags = li.find_tags_by_class(TaxonomyTag)
        for tag in taxonomy_tags:
            labeling = tag.attr.get('labeling', 'false').lower() == 'true'
            if labeling:
                return False
            api_url = tag.attr.get('apiUrl', None)
            if api_url is not None:
                return False

        # If all checks pass, return True
        return True

    @staticmethod
    def get_parsed_label_config(project):
        return project.get_parsed_config()

    def to_internal_value(self, data):
        # FIXME: remake this logic with start_training_on_annotation_update
        initial_data = data
        data = super().to_internal_value(data)

        if 'expert_instruction' in initial_data:
            data['expert_instruction'] = bleach.clean(
                initial_data['expert_instruction'], tags=SAFE_HTML_TAGS, attributes=SAFE_HTML_ATTRIBUTES
            )

        return data

    def validate_color(self, value):
        # color : "#FF4C25"
        if value.startswith('#') and len(value) == 7:
            try:
                int(value[1:], 16)
                return value
            except ValueError:
                pass
        raise serializers.ValidationError('Color must be in "#RRGGBB" format')

    class Meta:
        model = Project
        extra_kwargs = {
            'memberships': {'required': False},
            'title': {'required': False},
            'created_by': {'required': False},
        }
        fields = [
            'id',
            'title',
            'description',
            'label_config',
            'expert_instruction',
            'show_instruction',
            'show_skip_button',
            'enable_empty_annotation',
            'show_annotation_history',
            'organization',
            'color',
            'maximum_annotations',
            'is_published',
            'created_by',
            'created_at',
            'created_at',
            'num_tasks_with_annotations',
            'task_number',
            'useful_annotation_number',
            'ground_truth_number',
            'skipped_annotations_number',
            'total_annotations_number',
            'total_predictions_number',
            'sampling',
            'show_ground_truth_first',
            'show_overlap_first',
            'overlap_cohort_percentage',
            'task_data_login',
            'task_data_password',
            'control_weights',
            'parsed_label_config',
            'config_has_control_tags',
            'skip_queue',
            'reveal_preannotations_interactively',
            'pinned_at',
            'finished_task_number',
            'queue_total',
            'queue_done',
            'config_suitable_for_bulk_annotation',
            'state',
            '_annotator_assigned_tasks',
            '_annotator_completed_tasks',
            # Expertise requirements for assignment filtering
            'required_expertise_category',
            'required_expertise_specialization',
            'expertise_required',
        ]

    def validate_label_config(self, value):
        if self.instance is None:
            # No project created yet
            Project.validate_label_config(value)
        else:
            # Existing project is updated
            self.instance.validate_config(value)
        return value

    def get_queue_total(self, project) -> int:
        remain = project.tasks.filter(
            Q(is_labeled=False) & ~Q(annotations__completed_by_id=self.user_id)
            | Q(annotations__completed_by_id=self.user_id)
        ).distinct()
        return remain.count()

    def get_queue_done(self, project) -> int:
        tasks_filter = {
            'project': project,
            'annotations__completed_by_id': self.user_id,
        }

        if project.skip_queue == project.SkipQueue.REQUEUE_FOR_ME:
            tasks_filter['annotations__was_cancelled'] = False

        already_done_tasks = Task.objects.filter(**tasks_filter)
        result = already_done_tasks.distinct().count()

        return result

    def get__annotator_assigned_tasks(self, project) -> int:
        request = self.context.get('request')
        
        logger.info(f"[ANNOTATOR TASKS DEBUG] get__annotator_assigned_tasks called for project {project.id}")
        logger.info(f"[ANNOTATOR TASKS DEBUG] Request exists: {request is not None}")
        logger.info(f"[ANNOTATOR TASKS DEBUG] User authenticated: {request and request.user.is_authenticated}")
        logger.info(f"[ANNOTATOR TASKS DEBUG] User is_annotator: {request and request.user.is_annotator if request else 'N/A'}")
        
        if not request or not request.user.is_authenticated:
            logger.info(f"[ANNOTATOR TASKS DEBUG] Returning 0 - no request or not authenticated")
            return 0
            
        # Import here to avoid circular dependencies
        from annotators.models import TaskAssignment, AnnotatorProfile
        
        # Try to get the annotator profile
        profile = None
        try:
            profile = request.user.annotator_profile
            logger.info(f"[ANNOTATOR TASKS DEBUG] Found existing profile: {profile.id}")
        except AnnotatorProfile.DoesNotExist:
            logger.info(f"[ANNOTATOR TASKS DEBUG] Profile does not exist, is_annotator={request.user.is_annotator}")
            if request.user.is_annotator:
                try:
                    profile, created = AnnotatorProfile.objects.get_or_create(user=request.user)
                    logger.info(f"[ANNOTATOR TASKS DEBUG] Profile {'created' if created else 'retrieved'}: {profile.id}")
                except Exception as e:
                    logger.error(f"[ANNOTATOR TASKS DEBUG] Error creating annotator profile for user {request.user.id}: {e}")
                    return 0
        except Exception as e:
            logger.error(f"[ANNOTATOR TASKS DEBUG] Error accessing annotator profile for user {request.user.id}: {e}")
            return 0
        
        if profile:
            try:
                count = TaskAssignment.objects.filter(
                    annotator=profile,
                    task__project=project,
                    status__in=['assigned', 'in_progress']
                ).count()
                logger.info(f"[ANNOTATOR TASKS DEBUG] Found {count} assigned/in_progress tasks for project {project.id}")
                return count
            except Exception as e:
                logger.error(f"[ANNOTATOR TASKS DEBUG] Error counting assigned tasks for project {project.id}: {e}")
        else:
            logger.info(f"[ANNOTATOR TASKS DEBUG] No profile found, returning 0")
                
        return 0

    def get__annotator_completed_tasks(self, project) -> int:
        request = self.context.get('request')
        
        logger.info(f"[ANNOTATOR COMPLETED DEBUG] get__annotator_completed_tasks called for project {project.id}")
        
        if not request or not request.user.is_authenticated:
            logger.info(f"[ANNOTATOR COMPLETED DEBUG] Returning 0 - no request or not authenticated")
            return 0
            
        # Import here to avoid circular dependencies
        from annotators.models import TaskAssignment, AnnotatorProfile
        
        # Try to get the annotator profile
        profile = None
        try:
            profile = request.user.annotator_profile
            logger.info(f"[ANNOTATOR COMPLETED DEBUG] Found existing profile: {profile.id}")
        except AnnotatorProfile.DoesNotExist:
            logger.info(f"[ANNOTATOR COMPLETED DEBUG] Profile does not exist")
            if request.user.is_annotator:
                try:
                    profile, created = AnnotatorProfile.objects.get_or_create(user=request.user)
                    logger.info(f"[ANNOTATOR COMPLETED DEBUG] Profile {'created' if created else 'retrieved'}: {profile.id}")
                except Exception as e:
                    logger.error(f"[ANNOTATOR COMPLETED DEBUG] Error creating annotator profile for user {request.user.id}: {e}")
                    return 0
        except Exception as e:
            logger.error(f"[ANNOTATOR COMPLETED DEBUG] Error accessing annotator profile for user {request.user.id}: {e}")
            return 0
        
        if profile:
            try:
                count = TaskAssignment.objects.filter(
                    annotator=profile,
                    task__project=project,
                    status='completed'
                ).count()
                logger.info(f"[ANNOTATOR COMPLETED DEBUG] Found {count} completed tasks for project {project.id}")
                return count
            except Exception as e:
                logger.error(f"[ANNOTATOR COMPLETED DEBUG] Error counting completed tasks for project {project.id}: {e}")
        else:
            logger.info(f"[ANNOTATOR COMPLETED DEBUG] No profile found, returning 0")
                
        return 0


class ProjectCountsSerializer(ProjectSerializer):
    class Meta:
        model = Project
        fields = [
            'id',
            'task_number',
            'finished_task_number',
            'total_predictions_number',
            'total_annotations_number',
            'num_tasks_with_annotations',
            'useful_annotation_number',
            'ground_truth_number',
            'ground_truth_number',
            'skipped_annotations_number',
            '_annotator_assigned_tasks',
            '_annotator_completed_tasks',
        ]


class ProjectOnboardingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectOnboarding
        fields = '__all__'


class ProjectLabelConfigSerializer(serializers.Serializer):
    label_config = serializers.CharField(help_text=Project.label_config.field.help_text)

    def validate_label_config(self, config):
        Project.validate_label_config(config)
        return config


class ProjectSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectSummary
        fields = '__all__'


class ProjectImportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectImport
        fields = [
            'id',
            'project',
            'preannotated_from_fields',
            'commit_to_project',
            'return_task_ids',
            'status',
            'url',
            'error',
            'created_at',
            'updated_at',
            'finished_at',
            'task_count',
            'annotation_count',
            'prediction_count',
            'duration',
            'file_upload_ids',
            'could_be_tasks_list',
            'found_formats',
            'data_columns',
            'tasks',
            'task_ids',
        ]


class ProjectReimportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectReimport
        fields = [
            'id',
            'project',
            'status',
            'error',
            'task_count',
            'annotation_count',
            'prediction_count',
            'duration',
            'file_upload_ids',
            'files_as_tasks_list',
            'found_formats',
            'data_columns',
        ]





class GetFieldsSerializer(serializers.Serializer):
    include = serializers.CharField(
        required=False,
        help_text=(
            'Comma-separated list of count fields to include in the response to optimize performance. '
            'Available fields: task_number, finished_task_number, total_predictions_number, '
            'total_annotations_number, num_tasks_with_annotations, useful_annotation_number, '
            'ground_truth_number, skipped_annotations_number. If not specified, all count fields are included.'
        ),
    )
    filter = serializers.CharField(
        required=False,
        default='all',
        help_text=(
            "Filter projects by pinned status. Use 'pinned_only' to return only pinned projects, "
            "'exclude_pinned' to return only non-pinned projects, or 'all' to return all projects."
        ),
    )
    search = serializers.CharField(
        required=False, default=None, help_text='Search term for project title and description'
    )

    def validate_include(self, value):
        if value is not None:
            value = value.split(',')
        return value

    def validate_filter(self, value):
        if value in ['all', 'pinned_only', 'exclude_pinned']:
            return value






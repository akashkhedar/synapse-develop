"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license.
"""
import logging

from core.feature_flags import flag_set
from core.mixins import GetParentObjectMixin
from core.utils.common import load_func
from django.conf import settings
from django.urls import reverse
from django.utils.decorators import method_decorator
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from organizations.models import Organization, OrganizationMember
from organizations.serializers import (
    OrganizationIdSerializer,
    OrganizationInviteSerializer,
    OrganizationMemberListParamsSerializer,
    OrganizationMemberListSerializer,
    OrganizationMemberSerializer,
    OrganizationSerializer,
)
from projects.models import Project
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView
from tasks.models import Annotation
from users.models import User

from synapse.core.permissions import ViewClassPermission, all_permissions
from synapse.core.utils.params import bool_from_request

logger = logging.getLogger(__name__)

HasObjectPermission = load_func(settings.MEMBER_PERM)


@method_decorator(
    name='get',
    decorator=extend_schema(
        tags=['Organizations'],
        summary='List your organizations',
        description="""
        Return a list of the organizations you've created or that you have access to.
        """,
        extensions={
            'x-fern-sdk-group-name': 'organizations',
            'x-fern-sdk-method-name': 'list',
            'x-fern-audiences': ['public'],
        },
    ),
)
class OrganizationListAPI(generics.ListCreateAPIView):
    queryset = Organization.objects.all()
    parser_classes = (JSONParser, FormParser, MultiPartParser)
    permission_required = ViewClassPermission(
        GET=all_permissions.organizations_view,
        PUT=all_permissions.organizations_change,
        POST=all_permissions.organizations_create,
        PATCH=all_permissions.organizations_change,
        DELETE=all_permissions.organizations_change,
    )
    serializer_class = OrganizationIdSerializer

    def filter_queryset(self, queryset):
        return queryset.filter(
            organizationmember__in=self.request.user.om_through.filter(deleted_at__isnull=True)
        ).distinct()

    def get(self, request, *args, **kwargs):
        return super(OrganizationListAPI, self).get(request, *args, **kwargs)

    @extend_schema(exclude=True)
    def post(self, request, *args, **kwargs):
        """Create a new organization with the current user as the creator and member."""
        title = request.data.get('title', 'New Organization')
        org = Organization.create_organization(created_by=request.user, title=title)
        
        # Set the new organization as active for this user
        request.user.active_organization = org
        request.user.save()
        
        serializer = self.get_serializer(org)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrganizationMemberListPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'

    def get_page_size(self, request):
        # emulate "unlimited" page_size
        if (
            self.page_size_query_param in request.query_params
            and request.query_params[self.page_size_query_param] == '-1'
        ):
            return 1000000
        return super().get_page_size(request)


@method_decorator(
    name='get',
    decorator=extend_schema(
        tags=['Organizations'],
        summary='Get organization members list',
        description='Retrieve a list of the organization members and their IDs.',
        extensions={
            'x-fern-sdk-group-name': ['organizations', 'members'],
            'x-fern-sdk-method-name': 'list',
            'x-fern-audiences': ['public'],
            'x-fern-pagination': {
                'offset': '$request.page',
                'results': '$response.results',
            },
        },
    ),
)
class OrganizationMemberListAPI(generics.ListAPIView):
    parser_classes = (JSONParser, FormParser, MultiPartParser)
    permission_required = ViewClassPermission(
        GET=all_permissions.organizations_view,
        PUT=all_permissions.organizations_change,
        PATCH=all_permissions.organizations_change,
        DELETE=all_permissions.organizations_change,
    )
    serializer_class = OrganizationMemberListSerializer
    pagination_class = OrganizationMemberListPagination

    def _get_created_projects_map(self):
        members = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
        user_ids = [member.user_id for member in members]
        projects = (
            Project.objects.filter(created_by_id__in=user_ids, organization=self.request.user.active_organization)
            .values('created_by_id', 'id', 'title')
            .distinct()
        )
        projects_map = {}
        for project in projects:
            projects_map.setdefault(project['created_by_id'], []).append(
                {
                    'id': project['id'],
                    'title': project['title'],
                }
            )
        return projects_map

    def _get_contributed_to_projects_map(self):
        members = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
        user_ids = [member.user_id for member in members]
        org_project_ids = Project.objects.filter(organization=self.request.user.active_organization).values_list(
            'id', flat=True
        )
        annotations = (
            Annotation.objects.filter(completed_by__in=list(user_ids), project__in=list(org_project_ids))
            .values('completed_by', 'project_id')
            .distinct()
        )
        project_ids = [annotation['project_id'] for annotation in annotations]
        projects_map = Project.objects.in_bulk(id_list=project_ids, field_name='id')

        contributed_to_projects_map = {}
        for annotation in annotations:
            project = projects_map[annotation['project_id']]
            contributed_to_projects_map.setdefault(annotation['completed_by'], []).append(
                {
                    'id': project.id,
                    'title': project.title,
                }
            )
        return contributed_to_projects_map

    def get_serializer_context(self):
        context = super().get_serializer_context()
        contributed_to_projects = bool_from_request(self.request.GET, 'contributed_to_projects', False)
        return {
            'contributed_to_projects': contributed_to_projects,
            'created_projects_map': self._get_created_projects_map() if contributed_to_projects else None,
            'contributed_to_projects_map': self._get_contributed_to_projects_map()
            if contributed_to_projects
            else None,
            **context,
        }

    def get_queryset(self):
        org = generics.get_object_or_404(self.request.user.organizations, pk=self.kwargs[self.lookup_field])
        if flag_set('fix_backend_dev_3134_exclude_deactivated_users', self.request.user):
            serializer = OrganizationMemberListParamsSerializer(data=self.request.GET)
            serializer.is_valid(raise_exception=True)
            active = serializer.validated_data.get('active')

            # return only active users (exclude DISABLED and NOT_ACTIVATED)
            if active:
                return org.active_members.prefetch_related('user__om_through').order_by('user__username')

            # organization page to show all members
            return org.members.prefetch_related('user__om_through').order_by('user__username')
        else:
            return org.members.prefetch_related('user__om_through').order_by('user__username')


@method_decorator(
    name='get',
    decorator=extend_schema(
        tags=['Organizations'],
        summary='Get organization member details',
        description='Get organization member details by user ID.',
        parameters=[
            OpenApiParameter(
                name='user_pk',
                type=OpenApiTypes.INT,
                location='path',
                description='A unique integer value identifying the user to get organization details for.',
            ),
        ],
        responses={200: OrganizationMemberSerializer()},
        extensions={
            'x-fern-sdk-group-name': ['organizations', 'members'],
            'x-fern-sdk-method-name': 'get',
            'x-fern-audiences': ['public'],
        },
    ),
)
@method_decorator(
    name='delete',
    decorator=extend_schema(
        tags=['Organizations'],
        summary='Soft delete an organization member',
        description='Soft delete a member from the organization.',
        parameters=[
            OpenApiParameter(
                name='user_pk',
                type=OpenApiTypes.INT,
                location='path',
                description='A unique integer value identifying the user to be deleted from the organization.',
            ),
        ],
        responses={
            204: OpenApiResponse(description='Member deleted successfully.'),
            405: OpenApiResponse(description='User cannot soft delete self.'),
            404: OpenApiResponse(description='Member not found'),
            403: OpenApiResponse(description='You can delete members only for your current active organization'),
        },
        extensions={
            'x-fern-sdk-group-name': ['organizations', 'members'],
            'x-fern-sdk-method-name': 'delete',
            'x-fern-audiences': ['public'],
        },
    ),
)
class OrganizationMemberDetailAPI(GetParentObjectMixin, generics.RetrieveDestroyAPIView):
    permission_required = ViewClassPermission(
        GET=all_permissions.organizations_view,
        DELETE=all_permissions.organizations_change,
    )
    parent_queryset = Organization.objects.all()
    parser_classes = (JSONParser, FormParser, MultiPartParser)
    serializer_class = OrganizationMemberSerializer
    http_method_names = ['delete', 'get']

    @property
    def permission_classes(self):
        if self.request.method == 'DELETE':
            return [IsAuthenticated, HasObjectPermission]
        return api_settings.DEFAULT_PERMISSION_CLASSES

    def get_queryset(self):
        return OrganizationMember.objects.filter(organization=self.parent_object, deleted_at__isnull=True)

    def get_serializer_context(self):
        return {
            **super().get_serializer_context(),
            'organization': self.parent_object,
        }

    def get(self, request, pk, user_pk):
        queryset = self.get_queryset()
        user = get_object_or_404(User, pk=user_pk)
        member = get_object_or_404(queryset, user=user)
        self.check_object_permissions(request, member)
        serializer = self.get_serializer(member)
        return Response(serializer.data)

    def delete(self, request, pk=None, user_pk=None):
        org = self.parent_object
        if org != request.user.active_organization:
            raise PermissionDenied('You can delete members only for your current active organization')

        user = get_object_or_404(User, pk=user_pk)
        member = get_object_or_404(OrganizationMember, user=user, organization=org)
        if member.deleted_at is not None:
            raise NotFound('Member not found')

        if member.user_id == request.user.id:
            return Response({'detail': 'User cannot soft delete self'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

        # Check if requester has permission to remove members
        requester_member = get_object_or_404(OrganizationMember, user=request.user, organization=org, deleted_at__isnull=True)
        
        # Only owner and admins can remove members
        if not requester_member.can_manage_members():
            raise PermissionDenied('Only owners and admins can remove members')
        
        # Cannot remove the owner
        if member.is_owner:
            raise PermissionDenied('Cannot remove the organization owner')

        member.soft_delete()
        return Response(status=204)  # 204 No Content is a common HTTP status for successful delete requests


@extend_schema(
    tags=['Organizations'],
    summary='Promote member to admin',
    description='Promote a regular member to admin role. Only the organization owner can promote members.',
    request=None,
    responses={
        200: OpenApiResponse(description='Member promoted successfully'),
        403: OpenApiResponse(description='Only owner can promote members'),
        404: OpenApiResponse(description='Member not found'),
        400: OpenApiResponse(description='Cannot promote owner or already an admin'),
    },
    extensions={
        'x-fern-sdk-group-name': ['organizations', 'members'],
        'x-fern-sdk-method-name': 'promote',
        'x-fern-audiences': ['public'],
    },
)
class OrganizationMemberPromoteAPI(GetParentObjectMixin, APIView):
    permission_required = ViewClassPermission(
        POST=all_permissions.organizations_change,
    )
    parent_queryset = Organization.objects.all()
    permission_classes = [IsAuthenticated, HasObjectPermission]

    def post(self, request, pk, user_pk):
        org = get_object_or_404(Organization, pk=pk)
        if org != request.user.active_organization:
            raise PermissionDenied('You can only manage members in your current active organization')

        # Get the member to promote
        user = get_object_or_404(User, pk=user_pk)
        member = get_object_or_404(OrganizationMember, user=user, organization=org, deleted_at__isnull=True)

        # Check if requester is the owner
        requester_member = get_object_or_404(OrganizationMember, user=request.user, organization=org, deleted_at__isnull=True)
        if not requester_member.is_owner:
            raise PermissionDenied('Only the organization owner can promote members to admin')

        # Cannot promote owner or already admin
        if member.is_owner:
            return Response({'error': 'Cannot promote owner'}, status=status.HTTP_400_BAD_REQUEST)
        if member.is_admin:
            return Response({'error': 'User is already an admin'}, status=status.HTTP_400_BAD_REQUEST)

        # Promote to admin
        member.role = OrganizationMember.ROLE_ADMIN
        member.save(update_fields=['role'])

        # Send email notification
        from organizations.email_notifications import send_admin_promotion_email
        send_admin_promotion_email(user, org, request.user)

        from .serializers import OrganizationMemberSerializer
        serializer = OrganizationMemberSerializer(member, context={'organization': org})
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Organizations'],
    summary='Demote admin to member',
    description='Demote an admin back to regular member role. Only the organization owner can demote admins.',
    request=None,
    responses={
        200: OpenApiResponse(description='Admin demoted successfully'),
        403: OpenApiResponse(description='Only owner can demote admins'),
        404: OpenApiResponse(description='Member not found'),
        400: OpenApiResponse(description='Cannot demote owner or not an admin'),
    },
    extensions={
        'x-fern-sdk-group-name': ['organizations', 'members'],
        'x-fern-sdk-method-name': 'demote',
        'x-fern-audiences': ['public'],
    },
)
class OrganizationMemberDemoteAPI(GetParentObjectMixin, APIView):
    permission_required = ViewClassPermission(
        POST=all_permissions.organizations_change,
    )
    parent_queryset = Organization.objects.all()
    permission_classes = [IsAuthenticated, HasObjectPermission]

    def post(self, request, pk, user_pk):
        org = get_object_or_404(Organization, pk=pk)
        if org != request.user.active_organization:
            raise PermissionDenied('You can only manage members in your current active organization')

        # Get the member to demote
        user = get_object_or_404(User, pk=user_pk)
        member = get_object_or_404(OrganizationMember, user=user, organization=org, deleted_at__isnull=True)

        # Check if requester is the owner
        requester_member = get_object_or_404(OrganizationMember, user=request.user, organization=org, deleted_at__isnull=True)
        if not requester_member.is_owner:
            raise PermissionDenied('Only the organization owner can demote admins')

        # Cannot demote owner or non-admin
        if member.is_owner:
            return Response({'error': 'Cannot demote owner'}, status=status.HTTP_400_BAD_REQUEST)
        if not member.is_admin:
            return Response({'error': 'User is not an admin'}, status=status.HTTP_400_BAD_REQUEST)

        # Demote to member
        member.role = OrganizationMember.ROLE_MEMBER
        member.save(update_fields=['role'])

        from .serializers import OrganizationMemberSerializer
        serializer = OrganizationMemberSerializer(member, context={'organization': org})
        return Response(serializer.data, status=status.HTTP_200_OK)


@method_decorator(
    name='get',
    decorator=extend_schema(
        tags=['Organizations'],
        summary='Get organization settings',
        description='Retrieve the settings for a specific organization by ID.',
        extensions={
            'x-fern-sdk-group-name': 'organizations',
            'x-fern-sdk-method-name': 'get',
            'x-fern-audiences': ['public'],
        },
    ),
)
@method_decorator(
    name='patch',
    decorator=extend_schema(
        tags=['Organizations'],
        summary='Update organization settings',
        description='Update the settings for a specific organization by ID.',
        extensions={
            'x-fern-sdk-group-name': 'organizations',
            'x-fern-sdk-method-name': 'update',
            'x-fern-audiences': ['public'],
        },
    ),
)
class OrganizationAPI(generics.RetrieveUpdateAPIView):

    parser_classes = (JSONParser, FormParser, MultiPartParser)
    queryset = Organization.objects.all()
    permission_required = all_permissions.organizations_change
    serializer_class = OrganizationSerializer

    redirect_route = 'organizations-dashboard'
    redirect_kwarg = 'pk'

    def get(self, request, *args, **kwargs):
        return super(OrganizationAPI, self).get(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return super(OrganizationAPI, self).patch(request, *args, **kwargs)

    @extend_schema(exclude=True)
    def put(self, request, *args, **kwargs):
        return super(OrganizationAPI, self).put(request, *args, **kwargs)


@method_decorator(
    name='get',
    decorator=extend_schema(
        tags=['Invites'],
        summary='Get organization invite link',
        description='Get a link to use to invite a new member to an organization in Synapse Enterprise.',
        responses={200: OrganizationInviteSerializer()},
        extensions={
            'x-fern-sdk-group-name': 'organizations',
            'x-fern-sdk-method-name': 'get_invite',
            'x-fern-audiences': ['public'],
        },
    ),
)
class OrganizationInviteAPI(generics.RetrieveAPIView):
    parser_classes = (JSONParser,)
    queryset = Organization.objects.all()
    permission_required = all_permissions.organizations_invite

    def get(self, request, *args, **kwargs):
        org = request.user.active_organization
        invite_url = '/invite?token={}'.format(org.token)
        if hasattr(settings, 'FORCE_SCRIPT_NAME') and settings.FORCE_SCRIPT_NAME:
            invite_url = invite_url.replace(settings.FORCE_SCRIPT_NAME, '', 1)
        serializer = OrganizationInviteSerializer(data={'invite_url': invite_url, 'token': org.token})
        serializer.is_valid()
        return Response(serializer.data, status=200)


@method_decorator(
    name='post',
    decorator=extend_schema(
        tags=['Invites'],
        summary='Reset organization token',
        description='Reset the token used in the invitation link to invite someone to an organization.',
        responses={200: OrganizationInviteSerializer()},
        extensions={
            'x-fern-sdk-group-name': 'organizations',
            'x-fern-sdk-method-name': 'reset_token',
            'x-fern-audiences': ['public'],
        },
    ),
)
class OrganizationResetTokenAPI(APIView):
    permission_required = all_permissions.organizations_invite
    parser_classes = (JSONParser,)

    def post(self, request, *args, **kwargs):
        org = request.user.active_organization
        org.reset_token()
        logger.debug(f'New token for organization {org.pk} is {org.token}')
        invite_url = '/invite?token={}'.format(org.token)
        serializer = OrganizationInviteSerializer(data={'invite_url': invite_url, 'token': org.token})
        serializer.is_valid()
        return Response(serializer.data, status=201)


@method_decorator(
    name='post',
    decorator=extend_schema(
        tags=['Invites'],
        summary='Accept organization invite',
        description='Accept an invitation to join an organization using an invite token.',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'token': {
                        'type': 'string',
                        'description': 'Invite token from the invitation link'
                    }
                },
                'required': ['token']
            }
        },
        responses={
            200: OrganizationSerializer(),
            400: OpenApiResponse(description='Invalid or expired token'),
            404: OpenApiResponse(description='Organization not found'),
        },
        extensions={
            'x-fern-sdk-group-name': 'organizations',
            'x-fern-sdk-method-name': 'accept_invite',
            'x-fern-audiences': ['public'],
        },
    ),
)
class OrganizationAcceptInviteAPI(APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (JSONParser,)

    def post(self, request, *args, **kwargs):
        token = request.data.get('token')
        if not token:
            return Response({'error': 'Token is required'}, status=400)
        
        # Find organization by token
        try:
            organization = Organization.objects.get(token=token)
        except Organization.DoesNotExist:
            return Response({'error': 'Invalid invite token'}, status=404)
        
        # Check if user is already an active member (excluding soft-deleted)
        existing_member = OrganizationMember.objects.filter(
            organization=organization, 
            user=request.user
        ).first()
        
        if existing_member and existing_member.deleted_at is None:
            # Already an active member, just switch to this organization
            request.user.active_organization = organization
            request.user.save(update_fields=['active_organization'])
            serializer = OrganizationSerializer(organization)
            return Response(serializer.data, status=200)
        
        # Add user to organization (will restore if soft-deleted)
        organization.add_user(request.user)
        
        # Switch to the new organization
        request.user.active_organization = organization
        request.user.save(update_fields=['active_organization'])
        
        logger.info(f'User {request.user.email} joined organization {organization.title} via invite')
        
        serializer = OrganizationSerializer(organization)
        return Response(serializer.data, status=200)


@method_decorator(
    name='post',
    decorator=extend_schema(
        tags=['Organizations'],
        summary='Send organization invite via email',
        description='Send an email invitation to join the organization. The recipient will receive an email with a link to join.',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'email': {
                        'type': 'string',
                        'format': 'email',
                        'description': 'Email address to send the invitation to'
                    }
                },
                'required': ['email']
            }
        },
        responses={
            200: OpenApiResponse(description='Invitation email sent successfully'),
            400: OpenApiResponse(description='Invalid email or organization'),
            403: OpenApiResponse(description='User does not have permission to invite members'),
        },
    )
)
class OrganizationInviteViaEmailAPI(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk=None):
        """Send an invitation email to join the organization"""
        from organizations.email_notifications import send_organization_invite_email
        
        # Get the organization
        org = get_object_or_404(Organization, pk=pk)
        
        # Check if user is a member of this organization and can manage members
        try:
            member = OrganizationMember.objects.get(organization=org, user=request.user, deleted_at__isnull=True)
            if not member.can_manage_members():
                return Response(
                    {'error': 'You do not have permission to invite members to this organization'},
                    status=403
                )
        except OrganizationMember.DoesNotExist:
            return Response(
                {'error': 'You are not a member of this organization'},
                status=403
            )
        
        # Get email from request
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email address is required'}, status=400)
        
        # Validate email format
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        try:
            validate_email(email)
        except ValidationError:
            return Response({'error': 'Invalid email address'}, status=400)
        
        # Generate invite URL
        invite_url = request.build_absolute_uri(f'/user/signup/?token={org.token}')
        
        # Send the email
        success = send_organization_invite_email(
            email=email,
            organization=org,
            inviter=request.user,
            invite_url=invite_url,
            request=request
        )
        
        if success:
            logger.info(f'Invitation email sent to {email} for organization {org.title} by {request.user.email}')
            return Response({
                'success': True,
                'message': f'Invitation sent to {email}'
            }, status=200)
        else:
            return Response({
                'success': False,
                'error': 'Failed to send email. Please check your email configuration.'
            }, status=500)


@method_decorator(
    name='post',
    decorator=extend_schema(
        tags=['Organizations'],
        summary='Leave organization',
        description='Leave the current active organization. User must have at least one other organization to switch to.',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'organization_id': {
                        'type': 'integer',
                        'description': 'ID of the organization to leave'
                    }
                },
                'required': ['organization_id']
            }
        },
        responses={
            200: OpenApiResponse(description='Successfully left organization'),
            400: OpenApiResponse(description='Cannot leave - user must belong to at least one organization'),
            403: OpenApiResponse(description='Cannot leave - user is the creator or only member'),
            404: OpenApiResponse(description='Organization not found'),
        },
        extensions={
            'x-fern-sdk-group-name': 'organizations',
            'x-fern-sdk-method-name': 'leave',
            'x-fern-audiences': ['public'],
        },
    ),
)
class OrganizationLeaveAPI(APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (JSONParser,)

    def post(self, request, *args, **kwargs):
        org_id = request.data.get('organization_id')
        if not org_id:
            return Response({'error': 'Organization ID is required'}, status=400)
        
        try:
            organization = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return Response({'error': 'Organization not found'}, status=404)
        
        # Check if user is the creator - creators cannot leave their own organization
        if organization.created_by == request.user:
            return Response({
                'error': 'You cannot leave an organization you created. Transfer ownership or delete the organization instead.'
            }, status=403)
        
        # Check if user is a member of this organization
        try:
            member = OrganizationMember.objects.get(organization=organization, user=request.user, deleted_at__isnull=True)
        except OrganizationMember.DoesNotExist:
            return Response({'error': 'You are not a member of this organization'}, status=404)
        
        # Get user's other organizations
        other_orgs = Organization.objects.filter(
            organizationmember__user=request.user,
            organizationmember__deleted_at__isnull=True
        ).exclude(id=org_id)
        
        if not other_orgs.exists():
            return Response({
                'error': 'You must belong to at least one organization. Create a new organization before leaving this one.'
            }, status=400)
        
        # Remove user from the organization
        member.soft_delete()
        
        # If this was the user's active organization, switch to another one
        if request.user.active_organization == organization:
            new_active_org = other_orgs.first()
            request.user.active_organization = new_active_org
            request.user.save(update_fields=['active_organization'])
            
            logger.info(f'User {request.user.email} left organization {organization.title} and switched to {new_active_org.title}')
        else:
            logger.info(f'User {request.user.email} left organization {organization.title}')
        
        return Response({
            'message': 'Successfully left organization',
            'switched_to': request.user.active_organization.id if request.user.active_organization else None
        }, status=200)


@method_decorator(
    name='post',
    decorator=extend_schema(
        tags=['Organizations'],
        summary='Switch active organization',
        description='Switch the user\'s active organization to access different projects and data.',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'organization_id': {
                        'type': 'integer',
                        'description': 'ID of the organization to switch to'
                    }
                },
                'required': ['organization_id']
            }
        },
        responses={
            200: OrganizationSerializer(),
            403: OpenApiResponse(description='User is not a member of this organization'),
            404: OpenApiResponse(description='Organization not found'),
        },
        extensions={
            'x-fern-sdk-group-name': 'organizations',
            'x-fern-sdk-method-name': 'switch',
            'x-fern-audiences': ['public'],
        },
    ),
)
class OrganizationSwitchAPI(APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (JSONParser,)

    def post(self, request, *args, **kwargs):
        organization_id = request.data.get('organization_id')
        
        if not organization_id:
            return Response(
                {'error': 'organization_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            organization = Organization.objects.get(pk=organization_id)
        except Organization.DoesNotExist:
            return Response(
                {'error': 'Organization not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user is a member of this organization
        if not organization.has_user(request.user):
            return Response(
                {'error': 'You are not a member of this organization'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Switch active organization
        request.user.active_organization = organization
        request.user.save(update_fields=['active_organization'])
        
        logger.info(f'User {request.user.email} switched to organization {organization.id}')
        
        serializer = OrganizationSerializer(organization)
        return Response(serializer.data, status=status.HTTP_200_OK)






"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license.
"""
from django.urls import include, path
from organizations import api, views

app_name = 'organizations'

# TODO: there should be only one patterns list based on API (with api/ prefix removed)
# Page URLs
_urlpatterns = [
    # get organization page
    path('', views.organization_people_list, name='organization-index'),
]

# API URLs
_api_urlpattens = [
    # organization list viewset
    path('', api.OrganizationListAPI.as_view(), name='organization-list'),
    # organization detail viewset
    path('<int:pk>/', api.OrganizationAPI.as_view(), name='organization-detail'),
    path('<int:pk>', api.OrganizationAPI.as_view(), name='organization-detail-no-slash'),
    # organization memberships list viewset (with and without trailing slash)
    path('<int:pk>/memberships/', api.OrganizationMemberListAPI.as_view(), name='organization-memberships-list'),
    path('<int:pk>/memberships', api.OrganizationMemberListAPI.as_view(), name='organization-memberships-list-no-slash'),
    path(
        '<int:pk>/memberships/<int:user_pk>/',
        api.OrganizationMemberDetailAPI.as_view(),
        name='organization-membership-detail',
    ),
    # promote/demote member
    path(
        '<int:pk>/memberships/<int:user_pk>/promote',
        api.OrganizationMemberPromoteAPI.as_view(),
        name='organization-membership-promote',
    ),
    path(
        '<int:pk>/memberships/<int:user_pk>/demote',
        api.OrganizationMemberDemoteAPI.as_view(),
        name='organization-membership-demote',
    ),
]
# TODO: these urlpatterns should be moved in core/urls with include('organizations.urls')
urlpatterns = [
    path('organization/', views.simple_view, name='organization-simple'),
    path('organization/<int:org_pk>/', views.organization_people_list, name='organization-detail'),
    path('organization/webhooks', views.simple_view, name='organization-simple-webhooks'),
    path('people/', include(_urlpatterns)),
    # TODO: temporary route, remove as needed
    path('models/', views.simple_view, name='models'),
    path('api/organizations/', include((_api_urlpattens, app_name), namespace='api')),
    # invite
    path('api/invite', api.OrganizationInviteAPI.as_view(), name='organization-invite'),
    path('api/invite/reset-token', api.OrganizationResetTokenAPI.as_view(), name='organization-reset-token'),
    path('api/invite/accept', api.OrganizationAcceptInviteAPI.as_view(), name='organization-accept-invite'),
    # invite via email
    path('api/organizations/<int:pk>/invite/email', api.OrganizationInviteViaEmailAPI.as_view(), name='organization-invite-email'),
    # switch organization
    path('api/organizations/switch', api.OrganizationSwitchAPI.as_view(), name='organization-switch'),
    # leave organization
    path('api/organizations/leave', api.OrganizationLeaveAPI.as_view(), name='organization-leave'),
]






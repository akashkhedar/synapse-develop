from django.urls import path

from . import views

app_name = 'jwt_auth'

urlpatterns = [
    path('api/jwt/settings', views.JWTSettingsAPI.as_view(), name='api-jwt-settings'),
    path('api/token/', views.LSAPITokenView.as_view(), name='token_manage'),
    path('api/token/refresh/', views.DecoratedTokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/blacklist/', views.LSTokenBlacklistView.as_view(), name='token_blacklist'),
    path('api/token/rotate/', views.LSAPITokenRotateView.as_view(), name='token_rotate'),
    
    # API Key management endpoints
    path('api/api-keys/', views.APIKeyListCreateView.as_view(), name='api-key-list-create'),
    path('api/api-keys/<int:id>/', views.APIKeyDetailView.as_view(), name='api-key-detail'),
    path('api/api-keys/<int:id>/regenerate/', views.APIKeyRegenerateView.as_view(), name='api-key-regenerate'),
]






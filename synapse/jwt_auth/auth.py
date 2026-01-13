import logging

from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import TokenAuthentication, BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)


class APIKeyAuthentication(BaseAuthentication):
    """
    API Key authentication for SDK/programmatic access.
    
    Supports both header-based and query parameter authentication:
    - Header: X-API-KEY: syn_xxxxx or Authorization: ApiKey syn_xxxxx
    - Query: ?api_key=syn_xxxxx
    """
    
    keyword = 'ApiKey'
    header_name = 'HTTP_X_API_KEY'
    auth_header = 'HTTP_AUTHORIZATION'
    
    def authenticate(self, request):
        """Authenticate using API key."""
        from core.current_request import CurrentContext
        from jwt_auth.models import APIKey
        
        api_key = self._get_api_key(request)
        if not api_key:
            return None
        
        try:
            key_obj = APIKey.objects.select_related('user', 'organization').get(key=api_key)
        except APIKey.DoesNotExist:
            raise AuthenticationFailed('Invalid API key')
        
        if not key_obj.is_valid():
            if not key_obj.is_active:
                raise AuthenticationFailed('API key has been deactivated')
            raise AuthenticationFailed('API key has expired')
        
        # Update last used timestamp (non-blocking)
        try:
            key_obj.update_last_used()
        except Exception:
            pass  # Don't fail auth if we can't update timestamp
        
        user = key_obj.user
        
        # Update CurrentContext with authenticated user
        CurrentContext.set_user(user)
        
        logger.info(
            'API key authentication used',
            extra={
                'user_id': user.id,
                'api_key_id': key_obj.id,
                'api_key_name': key_obj.name,
                'endpoint': request.path,
            },
        )
        
        return (user, key_obj)
    
    def _get_api_key(self, request):
        """Extract API key from request headers or query params."""
        # Check X-API-KEY header first
        api_key = request.META.get(self.header_name)
        if api_key:
            return api_key
        
        # Check Authorization header with ApiKey prefix
        auth_header = request.META.get(self.auth_header, '')
        if auth_header.startswith(f'{self.keyword} '):
            return auth_header[len(self.keyword) + 1:].strip()
        
        # Check query parameter (for convenience, though less secure)
        api_key = request.GET.get('api_key')
        if api_key:
            return api_key
        
        return None
    
    def authenticate_header(self, request):
        """Return a string to be used in WWW-Authenticate header."""
        return self.keyword


class APIKeyAuthScheme(OpenApiAuthenticationExtension):
    """OpenAPI schema extension for API Key authentication."""
    
    target_class = 'jwt_auth.auth.APIKeyAuthentication'
    name = 'ApiKey'
    
    def get_security_definition(self, auto_schema):
        return {
            'type': 'apiKey',
            'name': 'X-API-KEY',
            'in': 'header',
            'description': 'API key for SDK/programmatic access. '
            'Create and manage API keys in Account Settings. Example: '
            '<br><pre><code class="language-bash">'
            'curl https://synapse-host/api/projects -H "X-API-KEY: syn_xxxxx"'
            '</code></pre>'
            '<br>Or use the Authorization header with ApiKey prefix:'
            '<br><pre><code class="language-bash">'
            'curl https://synapse-host/api/projects -H "Authorization: ApiKey syn_xxxxx"'
            '</code></pre>',
            'x-fern-header': {
                'name': 'api_key',
                'env': 'SYNAPSE_API_KEY',
            },
        }


class TokenAuthenticationPhaseout(TokenAuthentication):
    """TokenAuthentication with features to help phase out legacy token auth

    Logs usage and triggers a 401 if legacy token auth is not enabled for the organization."""

    def authenticate(self, request):
        """Authenticate the request and log if successful."""
        from core.current_request import CurrentContext
        from core.feature_flags import flag_set

        auth_result = super().authenticate(request)

        # Update CurrentContext with authenticated user
        if auth_result is not None:
            user, _ = auth_result
            CurrentContext.set_user(user)

        JWT_ACCESS_TOKEN_ENABLED = flag_set('fflag__feature_develop__prompts__dia_1829_jwt_token_auth')
        if JWT_ACCESS_TOKEN_ENABLED and (auth_result is not None):
            user, _ = auth_result
            org = user.active_organization
            org_id = org.id if org else None

            # raise 401 if legacy API token auth disabled (i.e. this token is no longer valid)
            if org and (not org.jwt.legacy_api_tokens_enabled):
                raise AuthenticationFailed(
                    'Authentication token no longer valid: legacy token authentication has been disabled for this organization'
                )

            logger.info(
                'Legacy token authentication used',
                extra={'user_id': user.id, 'organization_id': org_id, 'endpoint': request.path},
            )
        return auth_result


class JWTAuthScheme(OpenApiAuthenticationExtension):
    target_class = 'jwt_auth.auth.TokenAuthenticationPhaseout'
    name = 'Token'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'The token (or API key) must be passed as a request header. '
            'You can find your user token on the User Account page in Synapse. Example: '
            '<br><pre><code class="language-bash">'
            'curl https://synapse-host/api/projects -H "Authorization: Token [your-token]"'
            '</code></pre>',
            'x-fern-header': {
                'name': 'api_key',
                'env': 'SYNAPSE_API_KEY',
                'prefix': 'Token ',
            },
        }







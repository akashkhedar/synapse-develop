from jwt_auth.models import JWTSettings, LSAPIToken, TruncatedLSAPIToken, APIKey
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenBlacklistSerializer
from rest_framework_simplejwt.tokens import RefreshToken


# Recommended implementation from JWT to support auto API documentation
class TokenRefreshResponseSerializer(serializers.Serializer):
    access = serializers.CharField()


class JWTSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = JWTSettings
        fields = ('api_tokens_enabled', 'legacy_api_tokens_enabled')


class LSAPITokenCreateSerializer(serializers.Serializer):
    token = serializers.SerializerMethodField()

    def get_token(self, obj):
        return obj.get_full_jwt()

    class Meta:
        model = LSAPIToken
        fields = ['token']


class LSAPITokenListSerializer(LSAPITokenCreateSerializer):
    def get_token(self, obj):
        # only return header/payload portion of token, using LSTokenBackend
        return str(obj)


class LSAPITokenBlacklistSerializer(TokenBlacklistSerializer):
    token_class = TruncatedLSAPIToken


class LSAPITokenRotateSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, data):
        refresh = data.get('refresh')
        try:
            token = RefreshToken(refresh)
        except Exception:
            raise serializers.ValidationError('Invalid refresh token')
        data['refresh'] = token
        return data


class TokenRotateResponseSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class APIKeyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new API keys."""
    
    key = serializers.CharField(read_only=True)
    key_prefix = serializers.CharField(read_only=True)
    
    class Meta:
        model = APIKey
        fields = ['id', 'name', 'description', 'key', 'key_prefix', 'expires_at', 'created_at']
        read_only_fields = ['id', 'key', 'key_prefix', 'created_at']
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user:
            validated_data['user'] = request.user
            validated_data['organization'] = request.user.active_organization
        return super().create(validated_data)


class APIKeyListSerializer(serializers.ModelSerializer):
    """Serializer for listing API keys (hides full key value)."""
    
    class Meta:
        model = APIKey
        fields = [
            'id', 'name', 'description', 'key_prefix', 'is_active',
            'last_used_at', 'expires_at', 'created_at', 'updated_at'
        ]
        read_only_fields = fields


class APIKeyDetailSerializer(serializers.ModelSerializer):
    """Serializer for API key details including the full key (used only on creation)."""
    
    class Meta:
        model = APIKey
        fields = [
            'id', 'name', 'description', 'key', 'key_prefix', 'is_active',
            'last_used_at', 'expires_at', 'created_at', 'updated_at'
        ]
        read_only_fields = fields


class APIKeyUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating API key metadata."""
    
    class Meta:
        model = APIKey
        fields = ['id', 'name', 'description', 'is_active']
        read_only_fields = ['id']


class APIKeyRegenerateSerializer(serializers.Serializer):
    """Serializer for regenerating an API key."""
    
    key = serializers.CharField(read_only=True)
    key_prefix = serializers.CharField(read_only=True)






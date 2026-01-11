import os
from django.apps import AppConfig


class JWTAuthConfig(AppConfig):
    name = 'jwt_auth'
    path = os.path.dirname(os.path.abspath(__file__))






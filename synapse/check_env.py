#!/usr/bin/env python
"""Check if .env is loaded correctly"""
import os
import sys
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path, override=True)
        print(f"✓ Loaded environment from {env_path}\n")
    else:
        print(f"✗ .env file not found at {env_path}\n")
        sys.exit(1)
except ImportError:
    print("✗ python-dotenv not installed\n")
    sys.exit(1)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.synapse')

# Now check Django settings
import django
django.setup()

from django.conf import settings

print("="*80)
print("DJANGO EMAIL SETTINGS")
print("="*80 + "\n")

print(f"EMAIL_BACKEND:       {settings.EMAIL_BACKEND}")
print(f"DEFAULT_FROM_EMAIL:  {settings.DEFAULT_FROM_EMAIL}")
print(f"EMAIL_HOST:          {settings.EMAIL_HOST}")
print(f"EMAIL_PORT:          {settings.EMAIL_PORT}")
print(f"EMAIL_USE_TLS:       {settings.EMAIL_USE_TLS}")
print(f"EMAIL_HOST_USER:     {settings.EMAIL_HOST_USER}")
print(f"EMAIL_HOST_PASSWORD: {'*' * len(settings.EMAIL_HOST_PASSWORD) if settings.EMAIL_HOST_PASSWORD else '(not set)'}")

print("\n" + "="*80)
print("ENVIRONMENT VARIABLES (from os.environ)")
print("="*80 + "\n")

print(f"EMAIL_BACKEND:       {os.environ.get('EMAIL_BACKEND', '(not set)')}")
print(f"DEFAULT_FROM_EMAIL:  {os.environ.get('DEFAULT_FROM_EMAIL', '(not set)')}")
print(f"EMAIL_HOST:          {os.environ.get('EMAIL_HOST', '(not set)')}")
print(f"EMAIL_HOST_USER:     {os.environ.get('EMAIL_HOST_USER', '(not set)')}")
print(f"EMAIL_HOST_PASSWORD: {'*' * len(os.environ.get('EMAIL_HOST_PASSWORD', '')) if os.environ.get('EMAIL_HOST_PASSWORD') else '(not set)'}")
print()

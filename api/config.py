"""API configuration"""
import os

API_HOST = os.environ.get('API_HOST', '127.0.0.1')
API_PORT = int(os.environ.get('API_PORT', '8000'))
DEBUG = os.environ.get('DEBUG', 'true').lower() == 'true'

CORS_ORIGINS = [
    'http://localhost:8501',
    'http://127.0.0.1:8501',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

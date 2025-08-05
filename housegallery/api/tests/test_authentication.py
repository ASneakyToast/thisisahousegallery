from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from housegallery.api.models import APIKey
from housegallery.artists.models import Artist


class APIKeyAuthenticationTest(TestCase):
    """Test API key authentication"""
    
    def setUp(self):
        self.client = APIClient()
        self.artist = Artist.objects.create(
            name="Test Artist",
            bio="Test bio"
        )
        self.api_key = APIKey.objects.create(
            name="Test API Key",
            artist=self.artist
        )
    
    def test_authentication_required(self):
        """Test that API endpoints require authentication"""
        response = self.client.get('/api/v1/artists/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_valid_api_key_authentication(self):
        """Test authentication with valid API key"""
        self.client.credentials(HTTP_API_KEY=self.api_key.key)
        response = self.client.get('/api/v1/artists/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_invalid_api_key_authentication(self):
        """Test authentication with invalid API key"""
        self.client.credentials(HTTP_API_KEY='invalid-key')
        response = self.client.get('/api/v1/artists/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_inactive_api_key_authentication(self):
        """Test authentication with inactive API key"""
        self.api_key.is_active = False
        self.api_key.save()
        self.client.credentials(HTTP_API_KEY=self.api_key.key)
        response = self.client.get('/api/v1/artists/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_api_key_usage_tracking(self):
        """Test that API key usage is tracked"""
        initial_count = self.api_key.usage_count
        self.client.credentials(HTTP_API_KEY=self.api_key.key)
        self.client.get('/api/v1/artists/')
        
        self.api_key.refresh_from_db()
        self.assertEqual(self.api_key.usage_count, initial_count + 1)
        self.assertIsNotNone(self.api_key.last_used)
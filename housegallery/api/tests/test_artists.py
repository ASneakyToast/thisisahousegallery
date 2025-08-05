from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from housegallery.api.models import APIKey
from housegallery.artists.models import Artist


class ArtistAPITest(TestCase):
    """Test Artist API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test artists
        self.artist1 = Artist.objects.create(
            name="Artist One",
            bio="Bio for artist one",
            website="https://artist1.com"
        )
        self.artist2 = Artist.objects.create(
            name="Artist Two",
            bio="Bio for artist two",
            website="https://artist2.com"
        )
        
        # Create API keys
        self.api_key1 = APIKey.objects.create(
            name="Artist One API Key",
            artist=self.artist1
        )
        self.api_key2 = APIKey.objects.create(
            name="Artist Two API Key",
            artist=self.artist2
        )
    
    def test_artist_list_returns_only_authenticated_artist(self):
        """Test that artist list returns only the authenticated artist"""
        self.client.credentials(HTTP_API_KEY=self.api_key1.key)
        response = self.client.get('/api/v1/artists/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.artist1.id)
        self.assertEqual(response.data['results'][0]['name'], self.artist1.name)
    
    def test_artist_profile_endpoint(self):
        """Test the profile endpoint returns authenticated artist"""
        self.client.credentials(HTTP_API_KEY=self.api_key1.key)
        response = self.client.get('/api/v1/artists/profile/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.artist1.id)
        self.assertEqual(response.data['name'], self.artist1.name)
        self.assertEqual(response.data['bio'], self.artist1.bio)
        self.assertEqual(response.data['website'], self.artist1.website)
    
    def test_artist_detail_cross_artist_access_denied(self):
        """Test that artists cannot access other artists' data"""
        self.client.credentials(HTTP_API_KEY=self.api_key1.key)
        response = self.client.get(f'/api/v1/artists/{self.artist2.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_artist_metadata_included(self):
        """Test that artist metadata is included in response"""
        self.client.credentials(HTTP_API_KEY=self.api_key1.key)
        response = self.client.get('/api/v1/artists/profile/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('metadata', response.data)
        self.assertIn('artwork_count', response.data['metadata'])
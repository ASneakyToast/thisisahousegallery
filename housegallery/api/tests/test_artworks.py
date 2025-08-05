from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from housegallery.api.models import APIKey
from housegallery.artists.models import Artist
from housegallery.artworks.models import Artwork


class ArtworkAPITest(TestCase):
    """Test Artwork API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test artists
        self.artist1 = Artist.objects.create(name="Artist One")
        self.artist2 = Artist.objects.create(name="Artist Two")
        
        # Create API keys
        self.api_key1 = APIKey.objects.create(
            name="Artist One API Key",
            artist=self.artist1
        )
        
        # Create artworks
        self.artwork1 = Artwork.objects.create(
            title="Artwork 1",
            description="Description 1",
            size="100x100cm",
            date=timezone.now()
        )
        self.artwork1.artists.add(self.artist1)
        
        self.artwork2 = Artwork.objects.create(
            title="Artwork 2",
            description="Description 2",
            size="50x50cm",
            date=timezone.now()
        )
        self.artwork2.artists.add(self.artist1)
        
        # Artwork belonging to different artist
        self.artwork3 = Artwork.objects.create(
            title="Artwork 3",
            description="Description 3",
            date=timezone.now()
        )
        self.artwork3.artists.add(self.artist2)
    
    def test_artwork_list_filtered_by_artist(self):
        """Test that artwork list is filtered by authenticated artist"""
        self.client.credentials(HTTP_API_KEY=self.api_key1.key)
        response = self.client.get('/api/v1/artworks/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        
        # Check that only artist1's artworks are returned
        artwork_ids = [a['id'] for a in response.data['results']]
        self.assertIn(self.artwork1.id, artwork_ids)
        self.assertIn(self.artwork2.id, artwork_ids)
        self.assertNotIn(self.artwork3.id, artwork_ids)
    
    def test_artwork_detail_access_control(self):
        """Test that artists can only access their own artwork details"""
        self.client.credentials(HTTP_API_KEY=self.api_key1.key)
        
        # Can access own artwork
        response = self.client.get(f'/api/v1/artworks/{self.artwork1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.artwork1.id)
        
        # Cannot access other artist's artwork
        response = self.client.get(f'/api/v1/artworks/{self.artwork3.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_artwork_search(self):
        """Test artwork search functionality"""
        self.client.credentials(HTTP_API_KEY=self.api_key1.key)
        response = self.client.get('/api/v1/artworks/', {'search': 'Artwork 1'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.artwork1.id)
    
    def test_artwork_ordering(self):
        """Test artwork ordering"""
        self.client.credentials(HTTP_API_KEY=self.api_key1.key)
        
        # Test ordering by date descending (default)
        response = self.client.get('/api/v1/artworks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Create artwork with different date
        old_artwork = Artwork.objects.create(
            title="Old Artwork",
            date=timezone.now() - timezone.timedelta(days=365)
        )
        old_artwork.artists.add(self.artist1)
        
        response = self.client.get('/api/v1/artworks/', {'ordering': 'date'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['id'], old_artwork.id)
    
    def test_artwork_featured_endpoint(self):
        """Test featured artworks endpoint"""
        self.client.credentials(HTTP_API_KEY=self.api_key1.key)
        response = self.client.get('/api/v1/artworks/featured/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertLessEqual(len(response.data), 6)  # Should return max 6 items
    
    def test_artwork_materials_endpoint(self):
        """Test materials endpoint"""
        # Add some materials to artworks
        self.artwork1.materials.add("oil", "canvas")
        self.artwork2.materials.add("watercolor", "paper")
        
        self.client.credentials(HTTP_API_KEY=self.api_key1.key)
        response = self.client.get('/api/v1/artworks/materials/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('materials', response.data)
        materials = response.data['materials']
        self.assertIn('oil', materials)
        self.assertIn('canvas', materials)
        self.assertIn('watercolor', materials)
        self.assertIn('paper', materials)
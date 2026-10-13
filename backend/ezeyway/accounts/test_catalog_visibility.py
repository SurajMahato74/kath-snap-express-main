from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from .api_views import (
    CustomerProductSearchView, CustomerVendorSearchView,
    image_search_api, search_products_api,
)
from .models import CustomUser, Product, VendorProfile
from .serializers import VendorProfileSerializer


class CatalogVisibilityTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.visible_products = set()
        self.visible_vendors = set()
        for index, (latitude, longitude, online, approved) in enumerate([
            (27.66, 85.35, True, True),
            (-33.86, 151.21, True, True),
            (None, None, True, True),
            (0, 0, True, True),
            (27.66, 85.35, False, True),
            (27.66, 85.35, True, False),
        ]):
            owner = CustomUser.objects.create_user(username=f'catalog{index}')
            vendor = VendorProfile.objects.create(
                user=owner, business_name=f'Shop {index}', latitude=latitude,
                longitude=longitude, is_active=online, is_approved=approved,
            )
            product = Product.objects.create(
                vendor=vendor, name=f'Item {index}', price=10, quantity=5,
                category='Food', status='active', featured=index == 1,
            )
            if online and approved:
                self.visible_vendors.add(vendor.pk)
                self.visible_products.add(product.pk)
        Product.objects.create(
            vendor=VendorProfile.objects.first(), name='Draft', price=10,
            category='Food', status='draft',
        )

    def test_product_search_is_independent_of_location(self):
        for view in [search_products_api, CustomerProductSearchView.as_view()]:
            for coordinates in [{}, {'latitude': 27.66, 'longitude': 85.35},
                                {'latitude': -80, 'longitude': -170},
                                {'latitude': 'invalid', 'longitude': 'invalid'}]:
                with self.subTest(view=view, coordinates=coordinates):
                    response = view(self.factory.get('/search/', coordinates))
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual({p['id'] for p in response.data['results']}, self.visible_products)

    def test_vendor_search_includes_distant_and_missing_locations(self):
        response = CustomerVendorSearchView.as_view()(self.factory.get(
            '/vendors/', {'latitude': 27.66, 'longitude': 85.35},
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual({v['id'] for v in response.data['results']}, self.visible_vendors)

    def test_image_search_does_not_filter_by_distance(self):
        request = self.factory.post('/image-search/', {
            'image': SimpleUploadedFile('item.jpg', b'image', content_type='image/jpeg'),
            'latitude': '-80', 'longitude': '-170',
        }, format='multipart')
        response = image_search_api(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual({p['id'] for p in response.data['results']}, self.visible_products)

    def test_vendor_profile_no_longer_exposes_radius(self):
        self.assertNotIn('delivery_radius', VendorProfileSerializer().fields)

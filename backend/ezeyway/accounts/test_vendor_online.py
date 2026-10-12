from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import CustomUser, VendorProfile


class VendorOnlineAdminTests(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(username='online_admin', is_superuser=True)
        self.owner = CustomUser.objects.create_user(username='online_owner')
        self.vendor = VendorProfile.objects.create(
            user=self.owner, business_name='Test Shop', business_email='shop@example.com',
            business_phone='1234567890', business_address='Market Street', state='Test',
            is_active=False, is_approved=False,
        )
        self.url = reverse('manage_vendors')
        self.client.force_login(self.admin)

    def set_status(self, value):
        return self.client.post(self.url, {
            'action': 'set_vendor_online', 'vendor_id': self.vendor.pk, 'is_active': value,
        })

    def test_admin_can_set_any_vendor_online_and_offline_without_changing_approval(self):
        for value in ['true', 'true', 'false']:
            self.assertEqual(self.set_status(value).status_code, 302)
            self.vendor.refresh_from_db()
            self.assertEqual(self.vendor.is_active, value == 'true')
            self.assertFalse(self.vendor.is_approved)
            self.assertTrue(self.vendor.status_override)
            self.assertEqual(self.vendor.status_override_date, timezone.localdate())

    def test_non_admin_cannot_change_status(self):
        self.client.force_login(self.owner)
        self.set_status('true')
        self.vendor.refresh_from_db()
        self.assertFalse(self.vendor.is_active)

    def test_anonymous_cannot_change_status(self):
        self.client.logout()
        self.assertEqual(self.set_status('true').status_code, 302)
        self.vendor.refresh_from_db()
        self.assertFalse(self.vendor.is_active)

    def test_invalid_status_does_not_change_vendor(self):
        self.set_status('invalid')
        self.vendor.refresh_from_db()
        self.assertFalse(self.vendor.is_active)

    def test_csrf_is_required(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        response = client.post(self.url, {
            'action': 'set_vendor_online', 'vendor_id': self.vendor.pk, 'is_active': 'true',
        })
        self.assertEqual(response.status_code, 403)

    def test_desktop_and_mobile_show_online_control(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'vendor-online-form', count=3)  # two forms + submit handler
        self.assertContains(response, 'Set Online', count=2)
        self.assertContains(response, 'name="csrfmiddlewaretoken"', count=2)
        self.vendor.refresh_from_db()
        self.assertFalse(self.vendor.is_active)  # Reading the page never toggles status.

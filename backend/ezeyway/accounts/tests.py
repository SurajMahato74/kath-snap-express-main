from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import CustomUser, VendorProfile, VendorWallet, WalletTransaction


class InitialWalletPointsAdminTests(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            username='wallet_admin',
            password='test-password',
            user_type='superuser',
            is_superuser=True,
        )
        self.vendor_user = CustomUser.objects.create_user(
            username='wallet_vendor',
            email='vendor@example.com',
            password='test-password',
            user_type='vendor',
        )
        self.vendor = VendorProfile.objects.create(
            user=self.vendor_user,
            business_name='Northside Market',
            business_email='business@example.com',
            business_phone='1234567890',
            business_address='1 Market Street',
            state='Test State',
        )
        self.client.force_login(self.admin)
        self.url = reverse('manage_initial_wallet_points')

    def test_search_finds_vendor_by_business_name(self):
        response = self.client.get(self.url, {'vendor_search': 'northside'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Northside Market')
        self.assertContains(response, 'wallet_vendor')
        self.assertContains(response, 'Add Points')

    def test_admin_credit_updates_wallet_and_records_transaction(self):
        response = self.client.post(
            self.url,
            {
                'action': 'credit_vendor_wallet',
                'vendor_id': self.vendor.id,
                'points': '25.75',
                'vendor_search': 'Northside',
            },
        )

        self.assertRedirects(response, f'{self.url}?vendor_search=Northside')
        wallet = VendorWallet.objects.get(vendor=self.vendor)
        self.assertEqual(wallet.balance, Decimal('25.75'))
        self.assertEqual(wallet.total_earned, Decimal('25.75'))
        transaction = WalletTransaction.objects.get(wallet=wallet)
        self.assertEqual(transaction.transaction_type, 'credit')
        self.assertEqual(transaction.amount, Decimal('25.75'))
        self.assertEqual(transaction.status, 'completed')
        self.assertIn('wallet_admin', transaction.description)

    def test_invalid_credit_does_not_change_wallet(self):
        response = self.client.post(
            self.url,
            {
                'action': 'credit_vendor_wallet',
                'vendor_id': self.vendor.id,
                'points': '0',
            },
            follow=True,
        )

        self.assertContains(response, 'must be greater than zero')
        wallet = VendorWallet.objects.get(vendor=self.vendor)
        self.assertEqual(wallet.balance, Decimal('0.00'))
        self.assertFalse(wallet.transactions.exists())

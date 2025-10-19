from django.core.management.base import BaseCommand
from accounts.models import CustomUser

class Command(BaseCommand):
    help = 'Generate referral codes for existing vendors who do not have one'

    def handle(self, *args, **options):
        vendors_without_codes = CustomUser.objects.filter(
            user_type='vendor',
            referral_code__isnull=True
        )
        
        count = 0
        for vendor in vendors_without_codes:
            vendor.generate_referral_code()
            count += 1
            self.stdout.write(
                self.style.SUCCESS(f'Generated referral code {vendor.referral_code} for vendor: {vendor.username}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully generated referral codes for {count} vendors')
        )
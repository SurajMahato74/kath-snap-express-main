import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
django.setup()

from accounts.models import CustomUser

# Generate referral codes for existing vendors
vendors_without_codes = CustomUser.objects.filter(
    user_type='vendor',
    referral_code__isnull=True
)

count = 0
for vendor in vendors_without_codes:
    vendor.generate_referral_code()
    count += 1
    print(f'Generated referral code {vendor.referral_code} for vendor: {vendor.username}')

print(f'Successfully generated referral codes for {count} vendors')
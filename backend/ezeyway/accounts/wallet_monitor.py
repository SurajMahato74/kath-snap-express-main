from django.utils import timezone
from .models import VendorProfile, VendorWallet
import logging

logger = logging.getLogger(__name__)

def check_and_disable_low_balance_vendors():
    """
    Check all active vendors and disable those with wallet balance < 100
    """
    try:
        # Get all active vendors
        active_vendors = VendorProfile.objects.filter(
            is_active=True,
            is_approved=True
        )
        
        disabled_count = 0
        
        for vendor in active_vendors:
            try:
                wallet, created = VendorWallet.objects.get_or_create(vendor=vendor)
                
                if wallet.balance < 100:
                    # Disable vendor
                    vendor.is_active = False
                    vendor.status_override = True
                    vendor.status_override_date = timezone.now().date()
                    vendor.save()
                    
                    disabled_count += 1
                    logger.info(f"Disabled vendor {vendor.business_name} due to low balance: {wallet.balance}")
                    
            except Exception as e:
                logger.error(f"Error checking wallet for vendor {vendor.id}: {str(e)}")
                continue
        
        if disabled_count > 0:
            logger.info(f"Disabled {disabled_count} vendors due to low wallet balance")
        
        return disabled_count
        
    except Exception as e:
        logger.error(f"Error in wallet monitor: {str(e)}")
        return 0
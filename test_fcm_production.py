#!/usr/bin/env python3
"""
Production FCM Test Script
Tests FCM notifications in production environment
"""

import os
import sys
import django
import logging
from pathlib import Path

# --------------------------------------------------------------------------- #
# 1. Setup logging
# --------------------------------------------------------------------------- #
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# 2. Add backend/ezeyway to PYTHONPATH
# --------------------------------------------------------------------------- #
# The script lives in the repo root:  kath-snap-express-main/
# The Django project lives in:      backend/ezeyway/
repo_root = Path(__file__).resolve().parent
backend_path = repo_root / "backend" / "ezeyway"

if not backend_path.is_dir():
    log.error("Cannot locate backend/ezeyway directory at %s", backend_path)
    sys.exit(1)

sys.path.insert(0, str(backend_path))

# --------------------------------------------------------------------------- #
# 3. Django bootstrap
# --------------------------------------------------------------------------- #
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ezeyway.settings")
django.setup()

# --------------------------------------------------------------------------- #
# 4. Imports after Django is ready
# --------------------------------------------------------------------------- #
from accounts.fcm_service import fcm_service
from accounts.models import VendorProfile

# --------------------------------------------------------------------------- #
# 5. Helper: verify service-account path
# --------------------------------------------------------------------------- #
def ensure_firebase_key() -> None:
    key_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    if not key_path:
        log.error(
            "FIREBASE_SERVICE_ACCOUNT_PATH environment variable is NOT set.\n"
            "  export FIREBASE_SERVICE_ACCOUNT_PATH=\"/opt/ezeyway/secrets/ezeyway-2f869-....json\""
        )
        sys.exit(1)

    key_path = Path(key_path).expanduser().resolve()
    if not key_path.is_file():
        log.error("Firebase service-account file not found: %s", key_path)
        sys.exit(1)

    log.info("Firebase service-account: %s", key_path)


# --------------------------------------------------------------------------- #
# 6. Main test routine
# --------------------------------------------------------------------------- #
def test_fcm_production() -> None:
    print("\nTesting FCM in Production Environment")
    print("=" * 58)

    # ---- 1. Verify Firebase key ------------------------------------------------
    print("\n1. Verifying Firebase service-account ...")
    ensure_firebase_key()

    # ---- 2. Find a vendor with a token ----------------------------------------
    print("\n2. Looking for a vendor with an FCM token ...")
    vendors = (
        VendorProfile.objects.filter(fcm_token__isnull=False, is_approved=True)
        .exclude(fcm_token="")
        .order_by("id")
    )

    if not vendors.exists():
        log.warning("No approved vendors with FCM tokens found.")
        log.info(
            "Make sure a vendor has logged into the mobile app at least once."
        )
        return

    vendor = vendors.first()
    log.info("Vendor selected: %s", vendor.business_name)
    log.info("FCM token (preview): %s...", vendor.fcm_token[:30])

    # ---- 3. Send test notification --------------------------------------------
    print("\n3. Sending test FCM notification ...")
    order_data = {
        "orderId": "TEST-999",
        "orderNumber": "TEST-999",
        "amount": "500.00",
    }

    try:
        success = fcm_service.send_order_notification(vendor.fcm_token, order_data)
        if success:
            log.info("FCM notification sent successfully!")
            log.info("Check the vendor's phone – it should ring and open the app when tapped.")
        else:
            log.error("FCM notification failed (function returned False).")
            log.info("Inspect server logs for the root cause.")
    except Exception as exc:  # pylint: disable=broad-except
        log.error("Unexpected error while sending FCM: %s", exc)
        log.debug("", exc_info=True)

    print("\n" + "=" * 58)
    print("FCM Production Test Complete\n")


# --------------------------------------------------------------------------- #
# 7. Entrypoint
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    test_fcm_production()
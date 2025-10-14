from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone

def send_vendor_submission_email(vendor_profile):
    """Send email when vendor submits profile for approval"""
    subject = "Vendor Application Submitted - Pending Approval"
    
    message = f"""
Dear {vendor_profile.owner_name},

Thank you for submitting your vendor application for {vendor_profile.business_name}.

Your application has been received and is currently under review by our admin team. 
You will be notified via email once your application has been processed.

Application Details:
- Business Name: {vendor_profile.business_name}
- Owner Name: {vendor_profile.owner_name}
- Business Email: {vendor_profile.business_email}
- Business Phone: {vendor_profile.business_phone}
- Submission Date: {vendor_profile.created_at.strftime('%B %d, %Y at %I:%M %p')}

We typically review applications within 24-48 hours. Thank you for your patience.

Best regards,
ezeyway Team
"""
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[vendor_profile.user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send submission email: {e}")
        return False

def send_vendor_approval_email(vendor_profile):
    """Send email when vendor profile is approved"""
    subject = "Congratulations! Your Vendor Application Has Been Approved"
    
    message = f"""
Dear {vendor_profile.owner_name},

Congratulations! Your vendor application for {vendor_profile.business_name} has been approved.

You can now log in to your vendor dashboard and start managing your business on our platform.

Application Details:
- Business Name: {vendor_profile.business_name}
- Approval Date: {vendor_profile.approval_date.strftime('%B %d, %Y at %I:%M %p')}

Next Steps:
1. Log in to your vendor account
2. Complete your product listings
3. Set up your business hours
4. Start receiving orders

Welcome to the ezeyway family!

Best regards,
ezeyway Team
"""
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[vendor_profile.user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send approval email: {e}")
        return False

def send_vendor_rejection_email(vendor_profile):
    """Send email when vendor profile is rejected"""
    subject = "Vendor Application Update Required"
    
    message = f"""
Dear {vendor_profile.owner_name},

Thank you for your interest in becoming a vendor with ezeyway.

After reviewing your application for {vendor_profile.business_name}, we need you to make some updates before we can approve your account.

Reason for Update Request:
{vendor_profile.rejection_reason}

What to do next:
1. Log in to your account
2. Update your application with the required changes
3. Resubmit for review

We're here to help you succeed. Please make the necessary updates and resubmit your application.

If you have any questions, please contact our support team.

Best regards,
ezeyway Team
"""
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[vendor_profile.user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send rejection email: {e}")
        return False
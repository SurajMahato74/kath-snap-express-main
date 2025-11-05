#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
django.setup()

from accounts.models import CustomUser
from django.contrib.auth import authenticate

def check_superuser_login():
    print("=== Superuser Login Test ===\n")
    
    # Get all superusers
    superusers = CustomUser.objects.filter(is_superuser=True)
    
    if not superusers.exists():
        print("No superusers found!")
        return
    
    print("Found superusers:")
    for user in superusers:
        print(f"- Username: {user.username}")
        print(f"  Email: {user.email}")
        print(f"  Active: {user.is_active}")
        print(f"  Has password: {user.has_usable_password()}")
        if hasattr(user, 'plain_password') and user.plain_password:
            print(f"  Plain password: {user.plain_password}")
        print()
    
    # Test common passwords
    test_passwords = ['admin', 'password', '123456', 'admin123', 'ezeyway', 'demo']
    
    print("Testing common passwords...")
    for user in superusers:
        print(f"\nTesting user: {user.username}")
        for password in test_passwords:
            auth_user = authenticate(username=user.username, password=password)
            if auth_user:
                print(f"SUCCESS! Username: {user.username}, Password: {password}")
                return
            else:
                print(f"Failed: {password}")
    
    print("\nNo common passwords worked. You may need to reset the password.")
    print("\nTo reset password, run:")
    print("python manage.py changepassword <username>")
    print("\nOr create a new superuser:")
    print("python manage.py createsuperuser")

if __name__ == "__main__":
    check_superuser_login()
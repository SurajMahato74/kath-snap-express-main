#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
django.setup()

from accounts.models import CustomUser
from django.contrib.auth import authenticate

def test_login():
    """Test login with the credentials you provided"""
    username = 'ezeyway'
    password = 'password'
    
    print(f"Testing login with username: {username}, password: {password}")
    
    # Check if user exists
    try:
        user = CustomUser.objects.get(username=username)
        print(f"User found: {user.username}")
        print(f"Email: {user.email}")
        print(f"User type: {user.user_type}")
        print(f"Is superuser: {user.is_superuser}")
        print(f"Is active: {user.is_active}")
        print(f"Email verified: {user.email_verified}")
        print(f"Plain password stored: {user.plain_password}")
        
        # Test authentication
        auth_user = authenticate(username=username, password=password)
        if auth_user:
            print("✅ Authentication successful!")
        else:
            print("❌ Authentication failed!")
            
            # Try to fix the password
            print("Attempting to fix password...")
            user.set_password(password)
            user.plain_password = password
            user.save()
            
            # Test again
            auth_user = authenticate(username=username, password=password)
            if auth_user:
                print("✅ Authentication successful after password fix!")
            else:
                print("❌ Authentication still failing!")
        
    except CustomUser.DoesNotExist:
        print(f"❌ User '{username}' does not exist!")
        print("Creating user...")
        
        # Create the user
        user = CustomUser.objects.create_user(
            username=username,
            email='ezeyway@example.com',
            password=password
        )
        user.user_type = 'superuser'
        user.is_superuser = True
        user.is_staff = True
        user.plain_password = password
        user.email_verified = True
        user.is_verified = True
        user.save()
        
        print(f"✅ User '{username}' created successfully!")
        print(f"Username: {username}")
        print(f"Password: {password}")
        print(f"User type: {user.user_type}")
        print(f"Is superuser: {user.is_superuser}")

if __name__ == '__main__':
    test_login()
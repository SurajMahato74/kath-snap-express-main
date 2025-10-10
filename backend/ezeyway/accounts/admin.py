from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, VendorProfile, Slider

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'user_type', 'is_verified', 'is_active', 'date_joined']
    list_filter = ['user_type', 'is_verified', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'phone_number']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'phone_number', 'address', 'date_of_birth', 'profile_picture', 'is_verified')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'phone_number', 'address', 'date_of_birth', 'profile_picture', 'is_verified')
        }),
    )

class VendorProfileAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'user', 'business_email', 'is_approved', 'approval_date']
    list_filter = ['is_approved', 'approval_date']
    search_fields = ['business_name', 'user__username', 'business_email']
    
class SliderAdmin(admin.ModelAdmin):
    list_display = ['title', 'visibility', 'display_order', 'is_active', 'start_date', 'end_date', 'created_at']
    list_filter = ['visibility', 'is_active', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['display_order', 'created_at']

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(VendorProfile, VendorProfileAdmin)
admin.site.register(Slider, SliderAdmin)

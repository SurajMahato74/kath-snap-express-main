from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, VendorProfile, Slider, Category, SubCategory

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

class SubCategoryInline(admin.TabularInline):
    model = SubCategory
    extra = 1
    fields = ['name', 'icon', 'description', 'is_active', 'display_order']
    ordering = ['display_order', 'name']

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'subcategories_count', 'is_active', 'display_order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['display_order', 'name']
    inlines = [SubCategoryInline]
    
    def subcategories_count(self, obj):
        return obj.subcategories.count()
    subcategories_count.short_description = 'Subcategories'

class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_active', 'display_order', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'category__name', 'description']
    ordering = ['category__name', 'display_order', 'name']
    list_select_related = ['category']

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(VendorProfile, VendorProfileAdmin)
admin.site.register(Slider, SliderAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(SubCategory, SubCategoryAdmin)

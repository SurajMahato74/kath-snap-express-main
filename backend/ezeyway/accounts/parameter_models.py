from django.db import models
from .models import Category, SubCategory

class CategoryParameter(models.Model):
    """Parameters/attributes for categories"""
    FIELD_TYPE_CHOICES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('select', 'Select (Single Choice)'),
        ('multiselect', 'Multi-Select'),
        ('textarea', 'Textarea'),
        ('boolean', 'Boolean (Yes/No)'),
        ('date', 'Date'),
        ('color', 'Color'),
        ('range', 'Range'),
    ]
    
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='parameters')
    name = models.CharField(max_length=100, help_text="Parameter name (e.g., 'brand', 'size')")
    label = models.CharField(max_length=100, help_text="Display label (e.g., 'Brand Name', 'Size')")
    field_type = models.CharField(max_length=20, choices=FIELD_TYPE_CHOICES, default='text')
    is_required = models.BooleanField(default=False, help_text="Is this parameter required?")
    options = models.JSONField(default=list, blank=True, help_text="Options for select/multiselect fields")
    placeholder = models.CharField(max_length=200, blank=True, null=True, help_text="Placeholder text")
    description = models.TextField(blank=True, null=True, help_text="Help text for this parameter")
    min_value = models.FloatField(blank=True, null=True, help_text="Minimum value for number/range fields")
    max_value = models.FloatField(blank=True, null=True, help_text="Maximum value for number/range fields")
    step = models.FloatField(blank=True, null=True, help_text="Step value for number/range fields")
    display_order = models.PositiveIntegerField(default=0, help_text="Display order")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', 'name']
        unique_together = ('category', 'name')
    
    def __str__(self):
        return f"{self.category.name} - {self.label} ({self.field_type})"

class SubCategoryParameter(models.Model):
    """Parameters/attributes for subcategories"""
    FIELD_TYPE_CHOICES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('select', 'Select (Single Choice)'),
        ('multiselect', 'Multi-Select'),
        ('textarea', 'Textarea'),
        ('boolean', 'Boolean (Yes/No)'),
        ('date', 'Date'),
        ('color', 'Color'),
        ('range', 'Range'),
    ]
    
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, related_name='parameters')
    name = models.CharField(max_length=100, help_text="Parameter name (e.g., 'material', 'color')")
    label = models.CharField(max_length=100, help_text="Display label (e.g., 'Material Type', 'Color')")
    field_type = models.CharField(max_length=20, choices=FIELD_TYPE_CHOICES, default='text')
    is_required = models.BooleanField(default=False, help_text="Is this parameter required?")
    options = models.JSONField(default=list, blank=True, help_text="Options for select/multiselect fields")
    placeholder = models.CharField(max_length=200, blank=True, null=True, help_text="Placeholder text")
    description = models.TextField(blank=True, null=True, help_text="Help text for this parameter")
    min_value = models.FloatField(blank=True, null=True, help_text="Minimum value for number/range fields")
    max_value = models.FloatField(blank=True, null=True, help_text="Maximum value for number/range fields")
    step = models.FloatField(blank=True, null=True, help_text="Step value for number/range fields")
    display_order = models.PositiveIntegerField(default=0, help_text="Display order")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', 'name']
        unique_together = ('subcategory', 'name')
    
    def __str__(self):
        return f"{self.subcategory.category.name} > {self.subcategory.name} - {self.label} ({self.field_type})"
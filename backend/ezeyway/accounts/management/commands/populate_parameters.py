from django.core.management.base import BaseCommand
from accounts.models import Category, SubCategory
from accounts.parameter_models import CategoryParameter, SubCategoryParameter

class Command(BaseCommand):
    help = 'Populate sample parameters for categories and subcategories'

    def handle(self, *args, **options):
        self.stdout.write('Populating sample parameters...')
        
        # Get or create categories
        clothing_cat, _ = Category.objects.get_or_create(name='Clothing')
        electronics_cat, _ = Category.objects.get_or_create(name='Electronics')
        grocery_cat, _ = Category.objects.get_or_create(name='Grocery')
        
        # Add parameters for Clothing category
        CategoryParameter.objects.get_or_create(
            category=clothing_cat,
            name='brand',
            defaults={
                'label': 'Brand',
                'field_type': 'text',
                'placeholder': 'e.g., Nike, Adidas',
                'is_required': False,
                'display_order': 1
            }
        )
        
        CategoryParameter.objects.get_or_create(
            category=clothing_cat,
            name='size',
            defaults={
                'label': 'Available Sizes',
                'field_type': 'multiselect',
                'options': ['XS', 'S', 'M', 'L', 'XL', 'XXL'],
                'is_required': True,
                'display_order': 2
            }
        )
        
        CategoryParameter.objects.get_or_create(
            category=clothing_cat,
            name='color',
            defaults={
                'label': 'Available Colors',
                'field_type': 'multiselect',
                'options': ['Black', 'White', 'Red', 'Blue', 'Green', 'Yellow', 'Pink', 'Gray'],
                'is_required': True,
                'display_order': 3
            }
        )
        
        CategoryParameter.objects.get_or_create(
            category=clothing_cat,
            name='material',
            defaults={
                'label': 'Material',
                'field_type': 'select',
                'options': ['Cotton', 'Polyester', 'Silk', 'Wool', 'Denim', 'Leather'],
                'is_required': False,
                'display_order': 4
            }
        )
        
        # Add parameters for Electronics category
        CategoryParameter.objects.get_or_create(
            category=electronics_cat,
            name='brand',
            defaults={
                'label': 'Brand',
                'field_type': 'text',
                'placeholder': 'e.g., Samsung, Apple, Sony',
                'is_required': True,
                'display_order': 1
            }
        )
        
        CategoryParameter.objects.get_or_create(
            category=electronics_cat,
            name='warranty',
            defaults={
                'label': 'Warranty Period',
                'field_type': 'select',
                'options': ['No Warranty', '6 months', '1 year', '2 years', '3 years'],
                'is_required': True,
                'display_order': 2
            }
        )
        
        CategoryParameter.objects.get_or_create(
            category=electronics_cat,
            name='power_consumption',
            defaults={
                'label': 'Power Consumption (Watts)',
                'field_type': 'number',
                'placeholder': 'e.g., 100',
                'min_value': 0,
                'max_value': 5000,
                'is_required': False,
                'display_order': 3
            }
        )
        
        # Add parameters for Grocery category
        CategoryParameter.objects.get_or_create(
            category=grocery_cat,
            name='weight',
            defaults={
                'label': 'Weight/Volume',
                'field_type': 'text',
                'placeholder': 'e.g., 1kg, 500ml, 250g',
                'is_required': True,
                'display_order': 1
            }
        )
        
        CategoryParameter.objects.get_or_create(
            category=grocery_cat,
            name='expiry_date',
            defaults={
                'label': 'Expiry Date',
                'field_type': 'date',
                'is_required': True,
                'display_order': 2
            }
        )
        
        CategoryParameter.objects.get_or_create(
            category=grocery_cat,
            name='organic',
            defaults={
                'label': 'Organic Product',
                'field_type': 'boolean',
                'is_required': False,
                'display_order': 3
            }
        )
        
        # Create some subcategories and their parameters
        # T-Shirts subcategory under Clothing
        tshirts_sub, _ = SubCategory.objects.get_or_create(
            category=clothing_cat,
            name='T-Shirts'
        )
        
        SubCategoryParameter.objects.get_or_create(
            subcategory=tshirts_sub,
            name='neck_type',
            defaults={
                'label': 'Neck Type',
                'field_type': 'select',
                'options': ['Round Neck', 'V-Neck', 'Polo', 'Henley'],
                'is_required': False,
                'display_order': 1
            }
        )
        
        SubCategoryParameter.objects.get_or_create(
            subcategory=tshirts_sub,
            name='sleeve_type',
            defaults={
                'label': 'Sleeve Type',
                'field_type': 'select',
                'options': ['Short Sleeve', 'Long Sleeve', '3/4 Sleeve'],
                'is_required': False,
                'display_order': 2
            }
        )
        
        # Smartphones subcategory under Electronics
        smartphones_sub, _ = SubCategory.objects.get_or_create(
            category=electronics_cat,
            name='Smartphones'
        )
        
        SubCategoryParameter.objects.get_or_create(
            subcategory=smartphones_sub,
            name='storage',
            defaults={
                'label': 'Storage Capacity',
                'field_type': 'select',
                'options': ['32GB', '64GB', '128GB', '256GB', '512GB', '1TB'],
                'is_required': True,
                'display_order': 1
            }
        )
        
        SubCategoryParameter.objects.get_or_create(
            subcategory=smartphones_sub,
            name='ram',
            defaults={
                'label': 'RAM',
                'field_type': 'select',
                'options': ['2GB', '3GB', '4GB', '6GB', '8GB', '12GB', '16GB'],
                'is_required': True,
                'display_order': 2
            }
        )
        
        SubCategoryParameter.objects.get_or_create(
            subcategory=smartphones_sub,
            name='screen_size',
            defaults={
                'label': 'Screen Size (inches)',
                'field_type': 'number',
                'placeholder': 'e.g., 6.1',
                'min_value': 3.0,
                'max_value': 8.0,
                'step': 0.1,
                'is_required': False,
                'display_order': 3
            }
        )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully populated sample parameters!')
        )
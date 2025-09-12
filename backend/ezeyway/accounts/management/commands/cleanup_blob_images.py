from django.core.management.base import BaseCommand
from accounts.models import ProductImage

class Command(BaseCommand):
    help = 'Clean up blob URLs from ProductImage records'

    def handle(self, *args, **options):
        # Find all ProductImage records with blob URLs
        blob_images = ProductImage.objects.filter(image__contains='blob:')
        
        self.stdout.write(f'Found {blob_images.count()} images with blob URLs')
        
        if blob_images.count() > 0:
            # Delete these invalid image records
            deleted_count = blob_images.count()
            blob_images.delete()
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {deleted_count} invalid image records')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('No blob URLs found in database')
            )
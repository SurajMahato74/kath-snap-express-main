from django.core.management.base import BaseCommand
from accounts.order_models import Order
from accounts.models import VendorProfile

class Command(BaseCommand):
    help = 'Check if a specific order exists and show details'

    def add_arguments(self, parser):
        parser.add_argument('order_id', type=int, help='Order ID to check')

    def handle(self, *args, **options):
        order_id = options['order_id']
        
        try:
            order = Order.objects.get(id=order_id)
            self.stdout.write(
                self.style.SUCCESS(f'✅ Order {order_id} EXISTS')
            )
            self.stdout.write(f'Order Number: {order.order_number}')
            self.stdout.write(f'Status: {order.status}')
            self.stdout.write(f'Customer: {order.customer.username}')
            self.stdout.write(f'Vendor: {order.vendor.business_name} (ID: {order.vendor.id})')
            self.stdout.write(f'Total Amount: ₹{order.total_amount}')
            self.stdout.write(f'Created: {order.created_at}')
            
        except Order.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ Order {order_id} NOT FOUND')
            )
            
            # Show available orders
            self.stdout.write('\nAvailable orders:')
            orders = Order.objects.all().order_by('-id')[:10]
            for order in orders:
                self.stdout.write(f'  Order {order.id}: {order.status} - {order.vendor.business_name}')
            
            if not orders:
                self.stdout.write('  No orders found in database')
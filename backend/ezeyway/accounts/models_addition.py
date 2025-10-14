# Add this VendorShopImage model to your models.py file after the VendorDocument class

class VendorShopImage(models.Model):
    vendor_profile = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, related_name='shop_images')
    image = models.CharField(max_length=500)
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_primary', 'uploaded_at']
    
    def __str__(self):
        return f"Shop Image for {self.vendor_profile.business_name}"
# Add this VendorShopImageSerializer to your serializers.py file

class VendorShopImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = VendorShopImage
        fields = ['id', 'vendor_profile', 'image', 'image_url', 'is_primary', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']
    
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image:
            if request:
                return request.build_absolute_uri(f'/media/{obj.image}')
            return f'/media/{obj.image}'
        return None
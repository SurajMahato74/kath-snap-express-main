# Add this VendorShopImageListCreateView to your api_views.py file

class VendorShopImageListCreateView(generics.ListCreateAPIView):
    serializer_class = VendorShopImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return VendorShopImage.objects.all()
        return VendorShopImage.objects.filter(vendor_profile__user=self.request.user)

    def perform_create(self, serializer):
        vendor_profile_id = self.request.data.get('vendor_profile')
        try:
            vendor_profile = VendorProfile.objects.get(id=vendor_profile_id, user=self.request.user)
        except VendorProfile.DoesNotExist:
            from rest_framework import serializers as drf_serializers
            raise drf_serializers.ValidationError({'vendor_profile': 'Invalid vendor profile or access denied.'})
        
        # Handle file upload
        uploaded_file = self.request.FILES.get('image')
        if uploaded_file:
            import os
            from django.conf import settings
            from django.core.files.storage import default_storage
            
            # Create filename
            file_extension = os.path.splitext(uploaded_file.name)[1]
            filename = f"shop_images/{vendor_profile.id}_{timezone.now().timestamp()}{file_extension}"
            
            # Save file
            file_path = default_storage.save(filename, uploaded_file)
            serializer.save(vendor_profile=vendor_profile, image=file_path)
        else:
            raise drf_serializers.ValidationError({'image': 'Image file is required.'})
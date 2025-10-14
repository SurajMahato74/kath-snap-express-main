# Add this URL to your api_urls.py file in the urlpatterns list:

path('vendor-shop-images/', api_views.VendorShopImageListCreateView.as_view(), name='api_vendor_shop_images'),
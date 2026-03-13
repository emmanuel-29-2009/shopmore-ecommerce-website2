


from django.contrib import admin
from django.utils.html import format_html  # Add this import
from .models import Category  # Make sure to import your model
from .models import Category, Product, UserProfile, Order, OrderItem

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'image_preview']  # or whatever fields you have
    
    def image_preview(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            return format_html(f'<img src="{obj.image.url}" style="width: 50px; height: 50px; object-fit: cover;" />')
        return ""
    image_preview.short_description = 'Image Preview'

admin.site.register(Category, CategoryAdmin)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'category', 'stock', 'is_featured', 'created_at']
    list_filter = ['category', 'is_featured', 'created_at']
    list_editable = ['price', 'stock', 'is_featured']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'created_at']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price']

admin.site.site_header = "ShopMore Admin"
admin.site.site_title = "ShopMore Admin Portal"
admin.site.index_title = "Welcome to ShopMore Admin"

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shopmore.settings')
django.setup()

from core.models import Category, Product

def create_sample_data():
    # Create categories
    electronics, _ = Category.objects.get_or_create(
        name='Electronics',
        slug='electronics',
        defaults={'description': 'Latest gadgets and electronics'}
    )
    
    fashion, _ = Category.objects.get_or_create(
        name='Fashion',
        slug='fashion',
        defaults={'description': 'Trendy clothes and accessories'}
    )
    
    home, _ = Category.objects.get_or_create(
        name='Home & Garden',
        slug='home-garden',
        defaults={'description': 'Furniture and home decor'}
    )
    
    # Create sample products
    Product.objects.get_or_create(
        name='Smartphone X',
        slug='smartphone-x',
        defaults={
            'description': 'Latest smartphone with advanced features',
            'price': 699.99,
            'old_price': 799.99,
            'category': electronics,
            'stock': 50,
            'is_featured': True
        }
    )
    
    Product.objects.get_or_create(
        name='Wireless Headphones',
        slug='wireless-headphones',
        defaults={
            'description': 'Premium wireless headphones with noise cancellation',
            'price': 199.99,
            'category': electronics,
            'stock': 30,
            'is_featured': True
        }
    )
    
    Product.objects.get_or_create(
        name='Designer T-Shirt',
        slug='designer-tshirt',
        defaults={
            'description': 'Premium cotton t-shirt with unique design',
            'price': 29.99,
            'category': fashion,
            'stock': 100,
            'is_featured': True
        }
    )
    
    print("Sample data created successfully!")

if __name__ == '__main__':
    create_sample_data()
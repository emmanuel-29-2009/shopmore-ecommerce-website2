from django.urls import path, include
from . import views

urlpatterns = [

    path('', views.home_view, name='home'),

    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),

    path('products/', views.products_view, name='products'),
    path('products/<int:product_id>/', views.product_detail_view, name='product_detail'),

    path('category/<slug:category_slug>/', views.category_view, name='category'),
    path('search/', views.search_view, name='search'),
    path("live-search/", views.live_search, name="live_search"),


    path('settings/', views.settings_view, name='settings'),
    path('deals/', views.deals_view, name='deals'),
    path('new-arrivals/', views.new_arrivals_view, name='new_arrivals'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),

    # Cart
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),

    # Wishlist
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/clear/', views.clear_wishlist, name='clear_wishlist'),

    # Checkout
    path('checkout/', views.checkout_view, name='checkout'),
    path('checkout/process/', views.process_checkout, name='process_checkout'),
    path('order/success/<int:order_id>/', views.order_success, name='order_success'),

    path('orders/', views.orders_view, name='orders'),

    # ===== ORDER TRACKING URLs =====
    # Public tracking page - enter order/tracking number
    path('track-order/', views.track_order, name='track_order'),
    
    # Tracking details page - shows full tracking information
    path('track-order/<str:order_number>/', views.order_tracking_details, name='order_tracking_details'),
    
    # API endpoint for AJAX tracking (returns JSON)
    path('order/<str:order_number>/track/', views.track_my_order, name='track_my_order'),
    
    # Admin helper to add tracking events (staff only)
    path('shipment/<int:shipment_id>/add-event/', views.add_tracking_event, name='add_tracking_event'),

    path("payment/", include("paymentApp.urls")),

    path('debug-order/<int:order_id>/', views.debug_order_data, name='debug_order'),
]
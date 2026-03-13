from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random
import string

from .models import *
from .forms import *

from django import template

register = template.Library()

@register.filter
def add(value, arg):
    """Add the arg to the value"""
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return value

def home_view(request):
    return render(request, "home.html")


def signup_view(request):
    form = CustomUserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("dashboard")
    return render(request, "signup.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        user = authenticate(
            username=request.POST["username"],
            password=request.POST["password"],
        )
        if user:
            login(request, user)
            return redirect("dashboard")
    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("home")


@login_required
def dashboard_view(request):
    # Get user's recent orders for dashboard
    recent_orders = Order.objects.filter(user=request.user)[:5]
    return render(request, "dashboard.html", {
        "recent_orders": recent_orders
    })


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    form = UserProfileForm(request.POST or None, instance=profile)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile updated successfully!")

    return render(request, "profile.html", {"form": form})


def products_view(request):
    products = Product.objects.all()
    return render(request, "products.html", {"products": products})


def product_detail_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, "product_detail.html", {"product": product})


def category_view(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    products = Product.objects.filter(category=category)
    return render(request, "category.html", {
        "products": products,
        "category": category
    })


def search_view(request):
    q = request.GET.get("q", "").strip()
    products = Product.objects.none()

    if q:
        products = Product.objects.filter(
            Q(name__icontains=q) |
            Q(description__icontains=q) |
            Q(category__name__icontains=q)
        ).distinct()

    return render(request, "search.html", {
        "products": products,
        "query": q
    })


def live_search(request):
    query = request.GET.get("q", "").strip()
    results = []

    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )[:5]   # limit to 5 suggestions

        for product in products:
            results.append({
                "id": product.id,
                "name": product.name,
                "price": str(product.price),
                "image": product.image.url if product.image else "",
            })

    return JsonResponse({"results": results})


@login_required
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = CartItem.objects.filter(cart=cart)
    total = sum(i.total_price for i in items)

    # Calculate additional values for template
    subtotal = total
    shipping_cost = Decimal('10.00')
    tax = Decimal('0.00')
    discount = Decimal('0.00')
    
    # Check if free shipping applies (orders over $50)
    if subtotal > 50:
        shipping_cost = Decimal('0.00')
    
    grand_total = subtotal + shipping_cost + tax - discount
    
    # Calculate progress percentage for free shipping
    progress_percentage = min(100, (subtotal / 50) * 100) if subtotal < 50 else 100
    
    context = {
        'cart_items': items,
        'total': total,
        'subtotal': subtotal,
        'shipping': shipping_cost,
        'tax': tax,
        'discount': discount,
        'total_items': items.count(),
        'progress_percentage': progress_percentage,
    }
    return render(request, "cart.html", context)


@login_required
def add_to_cart(request, product_id):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    product = get_object_or_404(Product, id=product_id)

    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += 1
        item.save()
    
    messages.success(request, f"{product.name} added to cart!")

    return redirect("cart")


@login_required
def checkout_view(request):
    cart = Cart.objects.get(user=request.user)
    items = CartItem.objects.filter(cart=cart)

    if not items:
        messages.warning(request, "Your cart is empty!")
        return redirect("products")

    total = sum(i.total_price for i in items)

    return render(request, "checkout.html", {
        "cart_items": items,
        "total": total
    })


# ===== FIXED PROCESS CHECKOUT WITH PROPER DECIMAL HANDLING =====
@login_required
def process_checkout(request):
    cart = Cart.objects.get(user=request.user)
    items = CartItem.objects.filter(cart=cart)

    if not items:
        messages.warning(request, "Your cart is empty!")
        return redirect("products")

    # Calculate totals using Decimal to avoid type errors
    subtotal = Decimal('0.00')
    for item in items:
        subtotal += Decimal(str(item.total_price))
    
    # Default shipping cost as Decimal
    shipping_cost = Decimal('10.00')
    
    # Get shipping method from POST to adjust shipping cost
    if request.method == "POST":
        shipping_method = request.POST.get('shipping_method', 'standard')
        if shipping_method == 'express':
            shipping_cost = Decimal('20.00')
        elif shipping_method == 'standard':
            shipping_cost = Decimal('10.00')
    
    tax = Decimal('0.00')
    total = subtotal + shipping_cost + tax

    # Get user profile
    profile = UserProfile.objects.get(user=request.user)
    
    # DEBUG: Print all POST data to see what's being submitted
    print("=" * 50)
    print("CHECKOUT FORM DATA RECEIVED:")
    print("=" * 50)
    for key, value in request.POST.items():
        print(f"{key}: {value}")
    print("=" * 50)
    
    # Get shipping information from POST data (from checkout form)
    if request.method == "POST":
        full_name = request.POST.get('full_name') or request.POST.get('fullname') or request.POST.get('name') or request.user.get_full_name() or request.user.username
        email = request.POST.get('email') or request.user.email
        phone = request.POST.get('phone') or request.POST.get('phone_number') or request.POST.get('phonenumber') or profile.phone_number or "N/A"
        address = request.POST.get('address') or request.POST.get('address_line1') or request.POST.get('shipping_address') or profile.address or "Not provided"
        city = request.POST.get('city') or request.POST.get('shipping_city') or "Not provided"
        state = request.POST.get('state') or request.POST.get('shipping_state') or "Not provided"
        zip_code = request.POST.get('zip_code') or request.POST.get('zip') or request.POST.get('postal_code') or request.POST.get('postal') or "00000"
        country = request.POST.get('country') or request.POST.get('shipping_country') or "United States"
        payment_method = request.POST.get('payment_method', 'card')
        
        # DEBUG: Print the values we're using
        print("\nVALUES BEING SAVED TO ORDER:")
        print(f"Full Name: {full_name}")
        print(f"Email: {email}")
        print(f"Phone: {phone}")
        print(f"Address: {address}")
        print(f"City: {city}")
        print(f"State: {state}")
        print(f"ZIP: {zip_code}")
        print(f"Country: {country}")
        print(f"Shipping Method: {shipping_method}")
        print(f"Payment Method: {payment_method}")
        print(f"Subtotal: ${subtotal}")
        print(f"Shipping: ${shipping_cost}")
        print(f"Total: ${total}")
        print("=" * 50)
    else:
        # If no POST data (direct access), use profile information
        full_name = request.user.get_full_name() or request.user.username
        email = request.user.email
        phone = profile.phone_number or "N/A"
        address = profile.address or "Not provided"
        city = "Not provided"
        state = "Not provided"
        zip_code = "00000"
        country = "United States"
        payment_method = "card"

    # Create shipping address with real user information
    shipping_address = ShippingAddress.objects.create(
        user=request.user,
        full_name=full_name,
        phone_number=phone,
        address_line1=address,
        address_line2="",
        city=city,
        state=state,
        postal_code=zip_code,
        country=country,
        is_default=True  # Set as default for future orders
    )

    # Create order with AUTO-GENERATED ORDER NUMBER
    order = Order.objects.create(
        user=request.user,
        total_amount=subtotal,
        shipping_cost=shipping_cost,
        status="pending",
        shipping_address=shipping_address
    )

    # Create order items
    for item in items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=Decimal(str(item.product.price))  # Ensure price is Decimal
        )

    # Clear cart
    items.delete()

    # FIX: Check if shipment already exists before creating
    try:
        # Try to get existing shipment
        shipment = order.shipment
        print(f"Shipment already exists for order {order.id}")
    except Shipment.DoesNotExist:
        # Create shipment for the order (auto-generates tracking number)
        shipment = Shipment.objects.create(
            order=order,
            shipping_method=None,  # Will be updated later
            shipping_address=shipping_address,
            status=Shipment.ShipmentStatus.PENDING,
            estimated_delivery=timezone.now() + timedelta(days=5)  # Estimate 5 days delivery
        )
        print(f"Created new shipment for order {order.id}")

        # Create initial tracking event
        TrackingEvent.objects.create(
            shipment=shipment,
            event_type="Order Placed",
            location="Online Store",
            description="Your order has been placed successfully and is awaiting confirmation."
        )

    # Store in session for payment and success page
    request.session["checkout_order_id"] = order.id
    
    # SUCCESS MESSAGE WITH ORDER NUMBER
    messages.success(request, f"Order #{order.order_number} created successfully! You can track your order anytime.")
    
    # Send order confirmation email (optional)
    try:
        send_order_confirmation_email(order, request)
    except Exception as e:
        print(f"Email sending failed: {e}")  # For debugging
        pass  # Email sending failed, but order is still created

    # Redirect to Flutterwave payment page with order details
    # Update this URL to match your payment app's URL pattern
    from django.urls import reverse
    payment_url = f"/payment/?amount={total}&name={full_name}&email={email}&phone={phone}&address={address}"
    return redirect(payment_url)


# ===== DEBUG VIEW TO CHECK ORDER DATA =====
@login_required
def debug_order_data(request, order_id):
    """
    Debug view to check what data is stored in an order
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Order Debug Info</title>
        <style>
            body {{ font-family: Arial; padding: 20px; background: #111; color: #fff; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            .card {{ background: #1a1a1a; border: 1px solid #333; border-radius: 10px; padding: 20px; margin-bottom: 20px; }}
            h1 {{ color: #F68B1E; }}
            h2 {{ color: #F68B1E; margin-top: 0; }}
            .label {{ color: #9ca3af; font-weight: bold; }}
            .value {{ color: #fff; margin-bottom: 10px; }}
            .success {{ color: #28a745; }}
            .warning {{ color: #ffc107; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 Order Debug Information</h1>
            
            <div class="card">
                <h2>📦 Order: {order.order_number}</h2>
                <p><span class="label">Order ID:</span> <span class="value">{order.id}</span></p>
                <p><span class="label">Status:</span> <span class="value">{order.status}</span></p>
                <p><span class="label">Created:</span> <span class="value">{order.created_at}</span></p>
                <p><span class="label">Total:</span> <span class="value">${order.grand_total}</span></p>
            </div>
            
            <div class="card">
                <h2>📋 Shipping Address</h2>
                <p><span class="label">Full Name:</span> <span class="value">{order.shipping_address.full_name}</span></p>
                <p><span class="label">Phone:</span> <span class="value">{order.shipping_address.phone_number}</span></p>
                <p><span class="label">Address:</span> <span class="value">{order.shipping_address.address_line1}</span></p>
                <p><span class="label">City:</span> <span class="value">{order.shipping_address.city}</span></p>
                <p><span class="label">State:</span> <span class="value">{order.shipping_address.state}</span></p>
                <p><span class="label">ZIP Code:</span> <span class="value">{order.shipping_address.postal_code}</span></p>
                <p><span class="label">Country:</span> <span class="value">{order.shipping_address.country}</span></p>
            </div>
            
            <div class="card">
                <h2>🛒 Order Items</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="color: #F68B1E; border-bottom: 1px solid #333;">
                        <th style="text-align: left; padding: 10px;">Product</th>
                        <th style="text-align: center; padding: 10px;">Qty</th>
                        <th style="text-align: right; padding: 10px;">Price</th>
                    </tr>
    """
    
    for item in order.items.all():
        html += f"""
                    <tr style="border-bottom: 1px solid #333;">
                        <td style="padding: 10px;">{item.product.name}</td>
                        <td style="text-align: center; padding: 10px;">{item.quantity}</td>
                        <td style="text-align: right; padding: 10px;">${item.price}</td>
                    </tr>
        """
    
    html += f"""
                </table>
            </div>
            
            <div class="card">
                <h2>🚚 Shipment Info</h2>
    """
    
    try:
        shipment = order.shipment
        html += f"""
                <p><span class="label">Tracking Number:</span> <span class="value">{shipment.tracking_number}</span></p>
                <p><span class="label">Shipment Status:</span> <span class="value">{shipment.status}</span></p>
                <p><span class="label">Estimated Delivery:</span> <span class="value">{shipment.estimated_delivery}</span></p>
        """
    except:
        html += f"""<p><span class="warning">No shipment info available</span></p>"""
    
    html += f"""
            </div>
            
            <div class="card">
                <a href="/order/success/{order.id}/" style="background: #F68B1E; color: #000; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px;">View Order Success Page</a>
                <a href="/track-order/?order={order.order_number}" style="background: #333; color: #fff; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Track This Order</a>
            </div>
        </div>
    </body>
    </html>
    """
    
    from django.http import HttpResponse
    return HttpResponse(html)


# ===== FIXED ORDER SUCCESS PAGE - MORE ROBUST VERSION =====
@login_required
def order_success(request, order_id):
    """
    Display order success page with improved error handling
    """
    # First try to get the order by ID from the URL
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        # If not found by ID, try to get from session
        session_order_id = request.session.get('checkout_order_id')
        
        if session_order_id:
            try:
                order = Order.objects.get(id=session_order_id, user=request.user)
            except Order.DoesNotExist:
                # Try to find any recent order for this user
                recent_order = Order.objects.filter(user=request.user).order_by('-created_at').first()
                if recent_order:
                    order = recent_order
                else:
                    messages.error(request, "No orders found. Please place an order first.")
                    return redirect('products')
        else:
            # Try to find any recent order for this user
            recent_order = Order.objects.filter(user=request.user).order_by('-created_at').first()
            if recent_order:
                order = recent_order
            else:
                messages.error(request, "No orders found. Please place an order first.")
                return redirect('products')
    
    # Get shipment info
    try:
        shipment = order.shipment
    except Shipment.DoesNotExist:
        shipment = None
    
    context = {
        'order': order,
        'shipment': shipment,
        'tracking_url': request.build_absolute_uri(f"/track-order/?order={order.order_number}")
    }
    
    return render(request, "order_success.html", context)


def settings_view(request):
    return render(request, "settings.html")


def deals_view(request):
    return render(request, "deals.html")


def new_arrivals_view(request):
    return render(request, "new_arrivals.html")


def about_view(request):
    return render(request, "about.html")


def contact_view(request):
    return render(request, "contact.html")


@login_required
def orders_view(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, "orders.html", {"orders": orders})


# ===== CART EXTRA =====

@login_required
def update_cart_item(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    qty = int(request.POST.get("quantity", 1))
    if qty > 0:
        item.quantity = qty
        item.save()
        messages.success(request, "Cart updated!")
    return redirect("cart")


@login_required
def remove_from_cart(request, item_id):
    CartItem.objects.filter(id=item_id, cart__user=request.user).delete()
    messages.success(request, "Item removed from cart!")
    return redirect("cart")


@login_required
def clear_cart(request):
    CartItem.objects.filter(cart__user=request.user).delete()
    messages.success(request, "Cart cleared!")
    return redirect("cart")


# ===== WISHLIST =====

@login_required
def wishlist_view(request):
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    items = WishlistItem.objects.filter(wishlist=wishlist)

    return render(request, "wishlist.html", {
        "wishlist": wishlist,
        "items": items
    })


@login_required
def add_to_wishlist(request, product_id):
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    product = get_object_or_404(Product, id=product_id)

    _, created = WishlistItem.objects.get_or_create(
        wishlist=wishlist,
        product=product
    )
    
    if created:
        messages.success(request, f"{product.name} added to wishlist!")
    else:
        messages.info(request, f"{product.name} is already in your wishlist!")

    return redirect(request.META.get("HTTP_REFERER", "wishlist"))


@login_required
def remove_from_wishlist(request, product_id):
    wishlist = Wishlist.objects.get(user=request.user)

    WishlistItem.objects.filter(
        wishlist=wishlist,
        product_id=product_id
    ).delete()
    
    messages.success(request, "Item removed from wishlist!")

    return redirect("wishlist")


@login_required
def clear_wishlist(request):
    wishlist = Wishlist.objects.get(user=request.user)
    WishlistItem.objects.filter(wishlist=wishlist).delete()
    messages.success(request, "Wishlist cleared!")
    return redirect("wishlist")


# ===== ORDER TRACKING =====

def track_order(request):
    """
    Page to enter tracking number or order number
    """
    # Pre-fill from URL query parameter
    initial_order = request.GET.get('order', '')
    
    if request.method == 'POST':
        tracking_input = request.POST.get('tracking_number', '').strip()
        
        # Try to find order by tracking number
        try:
            # First try to find by tracking number in Shipment
            shipment = Shipment.objects.get(tracking_number=tracking_input)
            order = shipment.order
            return redirect('order_tracking_details', order_number=order.order_number)
        except Shipment.DoesNotExist:
            try:
                # Then try to find by order number
                order = Order.objects.get(order_number=tracking_input)
                return redirect('order_tracking_details', order_number=order.order_number)
            except Order.DoesNotExist:
                messages.error(request, 'Order not found. Please check your tracking/order number.')
                return redirect('track_order')
    
    return render(request, 'track_order.html', {'initial_order': initial_order})


def order_tracking_details(request, order_number):
    """
    Display detailed tracking information for an order
    """
    order = get_object_or_404(Order, order_number=order_number)
    
    # Check if user is authorized to view this order
    is_authorized = False
    
    if request.user.is_authenticated and request.user == order.user:
        # Authenticated user viewing their own order
        is_authorized = True
    elif request.session.get('guest_order') == order_number:
        # Guest user with session tracking
        is_authorized = True
    else:
        # For now, allow viewing with order number (you can make this stricter)
        is_authorized = True
    
    if not is_authorized:
        messages.error(request, 'Please use the tracking form to view your order.')
        return redirect('track_order')
    
    # Get shipment and tracking events
    try:
        shipment = order.shipment
        tracking_events = shipment.tracking_events.all()
    except Shipment.DoesNotExist:
        shipment = None
        tracking_events = []
    
    # Calculate progress percentage for tracking bar
    progress_map = {
        'pending': 10,
        'processing': 25,
        'shipped': 50,
        'in_transit': 65,
        'out_for_delivery': 85,
        'delivered': 100,
        'cancelled': 100,
    }
    
    if shipment:
        progress_percentage = progress_map.get(shipment.status, 0)
        current_status = shipment.get_status_display()
    else:
        progress_percentage = progress_map.get(order.status, 0)
        current_status = order.get_status_display()
    
    context = {
        'order': order,
        'shipment': shipment,
        'tracking_events': tracking_events,
        'progress_percentage': progress_percentage,
        'current_status': current_status,
    }
    
    return render(request, 'order_tracking_details.html', context)


@login_required
def track_my_order(request, order_number):
    """
    API endpoint for authenticated users to track orders
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    try:
        shipment = order.shipment
        tracking_events = shipment.tracking_events.all()
        
        tracking_data = {
            'order_number': order.order_number,
            'order_status': order.status,
            'order_status_display': order.get_status_display(),
            'tracking_number': shipment.tracking_number,
            'shipment_status': shipment.status,
            'shipment_status_display': shipment.get_status_display(),
            'estimated_delivery': shipment.estimated_delivery.strftime('%Y-%m-%d %H:%M') if shipment.estimated_delivery else None,
            'actual_delivery': shipment.actual_delivery.strftime('%Y-%m-%d %H:%M') if shipment.actual_delivery else None,
            'updates': [
                {
                    'event_type': event.event_type,
                    'location': event.location,
                    'description': event.description,
                    'timestamp': event.event_time.strftime('%Y-%m-%d %H:%M')
                }
                for event in tracking_events
            ]
        }
    except Shipment.DoesNotExist:
        tracking_data = {
            'order_number': order.order_number,
            'order_status': order.status,
            'order_status_display': order.get_status_display(),
            'tracking_number': None,
            'shipment_status': None,
            'updates': []
        }
    
    return JsonResponse(tracking_data)


# Helper function to create tracking events (for admin use)
@login_required
def add_tracking_event(request, shipment_id):
    """
    Add a tracking event to a shipment (admin/staff only)
    """
    if not request.user.is_staff:
        messages.error(request, 'Unauthorized access')
        return redirect('home')
    
    if request.method == 'POST':
        shipment = get_object_or_404(Shipment, id=shipment_id)
        
        event_type = request.POST.get('event_type')
        location = request.POST.get('location', '')
        description = request.POST.get('description')
        
        TrackingEvent.objects.create(
            shipment=shipment,
            event_type=event_type,
            location=location,
            description=description
        )
        
        # Update shipment status if provided
        new_status = request.POST.get('status')
        if new_status and new_status in dict(Shipment.ShipmentStatus.choices):
            shipment.status = new_status
            shipment.save()
        
        messages.success(request, 'Tracking event added successfully!')
        
        return redirect('order_tracking_details', order_number=shipment.order.order_number)
    
    return redirect('home')


# ===== HELPER FUNCTIONS =====

def send_order_confirmation_email(order, request):
    """
    Send order confirmation email with tracking info
    """
    subject = f"Order Confirmation - #{order.order_number}"
    
    # Get shipment info
    try:
        shipment = order.shipment
        tracking_number = shipment.tracking_number
    except:
        tracking_number = "Not available yet"
    
    context = {
        'order': order,
        'tracking_number': tracking_number,
        'tracking_url': request.build_absolute_uri(f"/track-order/?order={order.order_number}"),
        'domain': request.get_host(),
    }
    
    html_message = render_to_string('emails/order_confirmation.html', context)
    
    send_mail(
        subject,
        f"Your order #{order.order_number} has been confirmed.",
        settings.DEFAULT_FROM_EMAIL,
        [order.user.email],
        html_message=html_message,
        fail_silently=True,
    )


# ===== TEMPORARY DEBUG VIEW (Optional - Remove after fixing) =====
@login_required
def debug_orders(request):
    """
    Debug view to see all orders - REMOVE AFTER FIXING
    """
    orders = Order.objects.filter(user=request.user)
    html = "<h1>Your Orders</h1>"
    
    if orders:
        for order in orders:
            html += f"""
            <div style="margin: 20px; padding: 15px; border: 1px solid #ccc;">
                <p><strong>Order ID:</strong> {order.id}</p>
                <p><strong>Order Number:</strong> {order.order_number}</p>
                <p><strong>Status:</strong> {order.status}</p>
                <p><strong>Total:</strong> ${order.grand_total}</p>
                <p><a href="/order/success/{order.id}/">View Order {order.id}</a></p>
                <p><a href="/debug-order/{order.id}/">Debug This Order</a></p>
            </div>
            """
    else:
        html += "<p>No orders found.</p>"
    
    html += "<h2>Session Data</h2>"
    html += f"<p>checkout_order_id: {request.session.get('checkout_order_id', 'Not set')}</p>"
    
    from django.http import HttpResponse
    return HttpResponse(html)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from .models import Product, Category

# PAGE VIEWS

def browse(request):
    products = Product.objects.filter(is_available=True).select_related('category', 'producer')
    categories = Category.objects.filter(is_active=True)

    category_slug = request.GET.get('category')
    search = request.GET.get('search', '').strip()

    if category_slug:
        products = products.filter(category__slug=category_slug)
    if search:
        products = products.filter(name__icontains=search)

    return render(request, 'marketplace/browse.html', {
        'products': products,
        'categories': categories,
        'search': search,
        'selected_category': category_slug,
    })


def producers(request):
    from accounts.models import CustomUser
    producer_ids = Product.objects.values_list('producer', flat=True).distinct()
    producers_qs = CustomUser.objects.filter(id__in=producer_ids, role='producer')
    return render(request, 'marketplace/producers.html', {'producers': producers_qs})


def product_detail(request, product_id):
    """Product detail page - displays detailed information about a single product."""
    pass


@login_required
def add_product(request):
    """Add new product page - allows producers to add new products."""
    pass


@login_required
def edit_product(request, product_id):
    """Change product information page - allows producers to update their products."""
    pass


@login_required
def place_order(request):
    """Place order page - processes customer order from basket."""
    pass


# HELPER FUNCTIONS

@login_required
def add_to_basket(request, product_id):
    """Helper function - adds a product to user's shopping basket."""
    pass


@login_required
def cancel_order(request, order_id):
    """Helper function - cancels an existing order."""
    pass


def calculate_food_miles(origin, destination):
    """Helper function - calculates distance between producer and customer."""
    pass


def record_audit(action, user, details):
    """Helper function - records audit trail for important actions."""
    pass


def calculate_commission(order_total, user_role):
    """Helper function - calculates platform commission based on order and user type."""
    pass


def send_payment_request(order, payment_processor):
    """Helper function - sends payment request to external payment processor."""
    pass


def update_inventory(product_id, quantity_change):
    """Helper function - updates product stock levels."""
    pass


def generate_report(report_type, filters):
    """Helper function - generates various reports (sales, inventory, etc.)."""
    pass

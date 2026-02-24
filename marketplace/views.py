from django.shortcuts import render
from marketplace.models import Product, Category


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

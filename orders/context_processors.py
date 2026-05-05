from .models import Cart

# Roles that can have an active shopping cart.
# Producers and admins do not buy through the marketplace, so they are excluded.
BUYER_ROLES = (None, 'customer', 'community_group', 'restaurant')


def cart_context(request):
    """
    Global context processor to attach the total cart item count
    to every template rendering for any authenticated buyer role
    (customer, community group, or restaurant).
    """
    if request.user.is_authenticated and getattr(request.user, 'role', None) in BUYER_ROLES:
        cart = Cart.objects.filter(user=request.user, status=Cart.STATUS_ACTIVE).first()
        if cart:
            # Sum up actual quantity of all items, not just distinct products
            count = sum(item.quantity for item in cart.items.all())
            return {'cart_item_count': count}
    return {'cart_item_count': 0}

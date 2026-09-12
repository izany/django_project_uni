from mainapp.models import Category, CartItem
from mainapp.views import get_cart
from django.urls import resolve
from store.settings import PHONE_NUMBER

def base_context(request):
    # preprocessing
    if request.user.is_anonymous and not request.session.session_key:
        request.session.create()

    # page name
    try:
        match = resolve(request.path_info)
        page = match.url_name or ''
    except Exception as e:
        page = ''

    # context
    context = {
        "phone": PHONE_NUMBER,
        "category": [i[1] for i in Category.objects.values_list()],
        "is_authenticated": request.user.is_authenticated,
        "page": page.replace('_', ' ').title() or "Home",
    }

    # cart
    try:
        cart = get_cart(request)
        context["cart_total"] = cart.cart_total
        context["cart_total_count"] = cart.cart_total_count

        cart_items = dict()
        for i in CartItem.objects.filter(cart=cart):
            if i.item.id in cart_items:
                cart_items[i.item.id]["count"] += 1
            else:
                cart_items[i.item.id] = {
                    "id": str(i.item.id),
                    "count": 1,
                    "name": i.item.name,
                    "image": i.item.image,
                    "price": i.item.price - i.item.price * i.item.discount / 100,
                }
        context["cart_items"] = list(cart_items.values())
    except Exception as e:
        context["cart_total"] = 0
        context["cart_total_count"] = 0
        context["cart_items"] = []

    return context



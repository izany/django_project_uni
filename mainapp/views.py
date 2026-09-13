from django.http import HttpResponse
from django.template import loader
from .models import Cart, Category, CartItem, Item, Review, Profile, Order, OrderItem, AboutUsText, ClientSays, IndexSlider, TermsOfService, FAQ, SiteInformation
from django.contrib.sessions.models import Session
from django.contrib.auth import authenticate, logout
from django.contrib.auth import login as django_login
from django.shortcuts import redirect
from django.utils.datastructures import MultiValueDictKeyError
from .forms import RegisterForm, LoginForm, CommentForm, ImageForm
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import update_session_auth_hash
from mainapp.utils import standardize_image
from helpdesk.models import Queue, Ticket, FollowUp
from django.core.mail import send_mail
from django.conf import settings


class NotEnoughStock(Exception):
    pass


def get_cart(request):
    # via user
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user)
        # create cart if none exists
        if cart.count() == 0:
            cart = Cart(user=request.user, cart_total=0.0, cart_total_count=0)
            cart.save()
        else:
            cart = cart.first()
    # anonymous via session
    else:
        cart = Cart.objects.filter(session_id=request.session.session_key)
        # create cart if none exists
        if cart.count() == 0:
            cart = Cart(session=Session.objects.filter(session_key=request.session.session_key).first(),
                        cart_total=0.0, cart_total_count=0)
            cart.save()
        else:
            cart = cart.first()

    return cart


def add_to_cart(item, cart, count):
    count = int(count)
    if CartItem.objects.filter(cart=cart, item=item).count() + count > item.stock:
        raise NotEnoughStock
    cart.cart_total_count += count
    price = (item.price - item.price * item.discount / 100) * count
    cart.cart_total += price
    for i in range(count):
        CartItem(cart=cart, item=item).save()
    cart.save()
    return


def remove_from_cart_(request, product_id):
    cart = get_cart(request)
    item = Item.objects.filter(id=product_id).first()
    CartItem.objects.filter(cart=cart, item=item).first().delete()
    cart.cart_total -= item.price - item.price * item.discount / 100
    cart.cart_total_count -= 1
    cart.save()
    return

# deprecated
def base_old(func):
    def wrapper(request, **kwargs):

        context = dict()
        #context["page"] = str(func.__name__)
        context['page'] = str(func.__name__).replace('_', ' ').title()
        context["phone"] = "00989150001516"
        context["category"] = [i[1] for i in Category.objects.values_list()]
        context["is_authenticated"] = request.user.is_authenticated

        # main func
        res_func, template, context, request = func(request, context, kwargs)

        # postprocessing
        cart = get_cart(request)
        context["cart_total"] = cart.cart_total
        context["cart_total_count"] = cart.cart_total_count

        # left cart menu
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
                    "price": i.item.price - i.item.price * i.item.discount / 100
                }
        context["cart_items"] = list()
        for i in cart_items.values():
            context["cart_items"].append(i)

        # return
        if res_func == HttpResponse:
            return HttpResponse(template.render(context, request))
        elif res_func == redirect:
            return redirect(template)

    return wrapper

# should be removed fully
def base(func):
    def wrapper(request, *args, **kwargs):

        context = dict()
        # main func
        res_func, template, context, request, *rest = func(request, context, kwargs, *args)
        status = rest[0] if rest else 200

        # return
        if res_func == HttpResponse:
            return HttpResponse(template.render(context, request), status=status)
        elif res_func == redirect:
            return redirect(template)
        return None

    return wrapper


@base
def remove_from_cart(request, context: dict, kwargs):
    product_id = kwargs["product_id"]
    cart = get_cart(request)
    item = Item.objects.filter(id=product_id).first()
    for entity in CartItem.objects.filter(cart=cart, item=item):
        remove_from_cart_(request, product_id)
    return redirect, request.META["HTTP_REFERER"], context, request


@base
def login(request, context: dict, kwargs):
    if request.user.is_authenticated:
        return redirect, "index", context, request
    template = loader.get_template('login.html')
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if not form.cleaned_data.get('remember_me'):
                    request.session.set_expiry(0)
                    request.session.modified = True
                django_login(request, user)
                return redirect, "index", context, request

        context["form"] = LoginForm()
        context["invalid_credentials"] = True
        return HttpResponse, template, context, request

    context["form"] = LoginForm()
    return HttpResponse, template, context, request


@base
def logout(request, context: dict, kwargs):
    if not request.user.is_authenticated:
        return redirect, "index", context, request

    cart = Cart.objects.filter(user=request.user).first()
    cartitems = CartItem.objects.filter(cart=cart)
    new_cart = Cart(user=None, session=None, cart_total=cart.cart_total, cart_total_count=cart.cart_total_count)
    for i in cartitems:
        CartItem(cart=new_cart, item=i.item)

    logout(request)

    request.session.create()
    new_cart.session = Session.objects.filter(session_key=request.session.session_key).first()
    new_cart.save()

    return redirect, request.META["HTTP_REFERER"], context, request


@base
def contact(request, context: dict, kwargs):
    template = loader.get_template('contact.html')
    opening_hours = SiteInformation.objects.filter(field="opening_hours").first()
    context["opening_hours"] = opening_hours.text if opening_hours else ''

    # ticket system
    available_queues = Queue.objects.filter(allow_public_submission=True)
    context['available_queues'] = available_queues
    context['prefill_email'] = request.user.email if request.user.is_authenticated else ''

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        body = request.POST.get('message', '').strip()
        priority = request.POST.get('priority', '3')
        queue_id = request.POST.get('queue')

        # validation
        if not email or not subject or not body or not queue_id:
            context['error'] = 'Email, subject, message, and queue are all required.'
        else:
            try:
                priority = int(priority)
                if priority not in (1, 2, 3, 4, 5):
                    priority = 3
            except (TypeError, ValueError):
                priority = 3

            queue = available_queues.filter(pk=queue_id).first()
            if not queue:
                context['error'] = 'Invalid queue selected.'
            else:
                # create the ticket
                ticket = Ticket.objects.create(
                    title=subject,
                    queue=queue,
                    submitter_email=email,
                    status=Ticket.OPEN_STATUS,
                    priority=priority,
                )

                FollowUp.objects.create(
                    ticket=ticket,
                    user=request.user if request.user.is_authenticated else None,
                    title='',
                    comment=body,
                    public=True,
                )

                context['submitted'] = True
                context['ticket_id'] = ticket.id

    return HttpResponse, template, context, request


@base
def about_us(request, context: dict, kwargs):
    template = loader.get_template('about.html')
    aboutustext = SiteInformation.objects.filter(field="about_us").first()
    context["aboutustext"] = aboutustext.text if aboutustext else ''
    context["clientsays"] = ClientSays.objects.all()
    #for i in context["clientsays"]:
    #    i.image = i.image

    return HttpResponse, template, context, request

@base
def faq(request, context: dict, kwargs):
    template = loader.get_template('faq.html')
    context["questions"] = FAQ.objects.all().order_by("priority")

    return HttpResponse, template, context, request

@base
def terms_of_service(request, context: dict, kwargs):
    template = loader.get_template('terms.html')
    termsofservicetext = SiteInformation.objects.filter(field="terms_of_service").first()
    context["termsofservicetext"] = termsofservicetext.text if termsofservicetext else ''

    return HttpResponse, template, context, request


@base
def register(request, context: dict, kwargs):
    if request.user.is_authenticated:
        return redirect, "index", context, request
    template = loader.get_template('register.html')

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password1")
            user = authenticate(request, username=username, password=password)
            django_login(request, user)

            # profile_creation
            profile = Profile(user=user)
            profile.save()

            return redirect, "index", context, request

        else:
            context["form"] = RegisterForm()
            context["error_form"] = form.errors
            return HttpResponse, template, context, request

    else:

        context["form"] = RegisterForm()
        return HttpResponse, template, context, request


@base
def product(request, context: dict, kwargs):
    product_id = kwargs["product_id"]
    template = loader.get_template('product-details.html')
    item = Item.objects.filter(id=product_id).first()
    if not item:
        return redirect, "error_404", context, request
    item.image = item.image
    if item.discount != 0:
        item.final_price = item.price - item.price * item.discount / 100
    item.category_name = item.category.name

    context["product"] = item
    context["product"].rating_full = range(item.rating)
    context["product"].rating_empty = range(5 - item.rating)

    # new comment & add to cart
    submit_comment_form = CommentForm()
    context["submit_comment_form"] = submit_comment_form

    if request.method == "POST":
        # add to cart
        if request.POST["form_number"] == "1":
            count = request.POST["cart_input_count"]
            cart = get_cart(request)
            try:
                add_to_cart(item, cart, count)
            except NotEnoughStock:
                context["not_enough_stock"] = True

        # new comment
        if request.POST["form_number"] == "2":
            form = CommentForm(request.POST)
            if form.is_valid():
                comment = Review(user=request.user, item=Item.objects.filter(id=product_id).first(), rating=form["rating"].value(), comment=form["body"].value())
                comment.save()
                iit = Item.objects.filter(id=product_id).first()
                iit.total_reviews += 1
                x = Review.objects.filter(item=iit)
                ss = 0
                cc = 0
                for j in x:
                    cc += 1
                    ss += j.rating
                ss = ss/cc
                iit.rating = round(ss)
                iit.save()
                context["open_comments"] = True

    # load comments
    comments = list()
    reviews = Review.objects.filter(item=Item.objects.filter(id=product_id).first(), flag=False).order_by("c_date")
    for i in reviews:
        comments.append({
            "user_image": Profile.objects.filter(user=i.user).first().image,
            "user_username": i.user.username,
            "content": i.comment,
            "c_date": i.c_date,
            "rating_empty": range(5 - i.rating),
            "rating_full": range(i.rating)
        })
    context["comments"] = comments

    return HttpResponse, template, context, request


@base
def account(request, context: dict, kwargs):
    if not request.user.is_authenticated:
        return redirect, "index", context, request
    template = loader.get_template('account.html')

    if request.method == "POST":
        context["open_account"] = True
        form = ImageForm(request.POST, request.FILES)
        #profile = Profile.objects.filter(user=request.user).first()
        profile, _ = Profile.objects.get_or_create(user=request.user)
        #breakpoint()

        image = request.FILES.get("image")
        if image:
            profile.image = standardize_image(image, size=(300, 300), fmt='JPEG')
            #profile.image = image
            profile.save()
        if request.POST.get("ltn_Address_1"):
            profile.address_1 = request.POST["ltn_Address_1"]
        if request.POST.get("ltn_Address_2"):
            profile.address_2 = request.POST["ltn_Address_2"]
        if request.POST.get("ltn_city"):
            profile.city = request.POST["ltn_city"]
        if request.POST.get("ltn_state"):
            profile.state = request.POST["ltn_state"]
        if request.POST.get("ltn_zip"):
            try:
                profile.zip = int(request.POST["ltn_zip"])
            except ValueError:
                context["invalid_zip"] = True
        profile.save()
        if request.POST.get("ltn_first_name"):
            request.user.first_name = request.POST["ltn_first_name"]
        if request.POST.get("ltn_last_name"):
            request.user.last_name = request.POST["ltn_last_name"]
        request.user.save()

        # deprecated
        '''
        if request.POST.get("ltn_new_password"):
            if authenticate(request, username=request.user.username, password=request.POST["ltn_current_password"]) is not None:
                if request.POST["ltn_new_password"] == request.POST["ltn_confirm_new_password"]:
                    try:
                        validate_password(request.POST["ltn_new_password"], user=request.user)
                    except ValidationError as e:
                        context["invalid_password"] = True
                        context["password_errors"] = e.messages  # list of error strings
                    else:
                        request.user.set_password(request.POST["ltn_new_password"])
                        request.user.save()
                        update_session_auth_hash(request, request.user)
                        context["password_changed"] = True

                else:
                    context["invalid_confirm_password"] = True
            else:
                context["invalid_password"] = True
        if authenticate(request, username=request.user.username, password=request.POST["ltn_new_password"]) is None:
            #context["invalid_password"] = True
            pass
        '''

    context["orders"] = Order.objects.filter(user=request.user)
    profile = Profile.objects.filter(user=request.user).first()
    if profile:
        context["user"] = {
            "address_1": profile.address_1,
            "address_2": profile.address_2,
            "city": profile.city,
            "zip": profile.zip,
            "state": profile.state,
            "image": profile.image
        }
    else:
        context["user"] = {
            "address_1": '',
            "address_2": '',
            "city": '',
            "zip": 0,
            "state": '',
            "image": ''
        }
    context["image_form"] = ImageForm()

    return HttpResponse, template, context, request


# not used
@base
def error_404(request, context: dict, kwargs, exception=None):
    template = loader.get_template('404.html')
    context["page"] = "404"
    return HttpResponse, template, context, request, 404


@base
def home(request, context: dict, kwargs):
    template = loader.get_template('index.html')

    # main slider
    sliders = IndexSlider.objects.all()
    for slider in sliders:
        slider.image = slider.image
    context["sliders"] = sliders

    # new arrivals
    new_products = Item.objects.all().order_by("-c_date")[:8]
    for item in new_products:
        item.image = item.image
        item.final_price = item.price - item.price * item.discount / 100
    context["new_products"] = new_products

    # top products
    top_products = Item.objects.all().order_by("-total_sold")[:20]
    for item in top_products:
        item.image = item.image
        item.final_price = item.price - item.price * item.discount / 100
    context["top_products"] = top_products

    # adding to cart
    if request.method == "POST" and request.POST["form_number"] == "2":
        cart = get_cart(request)
        product = Item.objects.filter(id=request.POST["product_id"]).first()
        try:
            add_to_cart(product, cart, 1)
            del product
        except NotEnoughStock:
            pass

    return HttpResponse, template, context, request


@base
def shop(request, context: dict, kwargs):
    template = loader.get_template('shop-grid.html')
    if "search" in request.GET:
        keywords = str(request.GET["search"])
        context["search_phrase"] = keywords
        keywords = keywords.split(" ")
        items = Item.objects.all()
        for i in keywords:
            items = items.filter(name__icontains=i) | items.filter(tags__icontains=i) | items.filter(category__name__icontains=i) | items.filter(brief__icontains=i)
        context["type_flag"] = "search"

    elif "search_key" in kwargs:
        keywords = str(kwargs["search_key"])
        context["search_phrase"] = keywords
        keywords = keywords.split(" ")
        items = Item.objects.all()
        for i in keywords:
            items = items.filter(name__icontains=i) | items.filter(tags__icontains=i) | items.filter(category__name__icontains=i) | items.filter(brief__icontains=i)
        context["type_flag"] = "search"
    else:
        items = Item.objects.all()
        context["type_flag"] = "default"
    context["sort_type"] = 0

    # adding to cart
    if request.method == "POST":
        if request.POST["form_number"] == "2":
            cart = get_cart(request)
            product = Item.objects.filter(id=request.POST["product_id"]).first()
            try:
                add_to_cart(product, cart, 1)
                del product
            except NotEnoughStock:
                pass
        if request.POST["form_number"] == "1":
            sort_type = int(request.POST.get("sorttype"))
            context["sort_type"] = sort_type
            if sort_type == 0:
                items = items.order_by("id")
            if sort_type == 1:
                items = items.order_by("-total_sold")
            if sort_type == 2:
                items = items.order_by("-c_date")
            if sort_type == 3:
                items = items.order_by("price")
            if sort_type == 4:
                items = items.order_by("-price")

    for i in items:
        i.image = i.image
        i.final_price = i.price - i.price * i.discount / 100

    context["products"] = items

    return HttpResponse, template, context, request


@base
def checkout(request, context: dict, kwargs):
    if not request.user.is_authenticated:
        return redirect, "account_login", context, request

    if request.method == "POST":
        cart = get_cart(request)
        try:
            order = Order(
                user=request.user,
                total=cart.cart_total,
                note=request.POST["note"],
                address_1=request.POST["address_1"],
                address_2=request.POST["address_2"],
                city=request.POST["city"],
                state=request.POST["state"],
                zip=request.POST["zip"],
                first_name=request.POST["first_name"],
                last_name=request.POST["last_name"],
                status=0
            )
            order.save()
        except Exception as e:
            context["invalid_information"] = True
        else:
            cart = get_cart(cart)
            for i in CartItem.objects.filter(cart=cart):
                OrderItem(order=order, item=i.item).save()
                i.item.total_sold += 1
                i.item.stock -= 1
                i.item.save()
            cart.save()
            cart.delete()

    profile = Profile.objects.filter(user=request.user).first()
    context["user"] = profile

    template = loader.get_template('checkout.html')
    return HttpResponse, template, context, request


@base
def recover_password(request, context: dict, kwargs):
    return redirect, "index", context, request


@base
def cart(request, context: dict, kwargs):
    pass


'''def run(request):
    template = "runnnnn"
    for i in User.objects.all():
        if i.username != "zoe":
            profile = Profile(user=i)
            profile.save()

    return HttpResponse(template)'''

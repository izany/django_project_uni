from django.db import models
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from ckeditor.fields import RichTextField
import uuid
from mainapp.utils import standardize_image




def generate_id():
    return uuid.uuid4().hex


class County(models.Model):
    name = models.CharField(max_length=30, null=True)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    address_1 = models.CharField(max_length=80, null=True)
    address_2 = models.CharField(max_length=80, null=True)
    city = models.CharField(max_length=30, null=True)
    state = models.CharField(max_length=30, null=True)
    zip = models.IntegerField(null=True,)
    image = models.ImageField(upload_to="profiles/", default="static/img/product/1.png")

    def __str__(self):
        return self.user.username


class Category(models.Model):
    name = models.CharField(max_length=30, null=True)

    def __str__(self):
        return self.name


class Item(models.Model):
    name = models.CharField(max_length=30)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="product/", default="static/img/product/1.png")
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    tags = models.CharField(max_length=80, null=True)
    description = RichTextField(max_length=10000)
    brief = RichTextField(max_length=2000)
    total_reviews = models.IntegerField(default=0)
    rating_choices = [(0, "0"), (1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5")]
    rating = models.IntegerField(choices=rating_choices, default=0)
    stock = models.IntegerField(default=0)
    discount = models.IntegerField(default=0)
    c_date = models.DateTimeField(auto_now_add=True, editable=False)
    total_sold = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_image = self.image.name if self.image else None

    def save(self, *args, **kwargs):
        image_changed = (
            self.image and self.image.name != self._original_image and hasattr(self.image.file, 'content_type')
        )
        if image_changed:
            self.image = standardize_image(
                self.image.file,
                size=(800, 800),
                fmt='JPEG'
            )
        super().save(*args, **kwargs)
        self._original_image = self.image.name if self.image else None


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    rating_choices = [(0, "0"), (1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5")]
    rating = models.IntegerField(choices=rating_choices)
    comment = RichTextField(null=True)
    c_date = models.DateTimeField(auto_now_add=True, editable=False)
    e_date = models.DateTimeField(auto_now=True)
    flag = models.BooleanField(default=False)
    review_id = models.CharField(unique=True, default=generate_id, max_length=40)

    def __str__(self):
        return self.review_id


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    session = models.OneToOneField(Session, on_delete=models.CASCADE, null=True)
    cart_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    cart_total_count = models.IntegerField(default=0)

    def __str__(self):
        return self.user.username


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)

    def __str__(self):
        return self.cart.user.username


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    order_id = models.CharField(unique=True, default=generate_id, max_length=40)
    c_date = models.DateTimeField(auto_now_add=True, editable=False)
    note = models.TextField(default="", null=True)
    address_1 = models.CharField(max_length=80, null=True, default=None)
    address_2 = models.CharField(max_length=80, null=True, default=None)
    city = models.CharField(max_length=30, null=True, default=None)
    state = models.CharField(max_length=30, null=True, default=None)
    zip = models.IntegerField(null=True, default=None)
    first_name = models.CharField(null=False, max_length=50)
    last_name = models.CharField(null=False, max_length=50)
    status = models.IntegerField(choices=[(0, "Awaiting payment"), (1, "Completed"), (2, "Pending"), (3, "Canceled")], default=0)

    def __str__(self):
        return self.order_id


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)

    def __str__(self):
        return self.order.order_id


class AboutUsText(models.Model):
    text = RichTextField()

class TermsOfService(models.Model):
    text = RichTextField()

class SiteInformation(models.Model):
    field = models.CharField(max_length=300, unique=True)
    text = RichTextField()

    def __str__(self):
        return self.title

class FAQ(models.Model):
    priority = models.IntegerField(unique=True)
    title = models.CharField(max_length=300)
    text = RichTextField()

    def __str__(self):
        return str(self.priority) + " | " + self.title


class ClientSays(models.Model):
    image = image = models.ImageField(upload_to="client_says/", default="static/img/product/1.png")
    name = models.CharField(max_length=30)
    text = RichTextField()


class IndexSlider(models.Model):
    image = image = models.ImageField(upload_to="sslider/", default="static/img/product/1.png")
    title = models.CharField(max_length=30)
    description = models.CharField(max_length=30)
    url = models.CharField(max_length=100)

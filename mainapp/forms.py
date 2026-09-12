from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from ckeditor.widgets import CKEditorWidget
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from .models import Profile
from allauth.account.forms import SignupForm


# deprecated
class RegisterForm(UserCreationForm):
    first_name = forms.CharField(label="", max_length=30, required=True,
                                 widget=forms.TextInput(attrs={'placeholder': 'First Name', 'class': 'form-control'}))
    last_name = forms.CharField(label="", max_length=30, required=True,
                                widget=forms.TextInput(attrs={'placeholder': 'Last Name', 'class': 'form-control'}))
    email = forms.EmailField(label="", max_length=60, required=True,
                             widget=forms.TextInput(attrs={'placeholder': 'Email', 'class': 'form-control'}))
    username = forms.CharField(label="", max_length=30, required=True,
                               widget=forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-control'}))
    password1 = forms.CharField(label="", max_length=30, widget=forms.PasswordInput(
        attrs={'placeholder': 'Password', 'data-toggle': 'password', 'id': 'password'}))
    password2 = forms.CharField(label="", max_length=30, widget=forms.PasswordInput(
        attrs={'placeholder': 'Confirm Password', 'data-toggle': 'password', 'id': 'password'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        first_field = next(iter(self.fields))
        self.fields[first_field].widget.attrs['autofocus'] = True

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2']


# not used
class CustomSignupForm(SignupForm):
    first_name = forms.CharField(max_length=30, label='First name', required=True, widget=forms.TextInput(attrs={'placeholder': 'First name', 'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, label='Last name', required=True, widget=forms.TextInput(attrs={'placeholder': 'Last name', 'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing} form-control'.strip()

    def clean(self):
        cleaned_data = super().clean()
        if not self.data.get('consent'):
            raise forms.ValidationError('You must accept the privacy policy to register.')
        return cleaned_data

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        user.save()
        return user

# old
'''class RegisterForm(forms.Form):
    first_name = forms.CharField(label="", max_length=30, required=False, widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
    last_name = forms.CharField(label="", max_length=30, required=False, widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))
    email = forms.EmailField(label="", max_length=60, widget=forms.TextInput(attrs={'placeholder': 'Email*'}))
    username = forms.CharField(label="", max_length=30, widget=forms.TextInput(attrs={'placeholder': 'Username*'}))
    password = forms.CharField(label="", max_length=30, widget=forms.PasswordInput(attrs={'placeholder': 'Password*'}))
    confirm_password = forms.CharField(label="", max_length=30, widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password*'}))

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).count():
            raise ValidationError("duplicate username")
        else:
            return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).count():
            raise ValidationError("duplicate email")
        else:
            return email

    def clean_password(self):
        if len(self.cleaned_data.get("password")) < 8:
            raise ValidationError("invalid password: too short(8 characters minimum)")

    def clean(self):
        cleaned_data = super(RegisterForm, self).clean()
        if not cleaned_data.get("password") == cleaned_data.get("confirm_password"):
            for i in cleaned_data:
                print(cleaned_data.get(str(i)))
            self.add_error("password", "confirm password field incorrect")'''


class LoginForm(forms.Form):
    username = forms.CharField(label="", max_length=30, widget=forms.TextInput(attrs={'placeholder': 'Username*'}))
    password = forms.CharField(label="", max_length=30, widget=forms.PasswordInput(attrs={'placeholder': 'Password*'}))
    remember_me = forms.BooleanField(required=False)


class CommentForm(forms.Form):
    body = forms.CharField(widget=CKEditorWidget())
    rating_choices = [(0, "0"), (1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5")]
    rating = forms.ChoiceField(choices=rating_choices)


class AboutUsForm(forms.Form):
    body = forms.CharField(widget=CKEditorWidget())


class ImageForm(forms.Form):
    image = forms.ImageField(required=False)


'''class ImageForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["image"]'''


'''class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['user', 'note', 'address_1', 'address_2', 'city', 'state', 'zip', 'first_name', 'last_name']'''


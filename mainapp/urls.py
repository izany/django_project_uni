from django.urls import path, include, re_path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.http import Http404
from django.views.static import serve


def not_found(request, *args, **kwargs):
    raise Http404

urlpatterns = [
    path('', views.home, name='index'),
    path('shop/', views.shop, name='shop'),
    path('shop/<str:search_key>/', views.shop, name='shop'),

    # deprecated
    #path('login/', views.login, name='login'),
    #path('logout/', views.logout, name='logout'),
    #path('register/', views.register, name='register'),

    path('contact/', views.contact, name='contact'),
    path('about_us/', views.about_us, name='about_us'),
    path('terms/', views.terms_of_service, name='terms_of_service'),
    path('recover_password/', views.recover_password, name='recover_password'),

    path('product/<str:product_id>/', views.product, name='product'),
    path('checkout/', views.checkout, name='checkout'),
    path('remove_from_cart/<str:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('account/', views.account, name='account'),
    path('404/', views.error_404, name='error_404'),
    path('faq/', views.faq, name='faq'),

    # allath
    path('accounts/password/set/', not_found),
    path('accounts/reauthenticate/', not_found),

    path('accounts/', include('allauth.urls')),


    # media
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),

    # django-helpdesk
    path('support/', include('helpdesk.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

'''
    # -- allauth --
    # base
    path('accounts/login/', allauth_views.LoginView.as_view(), name='account_login'),
    path('accounts/signup/', allauth_views.SignupView.as_view(), name='account_signup'),
    path('accounts/logout/', allauth_views.LogoutView.as_view(), name='account_logout'),
    # password
    path('accounts/password/change/', allauth_views.PasswordChangeView.as_view(), name='account_change_password'),
    path('accounts/password/reset/', allauth_views.PasswordResetView.as_view(), name='account_reset_password'),
    path('accounts/password/reset/done/', allauth_views.PasswordResetDoneView.as_view(), name='account_reset_password_done'),
    path('accounts/password/reset/key/<str:uidb36>-<str:key>/', allauth_views.PasswordResetFromKeyView.as_view(), name='account_reset_password_from_key'),
    path('accounts/password/reset/key/done/', allauth_views.PasswordResetFromKeyDoneView.as_view(), name='account_reset_password_from_key_done'),
    # email
    path('accounts/confirm-email/', allauth_views.EmailVerificationSentView.as_view(), name='account_email_verification_sent'),
    path('accounts/confirm-email/<str:key>/', allauth_views.ConfirmEmailView.as_view(), name='account_confirm_email'),
    path('accounts/email/', allauth_views.EmailView.as_view(), name='account_email'),
    path('accounts/confirm-email/', allauth_views.EmailVerificationSentView.as_view(), name='account_email_verification_sent'),
    '''

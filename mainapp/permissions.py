from django.shortcuts import redirect


def help_desk_public_view_protector(request):
    if request.user.is_authenticated and request.user.is_staff:
        return None
    return redirect('index')
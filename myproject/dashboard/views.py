from django.shortcuts import render


# Create your views here.
#
def dashboard(request):
    if not request.user.is_anonymous and request.user.has_verified_email:
        return render(request, "dashboard/dashboard_base.html")
    else:
        return render(request, "accounts/sign_in.html")

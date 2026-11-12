from django.http import HttpResponse
from django.urls import path, include
from django.views.decorators.http import require_GET
from kerberos.views.ViewHome import home


@require_GET
def health_check(request):
    return HttpResponse("ok", content_type="text/plain")


urlpatterns = [
    path("accounts/", include("django.contrib.auth.urls")),
    path("healthz/", health_check, name="health_check"),
    path('', home , name='home'),
    path('kerberos/', include('kerberos.urls')),
]

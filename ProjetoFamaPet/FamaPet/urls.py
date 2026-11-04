from django.urls import path, include
from kerberos.views.ViewHome import home

urlpatterns = [
    path("accounts/", include("django.contrib.auth.urls")),
    path('', home , name='home'),
    path('kerberos/', include('kerberos.urls')),
]

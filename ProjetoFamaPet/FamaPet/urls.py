from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('kerberos.urls')),
    path('kerberos/', include('kerberos.urls')),
]

"""backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from users import views
from devices import urls as devices_urls
from users import urls as user_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/protected/', views.HelloView.as_view(), name='hello'),
    path('api/v1/devices/', include(devices_urls), name='devices'),
    path('api/v1/users/', include(user_urls), name='users'),
]

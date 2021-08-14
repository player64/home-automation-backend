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
from rest_framework_simplejwt import views as jwt_views
from devices import urls as devices_urls
from users import urls as user_urls
from devices import views as dash_view
from django.conf.urls.static import static
from django.conf import settings
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/protected/', views.HelloView.as_view(), name='hello'),
    path('api/v1/login/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/logout/', views.ApiLogout.as_view(), name='logout'),
    path('api/v1/token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/password-reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    # path('api/v1/dashboard/', dash_view.DashboardView.as_view(), name='dashboard'),
    # path('api/v1/workspace/<int:pk>/', dash_view.WorkspaceDetail.as_view(), name='workspaces')
    path('api/v1/devices/', include(devices_urls), name='devices'),
    path('api/v1/users/', include(user_urls), name='devices'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

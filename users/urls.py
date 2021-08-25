from django.urls import path, include
from users import views
from rest_framework_simplejwt import views as jwt_views

urlpatterns = [
    path('', views.UserList.as_view()),
    path('detail/<int:pk>/', views.UserDetail.as_view()),
    path('update-password/<int:pk>/', views.ChangePasswordView.as_view()),
    path('login/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('logout/', views.ApiLogout.as_view(), name='logout'),
    path('token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('password-reset/', views.ResetPasswordView.as_view()),
    # comment above and uncomment below if exception happened during resetting the password
    # path('password-reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
]

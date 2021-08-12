from django.urls import path
from users import views

urlpatterns = [
    path('', views.UserList.as_view()),
    path('detail/<int:pk>/', views.UserDetail.as_view()),
    path('update-password/<int:pk>/', views.ChangePasswordView.as_view())
]

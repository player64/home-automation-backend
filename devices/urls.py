from django.conf.urls import url
from django.urls import path

from devices import views

urlpatterns = [
    path('<int:pk>/', views.DeviceDetail.as_view()),
    path('details/', views.DeviceList.as_view()),
    path('dashboard/', views.DashboardView.as_view()),
    path('workspaces/', views.WorkspaceList.as_view()),
    path('workspace/<int:pk>/', views.WorkspaceDetail.as_view())
]

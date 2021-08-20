from django.conf.urls import url
from django.urls import path

from devices import views

urlpatterns = [
    path('<int:pk>/', views.DeviceDetail.as_view()),
    path('details/', views.DeviceList.as_view()),
    path('dashboard/', views.DashboardView.as_view()),
    path('workspaces/', views.WorkspaceList.as_view()),
    path('workspace/<int:pk>/', views.WorkspaceDetail.as_view()),
    path('update-readings/', views.UpdateReadings.as_view()),
    path('device-state/<int:device_id>/', views.UpdateState.as_view()),
    path('single/<int:device_id>/', views.DeviceSingle.as_view()),
    path('event/<int:pk>/', views.DeviceEventDetail.as_view()),
    path('event/', views.DeviceEventCreate.as_view()),
]

from django.conf.urls import url
from django.urls import path

from devices import views

urlpatterns = [
    path('<int:pk>/', views.DeviceDetail.as_view()),
    path('details/', views.DeviceList.as_view()),
    path('dashboard/', views.DashboardView.as_view()),
    path('workspaces/', views.WorkspaceList.as_view()),
    path('workspace/<int:pk>/', views.WorkspaceDetail.as_view()),
    path('eventhub/', views.UpdateReadings.as_view()),
    path('device-state/<int:device_id>/', views.UpdateState.as_view()),
    path('single/<int:device_id>/', views.DeviceSingle.as_view()),
    path('event/<int:pk>/', views.DeviceEventDetail.as_view()),
    path('event/', views.DeviceEventCreate.as_view()),
    path('log/<int:device_id>/', views.DeviceLogByDate.as_view()),
    path('workspace/single/<int:workspace_id>/', views.WorkspaceSingleWithDevices().as_view()),
    path('search/', views.DeviceSearch.as_view()),
    path('readings/<int:device_id>/', views.DeviceReadings.as_view()),
]

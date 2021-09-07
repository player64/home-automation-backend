from django.urls import path
from devices import views
from devices import views_events
from devices import views_workspaces

urlpatterns = [
    path('<int:pk>/', views.DeviceDetail.as_view()),
    path('details/', views.DeviceList.as_view()),
    path('dashboard/', views.DashboardView.as_view()),
    path('workspaces/', views_workspaces.WorkspaceList.as_view()),
    path('workspace/<int:pk>/', views_workspaces.WorkspaceDetail.as_view()),
    path('workspace/single/<int:workspace_id>/', views_workspaces.WorkspaceSingle.as_view()),
    path('eventhub/', views.UpdateReadings.as_view()),
    path('device-state/<int:device_id>/', views.UpdateState.as_view()),
    path('single/<int:device_id>/', views.DeviceSingle.as_view()),
    path('event/<int:pk>/', views_events.DeviceEventDetail.as_view()),
    path('event/', views_events.DeviceEventCreate.as_view()),
    path('events/<int:device_id>/', views_events.EventsDeviceList.as_view()),
    path('log/<int:device_id>/', views.DeviceLogByDate.as_view()),
    path('search/', views.DeviceSearch.as_view()),
    path('readings/<int:device_id>/', views.DeviceReadings.as_view()),
]

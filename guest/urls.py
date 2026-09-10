from django.urls import path
from . import views

urlpatterns = [
    path('', views.guest_chat_view, name='guest_chat'),
    path('api/upload/', views.guest_upload_api, name='guest_upload_api'),
    path('api/send/', views.guest_send_message_api, name='guest_send_message_api'),
    path('end-session/', views.guest_end_session_view, name='guest_end_session'),
]

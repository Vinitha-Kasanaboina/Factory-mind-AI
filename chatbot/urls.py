from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_view, name='chat'),
    path('session/<int:session_id>/', views.chat_view, name='chat_session'),
    path('session/new/', views.new_session_view, name='new_chat_session'),
    path('session/<int:session_id>/delete/', views.delete_session_view, name='delete_chat_session'),
    path('api/send/', views.send_message_api, name='chat_api_send'),
]

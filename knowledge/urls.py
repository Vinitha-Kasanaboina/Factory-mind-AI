from django.urls import path
from . import views

urlpatterns = [
    path('', views.document_list_view, name='document_list'),
    path('upload/', views.document_upload_view, name='document_upload'),
    path('<int:pk>/', views.document_detail_view, name='document_detail'),
    path('<int:pk>/delete/', views.document_delete_view, name='document_delete'),
    path('search/', views.semantic_search_view, name='semantic_search'),
]

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from knowledge.models import Document, DocumentChunk, Category
from chatbot.models import ChatSession
from accounts.models import CustomUser

def landing_view(request):
    """
    Landing page presenting two distinct choices:
    1. Registered Company Mode (Login / Register)
    2. Quick AI Assistant (No Registration Required)
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    return render(request, 'landing.html')


@login_required
def dashboard_index(request):
    total_documents = Document.objects.count()
    total_chunks = DocumentChunk.objects.count()
    total_categories = Category.objects.count()
    total_users = CustomUser.objects.count()

    category_stats = Category.objects.annotate(doc_count=Count('documents')).order_by('-doc_count')
    recent_documents = Document.objects.select_related('category', 'uploaded_by')[:6]
    recent_chat_sessions = ChatSession.objects.filter(user=request.user)[:5]

    context = {
        'total_documents': total_documents,
        'total_chunks': total_chunks,
        'total_categories': total_categories,
        'total_users': total_users,
        'category_stats': category_stats,
        'recent_documents': recent_documents,
        'recent_chat_sessions': recent_chat_sessions,
    }
    return render(request, 'dashboard/index.html', context)

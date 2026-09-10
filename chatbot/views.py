import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import ChatSession, ChatMessage
from .services.rag_engine import generate_rag_response
from knowledge.models import Category

@login_required
def chat_view(request, session_id=None):
    sessions = ChatSession.objects.filter(user=request.user)

    if session_id:
        current_session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    else:
        current_session = sessions.first()
        if not current_session:
            current_session = ChatSession.objects.create(
                user=request.user,
                title="Industrial AI Inquiry"
            )

    messages = current_session.messages.all() if current_session else []
    categories = Category.objects.all()

    context = {
        'sessions': sessions,
        'current_session': current_session,
        'messages': messages,
        'categories': categories,
    }
    return render(request, 'chatbot/chat.html', context)


@login_required
@require_POST
def send_message_api(request):
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id')
        category_filter = data.get('category_filter')

        if not user_message:
            return JsonResponse({'error': 'Message content cannot be empty.'}, status=400)

        if session_id:
            session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        else:
            # Auto update title from first message
            title = user_message[:35] + ("..." if len(user_message) > 35 else "")
            session = ChatSession.objects.create(user=request.user, title=title)

        # Save User Message
        ChatMessage.objects.create(
            session=session,
            sender=ChatMessage.Sender.USER,
            content=user_message
        )

        # Run RAG Engine
        ai_answer, citations = generate_rag_response(user_message, category_filter=category_filter)

        # Save AI Message
        ai_msg_obj = ChatMessage.objects.create(
            session=session,
            sender=ChatMessage.Sender.AI,
            content=ai_answer,
            citations_json=citations
        )

        session.updated_at = timezone.now()
        session.save()

        return JsonResponse({
            'status': 'success',
            'session_id': session.id,
            'message': {
                'id': ai_msg_obj.id,
                'sender': 'AI',
                'content': ai_answer,
                'citations': citations,
                'timestamp': ai_msg_obj.timestamp.strftime('%H:%M')
            }
        })
    except Exception as exc:
        return JsonResponse({'error': f'Server error: {str(exc)}'}, status=500)


@login_required
def new_session_view(request):
    session = ChatSession.objects.create(user=request.user, title="New Technical Session")
    return redirect('chat_session', session_id=session.id)


@login_required
def delete_session_view(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    session.delete()
    return redirect('chat')

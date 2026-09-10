import os
import json
import shutil
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.conf import settings

from .models import GuestDocument, GuestDocumentChunk, GuestChatMessage
from .forms import GuestDocumentUploadForm
from .services.guest_vector_store import rebuild_guest_vector_index, purge_guest_vector_index
from .services.guest_rag_engine import generate_guest_rag_response, MANDATORY_GUEST_DISCLAIMER
from knowledge.services.ocr import extract_text_from_file, generate_chunks, summarize_text

def get_or_create_guest_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def guest_chat_view(request):
    session_key = get_or_create_guest_session_key(request)
    
    documents = GuestDocument.objects.filter(session_key=session_key)
    chat_messages = GuestChatMessage.objects.filter(session_key=session_key)
    upload_form = GuestDocumentUploadForm()
    
    has_documents = documents.exists()

    context = {
        'session_key': session_key,
        'documents': documents,
        'chat_messages': chat_messages,
        'upload_form': upload_form,
        'has_documents': has_documents,
        'disclaimer': MANDATORY_GUEST_DISCLAIMER,
    }
    return render(request, 'guest/chat.html', context)


@require_POST
def guest_upload_api(request):
    session_key = get_or_create_guest_session_key(request)

    form = GuestDocumentUploadForm(request.POST, request.FILES)
    if form.is_valid():
        doc = form.save(commit=False)
        doc.session_key = session_key
        doc.save()

        # Perform OCR / Text Extraction
        file_path = doc.file.path
        full_text, page_map = extract_text_from_file(file_path, doc.file_type)

        doc.extracted_text = full_text
        doc.page_count = len(page_map) if page_map else 1
        doc.summary = summarize_text(full_text)
        doc.save()

        # Create Chunks
        chunks_data = generate_chunks(page_map)
        chunk_objs = []
        for item in chunks_data:
            chunk_objs.append(GuestDocumentChunk(
                document=doc,
                session_key=session_key,
                chunk_index=item['index'],
                content=item['content'],
                page_number=item['page_number']
            ))
        GuestDocumentChunk.objects.bulk_create(chunk_objs)

        # Rebuild Isolated Guest Vector Index
        try:
            rebuild_guest_vector_index(session_key)
        except Exception as exc:
            pass

        return JsonResponse({
            'status': 'success',
            'document': {
                'id': doc.id,
                'title': doc.title,
                'file_type': doc.file_type,
                'file_size': doc.readable_file_size,
                'chunks_count': len(chunk_objs)
            }
        })
    else:
        return JsonResponse({'error': 'Invalid file or upload parameters.'}, status=400)


@require_POST
def guest_send_message_api(request):
    session_key = get_or_create_guest_session_key(request)

    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()

        if not user_message:
            return JsonResponse({'error': 'Message content cannot be empty.'}, status=400)

        # Save Guest User Message
        GuestChatMessage.objects.create(
            session_key=session_key,
            sender=GuestChatMessage.Sender.USER,
            content=user_message
        )

        # Run Guest RAG Engine
        ai_answer, citations, mode = generate_guest_rag_response(session_key, user_message)

        # Save AI Message
        ai_msg = GuestChatMessage.objects.create(
            session_key=session_key,
            sender=GuestChatMessage.Sender.AI,
            content=ai_answer,
            mode=mode,
            citations_json=citations
        )

        return JsonResponse({
            'status': 'success',
            'message': {
                'id': ai_msg.id,
                'sender': 'AI',
                'content': ai_answer,
                'mode': mode,
                'citations': citations,
                'timestamp': ai_msg.timestamp.strftime('%H:%M')
            }
        })
    except Exception as exc:
        return JsonResponse({'error': f'Server error: {str(exc)}'}, status=500)


def guest_end_session_view(request):
    """
    Purges all temporary uploads, vector indices, DB entries, and resets session.
    """
    session_key = request.session.session_key
    if session_key:
        # Purge DB Records
        GuestChatMessage.objects.filter(session_key=session_key).delete()
        GuestDocumentChunk.objects.filter(session_key=session_key).delete()

        # Delete Guest Document files
        docs = GuestDocument.objects.filter(session_key=session_key)
        for doc in docs:
            try:
                if doc.file and os.path.exists(doc.file.path):
                    os.remove(doc.file.path)
            except Exception:
                pass
        docs.delete()

        # Purge Session Media Folder & Vector Index Folder
        guest_media_dir = os.path.join(settings.BASE_DIR, 'media', 'guest_docs', session_key)
        if os.path.exists(guest_media_dir):
            shutil.rmtree(guest_media_dir, ignore_errors=True)

        purge_guest_vector_index(session_key)

        request.session.flush()

    messages.info(request, "Guest Session ended. All temporary files, vector indices, and chat history have been permanently purged.")
    return redirect('landing')

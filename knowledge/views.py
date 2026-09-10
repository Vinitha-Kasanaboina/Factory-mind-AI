import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse, Http404

from .models import Document, Category, Tag, DocumentChunk
from .forms import DocumentUploadForm
from .services.ocr import extract_text_from_file, generate_chunks, summarize_text
from .services.vector_store import rebuild_vector_index, search_similar_chunks

@login_required
def document_list_view(request):
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '')
    tag_slug = request.GET.get('tag', '')

    documents = Document.objects.select_related('category', 'uploaded_by').all()

    if category_slug:
        documents = documents.filter(category__slug=category_slug)
    if tag_slug:
        documents = documents.filter(tags__slug=tag_slug)
    if query:
        documents = documents.filter(
            Q(title__icontains=query) |
            Q(extracted_text__icontains=query) |
            Q(summary__icontains=query)
        )

    categories = Category.objects.all()
    tags = Tag.objects.all()

    context = {
        'documents': documents,
        'categories': categories,
        'tags': tags,
        'selected_category': category_slug,
        'selected_tag': tag_slug,
        'query': query,
    }
    return render(request, 'knowledge/list.html', context)


@login_required
def document_upload_view(request):
    # Only Admin and Engineer can upload documents
    if not (request.user.is_superuser or request.user.role in ['ADMIN', 'ENGINEER']):
        messages.error(request, "Permission denied: Only Engineers and Admins can upload documents.")
        return redirect('document_list')

    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.uploaded_by = request.user
            doc.save()

            # Process Tags
            tags_str = form.cleaned_data.get('tags_input', '')
            if tags_str:
                for tag_name in tags_str.split(','):
                    tag_name_clean = tag_name.strip()
                    if tag_name_clean:
                        tag_obj, _ = Tag.objects.get_or_create(name=tag_name_clean)
                        doc.tags.add(tag_obj)

            # Process OCR & Text Extraction
            file_path = doc.file.path
            full_text, page_map = extract_text_from_file(file_path, doc.file_type)

            doc.extracted_text = full_text
            doc.page_count = len(page_map) if page_map else 1
            doc.summary = summarize_text(full_text)
            doc.is_ocr_processed = True
            doc.save()

            # Generate Chunks
            chunks_data = generate_chunks(page_map)
            DocumentChunk.objects.filter(document=doc).delete()
            
            chunk_objs = []
            for item in chunks_data:
                chunk_objs.append(DocumentChunk(
                    document=doc,
                    chunk_index=item['index'],
                    content=item['content'],
                    page_number=item['page_number']
                ))
            DocumentChunk.objects.bulk_create(chunk_objs)

            # Rebuild Vector Index
            try:
                rebuild_vector_index()
                doc.is_indexed = True
                doc.save()
            except Exception as exc:
                messages.warning(request, f"Document saved, but FAISS indexing had a warning: {exc}")

            messages.success(request, f"Document '{doc.title}' uploaded, processed & vector indexed successfully!")
            return redirect('document_detail', pk=doc.pk)
        else:
            messages.error(request, "Form validation failed. Please check your inputs.")
    else:
        form = DocumentUploadForm()

    categories = Category.objects.all()
    return render(request, 'knowledge/upload.html', {'form': form, 'categories': categories})


@login_required
def document_detail_view(request, pk):
    document = get_object_or_404(Document.objects.select_related('category', 'uploaded_by').prefetch_related('tags', 'chunks'), pk=pk)
    chunks = document.chunks.all()[:20]  # Display up to first 20 chunks
    
    context = {
        'document': document,
        'chunks': chunks,
    }
    return render(request, 'knowledge/detail.html', context)


@login_required
def document_delete_view(request, pk):
    if not (request.user.is_superuser or request.user.role in ['ADMIN', 'ENGINEER']):
        messages.error(request, "Permission denied: Only Engineers and Admins can delete documents.")
        return redirect('document_list')

    document = get_object_or_404(Document, pk=pk)
    title = document.title
    document.delete()
    
    # Update Vector Store
    try:
        rebuild_vector_index()
    except Exception:
        pass

    messages.success(request, f"Document '{title}' deleted and vector index updated.")
    return redirect('document_list')


@login_required
def semantic_search_view(request):
    query = request.GET.get('q', '').strip()
    category_filter = request.GET.get('category', '').strip()
    results = []

    if query:
        results = search_similar_chunks(query, top_k=6, category_filter=category_filter)

    categories = Category.objects.all()

    context = {
        'query': query,
        'results': results,
        'categories': categories,
        'selected_category': category_filter,
    }
    return render(request, 'knowledge/search.html', context)

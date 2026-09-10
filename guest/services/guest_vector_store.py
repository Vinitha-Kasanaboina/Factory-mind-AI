import os
import shutil
import pickle
import logging
import numpy as np
from django.conf import settings
from guest.models import GuestDocumentChunk
from knowledge.services.vector_store import embed_texts, get_faiss

logger = logging.getLogger(__name__)

def get_guest_session_dir(session_key):
    path = os.path.join(settings.GUEST_VECTOR_STORE_DIR, session_key)
    os.makedirs(path, exist_ok=True)
    return path

def rebuild_guest_vector_index(session_key):
    """
    Builds/saves temporary FAISS vector index isolated for guest's session_key.
    """
    chunks = list(GuestDocumentChunk.objects.filter(session_key=session_key).select_related('document').all())
    session_dir = get_guest_session_dir(session_key)
    index_file = os.path.join(session_dir, 'faiss_index.bin')
    metadata_file = os.path.join(session_dir, 'metadata.pkl')

    if not chunks:
        purge_guest_vector_index(session_key)
        return 0

    texts = [c.content for c in chunks]
    embeddings = embed_texts(texts)

    dimension = embeddings.shape[1]
    faiss = get_faiss()

    metadata = []
    for c in chunks:
        metadata.append({
            'chunk_id': c.id,
            'doc_id': c.document.id,
            'doc_title': c.document.title,
            'page_number': c.page_number,
            'content': c.content
        })

    if faiss:
        faiss.normalize_L2(embeddings)
        index = faiss.IndexFlatIP(dimension)
        index.add(embeddings)
        faiss.write_index(index, index_file)
    else:
        np.save(index_file + ".npy", embeddings)

    with open(metadata_file, 'wb') as f:
        pickle.dump(metadata, f)

    return len(chunks)


def search_guest_chunks(session_key, query, top_k=4):
    """
    Searches guest session's isolated vector index.
    """
    if not query or not query.strip():
        return []

    session_dir = get_guest_session_dir(session_key)
    index_file = os.path.join(session_dir, 'faiss_index.bin')
    metadata_file = os.path.join(session_dir, 'metadata.pkl')

    if not os.path.exists(metadata_file) and GuestDocumentChunk.objects.filter(session_key=session_key).exists():
        rebuild_guest_vector_index(session_key)

    if not os.path.exists(metadata_file):
        return []

    try:
        with open(metadata_file, 'rb') as f:
            metadata = pickle.load(f)
    except Exception as e:
        logger.error(f"Error loading guest vector metadata for {session_key}: {e}")
        return []

    if not metadata:
        return []

    query_emb = embed_texts([query])
    faiss = get_faiss()
    results = []

    if faiss and os.path.exists(index_file):
        index = faiss.read_index(index_file)
        faiss.normalize_L2(query_emb)
        scores, indices = index.search(query_emb, min(top_k * 3, len(metadata)))
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(metadata):
                continue
            item = metadata[idx].copy()
            item['score'] = float(score)
            results.append(item)
            if len(results) >= top_k:
                break
    else:
        emb_file = index_file + ".npy"
        if os.path.exists(emb_file):
            embeddings = np.load(emb_file)
            scores = np.dot(embeddings, query_emb[0])
            top_indices = np.argsort(scores)[::-1]
            for idx in top_indices[:top_k * 3]:
                item = metadata[idx].copy()
                item['score'] = float(scores[idx])
                results.append(item)
                if len(results) >= top_k:
                    break

    # Keyword fallback
    if len(results) < top_k:
        query_words = set(query.lower().split())
        for item in metadata:
            if any(r['chunk_id'] == item['chunk_id'] for r in results):
                continue
            matches = sum(1 for w in query_words if w in item['content'].lower())
            if matches > 0:
                item_copy = item.copy()
                item_copy['score'] = 0.5 + (matches * 0.1)
                results.append(item_copy)
                if len(results) >= top_k:
                    break

    return results


def purge_guest_vector_index(session_key):
    """Purges vector files for session_key."""
    path = os.path.join(settings.GUEST_VECTOR_STORE_DIR, session_key)
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)

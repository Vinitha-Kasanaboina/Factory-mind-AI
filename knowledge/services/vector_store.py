import os
import pickle
import logging
import numpy as np
from django.conf import settings
from knowledge.models import DocumentChunk

logger = logging.getLogger(__name__)

INDEX_FILE = os.path.join(settings.VECTOR_STORE_DIR, 'faiss_index.bin')
METADATA_FILE = os.path.join(settings.VECTOR_STORE_DIR, 'metadata.pkl')

_model = None
_faiss_module = None

def get_embedding_model():
    """Lazy load SentenceTransformer model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
            _model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer: {e}. Falling back to basic vectorizer.")
            _model = False
    return _model


def get_faiss():
    """Lazy load FAISS module."""
    global _faiss_module
    if _faiss_module is None:
        try:
            import faiss
            _faiss_module = faiss
        except Exception as e:
            logger.warning(f"FAISS module import error: {e}.")
            _faiss_module = False
    return _faiss_module


def embed_texts(texts):
    """Encodes list of strings into numpy float32 embeddings matrix."""
    model = get_embedding_model()
    if model:
        embeddings = model.encode(texts, show_progress_bar=False)
        return np.array(embeddings, dtype=np.float32)
    else:
        # Fallback pseudo-embeddings using simple character/word hash representation
        matrix = []
        for text in texts:
            vec = np.zeros(384, dtype=np.float32)
            words = text.lower().split()
            for idx, w in enumerate(words):
                h = abs(hash(w)) % 384
                vec[h] += 1.0
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec /= norm
            matrix.append(vec)
        return np.array(matrix, dtype=np.float32)


def rebuild_vector_index():
    """
    Reads all DocumentChunks from SQLite DB, generates embeddings,
    and builds/saves the FAISS index + chunk metadata map.
    """
    chunks = list(DocumentChunk.objects.select_related('document').all())
    if not chunks:
        # Clear index if empty
        if os.path.exists(INDEX_FILE):
            os.remove(INDEX_FILE)
        if os.path.exists(METADATA_FILE):
            os.remove(METADATA_FILE)
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
            'category': c.document.category.name if c.document.category else 'General',
            'content': c.content
        })

    if faiss:
        # Normalize vectors for cosine similarity (IndexFlatIP)
        faiss.normalize_L2(embeddings)
        index = faiss.IndexFlatIP(dimension)
        index.add(embeddings)
        faiss.write_index(index, INDEX_FILE)
    else:
        # Save raw embeddings matrix if FAISS isn't present
        np.save(INDEX_FILE + ".npy", embeddings)

    with open(METADATA_FILE, 'wb') as f:
        pickle.dump(metadata, f)

    logger.info(f"Rebuilt vector index with {len(chunks)} chunks.")
    return len(chunks)


def search_similar_chunks(query, top_k=4, category_filter=None):
    """
    Searches FAISS vector index for chunks matching user query.
    Returns: list of dicts [{'score': float, 'doc_title': str, 'page_number': int, 'content': str, ...}]
    """
    if not query or not query.strip():
        return []

    # If DB chunks exist but index files do not, trigger build
    if not os.path.exists(METADATA_FILE) and DocumentChunk.objects.exists():
        rebuild_vector_index()

    if not os.path.exists(METADATA_FILE):
        return []

    try:
        with open(METADATA_FILE, 'rb') as f:
            metadata = pickle.load(f)
    except Exception as e:
        logger.error(f"Error loading vector index metadata: {e}")
        return []

    if not metadata:
        return []

    query_emb = embed_texts([query])
    faiss = get_faiss()

    results = []

    if faiss and os.path.exists(INDEX_FILE):
        index = faiss.read_index(INDEX_FILE)
        faiss.normalize_L2(query_emb)
        scores, indices = index.search(query_emb, min(top_k * 3, len(metadata)))
        
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(metadata):
                continue
            item = metadata[idx].copy()
            item['score'] = float(score)
            if category_filter and item['category'].lower() != category_filter.lower():
                continue
            results.append(item)
            if len(results) >= top_k:
                break

    else:
        # Fallback numpy inner product search
        emb_file = INDEX_FILE + ".npy"
        if os.path.exists(emb_file):
            embeddings = np.load(emb_file)
            scores = np.dot(embeddings, query_emb[0])
            top_indices = np.argsort(scores)[::-1]
            for idx in top_indices[:top_k * 3]:
                item = metadata[idx].copy()
                item['score'] = float(scores[idx])
                if category_filter and item['category'].lower() != category_filter.lower():
                    continue
                results.append(item)
                if len(results) >= top_k:
                    break

    # Keyword fallback if vector scores are low or empty
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

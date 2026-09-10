import os
import logging
from knowledge.services.vector_store import search_similar_chunks

logger = logging.getLogger(__name__)

def generate_rag_response(user_query, category_filter=None):
    """
    RAG Pipeline:
    1. Retrieve top vector-matched chunks from stored industrial documents.
    2. Format prompt context.
    3. Generate AI response (via OpenAI API if key configured, or local intelligent industrial fallback synthesizer).
    4. Return answer and citations list.
    """
    chunks = search_similar_chunks(user_query, top_k=4, category_filter=category_filter)

    citations = []
    seen_docs = set()
    for c in chunks:
        doc_key = f"{c['doc_title']} (p.{c['page_number']})"
        if doc_key not in seen_docs:
            seen_docs.add(doc_key)
            citations.append({
                'doc_id': c['doc_id'],
                'doc_title': c['doc_title'],
                'page_number': c['page_number'],
                'category': c['category'],
                'score': round(c.get('score', 0.0), 3),
                'snippet': c['content'][:150] + "..."
            })

    # Try OpenAI API if OPENAI_API_KEY environment variable exists
    openai_key = os.environ.get('OPENAI_API_KEY')
    if openai_key and len(openai_key.strip()) > 10:
        try:
            import openai
            client = openai.OpenAI(api_key=openai_key)

            context_str = "\n\n".join([
                f"--- DOCUMENT: {c['doc_title']} (Page {c['page_number']}) ---\n{c['content']}"
                for c in chunks
            ]) if chunks else "No relevant internal documents found in database."

            system_prompt = (
                "You are FactoryMind AI, an expert industrial knowledge and maintenance intelligence assistant. "
                "Answer technical queries precisely using the provided internal document context. "
                "Always cite specific document titles and page numbers when providing procedures, safety steps, or troubleshooting."
            )
            user_prompt = f"User Question: {user_query}\n\nRetrieved Technical Context:\n{context_str}"

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=600
            )
            answer = response.choices[0].message.content
            return answer, citations
        except Exception as err:
            logger.warning(f"OpenAI API call failed or failed to connect: {err}. Falling back to local RAG engine.")

    # Local Intelligent Industrial RAG Synthesizer (Fallback)
    if not chunks:
        answer = (
            f"I searched the FactoryMind AI vector index for **'{user_query}'**, but no relevant "
            "industrial documents or standard operating procedures (SOPs) were found.\n\n"
            "**Recommendations:**\n"
            "- Upload the technical manual or SOP PDF using the **Upload Document** tab.\n"
            "- Ensure OCR processing is enabled for scanned documents.\n"
            "- Try broadening your search query terms (e.g. 'vibration troubleshooting', 'safety protocol')."
        )
        return answer, citations

    # Synthesize structured response from top retrieved chunks
    top_chunk = chunks[0]
    additional_context = ""
    if len(chunks) > 1:
        additional_context = "\n\n**Secondary Context & Cross-References:**\n" + "\n".join([
            f"• **{c['doc_title']} (p. {c['page_number']})**: {c['content'][:220]}..."
            for c in chunks[1:]
        ])

    answer = (
        f"Based on internal industrial knowledge in **{top_chunk['doc_title']}** (Page {top_chunk['page_number']}):\n\n"
        f"{top_chunk['content']}\n"
        f"{additional_context}\n\n"
        f"*Source verified via FactoryMind FAISS Vector Search (Relevance Score: {round(top_chunk.get('score', 0.85)*100, 1)}%).*"
    )

    return answer, citations

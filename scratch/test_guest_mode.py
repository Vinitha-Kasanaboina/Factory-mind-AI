import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'factorymind.settings')

import django
django.setup()

from guest.models import GuestDocument, GuestDocumentChunk, GuestChatMessage
from guest.services.guest_rag_engine import generate_guest_rag_response, MANDATORY_GUEST_DISCLAIMER
from guest.services.guest_vector_store import rebuild_guest_vector_index, search_guest_chunks, purge_guest_vector_index

def test_guest_mode():
    test_session = "test_guest_session_12345"
    print(f"--- Testing Guest Mode for Session {test_session} ---")

    # 1. Test General Industrial AI Mode (No Documents Uploaded)
    print("\n1. Testing General Industrial AI Mode (No Documents Uploaded):")
    answer, citations, mode = generate_guest_rag_response(test_session, "How to troubleshoot pump cavitation?")
    print(f"Mode: {mode}")
    print(f"Answer snippet:\n{answer[:250]}...")
    assert mode == 'GENERAL'
    assert MANDATORY_GUEST_DISCLAIMER in answer
    print(" -> General Industrial AI Mode verified!")

    # 2. Test Custom Document Mode (Upload Temporary Document)
    print("\n2. Testing Custom Document Mode (Uploading session document):")
    doc = GuestDocument.objects.create(
        session_key=test_session,
        title="Temp Centrifugal Pump Manual",
        file_type=GuestDocument.FileType.TXT,
        extracted_text="CENTRIFUGAL PUMP MANUAL: Check Net Positive Suction Head (NPSH). Clear suction strainer if flow drops.",
        summary="Pump NPSH manual."
    )
    chunk = GuestDocumentChunk.objects.create(
        document=doc,
        session_key=test_session,
        chunk_index=0,
        content="CENTRIFUGAL PUMP MANUAL: Check Net Positive Suction Head (NPSH). Clear suction strainer if flow drops.",
        page_number=1
    )
    rebuild_guest_vector_index(test_session)

    answer_doc, citations_doc, mode_doc = generate_guest_rag_response(test_session, "What to check if flow drops?")
    print(f"Mode: {mode_doc}")
    print(f"Citations count: {len(citations_doc)}")
    print(f"Answer snippet:\n{answer_doc}")
    assert mode_doc == 'DOCUMENT'
    assert len(citations_doc) > 0
    print(" -> Custom Document RAG Mode verified!")

    # 3. Test Session Purge
    print("\n3. Testing Session Purging:")
    GuestChatMessage.objects.filter(session_key=test_session).delete()
    GuestDocumentChunk.objects.filter(session_key=test_session).delete()
    GuestDocument.objects.filter(session_key=test_session).delete()
    purge_guest_vector_index(test_session)
    print(" -> Session purged successfully!")
    print("ALL GUEST MODE TESTS PASSED PERFECTLY!")

if __name__ == '__main__':
    test_guest_mode()

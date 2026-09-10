import os
import shutil
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings

from guest.models import GuestDocument, GuestDocumentChunk, GuestChatMessage
from guest.services.guest_vector_store import purge_guest_vector_index

class Command(BaseCommand):
    help = 'Purges temporary guest session files, database records, and vector indices older than 30 minutes.'

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(minutes=30)
        old_docs = GuestDocument.objects.filter(uploaded_at__lt=cutoff)
        session_keys = set(old_docs.values_list('session_key', flat=True))

        count = 0
        for s_key in session_keys:
            GuestChatMessage.objects.filter(session_key=s_key).delete()
            GuestDocumentChunk.objects.filter(session_key=s_key).delete()
            
            docs = GuestDocument.objects.filter(session_key=s_key)
            for d in docs:
                try:
                    if d.file and os.path.exists(d.file.path):
                        os.remove(d.file.path)
                except Exception:
                    pass
            docs.delete()

            # Delete folder
            media_dir = os.path.join(settings.BASE_DIR, 'media', 'guest_docs', s_key)
            if os.path.exists(media_dir):
                shutil.rmtree(media_dir, ignore_errors=True)

            purge_guest_vector_index(s_key)
            count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully purged {count} expired guest sessions."))

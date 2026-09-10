import os
from django.db import models
from django.conf import settings

def guest_upload_path(instance, filename):
    return f"guest_docs/{instance.session_key}/{filename}"

class GuestDocument(models.Model):
    class FileType(models.TextChoices):
        PDF = 'PDF', 'PDF Document'
        DOCX = 'DOCX', 'Word Document'
        IMAGE = 'IMAGE', 'Scanned Image (PNG/JPG)'
        TXT = 'TXT', 'Plain Text / Markdown'

    session_key = models.CharField(max_length=100, db_index=True)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to=guest_upload_path)
    file_type = models.CharField(max_length=10, choices=FileType.choices, default=FileType.PDF)
    
    extracted_text = models.TextField(blank=True, default='')
    summary = models.TextField(blank=True, default='')
    file_size = models.BigIntegerField(default=0)
    page_count = models.IntegerField(default=1)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    @property
    def readable_file_size(self):
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def __str__(self):
        return f"[Guest {self.session_key[:8]}] {self.title}"


class GuestDocumentChunk(models.Model):
    document = models.ForeignKey(GuestDocument, on_delete=models.CASCADE, related_name='chunks')
    session_key = models.CharField(max_length=100, db_index=True)
    chunk_index = models.IntegerField(default=0)
    content = models.TextField()
    page_number = models.IntegerField(default=1)

    class Meta:
        ordering = ['document', 'chunk_index']

    def __str__(self):
        return f"Guest Chunk {self.chunk_index} ({self.document.title})"


class GuestChatMessage(models.Model):
    class Sender(models.TextChoices):
        USER = 'USER', 'User'
        AI = 'AI', 'FactoryMind Guest AI'

    class Mode(models.TextChoices):
        DOCUMENT = 'DOCUMENT', 'Custom Document RAG'
        GENERAL = 'GENERAL', 'General Industrial AI Assistant'

    session_key = models.CharField(max_length=100, db_index=True)
    sender = models.CharField(max_length=10, choices=Sender.choices, default=Sender.USER)
    content = models.TextField()
    mode = models.CharField(max_length=15, choices=Mode.choices, default=Mode.GENERAL)
    citations_json = models.JSONField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"[{self.session_key[:8]}][{self.sender}] {self.content[:30]}..."

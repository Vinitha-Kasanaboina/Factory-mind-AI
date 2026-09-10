import os
from django.db import models
from django.conf import settings
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon_class = models.CharField(max_length=50, default='bi-folder2-open')

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Document(models.Model):
    class FileType(models.TextChoices):
        PDF = 'PDF', 'PDF Document'
        DOCX = 'DOCX', 'Word Document'
        IMAGE = 'IMAGE', 'Scanned Image (PNG/JPG)'
        TXT = 'TXT', 'Plain Text / Markdown'

    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/%Y/%m/')
    file_type = models.CharField(max_length=10, choices=FileType.choices, default=FileType.PDF)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='documents')
    tags = models.ManyToManyField(Tag, blank=True, related_name='documents')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='uploaded_documents')
    upload_date = models.DateTimeField(auto_now_add=True)
    
    extracted_text = models.TextField(blank=True, default='')
    summary = models.TextField(blank=True, default='')
    file_size = models.BigIntegerField(default=0, help_text="Size in bytes")
    page_count = models.IntegerField(default=1)
    
    is_ocr_processed = models.BooleanField(default=False)
    is_indexed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-upload_date']

    def save(self, *args, **kwargs):
        if self.file and not self.file_size:
            try:
                self.file_size = self.file.size
            except Exception:
                pass
        
        if self.file and not self.file_type:
            ext = os.path.splitext(self.file.name)[1].lower()
            if ext == '.pdf':
                self.file_type = self.FileType.PDF
            elif ext in ['.docx', '.doc']:
                self.file_type = self.FileType.DOCX
            elif ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
                self.file_type = self.FileType.IMAGE
            else:
                self.file_type = self.FileType.TXT
                
        super().save(*args, **kwargs)

    @property
    def readable_file_size(self):
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def __str__(self):
        return self.title

class DocumentChunk(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    chunk_index = models.IntegerField(default=0)
    content = models.TextField()
    page_number = models.IntegerField(default=1)

    class Meta:
        ordering = ['document', 'chunk_index']

    def __str__(self):
        return f"{self.document.title} - Chunk {self.chunk_index} (p.{self.page_number})"

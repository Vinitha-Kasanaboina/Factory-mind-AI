from django.contrib import admin
from .models import Category, Tag, Document, DocumentChunk

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon_class')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

class DocumentChunkInline(admin.TabularInline):
    model = DocumentChunk
    extra = 0
    fields = ('chunk_index', 'page_number', 'content')
    readonly_fields = ('chunk_index', 'page_number', 'content')

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'file_type', 'uploaded_by', 'upload_date', 'is_ocr_processed', 'is_indexed')
    list_filter = ('category', 'file_type', 'is_ocr_processed', 'is_indexed')
    search_fields = ('title', 'extracted_text', 'summary')
    inlines = [DocumentChunkInline]

@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ('document', 'chunk_index', 'page_number')
    search_fields = ('content',)

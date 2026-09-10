from django import forms
from .models import Document, Category, Tag

class DocumentUploadForm(forms.ModelForm):
    tags_input = forms.CharField(
        required=False,
        help_text="Comma-separated tags (e.g., Siemens, Motor, High-Temp)",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Bearings, Maintenance, Safety'})
    )

    class Meta:
        model = Document
        fields = ('title', 'file', 'category')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Document Title / Guide Name'}),
            'file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.docx,.doc,.png,.jpg,.jpeg,.txt'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ('name', 'description', 'icon_class')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'icon_class': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'bi-tools'}),
        }

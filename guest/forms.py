from django import forms
from .models import GuestDocument

class GuestDocumentUploadForm(forms.ModelForm):
    class Meta:
        model = GuestDocument
        fields = ('title', 'file')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Manual Title (e.g. Pump Repair Guide)'}),
            'file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.docx,.doc,.png,.jpg,.jpeg,.txt'}),
        }

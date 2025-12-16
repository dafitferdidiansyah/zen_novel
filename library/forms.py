from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5, 'class': 'rating-input'}),
            'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Tulis ulasanmu di sini...', 'style': 'width:100%; background:#111; color:#fff; border:1px solid #444; padding:10px;'}),
        }
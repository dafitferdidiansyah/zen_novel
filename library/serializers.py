from rest_framework import serializers
from .models import Novel, Chapter

class ChapterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = ['id', 'title', 'order', 'uploaded_at']

class NovelSerializer(serializers.ModelSerializer):
    chapters = ChapterSerializer(many=True, read_only=True)
    rating = serializers.FloatField(source='average_rating', read_only=True)

    class Meta:
        model = Novel
        fields = ['id', 'title', 'author', 'synopsis', 'cover', 'genre', 'status', 'rating', 'uploaded_at', 'chapters']
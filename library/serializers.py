from rest_framework import serializers
from .models import Novel, Chapter

# Penerjemah Chapter
class ChapterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = ['id', 'title', 'order', 'uploaded_at']

# Penerjemah Novel
class NovelSerializer(serializers.ModelSerializer):
    # Tampilkan list chapter di dalam detail novel (nested)
    # read_only=True artinya kita cuma baca, tidak edit chapter lewat endpoint novel
    chapters = ChapterSerializer(many=True, read_only=True)

    class Meta:
        model = Novel
        fields = ['id', 'title', 'author', 'synopsis', 'cover', 'genre', 'status', 'chapters']
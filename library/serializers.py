from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Novel, Chapter, UserSettings, Comment

# Serializer untuk Chapter (Dipakai di Detail Novel & Baca)
class ChapterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = ['id', 'title', 'order', 'uploaded_at']

# Serializer Ringan (Khusus untuk List di Halaman Depan)
class NovelListSerializer(serializers.ModelSerializer):
    rating = serializers.FloatField(source='average_rating', read_only=True)
    chapter_count = serializers.IntegerField(source='chapters.count', read_only=True)

    class Meta:
        model = Novel
        # HANYA ambil data penting, JANGAN ambil list chapters disini
        fields = ['id', 'title', 'cover', 'genre', 'status', 'rating', 'chapter_count', 'uploaded_at']

# Serializer Berat (Khusus untuk Halaman Detail saat diklik)
class NovelDetailSerializer(serializers.ModelSerializer):
    chapters = ChapterSerializer(many=True, read_only=True)
    rating = serializers.FloatField(source='average_rating', read_only=True)

    class Meta:
        model = Novel
        fields = ['id', 'title', 'author', 'synopsis', 'cover', 'genre', 'status', 'rating', 'uploaded_at', 'chapters']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = ['font_size', 'line_height', 'theme']
# Tambahkan di library/serializers.py

class CommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True) # Biar muncul nama, bukan ID

    class Meta:
        model = Comment
        fields = ['id', 'username', 'text', 'created_at']
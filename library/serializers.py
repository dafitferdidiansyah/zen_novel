from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Novel, Chapter, UserSettings, Comment, Tag, Bookmark

# --- 1. Serializer Helper (Tag & Chapter) ---

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']

class ChapterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = ['id', 'title', 'order', 'uploaded_at']

# --- 2. Serializer Utama (List & Detail) ---

class NovelListSerializer(serializers.ModelSerializer):
    rating = serializers.FloatField(source='average_rating', read_only=True)
    chapter_count = serializers.IntegerField(source='chapters.count', read_only=True)

    class Meta:
        model = Novel
        fields = [
            'id', 'title', 'cover', 'genre', 'status', 
            'rating', 'chapter_count', 'uploaded_at','views'
        ]

class NovelDetailSerializer(serializers.ModelSerializer):
    is_bookmarked = serializers.SerializerMethodField()
    chapters = ChapterSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    rating = serializers.FloatField(source='average_rating', read_only=True)

    class Meta:
        model = Novel
        fields = [
            'id', 'title', 'author', 'synopsis', 'tags', 'cover', 
            'genre', 'status', 'rating', 'uploaded_at', 
            'chapters', 'is_bookmarked','views','alternative_title'
        ]

    def get_is_bookmarked(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            # Cek apakah ada bookmark DAN is_in_library = True
            try:
                bookmark = Bookmark.objects.get(user=user, novel=obj)
                return bookmark.is_in_library
            except Bookmark.DoesNotExist:
                return False
        return False

# --- 3. Chapter Detail (UPDATE DISINI) ---

class ChapterDetailSerializer(serializers.ModelSerializer):
    # Ambil Judul & Cover Novel
    novel_title = serializers.CharField(source='novel.title', read_only=True)
    novel_cover = serializers.ImageField(source='novel.cover', read_only=True)
    
    # PERBAIKAN: Gunakan FloatField (bukan IntegerField)
    # Ini memungkinkan order bernilai 1.5 (untuk Side Chapter) atau 100.1
    chapter_number = serializers.FloatField(source='order', read_only=True)
    
    class Meta:
        model = Chapter
        fields = [
            'id', 'novel_id', 'title', 'content', 
            'chapter_number', 
            'novel_title', 'novel_cover'
        ]
# --- 4. User & Fitur Lainnya ---

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

class CommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'username', 'text', 'created_at']
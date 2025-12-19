from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Novel, Chapter, Bookmark, UserSettings, Comment,Tag, NovelVote
from .serializers import (
    NovelListSerializer, NovelDetailSerializer, ChapterSerializer, 
    UserSerializer, UserSettingsSerializer, CommentSerializer
)

# --- HOME DATA ---
@api_view(['GET'])
def home_data(request):
    hot_novels = Novel.objects.order_by('-views')[:6]
    latest_novels = Novel.objects.order_by('-uploaded_at')[:10]
    completed_novels = Novel.objects.filter(status='Completed')[:5]

    return Response({
        'hot': NovelListSerializer(hot_novels, many=True).data,
        'latest': NovelListSerializer(latest_novels, many=True).data,
        'completed': NovelListSerializer(completed_novels, many=True).data
    })

# --- NOVEL & CHAPTER ---
@api_view(['GET'])
def novel_list(request):
    query = request.GET.get('q')
    genre = request.GET.get('genre')
    novels = Novel.objects.all().order_by('-uploaded_at')

    if query:
        novels = novels.filter(Q(title__icontains=query) | Q(author__icontains=query))
    if genre:
        novels = novels.filter(genre__iexact=genre)

    paginator = PageNumberPagination()
    paginator.page_size = 12
    result_page = paginator.paginate_queryset(novels, request)
    serializer = NovelListSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)

@api_view(['GET'])
def novel_detail(request, pk):
    novel = get_object_or_404(Novel, pk=pk)
    novel.views += 1
    novel.save()
    serializer = NovelDetailSerializer(novel)
    return Response(serializer.data)

@api_view(['GET'])
def chapter_detail(request, pk):
    chapter = get_object_or_404(Chapter, pk=pk)
    serializer = ChapterSerializer(chapter)
    data = serializer.data
    data['content'] = chapter.content
    
    next_chap = Chapter.objects.filter(novel=chapter.novel, order__gt=chapter.order).order_by('order').first()
    prev_chap = Chapter.objects.filter(novel=chapter.novel, order__lt=chapter.order).order_by('-order').first()
    
    data['next_chapter_id'] = next_chap.id if next_chap else None
    data['prev_chapter_id'] = prev_chap.id if prev_chap else None
    data['novel_id'] = chapter.novel.id
    
    return Response(data)

# --- USER FEATURE ---
@api_view(['POST'])
def register_api(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'status': 'success'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_bookmarks(request):
    bookmarks = Bookmark.objects.filter(user=request.user)
    novels = [b.novel for b in bookmarks]
    serializer = NovelListSerializer(novels, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_bookmark_api(request, pk):
    novel = get_object_or_404(Novel, pk=pk)
    bookmark, created = Bookmark.objects.get_or_create(user=request.user, novel=novel)
    if created:
        return Response({'status': 'added'})
    else:
        bookmark.delete()
        return Response({'status': 'removed'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_progress(request, novel_id, chapter_id):
    novel = get_object_or_404(Novel, pk=novel_id)
    chapter = get_object_or_404(Chapter, pk=chapter_id)
    bookmark, _ = Bookmark.objects.get_or_create(user=request.user, novel=novel)
    bookmark.last_read_chapter = chapter
    bookmark.save()
    return Response({'status': 'updated'})

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def user_settings_api(request):
    settings, created = UserSettings.objects.get_or_create(user=request.user)
    if request.method == 'GET':
        serializer = UserSettingsSerializer(settings)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = UserSettingsSerializer(settings, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

@api_view(['GET'])
def get_chapter_comments(request, chapter_id):
    """Mengambil semua komentar di chapter tertentu"""
    comments = Comment.objects.filter(chapter_id=chapter_id)
    serializer = CommentSerializer(comments, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_chapter_comment(request, chapter_id):
    """Mengirim komentar baru"""
    chapter = get_object_or_404(Chapter, pk=chapter_id)
    
    # Buat instance serializer dengan data manual
    serializer = CommentSerializer(data=request.data)
    
    if serializer.is_valid():
        # Simpan dengan user yang sedang login & chapter yang dipilih
        serializer.save(user=request.user, chapter=chapter)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_comment(request, comment_id):
    """Hapus komentar (Cuma bisa hapus punya sendiri)"""
    comment = get_object_or_404(Comment, pk=comment_id)
    
    if comment.user != request.user:
        return Response({'detail': 'Not your comment!'}, status=status.HTTP_403_FORBIDDEN)
        
    comment.delete()
    return Response({'status': 'deleted'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rate_novel(request, pk):
    """User memberi rating bintang (1-5)"""
    novel = get_object_or_404(Novel, pk=pk)
    score = request.data.get('score')

    # Validasi input
    if not score or not (1 <= int(score) <= 5):
        return Response({'message': 'Score must be 1-5'}, status=400)

    # Simpan/Update Vote
    vote, created = NovelVote.objects.update_or_create(
        novel=novel,
        user=request.user,
        defaults={'score': score}
    )

    # Hitung rata-rata baru (disimpan di novel biar cepat loadnya)
    novel.rating_score = novel.average_rating()
    novel.save()

    return Response({'status': 'success', 'new_rating': novel.rating_score})

@api_view(['GET'])
def novels_by_tag(request, tag_slug):
    """Mencari novel berdasarkan Tag"""
    tag = get_object_or_404(Tag, slug=tag_slug)
    novels = Novel.objects.filter(tags=tag)
    
    # Gunakan pagination biar sama kayak list biasa
    paginator = PageNumberPagination()
    paginator.page_size = 12
    result_page = paginator.paginate_queryset(novels, request)
    serializer = NovelListSerializer(result_page, many=True)
    
    return paginator.get_paginated_response(serializer.data)
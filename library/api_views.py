from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q, F
from .models import Novel, Chapter, Bookmark, UserSettings, Comment, Tag, NovelVote
from .serializers import (
    NovelListSerializer, NovelDetailSerializer, ChapterSerializer, 
    UserSerializer, UserSettingsSerializer, CommentSerializer,
    ChapterDetailSerializer 
)

# --- HOME DATA ---
@api_view(['GET'])
@permission_classes([AllowAny])
def home_data(request):
    hot_novels = Novel.objects.order_by('-views')[:6]
    latest_novels = Novel.objects.order_by('-uploaded_at')[:10]
    completed_novels = Novel.objects.filter(status='Completed')[:5]
    
    # LOGIC RECENT READS (User Login)
    recent_reads = []
    if request.user.is_authenticated:
        bookmarks = Bookmark.objects.filter(
            user=request.user, 
            last_read_chapter__isnull=False
        ).select_related('novel', 'last_read_chapter').order_by('-updated_at')[:5]

        for b in bookmarks:
            # Gunakan getattr untuk keamanan jika order kosong
            chap_num = getattr(b.last_read_chapter, 'order', 0) if b.last_read_chapter else 0
            chap_idx = getattr(b.last_read_chapter, 'chapter_index', 0) if b.last_read_chapter else 0
            recent_reads.append({
                'id': b.novel.id,
                'title': b.novel.title,
                'cover': b.novel.cover.url if b.novel.cover else None,
                'chapter_id': b.last_read_chapter.id if b.last_read_chapter else None,
                'chapter_title': b.last_read_chapter.title if b.last_read_chapter else "",
                'chapter_order': chap_num, # Pastikan ini menggunakan variabel chap_num
                'chapter_index': chap_idx,
            })

    return Response({
        'hot': NovelListSerializer(hot_novels, many=True).data,
        'latest': NovelListSerializer(latest_novels, many=True).data,
        'completed': NovelListSerializer(completed_novels, many=True).data,
        'recent': recent_reads
    })

# --- NOVEL & CHAPTER ---
@api_view(['GET'])
def novel_list(request):
    query = request.GET.get('q')
    genre = request.GET.get('genre')
    tag = request.GET.get('tag')

    novels = Novel.objects.all().order_by('-uploaded_at')

    if query:
        novels = novels.filter(Q(title__icontains=query) | Q(author__icontains=query))
    if genre:
        novels = novels.filter(genre__iexact=genre)
    if tag:
        novels = novels.filter(tags__slug__iexact=tag) | novels.filter(tags__name__iexact=tag)
        novels = novels.distinct()

    paginator = PageNumberPagination()
    paginator.page_size = 12
    result_page = paginator.paginate_queryset(novels, request)
    serializer = NovelListSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)

@api_view(['GET'])
def novel_detail(request, pk):
    Novel.objects.filter(pk=pk).update(views=F('views') + 1)
    novel = get_object_or_404(Novel, pk=pk)
    serializer = NovelDetailSerializer(novel, context={'request': request}) 
    return Response(serializer.data)

@api_view(['GET'])
def chapter_detail(request, pk):
    chapter = get_object_or_404(Chapter, pk=pk)
    serializer = ChapterDetailSerializer(chapter)
    data = serializer.data
    
    # Navigasi Next/Prev manual (menggunakan order)
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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_bookmark(request, novel_id):
    novel = get_object_or_404(Novel, pk=novel_id)
    bookmark, created = Bookmark.objects.get_or_create(user=request.user, novel=novel)
    
    # Toggle Status
    bookmark.is_in_library = not bookmark.is_in_library
    bookmark.save()
    
    return Response({
        "status": "success",
        "is_bookmarked": bookmark.is_in_library,
        "message": "Added to library" if bookmark.is_in_library else "Removed from library"
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_progress(request, novel_id, chapter_id):
    novel = get_object_or_404(Novel, pk=novel_id)
    chapter = get_object_or_404(Chapter, pk=chapter_id)
    
    bookmark, created = Bookmark.objects.get_or_create(user=request.user, novel=novel)
    
    # Hanya update progress, JANGAN ubah status library
    bookmark.last_read_chapter = chapter
    bookmark.save()
    
    return Response({
        "status": "success", 
        "message": f"Progress updated to {chapter.title}",
        "chapter_id": chapter.id
    })

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

# --- COMMENTS ---
@api_view(['GET'])
def get_chapter_comments(request, chapter_id):
    comments = Comment.objects.filter(chapter_id=chapter_id).order_by('-created_at')
    serializer = CommentSerializer(comments, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_chapter_comment(request, chapter_id):
    chapter = get_object_or_404(Chapter, pk=chapter_id)
    serializer = CommentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user, chapter=chapter)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    if comment.user != request.user:
        return Response({'detail': 'Not your comment!'}, status=status.HTTP_403_FORBIDDEN)
    comment.delete()
    return Response({'status': 'deleted'})

# --- RATING ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rate_novel(request, pk):
    novel = get_object_or_404(Novel, pk=pk)
    score = request.data.get('score')
    if not score or not (1 <= int(score) <= 5):
        return Response({'message': 'Score must be 1-5'}, status=400)

    NovelVote.objects.update_or_create(novel=novel, user=request.user, defaults={'score': score})
    
    # Recalculate rating manually (simple avg)
    votes = NovelVote.objects.filter(novel=novel)
    total = sum(v.score for v in votes)
    count = votes.count()
    novel.rating_score = round(total / count, 1) if count > 0 else 0
    novel.save()
    
    return Response({'status': 'success', 'new_rating': novel.rating_score})

# --- TAGS & GENRES ---
@api_view(['GET'])
def novels_by_tag(request, tag_slug):
    tag = get_object_or_404(Tag, slug=tag_slug)
    novels = Novel.objects.filter(tags=tag)
    paginator = PageNumberPagination()
    paginator.page_size = 12
    result_page = paginator.paginate_queryset(novels, request)
    serializer = NovelListSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def genre_list_api(request):
    genres = Novel.objects.values_list('genre', flat=True).distinct().order_by('genre')
    return Response(list(genres))

# --- LIBRARY & HISTORY (FIXED) ---

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_bookmarks(request):
    # Filter: is_in_library=True
    bookmarks = Bookmark.objects.filter(user=request.user, is_in_library=True).select_related('novel', 'last_read_chapter').order_by('-updated_at')
    
    data = []
    for b in bookmarks:
        # PERBAIKAN: Gunakan .order (bukan .chapter_number)
        chap_num = getattr(b.last_read_chapter, 'order', 0) if b.last_read_chapter else 0
        chap_idx = getattr(b.last_read_chapter, 'chapter_index', 0) if b.last_read_chapter else 0
        data.append({
            "id": b.novel.id,
            "title": b.novel.title,
            "cover": b.novel.cover.url if b.novel.cover else None,
            "current_chapter_id": b.last_read_chapter.id if b.last_read_chapter else None,
            "current_chapter_title": b.last_read_chapter.title if b.last_read_chapter else "Belum dibaca",
            "current_chapter_number": chap_num, # SUDAH DIPERBAIKI
            "current_chapter_index": chap_idx,
            "updated_at": b.updated_at
        })
        
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_history(request):
    # Ambil semua yang pernah dibaca
    history = Bookmark.objects.filter(
        user=request.user, 
        last_read_chapter__isnull=False
    ).select_related('novel', 'last_read_chapter').order_by('-updated_at')
    
    data = []
    for h in history:
        # PERBAIKAN: Gunakan .order
        chap_num = getattr(h.last_read_chapter, 'order', 0) if h.last_read_chapter else 0
        chap_idx = getattr(h.last_read_chapter, 'chapter_index', 0) if h.last_read_chapter else 0
        data.append({
            "id": h.novel.id,
            "title": h.novel.title,
            "cover": h.novel.cover.url if h.novel.cover else None,
            "current_chapter_id": h.last_read_chapter.id,
            "current_chapter_title": h.last_read_chapter.title,
            "current_chapter_number": chap_num, # SUDAH DIPERBAIKI
            "current_chapter_index": chap_idx,
            "last_read_at": h.updated_at,
            "is_in_library": h.is_in_library
        })
        
    return Response(data)
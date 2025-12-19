from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Novel, Chapter, Bookmark
from .serializers import NovelListSerializer, NovelDetailSerializer, ChapterSerializer, UserSerializer

# --- API DATA HOME (NOVELBIN STYLE) ---

@api_view(['GET'])
def home_data(request):
    """
    API Khusus Home Page ala NovelBin.
    Mengirim data: Hot Novels, Latest Updates, dan Completed.
    """
    # 1. Hot Novels (Berdasarkan Views tertinggi, ambil 6)
    hot_novels = Novel.objects.order_by('-views')[:6]
    
    # 2. Latest Updates (Berdasarkan chapter yang baru diupload/novel diupdate)
    latest_novels = Novel.objects.order_by('-updated_at')[:10]
    
    # 3. Completed (Untuk Sidebar)
    completed_novels = Novel.objects.filter(status='Completed')[:5]

    return Response({
        'hot': NovelListSerializer(hot_novels, many=True).data,
        'latest': NovelListSerializer(latest_novels, many=True).data,
        'completed': NovelListSerializer(completed_novels, many=True).data
    })

# --- API LAINNYA TETAP SAMA ---

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
    # Tambah view count saat detail dibuka
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
        return Response({'status': 'added', 'message': 'Ditambahkan ke Library'})
    else:
        bookmark.delete()
        return Response({'status': 'removed', 'message': 'Dihapus dari Library'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_progress(request, novel_id, chapter_id):
    novel = get_object_or_404(Novel, pk=novel_id)
    chapter = get_object_or_404(Chapter, pk=chapter_id)
    bookmark, _ = Bookmark.objects.get_or_create(user=request.user, novel=novel)
    bookmark.last_read_chapter = chapter
    bookmark.save()
    return Response({'status': 'updated', 'chapter': chapter.title})

@api_view(['POST'])
def register_api(request):
    """API untuk mendaftar user baru dari React"""
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'status': 'success', 'message': 'User created successfully'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
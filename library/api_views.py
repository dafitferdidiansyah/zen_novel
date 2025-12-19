from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Novel, Chapter, Bookmark
from .serializers import NovelListSerializer, NovelDetailSerializer, ChapterSerializer

@api_view(['GET'])
def novel_list(request):
    """
    API List Novel dengan Paginasi, Search, dan Filter.
    Output: JSON berisi count, next, previous, dan results.
    """
    query = request.GET.get('q')
    genre = request.GET.get('genre')
    
    # Ambil semua novel, urutkan dari yang terbaru
    novels = Novel.objects.all().order_by('-uploaded_at')

    # Logika Filter & Search
    if query:
        novels = novels.filter(Q(title__icontains=query) | Q(author__icontains=query))
    if genre:
        novels = novels.filter(genre__iexact=genre)

    # Aktifkan Paginasi (Halaman 1, 2, 3...)
    paginator = PageNumberPagination()
    paginator.page_size = 12 # Bebas atur mau berapa per load
    result_page = paginator.paginate_queryset(novels, request)

    # Pakai Serializer RINGAN (NovelListSerializer)
    serializer = NovelListSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)

@api_view(['GET'])
def novel_detail(request, pk):
    """Mengambil detail lengkap satu novel beserta chapter-nya"""
    novel = get_object_or_404(Novel, pk=pk)
    # Pakai Serializer LENGKAP (NovelDetailSerializer)
    serializer = NovelDetailSerializer(novel)
    return Response(serializer.data)

@api_view(['GET'])
def chapter_detail(request, pk):
    """Mengambil isi teks chapter"""
    chapter = get_object_or_404(Chapter, pk=pk)
    serializer = ChapterSerializer(chapter)
    data = serializer.data
    data['content'] = chapter.content
    
    # Navigasi Smart (ID chapter sebelum dan sesudahnya)
    next_chap = Chapter.objects.filter(novel=chapter.novel, order__gt=chapter.order).order_by('order').first()
    prev_chap = Chapter.objects.filter(novel=chapter.novel, order__lt=chapter.order).order_by('-order').first()
    
    data['next_chapter_id'] = next_chap.id if next_chap else None
    data['prev_chapter_id'] = prev_chap.id if prev_chap else None
    data['novel_id'] = chapter.novel.id
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated]) # Wajib Login
def user_bookmarks(request):
    """Mengambil daftar novel yang dibookmark user"""
    bookmarks = Bookmark.objects.filter(user=request.user)
    # Kita ambil object novel-nya saja dari bookmark
    novels = [b.novel for b in bookmarks]
    serializer = NovelListSerializer(novels, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_bookmark_api(request, pk):
    """Menambah atau Menghapus Bookmark"""
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
    """Mencatat progress baca terakhir"""
    novel = get_object_or_404(Novel, pk=novel_id)
    chapter = get_object_or_404(Chapter, pk=chapter_id)
    
    # Update atau Buat Bookmark baru jika belum ada
    bookmark, _ = Bookmark.objects.get_or_create(user=request.user, novel=novel)
    bookmark.last_read_chapter = chapter
    bookmark.save() # Ini akan otomatis update field 'updated_at'
    
    return Response({'status': 'updated', 'chapter': chapter.title})
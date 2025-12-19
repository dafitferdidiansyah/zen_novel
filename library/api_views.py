from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Novel, Chapter
from .serializers import NovelSerializer, ChapterSerializer

# --- ENDPOINT NOVEL ---

@api_view(['GET'])
def novel_list(request):
    """Mengambil SEMUA daftar novel"""
    novels = Novel.objects.all()
    # many=True karena datanya banyak (list)
    serializer = NovelSerializer(novels, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
def novel_detail(request, pk):
    """Mengambil SATU novel beserta chapternya"""
    novel = get_object_or_404(Novel, pk=pk)
    serializer = NovelSerializer(novel, context={'request': request})
    return Response(serializer.data)

# --- ENDPOINT CHAPTER ---

@api_view(['GET'])
def chapter_detail(request, pk):
    """Mengambil ISI TEKS dari satu chapter"""
    chapter = get_object_or_404(Chapter, pk=pk)
    
    # Kita butuh serializernya
    serializer = ChapterSerializer(chapter)
    data = serializer.data
    
    # TAMBAHAN KHUSUS: Masukkan isi teks novel (content)
    # Karena di serializer tadi kita tidak masukkan field 'content' (biar ringan di list)
    # Tapi di sini kita butuh isinya.
    data['content'] = chapter.content 
    
    # Info navigasi (Next/Prev Chapter) untuk Frontend
    # Mencari chapter selanjutnya berdasarkan urutan (order)
    next_chap = Chapter.objects.filter(novel=chapter.novel, order__gt=chapter.order).order_by('order').first()
    prev_chap = Chapter.objects.filter(novel=chapter.novel, order__lt=chapter.order).order_by('-order').first()
    
    data['next_chapter_id'] = next_chap.id if next_chap else None
    data['prev_chapter_id'] = prev_chap.id if prev_chap else None
    data['novel_id'] = chapter.novel.id
    
    return Response(data)
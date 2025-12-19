from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Novel, Chapter
from .serializers import NovelSerializer, ChapterSerializer

@api_view(['GET'])
def novel_list(request):
    """API List Novel + Search + Filter"""
    query = request.GET.get('q')
    genre = request.GET.get('genre')
    
    novels = Novel.objects.all().order_by('-uploaded_at')

    if query:
        novels = novels.filter(Q(title__icontains=query) | Q(author__icontains=query))
    if genre:
        novels = novels.filter(genre__iexact=genre)

    serializer = NovelSerializer(novels, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def novel_detail(request, pk):
    novel = get_object_or_404(Novel, pk=pk)
    serializer = NovelSerializer(novel)
    return Response(serializer.data)

@api_view(['GET'])
def chapter_detail(request, pk):
    chapter = get_object_or_404(Chapter, pk=pk)
    serializer = ChapterSerializer(chapter)
    data = serializer.data
    data['content'] = chapter.content
    
    # Navigasi Next/Prev ID untuk Frontend
    next_chap = Chapter.objects.filter(novel=chapter.novel, order__gt=chapter.order).order_by('order').first()
    prev_chap = Chapter.objects.filter(novel=chapter.novel, order__lt=chapter.order).order_by('-order').first()
    
    data['next_chapter_id'] = next_chap.id if next_chap else None
    data['prev_chapter_id'] = prev_chap.id if prev_chap else None
    
    return Response(data)
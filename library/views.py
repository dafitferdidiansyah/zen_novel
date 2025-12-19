from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from .models import Novel, Chapter, Bookmark

# --- HALAMAN UTAMA & FILTER ---
def home(request):
    genre_query = request.GET.get('genre')
    if genre_query:
        novels = Novel.objects.filter(genre__iexact=genre_query)
    else:
        novels = Novel.objects.all().order_by('-uploaded_at')
    
    all_genres = Novel.objects.values_list('genre', flat=True).distinct()
    
    return render(request, 'library/home.html', {
        'novels': novels,
        'genres': all_genres,
        'current_genre': genre_query
    })

# --- FITUR PENCARIAN (FIXED) ---
def search(request):
    query = request.GET.get('q')
    if query:
        novels = Novel.objects.filter(
            Q(title__icontains=query) | Q(author__icontains=query)
        )
    else:
        novels = Novel.objects.none()
    return render(request, 'library/search.html', {'novels': novels, 'query': query})

# --- DETAIL NOVEL ---
def detail(request, novel_id):
    novel = get_object_or_404(Novel, pk=novel_id)
    is_bookmarked = False
    if request.user.is_authenticated:
        is_bookmarked = Bookmark.objects.filter(user=request.user, novel=novel).exists()
    return render(request, 'library/detail.html', {'novel': novel, 'is_bookmarked': is_bookmarked})

# --- BACA CHAPTER ---
def read_chapter(request, novel_id, chapter_id):
    novel = get_object_or_404(Novel, pk=novel_id)
    chapter = get_object_or_404(Chapter, pk=chapter_id, novel=novel)
    
    prev_chapter = Chapter.objects.filter(novel=novel, order__lt=chapter.order).order_by('-order').first()
    next_chapter = Chapter.objects.filter(novel=novel, order__gt=chapter.order).order_by('order').first()

    return render(request, 'library/read.html', {
        'novel': novel,
        'chapter': chapter,
        'prev_chapter': prev_chapter,
        'next_chapter': next_chapter
    })

# --- BOOKMARK TOGGLE ---
def toggle_bookmark(request, novel_id):
    if not request.user.is_authenticated:
        return redirect('login')
    
    novel = get_object_or_404(Novel, pk=novel_id)
    bookmark, created = Bookmark.objects.get_or_create(user=request.user, novel=novel)
    if not created:
        bookmark.delete()
    return redirect('detail', novel_id=novel_id)
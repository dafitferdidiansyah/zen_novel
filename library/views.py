from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Novel, Chapter, Bookmark, NovelVote
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

# --- Helper Context ---
def get_common_context():
    return {
        'all_genres': Novel.objects.values_list('genre', flat=True).distinct().order_by('genre')
    }

# --- VIEW UTAMA ---
def home(request):
    novels = Novel.objects.all().order_by('-uploaded_at')[:12]
    
    # History Logic
    recent_reads = []
    history_cookie = request.COOKIES.get('zn_history')
    if history_cookie:
        try:
            history_data = json.loads(history_cookie)
            for nid, cid in history_data.items():
                try:
                    chap = Chapter.objects.select_related('novel').get(id=cid)
                    recent_reads.append(chap)
                except: pass
        except: pass
    recent_reads.reverse()

    context = {
        'novels': novels,
        'recent_reads': recent_reads[:6],
        **get_common_context()
    }
    return render(request, 'library/home.html', context)

# --- VIEW SEARCH ---
def search_view(request):
    query = request.GET.get('q', '')
    selected_genres = request.GET.getlist('genre') 
    
    novels = Novel.objects.all()
    
    if query:
        novels = novels.filter(Q(title__icontains=query) | Q(author__icontains=query))
    
    if selected_genres:
        genre_query = Q()
        for g in selected_genres:
            genre_query |= Q(genre__icontains=g) 
        novels = novels.filter(genre_query)

    context = {
        'novels': novels,
        'query': query,
        'selected_genres': selected_genres,
        'is_search': True,
        **get_common_context()
    }
    return render(request, 'library/home.html', context)

# --- VIEW NOVEL & BACA ---
def novel_detail(request, novel_id):
    novel = get_object_or_404(Novel, id=novel_id)
    chapters = novel.chapters.all().order_by('order')
    
    is_bookmarked = False
    if request.user.is_authenticated:
        is_bookmarked = Bookmark.objects.filter(user=request.user, novel=novel).exists()

    context = {
        'novel': novel, 
        'chapters': chapters, 
        'is_bookmarked': is_bookmarked,
        **get_common_context()
    }
    return render(request, 'library/detail.html', context)

def read_chapter(request, chapter_id):
    chapter = get_object_or_404(Chapter, id=chapter_id)
    novel = chapter.novel
    prev_chap = novel.chapters.filter(order__lt=chapter.order).last()
    next_chap = novel.chapters.filter(order__gt=chapter.order).first()
    
    response = render(request, 'library/read.html', {
        'novel': novel, 'chapter': chapter, 'prev': prev_chap, 'next': next_chap,
        **get_common_context()
    })

    # Simpan History ke Cookie
    history_cookie = request.COOKIES.get('zn_history', '{}')
    try: data = json.loads(history_cookie)
    except: data = {}
    data[str(novel.id)] = chapter.id
    response.set_cookie('zn_history', json.dumps(data), max_age=2592000) 
    
    return response

# --- VIEW AUTH (LOGIN/LOGOUT/REGISTER) ---

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            if 'next' in request.GET: return redirect(request.GET['next'])
            return redirect('home')
    else: form = AuthenticationForm()
    # Title diubah ke Inggris
    return render(request, 'library/auth.html', {'form': form, 'title': 'Login', **get_common_context()})

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else: form = UserCreationForm()
    # Title diubah ke Inggris
    return render(request, 'library/auth.html', {'form': form, 'title': 'Register', **get_common_context()})

def logout_view(request):
    logout(request)
    return redirect('home')

# --- FITUR LAIN ---
@csrf_exempt
def rate_novel(request, novel_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            score = int(data.get('score', 0))
            if not request.session.session_key: request.session.create()
            session_key = request.session.session_key
            novel = Novel.objects.get(id=novel_id)
            NovelVote.objects.update_or_create(novel=novel, session_key=session_key, defaults={'score': score})
            return JsonResponse({'status': 'ok', 'new_avg': novel.average_rating()})
        except: pass
    return JsonResponse({'status': 'error'})

@login_required(login_url='/login/')
def toggle_bookmark(request, novel_id):
    novel = get_object_or_404(Novel, id=novel_id)
    bookmark = Bookmark.objects.filter(user=request.user, novel=novel).first()
    if bookmark: bookmark.delete()
    else: Bookmark.objects.create(user=request.user, novel=novel)
    return redirect('novel_detail', novel_id=novel.id)

@login_required(login_url='/login/')
def my_library(request):
    bookmarks = Bookmark.objects.filter(user=request.user).select_related('novel')
    return render(request, 'library/my_library.html', {'bookmarks': bookmarks, **get_common_context()})
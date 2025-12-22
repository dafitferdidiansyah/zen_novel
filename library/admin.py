from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Novel, Chapter, Bookmark, UserSettings, Comment, Tag, NovelVote
from .utils import generate_chapters, get_epub_metadata

# =====================================================
# 1. TAG ADMIN
# =====================================================
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

# =====================================================
# 2. NOVEL ADMIN (VERSI RINGAN & CEPAT)
# =====================================================
@admin.register(Novel)
class NovelAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'view_chapters_link', 'uploaded_at')
    search_fields = ('title', 'author')
    list_filter = ('status', 'genre', 'uploaded_at')
    filter_horizontal = ('tags',)
    
    # HAPUS INLINE (BIANG KEROK LEMOT)
    # inlines = [ChapterInline] 
    
    # Kita ganti dengan tombol custom
    readonly_fields = ('view_chapters_link', 'views', 'rating_score')

    # --- FITUR TOMBOL PINTAR ---
    def view_chapters_link(self, obj):
        count = obj.chapters.count()
        # Membuat URL ke halaman list chapter, difilter by id novel ini
        url = (
            reverse("admin:library_chapter_changelist")
            + f"?novel__id__exact={obj.id}"
        )
        return format_html(
            '<a class="button" href="{}" style="background-color:#417690; color:white; padding:5px 10px; border-radius:5px; text-decoration:none;">Edit {} Chapters</a>',
            url,
            count
        )
    view_chapters_link.short_description = "Chapters"
    view_chapters_link.allow_tags = True

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        
        # Proses EPUB
        if 'epub_file' in form.changed_data and obj.epub_file:
            try:
                meta = get_epub_metadata(obj.epub_file.path)
                updated = False
                if not obj.title or obj.title in ["New Novel", "."]:
                    if meta.get('title'): obj.title = meta['title']; updated = True
                if not obj.author or obj.author == "Unknown":
                    if meta.get('author'): obj.author = meta['author']; updated = True
                if not obj.synopsis:
                    if meta.get('synopsis'): obj.synopsis = meta['synopsis']; updated = True
                
                if updated: obj.save()

                obj.chapters.all().delete()
                generate_chapters(obj)
                self.message_user(request, f"Sukses ekstrak chapter dari {obj.epub_file.name}", level='SUCCESS')
            except Exception as e:
                self.message_user(request, f"Gagal proses EPUB: {e}", level='ERROR')

# =====================================================
# 3. CHAPTER ADMIN (TEMPAT EDIT MASAL)
# =====================================================
@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    # Tampilkan kolom yang penting
    list_display = ('title', 'novel', 'order', 'chapter_index')
    
    # FITUR EDIT DI LIST (EDITABLE LIST)
    # Ini memungkinkan edit judul/urutan LANGSUNG di tabel daftar tanpa masuk detail
    list_editable = ('order', 'chapter_index', 'title') 
    
    search_fields = ('title', 'novel__title') 
    list_filter = ('novel',)
    autocomplete_fields = ['novel'] 
    
    # Pagination (50 item per halaman biar ringan)
    list_per_page = 50 
    ordering = ('novel', 'order')

# =====================================================
# 4. ADMIN LAINNYA
# =====================================================
@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'novel', 'last_read_chapter', 'updated_at')
    search_fields = ('user__username', 'novel__title')
    autocomplete_fields = ['user', 'novel', 'last_read_chapter']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'text_snippet', 'created_at')
    search_fields = ('text', 'user__username')
    
    def text_snippet(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text

@admin.register(NovelVote)
class NovelVoteAdmin(admin.ModelAdmin):
    list_display = ('novel', 'user', 'score', 'created_at')

@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'theme')
    search_fields = ('user__username',)
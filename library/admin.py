from django.contrib import admin
from .models import Novel, Chapter, Bookmark, UserSettings, Comment, Tag, NovelVote
from .utils import generate_chapters, get_epub_metadata

# =====================================================
# 1. INLINE: FITUR ADD MULTI CHAPTER
# =====================================================
# Ini membuat Anda bisa menambah/edit banyak chapter 
# langsung di dalam halaman edit Novel.
class ChapterInline(admin.TabularInline):
    model = Chapter
    fields = ('title', 'order', 'chapter_index')
    extra = 1 # Jumlah baris kosong default untuk tambah baru
    show_change_link = True # Tombol untuk edit detail chapter

# =====================================================
# 2. TAG ADMIN
# =====================================================
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

# =====================================================
# 3. NOVEL ADMIN (DENGAN FITUR EPUB PROCESSOR)
# =====================================================
@admin.register(Novel)
class NovelAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'total_chapters', 'views', 'uploaded_at')
    search_fields = ('title', 'author')
    list_filter = ('status', 'genre', 'tags', 'uploaded_at')
    filter_horizontal = ('tags',)
    
    # Masukkan ChapterInline ke sini agar muncul di bawah Novel
    inlines = [ChapterInline] 

    # Field yang hanya bisa dibaca (statistik)
    readonly_fields = ('views', 'rating_score')

    def total_chapters(self, obj):
        return obj.chapters.count()
    total_chapters.short_description = 'Chapters'

    def save_model(self, request, obj, form, change):
        # 1. Simpan file fisik dulu
        super().save_model(request, obj, form, change)

        # 2. Cek apakah ada file epub baru yang diupload
        if 'epub_file' in form.changed_data and obj.epub_file:
            try:
                # Ambil Metadata
                meta = get_epub_metadata(obj.epub_file.path)
                
                updated = False
                
                # Isi Metadata Otomatis
                if not obj.title or obj.title in ["New Novel", "."]:
                    if meta.get('title'):
                        obj.title = meta['title']
                        updated = True
                
                if not obj.author or obj.author == "Unknown":
                    if meta.get('author'):
                        obj.author = meta['author']
                        updated = True

                if not obj.synopsis:
                    if meta.get('synopsis'):
                        obj.synopsis = meta['synopsis']
                        updated = True
                
                if updated:
                    obj.save()

                # 3. Generate Chapters (Hapus lama, buat baru)
                # Warning: Ini akan menghapus chapter manual jika file epub diupdate
                obj.chapters.all().delete()
                generate_chapters(obj)
                
                self.message_user(request, f"Berhasil mengekstrak chapter dari {obj.epub_file.name}", level='SUCCESS')
                
            except Exception as e:
                self.message_user(request, f"Gagal proses EPUB: {e}", level='ERROR')

# =====================================================
# 4. CHAPTER ADMIN (FITUR SEARCH CHAPTER)
# =====================================================
@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('title', 'novel_link', 'order', 'chapter_index', 'uploaded_at')
    
    # --- FITUR SEARCH ---
    # Bisa cari berdasarkan judul chapter ATAU judul novelnya
    search_fields = ('title', 'novel__title') 
    
    list_filter = ('uploaded_at',)
    
    # Optimasi: Jika novel ada ribuan, pakai input search box, bukan dropdown
    autocomplete_fields = ['novel'] 
    
    list_per_page = 50 # Pagination biar loading enteng
    ordering = ('novel', 'order')

    # Helper untuk link ke novel agar mudah diklik
    def novel_link(self, obj):
        return obj.novel.title
    novel_link.short_description = 'Novel'
    novel_link.admin_order_field = 'novel__title'

# =====================================================
# 5. KOMENTAR, BOOKMARK, VOTE, USER SETTINGS
# =====================================================
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'novel_title', 'text_snippet', 'created_at')
    search_fields = ('text', 'user__username', 'chapter__novel__title')
    list_filter = ('created_at',)
    autocomplete_fields = ['chapter', 'user'] # Optimasi loading

    def novel_title(self, obj):
        if obj.chapter and obj.chapter.novel:
            return obj.chapter.novel.title
        return "-"
    
    def text_snippet(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text

@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'novel', 'chapter', 'created_at')
    search_fields = ('user__username', 'novel__title')
    autocomplete_fields = ['user', 'novel', 'chapter']

@admin.register(NovelVote)
class NovelVoteAdmin(admin.ModelAdmin):
    list_display = ('novel', 'user', 'score', 'created_at')
    list_filter = ('score',)

@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'theme', 'font_size')
    search_fields = ('user__username',)
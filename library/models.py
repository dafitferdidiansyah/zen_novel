from django.db import models
from django.db.models import Avg
from django.contrib.auth.models import User
from django.core.files import File # Tambahkan ini
from PIL import Image              # Tambahkan ini
from io import BytesIO
import os

class Tag(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

class Novel(models.Model):
    STATUS_CHOICES = [('Ongoing', 'Ongoing'), ('Completed', 'Completed')]
    
    title = models.CharField(max_length=255, blank=True, default="New Novel") 
    author = models.CharField(max_length=255, default="Unknown", blank=True)
    alternative_title = models.CharField(max_length=500, blank=True, null=True, help_text="Judul Asli / Jepang / Sinonim")
    synopsis = models.TextField(blank=True, null=True, help_text="Ringkasan cerita")
    genre = models.CharField(max_length=100, default="Action", help_text="Contoh: Fantasy, Romance")
    tags = models.ManyToManyField(Tag, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Ongoing')
    cover = models.ImageField(upload_to='covers/', null=True, blank=True)
    
    # Metadata Baru untuk Sorting
    views = models.IntegerField(default=0)
    rating_score = models.FloatField(default=0.0)
    
    epub_file = models.FileField(upload_to='epubs/', null=True, blank=True, help_text="Upload .epub/.txt di sini")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 
    def save(self, *args, **kwargs):
	if not self.alternative_title or self.alternative_title == "{title}":
            self.alternative_title = self.title
        # Jalankan kompresi jika ada file cover dan file tersebut baru/berubah
        if self.cover:
            self.compress_cover()
        super().save(*args, **kwargs)

    def compress_cover(self):
        """
        Fungsi untuk mengubah cover menjadi WebP dan kompresi kualitas
        """
        img = Image.open(self.cover)
        
        # Jika gambar dalam mode RGBA (transparan), ubah ke RGB agar bisa disimpan WebP dengan baik
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Proses Kompresi
        temp_handle = BytesIO()
        # Quality 70-80 sudah sangat cukup untuk web, method 6 adalah kompresi terlambat (paling kecil)
        img.save(temp_handle, format='WebP', quality=80, method=6)
        temp_handle.seek(0)

        # Ganti nama file menjadi .webp
        current_name = os.path.splitext(self.cover.name)[0]
        new_name = f"{current_name}.webp"

        # Simpan kembali ke field cover tanpa memicu save() berulang (save=False)
        self.cover.save(new_name, File(temp_handle), save=False)
    def average_rating(self):
        # Hitung rata-rata dari tabel votes
        avg = self.votes.aggregate(Avg('score'))['score__avg']
        return round(avg, 1) if avg else 0.0

    def __str__(self):
        return self.title

class Chapter(models.Model):
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name='chapters')
    title = models.CharField(max_length=255)
    content = models.TextField()
    order = models.FloatField(default=0.0)
    chapter_index = models.FloatField(default=0, help_text="Nomor asli dari judul chapter")
    uploaded_at = models.DateTimeField(auto_now_add=True) 

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.novel.title} - {self.title}"

class NovelVote(models.Model):
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE) # Sekarang pakai User
    score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('novel', 'user')

class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name='bookmarked_by')
    
    # Progress Bacaan (HISTORY)
    last_read_chapter = models.ForeignKey(Chapter, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)  # Waktu terakhir baca
    
    # Status Koleksi (LIBRARY)
    # Default False, artinya kalau cuma baca doang ga otomatis masuk library visual
    is_in_library = models.BooleanField(default=False) 

    class Meta:
        ordering = ['-updated_at']
        unique_together = ('user', 'novel') # Satu user satu entry per novel

    def __str__(self):
        return f"{self.user.username} - {self.novel.title}"

class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    font_size = models.IntegerField(default=18)
    line_height = models.FloatField(default=1.8)
    theme = models.CharField(max_length=20, default='dark') 
    
    def __str__(self):
        return f"Settings for {self.user.username}"

# Tambahkan di library/models.py

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.chapter.title}"
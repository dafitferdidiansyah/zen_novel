from django.db import models
from django.db.models import Avg
from django.contrib.auth.models import User
from django.core.files import File
from PIL import Image
from io import BytesIO
import os


# =========================
# TAG
# =========================
class Tag(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


# =========================
# NOVEL
# =========================
class Novel(models.Model):
    STATUS_CHOICES = [
        ('Ongoing', 'Ongoing'),
        ('Completed', 'Completed'),
    ]

    title = models.CharField(max_length=255, blank=True, default="New Novel")
    author = models.CharField(max_length=255, blank=True, default="Unknown")
    alternative_title = models.CharField(max_length=500, blank=True, null=True)
    synopsis = models.TextField(blank=True, null=True)
    genre = models.CharField(max_length=100, default="Action")
    tags = models.ManyToManyField(Tag, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Ongoing')
    cover = models.ImageField(upload_to='covers/', null=True, blank=True)

    views = models.IntegerField(default=0)
    rating_score = models.FloatField(default=0.0)

    epub_file = models.FileField(upload_to='epubs/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # =========================
    # SAVE OVERRIDE (SATU-SATUNYA)
    # =========================
    def save(self, *args, **kwargs):
        is_new_cover = False

        # Deteksi cover baru / diganti
        if self.pk:
            old = Novel.objects.get(pk=self.pk)
            if old.cover != self.cover:
                is_new_cover = True
                if old.cover:
                    old.cover.delete(save=False)
        else:
            if self.cover:
                is_new_cover = True

        if (
            not self.alternative_title
            or self.alternative_title == "New Novel"
        ):
            if self.title and self.title != "New Novel":
                self.alternative_title = self.title

        super().save(*args, **kwargs)

        # Kompres setelah file benar-benar tersimpan
        if is_new_cover:
            self.compress_cover()

    # =========================
    # COVER → WEBP
    # =========================
    def compress_cover(self):
        if not self.cover:
            return

        # Skip jika sudah WebP
        if self.cover.name.lower().endswith('.webp'):
            return

        try:
            img = Image.open(self.cover)

            # Pastikan RGB
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            buffer = BytesIO()
            img.save(buffer, format='WEBP', quality=80, method=6)
            buffer.seek(0)

            base, _ = os.path.splitext(self.cover.name)
            new_name = base + '.webp'

            # Ganti file
            self.cover.delete(save=False)
            self.cover.save(new_name, File(buffer), save=False)

            # Update DB tanpa trigger save() ulang
            super().save(update_fields=['cover'])

        except Exception as e:
            print(f"[WEBP ERROR] {e}")

    def average_rating(self):
        avg = self.votes.aggregate(Avg('score'))['score__avg']
        return round(avg, 1) if avg else 0.0

    def __str__(self):
        return self.title


# =========================
# CHAPTER
# =========================
class Chapter(models.Model):
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name='chapters')
    title = models.CharField(max_length=255)
    content = models.TextField()
    order = models.FloatField(default=0.0)
    chapter_index = models.FloatField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.novel.title} - {self.title}"


# =========================
# VOTE
# =========================
class NovelVote(models.Model):
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('novel', 'user')


# =========================
# BOOKMARK
# =========================
class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name='bookmarked_by')
    last_read_chapter = models.ForeignKey(Chapter, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_in_library = models.BooleanField(default=False)

    class Meta:
        ordering = ['-updated_at']
        unique_together = ('user', 'novel')

    def __str__(self):
        return f"{self.user.username} - {self.novel.title}"


# =========================
# USER SETTINGS
# =========================
class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    font_size = models.IntegerField(default=18)
    line_height = models.FloatField(default=1.8)
    theme = models.CharField(max_length=20, default='dark')

    def __str__(self):
        return f"Settings for {self.user.username}"


# =========================
# COMMENT
# =========================
class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.chapter.title}"

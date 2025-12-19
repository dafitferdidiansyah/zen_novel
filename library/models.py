from django.db import models
from django.db.models import Avg
from django.contrib.auth.models import User

class Novel(models.Model):
    STATUS_CHOICES = [('Ongoing', 'Ongoing'), ('Completed', 'Completed')]
    
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, default="Unknown")
    synopsis = models.TextField(blank=True, null=True, help_text="Ringkasan cerita")
    genre = models.CharField(max_length=100, default="Action", help_text="Contoh: Fantasy, Romance")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Ongoing')
    cover = models.ImageField(upload_to='covers/', null=True, blank=True)
    
    # File Upload untuk Admin (Auto generate chapter)
    epub_file = models.FileField(upload_to='epubs/', null=True, blank=True, help_text="Upload .epub/.txt di sini")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def average_rating(self):
        avg = self.votes.aggregate(Avg('score'))['score__avg']
        return round(avg, 1) if avg else 0.0

    def __str__(self):
        return self.title

class Chapter(models.Model):
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name='chapters')
    title = models.CharField(max_length=255)
    content = models.TextField()
    order = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True) 

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.novel.title} - {self.title}"

class NovelVote(models.Model):
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name='votes')
    session_key = models.CharField(max_length=40)
    score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('novel', 'session_key')

class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE)
    last_read_chapter = models.ForeignKey(Chapter, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'novel')
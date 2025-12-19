from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from library import views as html_views
from library import api_views as json_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- WEBSITE HTML ---
    path('', html_views.home, name='home'),
    path('search/', html_views.search, name='search'),  # <--- Ini yang bikin error tadi
    path('novel/<int:novel_id>/', html_views.detail, name='detail'),
    path('read/<int:novel_id>/<int:chapter_id>/', html_views.read_chapter, name='read'),
    path('bookmark/<int:novel_id>/', html_views.toggle_bookmark, name='toggle_bookmark'),

    # --- API ENDPOINTS ---
    path('api/novels/', json_views.novel_list, name='api_novel_list'),
    path('api/novels/<int:pk>/', json_views.novel_detail, name='api_novel_detail'),
    path('api/chapters/<int:pk>/', json_views.chapter_detail, name='api_chapter_detail'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
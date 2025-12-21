from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from library import api_views as json_views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- API ENDPOINTS ---
    path('api/home/', json_views.home_data, name='api_home_data'),
    path('api/novels/', json_views.novel_list, name='api_novel_list'),
    path('api/novels/<int:pk>/', json_views.novel_detail, name='api_novel_detail'),
    path('api/chapters/<int:pk>/', json_views.chapter_detail, name='api_chapter_detail'),

    # --- AUTH & USER ---
    path('api/register/', json_views.register_api, name='api_register'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # --- LIBRARY & HISTORY (Logika Baru) ---
    # Menggunakan 'get_bookmarks' sesuai yang ada di api_views.py
    path('api/bookmarks/', json_views.get_bookmarks, name='api_get_bookmarks'),
    
    # Toggle Bookmark & Update Progress
    path('api/bookmarks/toggle/<int:novel_id>/', json_views.toggle_bookmark, name='api_toggle_bookmark'),
    path('api/progress/<int:novel_id>/<int:chapter_id>/', json_views.update_progress, name='api_update_progress'),
    
    # Endpoint History (Konsisten pakai prefix api/)
    path('api/history/', json_views.get_history, name='api_get_history'),

    # User Settings
    path('api/user/settings/', json_views.user_settings_api, name='api_user_settings'),

    # --- COMMENTS ---
    path('api/comments/<int:chapter_id>/', json_views.get_chapter_comments, name='api_get_comments'),
    path('api/comments/post/<int:chapter_id>/', json_views.post_chapter_comment, name='api_post_comment'),
    path('api/comments/delete/<int:comment_id>/', json_views.delete_comment, name='api_delete_comment'),

    # --- RATING, GENRES & TAGS ---
    path('api/novels/<int:pk>/rate/', json_views.rate_novel, name='api_rate_novel'),
    path('api/tag/<slug:tag_slug>/', json_views.novels_by_tag, name='api_novels_by_tag'),
    path('api/genres/', json_views.genre_list_api, name='genre-list-api'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
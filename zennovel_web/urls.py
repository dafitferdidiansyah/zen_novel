from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from library import views as html_views
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
    path('api/bookmarks/', json_views.user_bookmarks, name='api_user_bookmarks'),
    path('api/bookmarks/toggle/<int:pk>/', json_views.toggle_bookmark_api, name='api_toggle_bookmark'),
    path('api/progress/<int:novel_id>/<int:chapter_id>/', json_views.update_progress, name='api_update_progress'),
    path('api/user/settings/', json_views.user_settings_api, name='api_user_settings'),

    # --- COMMENTS ---
    path('api/comments/<int:chapter_id>/', json_views.get_chapter_comments, name='api_get_comments'),
    path('api/comments/post/<int:chapter_id>/', json_views.post_chapter_comment, name='api_post_comment'),
    path('api/comments/delete/<int:comment_id>/', json_views.delete_comment, name='api_delete_comment'),

    # --- HTML LAMA (Opsional) ---
    path('', html_views.home, name='home'),
    path('search/', html_views.search, name='search'),
    path('novel/<int:novel_id>/', html_views.detail, name='detail'),
    path('read/<int:novel_id>/<int:chapter_id>/', html_views.read_chapter, name='read'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
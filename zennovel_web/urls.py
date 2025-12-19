from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Import file view API yang baru kita buat
from library import api_views 
from library import views # View lama (HTML)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- JALUR WEBSITE LAMA (HTML) ---
    # (Biarkan ini tetap ada supaya admin panel & web lama jalan)
    path('', views.home, name='home'),
    # ... url html lainnya boleh dibiarkan atau dikomentari ...

    # --- JALUR API BARU (JSON) ---
    # Frontend React akan menembak ke sini
    path('api/novels/', api_views.novel_list, name='api_novel_list'),
    path('api/novels/<int:pk>/', api_views.novel_detail, name='api_novel_detail'),
    path('api/chapters/<int:pk>/', api_views.chapter_detail, name='api_chapter_detail'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
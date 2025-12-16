from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('novel/<int:novel_id>/', views.novel_detail, name='novel_detail'),
    path('chapter/<int:chapter_id>/', views.read_chapter, name='read_chapter'),
    path('search/', views.search_view, name='search'),
    
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'), # <-- Pastikan ini pakai views.logout_view
    path('register/', views.register_view, name='register'),
    
    # Features
    path('bookmark/<int:novel_id>/', views.toggle_bookmark, name='toggle_bookmark'),
    path('my-library/', views.my_library, name='my_library'),
    path('api/rate/<int:novel_id>/', views.rate_novel, name='rate_novel'),
]
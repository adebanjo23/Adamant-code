from django.urls import path
from .views import create_post, delete_post, edit_post, get_posts

urlpatterns = [
    path('create_post/', create_post, name='create_post'),
    path('delete_post/', delete_post, name='delete_post'),
    path('edit_post/', edit_post, name='edit_post'),
    path('get_posts/', get_posts, name='get_posts'),
]
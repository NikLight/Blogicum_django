from django.urls import path

from . import views
from .views import (ProfileDetailView,
                    EditProfileView,
                    PostCreateView,
                    PostDetailView,
                    IndexView,
                    CategoryPostsView)

app_name = 'blog'

urlpatterns = [
    path('category/<slug:category_slug>/',
         CategoryPostsView.as_view(),
         name='category_posts'),
    path('', IndexView.as_view(), name='index'),
    path('posts/<int:post_id>/', PostDetailView.as_view(), name='post_detail'),
    path('posts/create/', PostCreateView.as_view(), name='create_post'),
    path('posts/<int:post_id>/edit/',
         views.EditPostView.as_view(), name='edit_post'),
    path('posts/<int:post_id>/delete/',
         views.DeletePostView.as_view(), name='delete_post'),

    path('posts/<int:post_id>/comment/',
         views.CommentPostView.as_view(), name='add_comment'),
    path('posts/<int:post_id>/edit_comment/<int:comment_id>/',
         views.CommentEditView.as_view(), name='edit_comment'),
    path('posts/<int:post_id>/delete_comment/<int:comment_id>/',
         views.CommentDeleteView.as_view(), name='delete_comment'),

    path('profile/<slug:username>/',
         ProfileDetailView.as_view(), name='profile'),
    path('edit-profile/<slug:username>/',
         EditProfileView.as_view(), name='edit_profile'),

]

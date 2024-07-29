from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.views.generic import (UpdateView, DeleteView,
                                  DetailView, CreateView, ListView)

from .forms import PostForm, UserForm, CommentForm
from .models import Post, Category, User, Comment


class OnlyAuthorMixin(UserPassesTestMixin):
    """Mixin, проверяющий, что текущий пользователь является автором."""

    def test_func(self):
        """Проверяет, что автор совпадает с текущим пользователем."""
        obj = self.get_object()
        return obj.author == self.request.user


class ProfileDetailView(DetailView):
    """Представление для отображения профиля пользователя и его постов."""

    model = User
    template_name = 'blog/profile.html'
    context_object_name = 'profile'
    success_url = reverse_lazy('profile', kwargs={'username': 'username'})

    def get_object(self):
        """Возвращает объект User по имени пользователя."""
        username = self.kwargs.get('username')
        return get_object_or_404(User, username=username)

    def get_context_data(self, **kwargs):
        """
        Добавляет в контекст данные о постах пользователя
        и объект пагинации.
        """
        context = super().get_context_data(**kwargs)
        user = self.object
        posts = Post.objects.filter(author=user).annotate(
            comment_count=Count('comments')).order_by('-pub_date')
        context['posts'] = posts
        context['page_obj'] = self.paginate_posts(context['posts'])
        return context

    def paginate_posts(self, posts):
        """
        Пагинирует список постов
        и возвращает объект текущей страницы.
        """
        paginator = Paginator(posts, 10)
        page_number = self.request.GET.get('page')
        return paginator.get_page(page_number)


class EditProfileView(LoginRequiredMixin, UpdateView):
    """Представление для редактирования профиля пользователя."""

    model = User
    form_class = UserForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        """Возвращает текущего авторизованного пользователя."""
        return self.request.user

    def get_success_url(self):
        """
        Возвращает URL для перенаправления
        после успешного сохранения изменений.
        """
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.object.username})


def get_filtered_posts():
    """
    Возвращает список опубликованных постов,
    отсортированных по дате публикации.
    """
    return Post.objects.select_related(
        'author', 'category', 'location'
    ).filter(
        is_published=True,
        pub_date__lt=now(),
        category__is_published=True
    ).annotate(comment_count=Count('comments')).order_by('-pub_date')


class IndexView(ListView):
    """Представление для отображения списка постов на главной странице."""

    template_name = 'blog/index.html'
    context_object_name = 'page_obj'
    paginate_by = settings.MAX_POSTS

    def get_queryset(self):
        """Возвращает отфильтрованные посты для главной страницы."""
        return get_filtered_posts()

    def get_context_data(self, **kwargs):
        """Добавляет в контекст объект пагинации для списка постов."""
        context = super().get_context_data(**kwargs)
        filtered_posts = self.get_queryset()
        paginator = Paginator(filtered_posts, self.paginate_by)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
        return context


class CategoryPostsView(ListView):
    """Представление для отображения постов в определённой категории."""

    template_name = 'blog/category.html'
    context_object_name = 'post_list'
    paginate_by = settings.MAX_POSTS

    def get_queryset(self):
        """Возвращает отфильтрованные посты для указанной категории."""
        category_slug = self.kwargs.get('category_slug')
        category = get_object_or_404(
            Category, slug=category_slug, is_published=True)
        return get_filtered_posts().filter(category=category)

    def get_context_data(self, **kwargs):
        """Добавляет в контекст информацию о категории."""
        context = super().get_context_data(**kwargs)
        category_slug = self.kwargs.get('category_slug')
        context['category'] = get_object_or_404(
            Category, slug=category_slug, is_published=True)
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    """Представление для создания нового поста."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        """Устанавливает текущего пользователя в качестве автора поста."""
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        """
        Возвращает URL для перенаправления
        после успешного создания поста.
        """
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username})


class EditPostView(LoginRequiredMixin, OnlyAuthorMixin, UpdateView):
    """Представление для редактирования поста."""

    model = Post
    pk_url_kwarg = 'post_id'
    form_class = PostForm
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        """
        Проверяет, что пользователь аутентифицирован
        и является автором поста.
        """
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        post = self.get_object()
        if post.author != self.request.user:
            return redirect('blog:post_detail', post_id=post.pk)
        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission(self):
        """Перенаправляет на страницу входа, если доступ запрещён."""
        return redirect('login')


class DeletePostView(LoginRequiredMixin, OnlyAuthorMixin, DeleteView):
    """Представление для удаления поста."""

    model = Post
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')


class PostDetailView(LoginRequiredMixin, DetailView):
    """Представление для отображения детальной информации о посте."""

    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_object(self, queryset=None):
        """
        Возвращает объект поста,
        если он доступен текущему пользователю.
        """
        post = super().get_object(queryset)

        if post.author != self.request.user and (
            not post.is_published
            or not post.category.is_published
            or post.pub_date > now()
        ):
            raise Http404
        return post

    def get_context_data(self, **kwargs):
        """
        Добавляет в контекст форму для
        комментариев и список комментариев.
        """
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related('author')
        return context


class CommentPostView(LoginRequiredMixin, CreateView):
    """Представление для создания нового комментария к посту."""

    model = Comment
    form_class = CommentForm

    def form_valid(self, form):
        """
        Устанавливает текущего пользователя
        как автора комментария и сохраняет его.
        """
        post_id = self.kwargs['post_id']
        post = get_object_or_404(Post, id=post_id)
        form.instance.author = self.request.user
        form.instance.post = post
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        """
        Возвращает URL для перенаправления
        после успешного создания комментария.
        """
        post_id = self.kwargs['post_id']
        return reverse_lazy('blog:post_detail',
                            kwargs={'post_id': post_id})


class CommentEditView(LoginRequiredMixin, UpdateView):
    """Представление для редактирования комментария."""

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_object(self, queryset=None):
        """
        Возвращает комментарий,
        если он принадлежит текущему пользователю.
        """
        comment = super().get_object(queryset)
        if comment.author != self.request.user:
            raise PermissionDenied(
                "Вы не можете редактировать этот комментарий")
        return comment

    def get_success_url(self):
        """
        Возвращает URL для перенаправления
        после успешного редактирования комментария.
        """
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': self.object.post.id})


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    """Представление для удаления комментария."""

    model = Comment
    pk_url_kwarg = 'comment_id'
    template_name = 'blog/comment.html'

    def get_object(self, queryset=None):
        """
        Возвращает комментарий,
        если он принадлежит текущему пользователю.
        """
        comment = super().get_object()
        if comment.author != self.request.user:
            raise PermissionDenied(
                "Вы не можете удалить этот комментарий")
        return comment

    def get_context_data(self, **kwargs):
        """
        Убирает форму из контекста,
        чтобы отображался только процесс удаления комментария.
        """
        context = super().get_context_data(**kwargs)
        context['form'] = None
        return context

    def get_success_url(self):
        """
        Возвращает URL для перенаправления
        после успешного удаления комментария.
        """
        return reverse_lazy('blog:post_detail',
                            kwargs={'post_id': self.object.post.id})

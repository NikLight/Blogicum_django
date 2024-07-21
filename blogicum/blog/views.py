from django.conf import settings

from django.http import HttpResponse, HttpRequest
from django.shortcuts import render, get_object_or_404
from django.utils.timezone import now

from .models import Post, Category


def get_filtered_posts():
    return Post.objects.select_related(
        'author', 'category', 'location',
    ).filter(
        is_published=True,
        pub_date__lt=now(),
        category__is_published=True,
    )


def index(request: HttpRequest) -> HttpResponse:
    posts = get_filtered_posts()[:settings.MAX_POSTS]

    return render(
        request, 'blog/index.html', {'post_list': posts}
    )


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category, slug=category_slug, is_published=True)
    posts = get_filtered_posts().filter(category=category)
    context = {
        'category': category,
        'post_list': posts,
    }
    return render(request, 'blog/category.html', context)


def post_detail(request: HttpRequest, post_id: int) -> HttpResponse:
    post = get_object_or_404(get_filtered_posts(), id=post_id)
    return render(
        request, 'blog/detail.html', {'post': post}
    )

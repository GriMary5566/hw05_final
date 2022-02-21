from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import get_page_obj


def index(request):
    template = 'posts/index.html'

    post_list = Post.objects.select_related('group', 'author')
    page_number = request.GET.get('page')
    page_obj = get_page_obj(page_number, post_list)
    index = True

    context = {'page_obj': page_obj, 'index': index}
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'

    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author')
    page_number = request.GET.get('page')
    page_obj = get_page_obj(page_number, post_list)

    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'

    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    page_number = request.GET.get('page')
    page_obj = get_page_obj(page_number, post_list)
    if not request.user.is_authenticated:
        following = None
    else:
        following = author.following.filter(user=request.user).exists()

    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'

    form = CommentForm(request.POST or None)
    post = get_object_or_404(Post, id=post_id)
    text = post.text
    num_posts = post.author.posts.count()
    post_comments = post.comments.all()

    context = {
        'post': post,
        'text': text,
        'num_posts_by_author': num_posts,
        'form': form,
        'comments': post_comments
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/post_create.html'

    if request.method != 'POST':
        form = PostForm()
        return render(request, template, {'form': form})

    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if not form.is_valid():
        return render(request, template, {'form': form})

    post = form.save(commit=False)
    post.author = request.user
    form.save(commit=True)
    return redirect('posts:profile', username=request.user)


@login_required
def post_edit(request, post_id):
    template = 'posts/post_create.html'

    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)

    is_edit = True
    if request.method != 'POST':
        form = PostForm(instance=post)
        context = {
            'form': form,
            'is_edit': is_edit,
            'post_id': post_id
        }
        return render(request, template, context)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if not form.is_valid():
        context = {
            'form': form,
            'is_edit': is_edit,
            'post_id': post_id
        }
        return render(request, template, context)

    form.save()
    return redirect('posts:post_detail', post_id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'

    following = request.user.follower.values_list('author')
    post_list = Post.objects.select_related('group', 'author').filter(
        author_id__in=following
    )
    page_number = request.GET.get('page')
    page_obj = get_page_obj(page_number, post_list)
    follow = True

    context = {'page_obj': page_obj, 'follow': follow}
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    is_exist = Follow.objects.filter(
        user=request.user, author=author
    ).exists()
    if request.user != author and not is_exist:
        Follow.objects.get_or_create(
            user=request.user,
            author=author
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    delete_author = Follow.objects.filter(user=request.user, author=author)
    delete_author.delete()
    return redirect('posts:profile', username=username)

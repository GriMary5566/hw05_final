from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import QuerySet

from .models import Post


def get_page_obj(
    page_number: int,
    post_list: QuerySet,
    num_posts: int = settings.NUM_POSTS
) -> Post:
    paginator: Paginator = Paginator(post_list, num_posts)
    page_obj: Post = paginator.get_page(page_number)
    return page_obj

from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='boss')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.posts = list(Post(
            text='Тестовый текст %s' % i,
            author=cls.user,
            group=cls.group
        ) for i in range(13))
        Post.objects.bulk_create(cls.posts)
        cls.url_names = {
            'posts:index': None,
            'posts:group_list': {'slug': cls.group.slug},
            'posts:profile': {'username': cls.user.username},
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        """Paginator для первой страницы index, group_list и profile работает
        корректно.На страницу выводится десять последних из тринадцати постов.
        Сортировка по убыванию.
        """
        EXPECTED_NUM_POSTS = 10
        for reverse_name, params in self.url_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(
                    reverse(reverse_name, kwargs=params)
                )
                num_posts = len(response.context['page_obj'])
                expected_post_text = Post.objects.get(id=13).text
                post_text = response.context.get(
                    'page_obj'
                ).object_list[0].text
                self.assertEqual(num_posts, EXPECTED_NUM_POSTS)
                self.assertTrue(post_text, 'Пост не передан на страницу')
                self.assertIsNotNone(post_text, 'Пост не передан на страницу')
                self.assertEqual(post_text, expected_post_text)

    def test_second_page_contains_three_records(self):
        """Paginator для второй страницы index, group_list и profile работает
        корректно. На страницу выводится три первых из тринадцати постов.
        Сортировка по убыванию.
        """
        EXPECTED_NUM_POSTS = 3
        for reverse_name, params in self.url_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(
                    reverse(reverse_name, kwargs=params), {'page': '2'}
                )
                num_posts = len(response.context['page_obj'])
                expected_post_text = Post.objects.get(id=1).text
                post_text = response.context.get(
                    'page_obj').object_list[2].text
                self.assertEqual(num_posts, EXPECTED_NUM_POSTS)
                self.assertTrue(post_text, 'Пост не передан на страницу')
                self.assertIsNotNone(post_text, 'Пост не передан на страницу')
                self.assertEqual(post_text, expected_post_text)

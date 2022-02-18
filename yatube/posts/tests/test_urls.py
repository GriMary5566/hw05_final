from http import HTTPStatus

from django.test import Client, TestCase

from ..models import Group, Post, User


class PostsUrlTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='boss')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
            id=1,
        )
        cls.url_index = ('/', 'posts/index.html',)
        cls.url_profile = (
            f'/profile/{cls.user.username}/',
            'posts/profile.html',
        )
        cls.url_posts = (f'/posts/{cls.post.id}/', 'posts/post_detail.html',)
        cls.url_group = (f'/group/{cls.group.slug}/', 'posts/group_list.html',)
        cls.url_create = ('/create/', 'posts/post_create.html',)
        cls.url_edit = (
            f'/posts/{cls.post.id}/edit/',
            'posts/post_create.html',
        )
        cls.url_comment = (
            f'/posts/{cls.post.id}/comment/',
            'posts/post_detail.html',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = PostsUrlTest.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_posts_urls_exists_at_desired_location_for_all(self):
        """Страницы доступны любому пользователю."""
        urls_names = [
            PostsUrlTest.url_index,
            PostsUrlTest.url_profile,
            PostsUrlTest.url_posts,
            PostsUrlTest.url_group,
        ]
        for url, _ in urls_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_unexisting_page(self):
        """Несуществующая страница вернет ошибку 404."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_posts_create_url_exists_at_desired_location(self):
        """Страница создания поста доступна авторизованному пользователю."""
        response = self.authorized_client.get(PostsUrlTest.url_create[0])
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_edit_url_exists_at_desired_location(self):
        """Страница редактирования поста доступна автору."""
        response = self.authorized_client.get(PostsUrlTest.url_edit[0])
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_create_url_redirect_anonymous_on_auth_login(self):
        """Страница /create/ перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.guest_client.get(
            PostsUrlTest.url_create[0],
            follow=True
        )
        self.assertRedirects(
            response, '/auth/login/?next=/create/')

    def test_posts_edit_url_redirect_anonymous_on_auth_login(self):
        """Страница /edit/ перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.guest_client.get(PostsUrlTest.url_edit[0], follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/posts/1/edit/')

    def test_posts_edit_redirect_is_not_author_on_posts_1(self):
        """Страница posts/1/edit/ перенаправит неавтора поста
        на страницу posts/1/.
        """
        self.user_another = User.objects.create_user(username='another')
        self.authorized_client_another = Client()
        self.authorized_client_another.force_login(self.user_another)
        response = self.authorized_client_another.get(
            PostsUrlTest.url_edit[0], follow=True)
        self.assertRedirects(
            response, '/posts/1/')

    def test_posts_urls_uses_correct_template(self):
        """URL-адрес приложения posts использует соответствующий шаблон."""
        url_templates_names = [
            PostsUrlTest.url_index,
            PostsUrlTest.url_profile,
            PostsUrlTest.url_posts,
            PostsUrlTest.url_group,
            PostsUrlTest.url_create,
            PostsUrlTest.url_edit,
        ]
        for url, template in url_templates_names:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_posts_comment_url_redirect_anonymous_on_auth_login(self):
        """Страница /comment/ перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.guest_client.get(
            PostsUrlTest.url_comment[0],
            follow=True
        )
        self.assertRedirects(
            response, '/auth/login/?next=/posts/1/comment/'
        )

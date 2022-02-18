from http import HTTPStatus

from django.test import Client, TestCase
from posts.models import Group, Post, User


class UsersUrlTest(TestCase):
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
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = UsersUrlTest.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_users_urls_exists_at_desired_location_for_all(self):
        """Страницы доступны любому пользователю.
        Несуществующая страница вернет ошибку 404
        """
        expected_response_status_code = {
            '/auth/signup/': HTTPStatus.OK.value,
            '/auth/login/': HTTPStatus.OK.value,
            '/auth/unexisting_page/': HTTPStatus.NOT_FOUND.value
        }
        for url, code in expected_response_status_code.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, code)

    # Проверяем доступность страниц для авторизованного пользователя
    def test_users_urls_exists_at_desired_location_for_autorized(self):
        """Страницы доступны авторизированному пользователю."""
        expected_response_status_code = {
            '/auth/logout/': HTTPStatus.OK.value,
            '/auth/password_reset/': HTTPStatus.OK.value,
            '/auth/password_reset/done/': HTTPStatus.OK.value,
            '/auth/reset/<uidb64>/<token>/': HTTPStatus.OK.value,
        }
        for url, code in expected_response_status_code.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, code)

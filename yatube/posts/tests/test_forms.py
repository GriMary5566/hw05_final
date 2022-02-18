from http import HTTPStatus
import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
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
            id=1
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = PostFormTest.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_valid_form_create_post(self):
        """Валидная форма создает запись в Post."""
        small_gif = (
             b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст 2',
            'group': PostFormTest.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        expected_post = Post.objects.get(id=2)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(expected_post.text, form_data['text'])
        self.assertEqual(expected_post.author, self.user)
        self.assertEqual(expected_post.group.id, form_data['group'])
        self.assertEqual(expected_post.image, 'posts/small.gif')

    def test_valid_form_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        form_data = {
            'text': 'Отредактированный тестовый текст',
            'group': PostFormTest.group.id,
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': 1}),
            data=form_data,
            follow=True
        )
        edit_post = Post.objects.get(id=1)
        new_text = edit_post.text
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': 1}
            )
        )
        self.assertEqual(new_text, form_data['text'])
        self.assertTrue(
            Post.objects.filter(
                text='Отредактированный тестовый текст',
                id=1
            ).exists()
        )

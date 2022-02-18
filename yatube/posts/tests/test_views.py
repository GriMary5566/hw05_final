from http import HTTPStatus
import shutil

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django import forms
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Follow, Group, Post, User
from .test_forms import TEMP_MEDIA_ROOT


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


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTest(TestCase):
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
        cls.index_url = ('posts:index', None, 'posts/index.html')
        cls.group_list_url = (
            'posts:group_list',
            (cls.group.slug,),
            'posts/group_list.html'
        )
        cls.profile_url = (
            'posts:profile',
            (cls.user.username,),
            'posts/profile.html'
        )
        cls.post_detail_url = (
            'posts:post_detail',
            (cls.post.id,),
            'posts/post_detail.html'
        )
        cls.post_create_url = (
            'posts:post_create',
            None,
            'posts/post_create.html'
        )
        cls.post_edit_url = (
            'posts:post_edit',
            (cls.post.id,),
            'posts/post_create.html'
        )
        cls.post_comment_url = (
            'posts:post_comment',
            (cls.post.id,),
            'posts/post_detail.html',
        )
        cls.follow_url = (
            'posts:follow_index',
            None,
            'posts/follow.html',
        )
        cls.profile_follow_url = (
            'posts:profile_follow',
            (cls.user.username,),
        )
        cls.profile_unfollow_url = (
            'posts:profile_unfollow',
            (cls.user.username,),
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_posts_pages_uses_correct_template(self):
        """URL-адрес view-функции использует соответствующий шаблон."""
        urls_list = [
            self.index_url,
            self.group_list_url,
            self.profile_url,
            self.post_detail_url,
            self.post_create_url,
            self.post_edit_url
        ]
        for url_name, params, template in urls_list:
            with self.subTest(template=template):
                response = self.authorized_client.get(
                    reverse(url_name, args=params)
                )
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_index_pages_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(self.index_url[0]))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object, self.post)

    def test_group_post_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(self.group_list_url[0], args=self.group_list_url[1])
        )
        group_field = response.context['group']
        self.assertEqual(group_field, self.group)
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object, self.post)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом.
        Для авторизированного пользователя в контекст передается правильное
        значение для following.
        """
        response = self.authorized_client.get(
            reverse(self.profile_url[0], args=self.profile_url[1])
        )
        author_field = response.context['author']
        first_object = response.context['page_obj'][0]
        following_field = response.context['following']
        self.assertEqual(author_field, self.user)
        self.assertEqual(first_object, self.post)
        self.assertIsNotNone(
            following_field,
            'Значение для following не задано'
        )

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(self.post_detail_url[0], args=self.post_detail_url[1])
        )
        post_field = response.context['post']
        text_field = response.context['text']
        num_posts_field = response.context['num_posts_by_author']
        expected_num_posts = self.user.posts.count()
        self.assertEqual(post_field, self.post)
        self.assertEqual(text_field, 'Тестовый текст')
        self.assertEqual(num_posts_field, expected_num_posts)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create для создания поста сформирован
        с правильным контекстом.
        """
        response = self.authorized_client.get(reverse(self.post_create_url[0]))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_create для редактирования поста сформирован
        с правильным контекстом.
        """
        response = self.authorized_client.get(
            reverse(self.post_edit_url[0], args=self.post_edit_url[1])
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                form_field_text = response.context['form'].initial['text']
                form_field_group = response.context['form'].initial['group']
                self.assertIsInstance(form_field, expected)
                self.assertEqual(form_field_text, self.post.text)
                self.assertEqual(form_field_group, self.group.id)
        is_edit_field = response.context['is_edit']
        post_id_field = response.context['post_id']
        self.assertTrue(is_edit_field)
        self.assertEqual(post_id_field, self.post.id)

    def test_new_post_is_correct_visible(self):
        """Новый пост с указанной группой появляется на страницах index,
        profile, правильной странице group_list.
        """
        # Проверяем, что создание нового поста увеличило количество постов
        # на главной странице, на странице выбранной группы, в профайле
        # пользователя и не изменило число постов на странице другой группы.
        group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-two-slug',
            description='Тестовое описание',
        )
        self.post_new = Post.objects.create(
            text='Тестовый текст 2',
            author=self.user,
            group=group_2
        )
        group_list_2_url = (
            'posts:group_list',
            (group_2.slug,),
            'posts/group_list.html'
        )
        expected_num_posts = {
            self.index_url: 2,
            self.group_list_url: 1,
            group_list_2_url: 1,
            self.profile_url: 2
        }
        for url_name, num in expected_num_posts.items():
            with self.subTest(page_name=url_name[0]):
                response = self.authorized_client.get(
                    reverse(url_name[0], args=url_name[1])
                )
                received_num_posts = (len(response.context['page_obj']))
                self.assertEqual(received_num_posts, num)

    def test_posts_pages_with_image_show_correct_context(self):
        """При выводе поста с картинкой изображение передается в context."""
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
        post_with_image = Post.objects.create(
            text='Тест с картинкой',
            author=self.user,
            group=self.group,
            image=uploaded
        )
        post_detail_image_url = (
            'posts:post_detail',
            (post_with_image.id,),
            'posts/post_detail.html'
        )
        expected_posts_image_url = [
            self.index_url,
            self.profile_url,
            self.group_list_url,
            post_detail_image_url
        ]
        for url_name in expected_posts_image_url:
            with self.subTest(page_name=url_name[0]):
                response = self.authorized_client.get(
                    reverse(url_name[0], args=url_name[1])
                )
                if url_name == post_detail_image_url:
                    image_field = response.context['post'].image
                else:
                    image_field = response.context['page_obj'][0].image
                self.assertEqual(image_field, post_with_image.image)

    def test_comment_is_correct_visible(self):
        """Созданный комментарий появляется на странице поста."""
        response = self.authorized_client.get(
            reverse(self.post_detail_url[0], args=self.post_detail_url[1])
        )
        initial_num_comments = (len(response.context['comments']))
        new_comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            text='Тестовый комментарий',
            id=1,
        )
        response = self.authorized_client.get(
            reverse(self.post_detail_url[0], args=self.post_detail_url[1])
        )
        received_num_comments = len(response.context['comments'])
        received_text_comment = response.context['comments'][0].text
        received_author_comment = response.context['comments'][0].author

        self.assertEqual(received_num_comments, initial_num_comments + 1)
        self.assertEqual(received_text_comment, new_comment.text)
        self.assertEqual(received_author_comment, new_comment.author)

    def test_cache_index_page(self):
        """Страница index кэшируется."""
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        cache_expected = response.content
        post = Post.objects.get(pk=1)
        post.delete()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.content, cache_expected)
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, cache_expected)

    def test_authorized_client_can_follow_unfollow(self):
        """Авторизованный пользователь может подписываться на других пользователей
        и удалять их из подписок.
        """
        follower = User.objects.create_user(username='Follower')
        authorized_follower = Client()
        authorized_follower.force_login(follower)
        self.response = authorized_follower.get(
            reverse(
                self.profile_follow_url[0],
                args=self.profile_follow_url[1]
            )
        )
        self.assertTrue(
            Follow.objects.filter(
                user=follower,
                author=self.user,
                id=1
            ).exists()
        )
        self.response = authorized_follower.get(
            reverse(
                self.profile_unfollow_url[0],
                args=self.profile_unfollow_url[1]
            )
        )
        self.assertFalse(
            Follow.objects.filter(
                user=follower,
                author=self.user,
                id=1
            ).exists()
        )

    def test_follow_index_new_post_is_correct_visible(self):
        """Новая запись пользователя появляется в ленте тех, кто на него подписан
        и не появляется в ленте тех, кто не подписан.
        """
        follower = User.objects.create_user(username='Follower')
        authorized_follower = Client()
        authorized_follower.force_login(follower)

        not_follower = User.objects.create_user(username='NotFollower')
        authorized_not_follower = Client()
        authorized_not_follower.force_login(not_follower)

        selected_author = self.user
        self.follow = Follow.objects.create(
            user=follower,
            author=selected_author
        )
        users = [authorized_follower, authorized_not_follower]
        for user in users:
            with self.subTest(user=user):
                response = user.get(reverse(self.follow_url[0]))
                initial_num_posts = len(response.context['page_obj'])
                new_post_by_selected_author = Post.objects.create(
                    text='Тестовый текст для подписчика',
                    author=selected_author,
                )
                response = user.get(reverse(self.follow_url[0]))
                received_num_posts = len(response.context['page_obj'])
                self.assertEqual(response.status_code, HTTPStatus.OK)
                if user == authorized_follower:
                    self.assertEqual(received_num_posts, initial_num_posts + 1)
                    self.assertEqual(
                        response.context['page_obj'][0].text,
                        new_post_by_selected_author.text
                    )
                else:
                    self.assertEqual(received_num_posts, initial_num_posts)

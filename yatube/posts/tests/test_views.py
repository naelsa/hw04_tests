import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Post, Group, Comment, Follow

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.guest_user = Client()
        cls.author = User.objects.create_user(username='test_user')
        cls.image = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='test.gif',
            content=cls.image,
            content_type='image/gif'
        )
        cls.uploaded2 = SimpleUploadedFile(
            name='test_2.gif',
            content=cls.image,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа2',
            slug='test_slug2',
            description='Тестовое описание2',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text='Тестовый пост',
            image=cls.uploaded,
        )
        cls.post_2 = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text='Тестовый пост',
            image=cls.uploaded2,
        )
        cls.comment = Comment.objects.create(
            text='Тестовый коммент',
            post=cls.post_2,
            author=cls.author
        )

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)
        self.page_names = (
            ('posts:index', None, 'posts/index.html'),
            ('posts:group_list', (self.group.slug,), 'posts/group_list.html'),
            ('posts:profile', (self.author.username,), 'posts/profile.html'),
            ('posts:post_detail', (self.post.id,), 'posts/post_detail.html'),
            ('posts:post_create', None, 'posts/create_post.html'),
            ('posts:post_edit', (self.post.id,), 'posts/create_post.html'),
        )
        self.post_forms = (
            ('posts:post_create', None, PostForm),
            ('posts:post_edit', (self.post.id,), PostForm),
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for reverse_name, args, template in self.page_names:
            with self.subTest():
                response = self.authorized_author.get(
                    reverse(viewname=reverse_name, args=args)
                )
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def contexts(self, response, post_1=False):
        post_context = (
            response.context['post']
            if post_1
            else response.context['page_obj'][0]
        )
        self.assertEqual(post_context.text, self.post.text)
        self.assertEqual(post_context.author, self.author)
        self.assertEqual(post_context.group, self.group)
        self.assertEqual(
            post_context.pub_date.strftime("%Y-%m-%d-%H.%M.%S"),
            self.post.pub_date.strftime("%Y-%m-%d-%H.%M.%S")
        ),
        self.assertEqual(post_context.image, self.post_2.image)

    def test_index_pages_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_author.get(reverse('posts:index'))
        self.contexts(response)

    def test_post_detail_show_correct_context(self):
        """Шаблон просмотра поста сформирован с правильным контекстом."""
        response = self.authorized_author.get(
            reverse('posts:post_detail', args=(self.post_2.id,))
        )
        self.assertEqual(response.context['comments'][0], self.comment)
        self.assertEqual(len(response.context['comments']), 1)
        self.contexts(response, True)

    def test_group_pages_show_correct_context(self):
        """Шаблон группы сформирован с правильным контекстом."""
        response = self.authorized_author.get(
            reverse('posts:group_list', args=(self.group.slug,))
        )
        self.assertEqual(response.context['group'], self.group)
        self.contexts(response)

    def test_profile_correct_context(self):
        """Шаблон профиля сформирован с правильным контекстом"""
        response = self.authorized_author.get(
            reverse('posts:profile', args=(self.author,))
        )
        self.assertEqual(response.context['author'], self.author)
        self.contexts(response)

    def test_post_another_group(self):
        """Пост не попал в другую группу."""
        response = self.authorized_author.get(
            reverse('posts:group_list', args=(self.group_2.slug,))
        )
        self.assertNotIn(self.post, response.context['page_obj'])
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_edit_and_create_post_show_correct_context(self):
        """Шаблон создания и редактирования поста
        сформирован с правильным контекстом.
        """
        for name, args, form in self.post_forms:
            with self.subTest(name=name):
                response = self.authorized_author.get(reverse(name, args=args))
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], form)

    def test_cache_index(self):
        """Проверка хранения и очищения кэша для index."""
        response = self.authorized_author.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='test_new_post',
            author=self.author,
        )
        response_old = self.authorized_author.get(reverse('posts:index'))
        old_posts = response_old.content
        self.assertEqual(old_posts, posts)
        cache.clear()
        response_new = self.authorized_author.get(reverse('posts:index'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts)


class PaginatorViewsTest(TestCase):
    ALL_POSTS_AMOUNT: int = 13

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_user2')
        cls.group = Group.objects.create(
            title='Тестовая группа2',
            slug='test_slug2',
            description='Тестовое описание2')
        cls.posts = [
            Post(
                text=f'Тестовый пост {num}',
                author=cls.author,
                group=cls.group
            ) for num in range(cls.ALL_POSTS_AMOUNT)
        ]
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.list_urls = (
            ('posts:index', None),
            ('posts:group_list', (self.group.slug,)),
            ('posts:profile', (self.author.username,)),
        )

    def test_first_page_contains_ten_posts(self):
        """Первая страница содержит 10 постов."""
        for name, args, in self.list_urls:
            with self.subTest():
                response = self.client.get(
                    reverse(viewname=name, args=args))
                self.assertEqual(
                    len(response.context['page_obj']), settings.POSTS_PER_PAGE)

    def test_second_page_contains_three_posts(self):
        """Вторая страница содержит 3 поста."""
        second_page_amount = self.ALL_POSTS_AMOUNT - settings.POSTS_PER_PAGE
        for name, args in self.list_urls:
            with self.subTest():
                response = self.client.get(
                    f'{reverse(viewname=name, args=args)}?page=2')
                self.assertEqual(
                    len(response.context['page_obj']), second_page_amount)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.author = User.objects.create_user(
            username='test_author'
        )
        cls.auth_author_client = Client()
        cls.auth_author_client.force_login(cls.author)

        cls.user_follow = User.objects.create_user(
            username='test_user_follow'
        )
        cls.authorized_user_follow_client = Client()
        cls.authorized_user_follow_client.force_login(cls.user_follow)

        cls.user_unfollow = User.objects.create_user(
            username='test_user_unfollow'
        )
        cls.authorized_user_unfollow_client = Client()
        cls.authorized_user_unfollow_client.force_login(cls.user_unfollow)
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
            description='test_description'
        )
        cls.post = Post.objects.create(
            text='test_post',
            group=cls.group,
            author=cls.author
        )

    def test_follow(self):
        """Тест работы подписки на автора."""
        self.authorized_user_unfollow_client.get(
            reverse(
                'posts:profile_follow',
                args=(self.author.username,)
            )
        )
        follower = Follow.objects.filter(
            user=self.user_unfollow,
            author=self.author
        ).exists()
        self.assertTrue(follower)

    def test_unfollow(self):
        """Тест работы отписки от автора."""
        self.authorized_user_unfollow_client.get(
            reverse('posts:profile_unfollow', args=(self.author.username,))
        )
        follower = Follow.objects.filter(
            user=self.user_unfollow,
            author=self.author
        ).exists()
        self.assertFalse(follower)

    def test_new_author_post_for_follower(self):
        self.authorized_user_follow_client.get(
            reverse('posts:profile_follow', args=(self.author.username,))
        )
        response_old = self.authorized_user_follow_client.get(
            reverse('posts:follow_index')
        )
        old_posts = response_old.context.get(
            'page_obj'
        ).object_list
        self.assertEqual(
            len(response_old.context.get('page_obj').object_list), 1
        )
        self.assertIn(
            FollowViewsTest.post,
            old_posts,
            'Старый пост не верен'
        )
        new_post = Post.objects.create(
            text='test_new_post',
            group=self.group,
            author=self.author
        )
        cache.clear()
        response_new = self.authorized_user_follow_client.get(
            reverse('posts:follow_index')
        )
        new_posts = response_new.context.get(
            'page_obj'
        ).object_list
        self.assertEqual(
            len(response_new.context.get('page_obj').object_list), 2
        )
        self.assertIn(new_post, new_posts)

    def test_new_author_post_for_not_follower(self):
        response_old = self.authorized_user_unfollow_client.get(
            reverse('posts:follow_index')
        )
        old_posts = response_old.context.get(
            'page_obj'
        ).object_list
        self.assertEqual(
            len(response_old.context.get('page_obj').object_list), 0
        )
        self.assertNotIn(FollowViewsTest.post, old_posts)
        new_post = Post.objects.create(
            text='test_new_post',
            group=self.group,
            author=self.author
        )
        cache.clear()
        response_new = self.authorized_user_unfollow_client.get(
            reverse('posts:follow_index')
        )
        new_posts = response_new.context.get(
            'page_obj'
        ).object_list
        self.assertEqual(
            len(response_new.context.get('page_obj').object_list), 0
        )
        self.assertNotIn(new_post, new_posts)

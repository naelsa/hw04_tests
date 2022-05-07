from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Post, Group

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_user')
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
        self.assertEqual(post_context.pub_date, self.post.pub_date)

    def test_index_pages_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_author.get(reverse('posts:index'))
        self.contexts(response)

    def test_post_detail_show_correct_context(self):
        """Шаблон просмотра поста сформирован с правильным контекстом."""
        response = self.authorized_author.get(
            reverse('posts:post_detail', args=(self.post.id,))
        )
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
        """Шаблон просмотра поста сформирован с правильным контекстом."""
        for name, args, form in self.post_forms:
            with self.subTest(name=name):
                response = self.authorized_author.get(reverse(name, args=args))
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], form)


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

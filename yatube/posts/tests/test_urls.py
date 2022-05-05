from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase, Client

from ..models import Group, Post

User = get_user_model()


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_user')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )
        cls.not_author = User.objects.create_user(username='test_user2')

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.author)
        self.not_author_client = Client()
        self.not_author_client.force_login(self.not_author)
        self.reverse_name = (
            ('posts:index', None, '/'),
            ('posts:group_list', (self.group.slug,),
             f'/group/{self.group.slug}/'),
            ('posts:profile', (self.author.username,),
             f'/profile/{self.author.username}/'),
            ('posts:post_detail', (self.post.id,),
             f'/posts/{self.post.id}/'),
            ('posts:post_create', None, '/create/'),
            ('posts:post_edit', (self.post.id,),
             f'/posts/{self.post.id}/edit/'),
        )

    def test_urls_accessible_for_authorized(self):
        """Страница доступны авторизованному пользователю."""
        for name, args, url in self.reverse_name:
            with self.subTest():
                self.assertEqual(reverse(name, args=args), url)

    def test_urls_has_code_200_author(self):
        """URL доступны для автора."""
        for name, args, _ in self.reverse_name:
            with self.subTest():
                response = self.author_client.get(
                    reverse(viewname=name, args=args)
                )
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_has_code_200_not_author(self):
        """URL доступны для не автора, кроме post_edit."""
        for name, args, _ in self.reverse_name:
            with self.subTest():
                response = self.not_author_client.get(
                    reverse(viewname=name, args=args)
                )
                if 'posts:post_edit' in name:
                    self.assertEqual(response.status_code, HTTPStatus.FOUND)
                    self.assertRedirects(response, f'/posts/{self.post.id}/')
                else:
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_for_unauthorized(self):
        """URL доступны для неавторизованного клиента,
        кроме post_create и post_edit.
        """
        for name, args, _ in self.reverse_name:
            with self.subTest():
                response = self.client.get(
                    reverse(viewname=name, args=args)
                )
                if 'posts:post_edit' in name:
                    self.assertEqual(response.status_code, HTTPStatus.FOUND)
                    self.assertRedirects(
                        response,
                        f'/auth/login/?next=/posts/{self.post.id}/edit/'
                    )
                elif 'posts:post_create' in name:
                    self.assertEqual(response.status_code, HTTPStatus.FOUND)
                    self.assertRedirects(
                        response,
                        '/auth/login/?next=/create/'
                    )
                else:
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_page_404(self):
        """При запросе несуществующей страницы сервер возвращает код 404."""
        response = self.client.get('/lol_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

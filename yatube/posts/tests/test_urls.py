from http import HTTPStatus

from django.contrib.auth import get_user_model, REDIRECT_FIELD_NAME
from django.test import TestCase, Client
from django.urls import reverse

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

    def test_urls_match(self):
        """Запрашиваемые URL соответствуют URL из списка."""
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
                    self.assertRedirects(
                        response, (reverse
                                   ('posts:post_detail', args=(self.post.id,)))
                    )
                else:
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_for_unauthorized(self):
        """post_create и post_edit перенаправляютя на страницу авторизации,
        остльные URL доступны для неавторизованного клиента.
        """
        login_url = reverse('users:login')
        for name, args, _ in self.reverse_name:
            with self.subTest():
                response = self.client.get(
                    reverse(viewname=name, args=args),
                )
                if name in ['posts:post_edit', 'posts:post_create']:
                    self.assertEqual(response.status_code, HTTPStatus.FOUND)
                    self.assertRedirects(
                        response,
                        (f'{login_url}?{REDIRECT_FIELD_NAME}='
                         f'{reverse(viewname=name, args=args)}')
                    )
                else:
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_page_404(self):
        """При запросе несуществующей страницы сервер возвращает код 404."""
        response = self.client.get('/lol_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

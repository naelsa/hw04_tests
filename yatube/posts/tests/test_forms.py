from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='test_slug2',
            description='Тестовое описание2',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст',
            group=cls.group
        )
        cls.form = PostForm()

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_auth_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тест поста',
            'group': self.group.id
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('posts:profile', args=(self.author,))
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=self.group.id,
                text='Тест поста'
            ).exists()
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

        post = Post.objects.first()

        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.group, self.group)

    def test_guest_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тест поста',
            'group': self.group.id
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )
        self.assertFalse(
            Post.objects.filter(
                group=self.group.id,
                text='Тест поста'
            ).exists()
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_auth_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тест редактирования',
            'group': self.group2.id
        }
        response = self.author_client.post(
            reverse('posts:post_edit', args=(self.post.pk,)),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('posts:post_detail', args=(self.post.pk,))
        )
        self.assertTrue(
            Post.objects.filter(
                group=self.group2.id,
                text='Тест редактирования'
            ).exists()
        )
        self.assertFalse(
            Post.objects.filter(
                group=self.group.id,
                text='Тест поста'
            ).exists()
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        post = Post.objects.first()

        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.group, self.group2)

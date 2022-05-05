from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = self.post
        group = self.group
        field_title_text = (
            (post.text, post.text[:15],),
            (group.title, group.title,),
        )
        for value, expected in field_title_text:
            with self.subTest(value=value):
                self.assertEqual(value, str(expected))

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = self.post
        field_verbose = (
            ('text', 'Текст',),
            ('pub_date', 'Дата публикации',),
            ('author', 'Автор',),
            ('group', 'Группа',),
        )
        for value, expected in field_verbose:
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = self.post
        field_help_texts = (
            ('text', 'Напишите текст поста',),
            ('group', 'Группа, к которой относится запись',),
        )
        for value, expected in field_help_texts:
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)

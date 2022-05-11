from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import UniqueConstraint

User = get_user_model()


class Group(models.Model):

    title = models.CharField(
        'Название',
        max_length=200
    )
    slug = models.SlugField(
        'Слаг',
        unique=True
    )
    description = models.TextField(
        'Описание'
    )

    class Meta:
        verbose_name = 'Сообщество'
        verbose_name_plural = 'Сообщества'

    def __str__(self):
        return f'{self.title}'


class Post(models.Model):

    text = models.TextField(
        'Текст',
        help_text='Напишите текст поста'
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Группа',
        help_text='Группа, к которой относится запись'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        verbose_name = 'Запись'
        verbose_name_plural = 'Записи'
        ordering = ('-pub_date',)

    def __str__(self):
        return f'{self.text[:30]}'


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        verbose_name='Комментарий',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField(
        verbose_name='Текст комментария.',
        help_text='Напишите текст комментария'
    )
    created = models.DateTimeField(
        'date_created',
        auto_now_add=True
    )

    class Meta:
        ordering = ('-created',)


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        related_name='follower',
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        related_name='following',
        on_delete=models.CASCADE,
    )

    class Meta:
        UniqueConstraint(fields=['user', 'author'], name='unique_follower')

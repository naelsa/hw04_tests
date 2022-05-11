from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        labels = {
            'group': 'Группа',
            'text': 'Текст нового поста',
            'image': 'Изображение'
        }
        help_texts = {
            'group': 'Выберите группу',
            'text': 'Введите текст',
            'image': 'Выберите изображение'
        }
        fields = ('text', 'group', 'image')


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)

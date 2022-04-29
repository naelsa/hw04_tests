from django import forms

from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        labels = {
            'group': 'Группа',
            'text': 'Текст нового поста'
        }
        help_texts = {'group': 'Выберите группу', 'text': 'Введите текст'}
        fields = ('text', 'group')

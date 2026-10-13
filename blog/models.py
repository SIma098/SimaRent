from django.conf import settings
from django.db import models
from django.utils import timezone


class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Post.Status.PUBLISHED)


class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DF', 'Черновик'
        PUBLISHED = 'PB', 'Опубликован'

    title = models.CharField(
        max_length=250,
        verbose_name='Заголовок'
    )
    slug = models.SlugField(
        max_length=250,
        verbose_name='Слаг'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blog_posts',
        verbose_name='Автор'
    )
    body = models.TextField(
        verbose_name='Текст'
    )
    publish = models.DateTimeField(
        default=timezone.now,
        verbose_name='Дата публикации'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создан'
    )
    updated = models.DateTimeField(
        auto_now=True,
        verbose_name='Изменён'
    )
    status = models.CharField(
        max_length=2,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name='Статус'
    )

    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        ordering = ['-publish']
        indexes = [
            models.Index(fields=['-publish']),
        ]
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.slug

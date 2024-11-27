from django.contrib.auth.models import AbstractUser
from django.db import models

from core.constants import MAX_LENGTH_EMAIL, MAX_LENGTH_USER_FIELD
from core.validators import avatar_extension_validator, username_validator


class CustomUser(AbstractUser):
    email = models.EmailField(
        verbose_name='адрес электронной почты',
        unique=True,
        max_length=MAX_LENGTH_EMAIL,
    )
    username = models.CharField(
        verbose_name='уникальный юзернейм',
        max_length=MAX_LENGTH_USER_FIELD,
        unique=True,
        validators=[username_validator],
    )
    first_name = models.CharField(
        verbose_name='имя', max_length=MAX_LENGTH_USER_FIELD
    )
    last_name = models.CharField(
        verbose_name='фамилия', max_length=MAX_LENGTH_USER_FIELD
    )
    avatar = models.ImageField(
        upload_to='users/',
        verbose_name='аватар',
        null=True,
        blank=True,
        validators=[avatar_extension_validator],
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['id']

    def __str__(self):
        return self.username


class Follow(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='подписчик',
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='автор',
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        default_related_name = 'follows'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_follow'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='prevent_self_follow',
            ),
        ]

    def __str__(self):
        return f'{self.user} подписан на {self.author}'

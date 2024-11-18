from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator, FileExtensionValidator


class CustomUser(AbstractUser):
    email = models.EmailField(
        verbose_name='адрес электронной почты', unique=True, max_length=254
    )
    username = models.CharField(
        verbose_name='уникальный юзернейм',
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message=(
                    'Имя пользователя может содержать только буквы, '
                    'цифры и символы @/./+/-/_'
                ),
            )
        ],
    )
    first_name = models.CharField(verbose_name='имя', max_length=150)
    last_name = models.CharField(verbose_name='фамилия', max_length=150)
    avatar = models.ImageField(
        upload_to='users/avatars/',
        verbose_name='аватар',
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png']),
        ],
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
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
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

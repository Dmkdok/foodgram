from users.models import Follow


class SubscriptionCheckMixin:
    """Миксин для проверки подписки пользователя на автора."""

    def is_subscribed(self, author=None):
        """
        Проверяет, подписан ли пользователь на автора.
        Если автор не передан, берется из контекста.
        """
        user = self.context['request'].user
        author = author or self.context['view'].get_object()
        return Follow.objects.filter(user=user, author=author).exists()

import re

from django.core.exceptions import ValidationError
from rest_framework import serializers
from users.models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=254)

    def validate_username(self, value):
        if value.lower() == 'me':
            raise ValidationError('Имя пользователя "me" недопустимо.')

        if not re.fullmatch(r'^[\w.@+-]+$', value):
            raise ValidationError(
                'Имя пользователя может содержать только '
                'буквы, цифры и символы @/./+/-/_'
            )
        return value

    class Meta:
        model = CustomUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
        )

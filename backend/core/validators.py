from django.core.validators import (
    FileExtensionValidator,
    MaxValueValidator,
    MinValueValidator,
    RegexValidator,
)

from core.constants import (
    ALLOWED_EXTENSIONS,
    MAX_COOKING_TIME,
    MAX_INGRDEINTS_AMOUNT,
    MIN_COOKING_TIME,
    MIN_INGRDEINTS_AMOUNT,
)

username_validator = RegexValidator(
    regex=r'^[\w.@+-]+$',
    message=(
        'Имя пользователя может содержать только буквы, '
        'цифры и символы @/./+/-/_'
    ),
)

avatar_extension_validator = FileExtensionValidator(
    allowed_extensions=ALLOWED_EXTENSIONS
)


max_amount_validator = MaxValueValidator(
    MAX_INGRDEINTS_AMOUNT,
    message=(f'Время не должно превышать {MAX_INGRDEINTS_AMOUNT} минут!'),
)


min_amount_validator = MinValueValidator(
    MIN_INGRDEINTS_AMOUNT,
    message=(f'Количество должно быть больше {MIN_INGRDEINTS_AMOUNT}!'),
)


min_cooking_time_validator = MinValueValidator(
    MIN_COOKING_TIME,
    message=f'Время должно быть больше {MIN_COOKING_TIME}!',
)


max_cooking_time_validator = MaxValueValidator(
    MAX_COOKING_TIME,
    message=f'Время не должно превышать {MAX_COOKING_TIME} минут!',
)

# Generated by Django 3.2 on 2024-11-15 17:43

import django.core.validators
from django.db import migrations, models
import django.db.models.expressions


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20241114_2241'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='first_name',
            field=models.CharField(max_length=150, verbose_name='имя'),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='last_name',
            field=models.CharField(max_length=150, verbose_name='фамилия'),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='username',
            field=models.CharField(max_length=150, unique=True, validators=[django.core.validators.RegexValidator(message='Имя пользователя может содержать только буквы, цифры и символы @/./+/-/_', regex='^[\\w.@+-]+$')], verbose_name='уникальный юзернейм'),
        ),
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.CheckConstraint(check=models.Q(_negated=True, user=django.db.models.expressions.F('author')), name='prevent_self_follow'),
        ),
    ]

import json
import os
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Load ingredients from JSON file'

    def handle(self, *args, **kwargs):
        # Получаем корневую директорию проекта
        base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

        # Путь к файлу ingredients.json
        file_path = os.path.join(
            base_dir, '..', '..', 'data', 'ingredients.json'
        )

        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'File {file_path} does not exist')
            )
            return

        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        for item in data:
            name = item.get('name')
            measurement_unit = item.get('measurement_unit')

            if not name or not measurement_unit:
                self.stdout.write(
                    self.style.WARNING(f'Skipping incomplete item: {item}')
                )
                continue

            ingredient, created = Ingredient.objects.update_or_create(
                name=name,
                measurement_unit=measurement_unit,
                defaults={'name': name, 'measurement_unit': measurement_unit},
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created ingredient: {name} ({measurement_unit})'
                    )
                )
            else:
                self.stdout.write(
                    self.style.NOTICE(
                        f'Updated ingredient: {name} ({measurement_unit})'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS('Ingredients loaded successfully')
        )

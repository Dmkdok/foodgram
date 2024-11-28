import json
import os

from django.core.management.base import BaseCommand
from tqdm import tqdm

from recipes.models import Ingredient, Tag


class Command(BaseCommand):
    help = 'Load ingredients from JSON file'

    def handle(self, *args, **kwargs):
        base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

        # Путь к файлу ingredients.json
        ingredients_file_path = os.path.join(
            base_dir, '..', 'data', 'ingredients.json'
        )

        # Путь к файлу tags.json
        tags_file_path = os.path.join(base_dir, '..', 'data', 'tags.json')

        # Загрузка ингредиентов
        if not os.path.exists(ingredients_file_path):
            self.stdout.write(
                self.style.ERROR(
                    f'File {ingredients_file_path} does not exist'
                )
            )
            return

        with open(ingredients_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        if not data:
            self.stdout.write(
                self.style.WARNING('No ingredients found in the file.')
            )
            return

        self.stdout.write(f'Processing {len(data)} ingredients...')

        for item in tqdm(data, desc="Loading ingredients"):
            name = item.get('name')
            measurement_unit = item.get('measurement_unit')

            if not name or not measurement_unit:
                continue

            Ingredient.objects.update_or_create(
                name=name,
                measurement_unit=measurement_unit,
                defaults={'name': name, 'measurement_unit': measurement_unit},
            )

        self.stdout.write(
            self.style.SUCCESS('Ingredients loaded successfully')
        )

        # Загрузка тегов
        if not os.path.exists(tags_file_path):
            self.stdout.write(
                self.style.ERROR(f'File {tags_file_path} does not exist')
            )
            return

        with open(tags_file_path, 'r', encoding='utf-8') as file:
            tags_data = json.load(file)

        if not tags_data:
            self.stdout.write(self.style.WARNING('No tags found in the file.'))
            return

        self.stdout.write(f'Processing {len(tags_data)} tags...')

        for item in tqdm(tags_data, desc="Loading tags"):
            name = item.get('name')
            slug = item.get('slug')

            if not name or not slug:
                continue

            Tag.objects.update_or_create(
                name=name,
                slug=slug,
                defaults={'name': name, 'slug': slug},
            )

        self.stdout.write(self.style.SUCCESS('Tags loaded successfully'))

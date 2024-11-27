import json
import os

from django.core.management.base import BaseCommand
from tqdm import tqdm

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Load ingredients from JSON file'

    def handle(self, *args, **kwargs):
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

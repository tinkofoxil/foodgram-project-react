import os
import json

from django.core.management.base import BaseCommand

from recipes.models import Ingredient
from foodgram.settings import BASE_DIR


class Command(BaseCommand):
    """Запись данных из json-файла в БД."""

    help = 'Write data from json file to database.'

    def handle(self, *args, **options):
        json_name = 'ingredients.json'
        location_json = os.path.join(
            BASE_DIR,
            'data/',
            json_name
        )
        with open(location_json, encoding='utf-8') as json_file:
            data = json.load(json_file)
            for i in data:
                name = i['name']
                measurement_unit = i['measurement_unit']
                Ingredient.objects.get_or_create(
                    name=name,
                    measurement_unit=measurement_unit
                )

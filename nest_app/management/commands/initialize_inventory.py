import json

from django.core.management.base import BaseCommand, CommandError

from nest_app.processing import init_catalog

product_info = json.loads(open('./test_inventory.json').read())


class Command(BaseCommand):
    help = 'Initialize Product Inventory on startup'

    def handle(self, *args, **kwargs):
        try:
            init_catalog(product_info)
        except Exception as e:
            raise CommandError('Initialization failed.')

import requests

from django.core.management.base import BaseCommand, CommandError

from bkz3.settings import HAYSTACK_CONNECTIONS
from bkz3 import elastic_index


class Command(BaseCommand):
    help = "Management ElasticSearch."
    haystack_settings: dict = dict()
    elastic_url: str = ''

    def __init__(self):

        elastic_engine = 'haystack.backends.elasticsearch7_backend.Elasticsearch7SearchEngine'
        haystack_settings = HAYSTACK_CONNECTIONS.get('default', dict())
        if not haystack_settings:
            raise CommandError('key "default" in HAYSTACK_CONNECTIONS not found.')
        if not haystack_settings.get('ENGINE', '') == elastic_engine:
            raise CommandError(
                'Haystack engine is not for elasticsearch. Check key "engine" in HAYSTACK_CONNECTIONS'
            )
        self.haystack_settings = haystack_settings

        elastic_url = haystack_settings.get('URL', '')
        if not elastic_url:
            raise CommandError('URL for elasticsearch not found. Check key "URL" in HAYSTACK_CONNECTIONS.')
        if not elastic_url.endswith('/'):
            elastic_url = elastic_url + '/'
        self.elastic_url = elastic_url

        super().__init__()

    def add_arguments(self, parser):
        parser.add_argument(
            '--check',
            action='store_true',
            help='Return cluster information.'
        )
        parser.add_argument(
            '--list_index',
            action='store_true',
            help='Return list indexes.'
        )
        parser.add_argument(
            '--detail_index',
            action='store',
            help='Return detail for index [index_name] or current index, if not [index_name]',
            const=self.haystack_settings.get('INDEX_NAME'),
            required=False,
            nargs='?',
            metavar='index_name'
        )
        parser.add_argument(
            '--delete_index',
            action='store',
            help='Delete index [index_name] or current index, if not [index_name].',
            required=False,
            const=self.haystack_settings.get('INDEX_NAME'),
            nargs='?',
            metavar='index_name'
        )
        parser.add_argument(
            '--create_index',
            const=self.haystack_settings.get('INDEX_NAME'),
            action='store',
            help='Create index with name [index_name] or current index, if not [index_name].',
            required=False,
            nargs='?',
            metavar='index_name'
        )
        parser.add_argument(
            '--rebuild_index',
            action='store',
            const=self.haystack_settings.get('INDEX_NAME'),
            help='Delete and create index [index_name] or current index, if not [index_name].',
            metavar='index_name',
            required=False,
            nargs='?',
        )

    def handle(self, *args, **options):

        if options['check']:
            import re
            match = re.search(r'https?://(?:www\.|)([\w.-]+).*', self.elastic_url)
            url = match[0]
            result = requests.get(
                url=url
            )
            self.return_result(result)
            return

        if options['list_index']:
            result = requests.get(
                url=f"{self.elastic_url}_cat/indices",
            )
            self.return_result(result)
            return
        if options['detail_index']:
            result = requests.get(
                url=self.elastic_url + options['detail_index']
            )
            self.return_result(result)
            return
        elif options['delete_index']:
            index_url = self.elastic_url + self.haystack_settings.get('INDEX_NAME')
            result = requests.delete(
                url=index_url,
            )
            self.return_result(result)
            return

        elif options['create_index']:
            index_url = self.elastic_url + options['create_index']

            result = requests.put(
                url=index_url,
                json=elastic_index.DEFAULT
            )
            self.return_result(result)
            return
        elif options['rebuild_index']:
            index_name = options['rebuild_index']
            index_url = self.elastic_url + index_name
            self.stdout.write(f'Delete current index "{index_name}"...')
            result = requests.delete(
                url=index_url,
            )
            self.return_result(result)
            self.stdout.write(f'Create index "{index_name}"...')
            result = requests.put(
                url=index_url,
                json=elastic_index.DEFAULT
            )
            self.return_result(result)
            self.stdout.write(self.style.SUCCESS('Complete!'))
        else:
            self.print_help('', None)

    def return_result(self, result: requests.Response):
        if result.status_code == 200:
            self.stdout.write(self.style.SUCCESS(f"Response from ElasticSearch server:"))
            self.stdout.write(result.text)
            self.stdout.write(self.style.SUCCESS('Success'))
        else:
            self.stdout.write(self.style.ERROR(f"Response from ElasticSearch server:"))
            self.stdout.write(result.text)
            self.stdout.write(self.style.ERROR('Fail'))
        return

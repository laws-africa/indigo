import json

from django.core.management.base import BaseCommand

from indigo_resolver.models import Authority, AuthorityReference


class Command(BaseCommand):
    help = "Imports Indigo Resolver Authority References from a json file. The JSON file must be an array " + \
           "of objects, each with a url, num, year and title."

    def add_arguments(self, parser):
        parser.add_argument(
            'filepath',
            action='store',
            help='The json file to import'
        )
        parser.add_argument(
            '--authority',
            action='store',
            dest='authority',
            required=True,
            help='The name the Authority (already added to Indigo) for which references are being imported.'
        )
        parser.add_argument(
            '--country',
            action='store',
            required=True,
            help='The two letter country code of the country.'
        )

    def debug(self, msg):
        if self.verbosity >= 2:
            self.stdout.write(str(msg))

    def handle(self, *args, **options):
        self.filepath = options['filepath']
        self.verbosity = options.get('verbosity', 1)
        self.authority = Authority.objects.get(name=options['authority'])
        self.country = options['country'].lower()

        with open(self.filepath) as f:
            data = json.load(f)

        self.import_data(data)

    def import_data(self, data):
        # existing refs
        refs = {r.frbr_uri: r for r in self.authority.references.all()}

        for entry in data:
            if 'year' not in entry or 'num' not in entry:
                continue

            frbr_uri = '/'.join(['', self.country, 'act', entry['year'], entry['num']])
            ref = refs.get(frbr_uri)
            if not ref:
                ref = refs[frbr_uri] = AuthorityReference(frbr_uri=frbr_uri, authority=self.authority)

            ref.title = entry['title']
            ref.url = entry['url']

            if ref.id is None:
                self.stdout.write(self.style.SUCCESS(f'Create reference: {ref}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Update reference: {ref}'))

            ref.save()

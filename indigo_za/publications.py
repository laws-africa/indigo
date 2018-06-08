# -*- coding: utf-8 -*-

from indigo.analysis.publications.base import BasePublicationFinder
from indigo.plugins import plugins

import boto3


@plugins.register('publications')
class PublicationFinderZA(BasePublicationFinder):

    locale = ('za', None, None)
    """ The locale this finder is suited for, as ``(country, language, locality)``.
    """

    bucket = 'archive.opengazettes.org.za'
    region = 'eu-west-1'

    def find_publications(self, params):
        # by now, we know it's for ZA

        date = params.get('date')
        number = params.get('number')
        place = self.get_place(params.get('name'))

        if not (date and number):
            raise ValueError("I need at least a date and number to find a gazette.")

        year = date.split('-', 1)[0]
        date = '-dated-%s' % date
        number = '-no-%s-' % number
        prefix = 'archive/%s/%s/' % (place, year)

        client = boto3.client('s3', region_name=self.region)
        paginator = client.get_paginator('list_objects')
        operation_parameters = {'Bucket': self.bucket,
                                'Prefix': prefix}
        page_iterator = paginator.paginate(**operation_parameters)

        items = []
        for page in page_iterator:
            for obj in page.get('Contents', []):
                if date in obj['Key'] and number in obj['Key']:
                    items.append(obj)

        return [{
            'url': 'https://%s/%s' % (self.bucket, obj['Key']),
            'size': obj['Size'],
        } for obj in items]

    def get_place(self, name):
        name = (name or '').lower()

        if 'eastern' in name:
            return 'ZA-EC'

        if 'free' in name:
            return 'ZA-FS'

        if 'gauteng' in name:
            return 'ZA-GT'

        if 'zulu' in name or 'natal' in name:
            return 'ZA-NL'

        if 'limpopo' in name:
            return 'ZA-LP'

        if 'mpumalanga' in name:
            return 'ZA-MP'

        if 'northern cape' in name:
            return 'ZA-NC'

        if 'north' in name and 'west' in name:
            return 'ZA-NW'

        if 'western cape' in name:
            return 'ZA-WC'

        if 'transvaal' in name:
            return 'ZA-transvaal'

        return 'ZA'

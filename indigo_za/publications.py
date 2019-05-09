# -*- coding: utf-8 -*-

from indigo.analysis.publications.base import BasePublicationFinder
from indigo.plugins import plugins

import requests


@plugins.register('publications')
class PublicationFinderZA(BasePublicationFinder):

    locale = ('za', None, None)
    """ The locale this finder is suited for, as ``(country, language, locality)``.
    """

    api_url = 'https://keeper.opengazettes.org.za/api/archived_gazettes/'

    def find_publications(self, params):
        # by now, we know it's for ZA

        date = params.get('date')
        number = params.get('number')
        place = self.get_place(params.get('publication'))

        if not date:
            raise ValueError("I need at least a date to find a gazette.")

        params = {
            'publication_date': date,
            'issue_number': number,
            'jurisdiction_code': place,
        }

        resp = requests.get(self.api_url, params=params, timeout=5.0)
        items = resp.json()['results']

        return [{
            'title': obj['full_title'],
            'url': obj['archive_url'],
            'trustworthy': True,
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

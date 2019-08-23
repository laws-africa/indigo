from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from indigo.plugins import plugins


class FindPublicationsView(APIView):
    """ Support for running term discovery and linking on a document.
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request, country, locality=None):
        country = country.lower()
        if locality:
            locality = locality.lower()

        finder = plugins.for_locale('publications', country, None, locality)
        publications = []

        if finder:
            try:
                params = {
                    'date': request.GET.get('date'),
                    'number': request.GET.get('number'),
                    'publication': request.GET.get('publication'),
                    'country': country,
                    'locality': locality,
                }
                publications = finder.find_publications(params)
            except ValueError as e:
                raise ValidationError({'message': str(e)})

        return Response({'publications': publications})

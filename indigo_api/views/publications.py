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

        if finder:
            try:
                publications = finder.find_publications(request.GET)
            except ValueError as e:
                raise ValidationError({'message': e.message})
            return Response({'publications': publications})

        return Response({'publications': []})

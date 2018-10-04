from rest_framework import viewsets
from ..serializers import CountrySerializer

from ..models import Country


class CountryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Country.objects.prefetch_related('localities', 'country')
    serializer_class = CountrySerializer

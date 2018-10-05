from rest_framework import viewsets, mixins
from ..serializers import CountrySerializer

from ..models import Country


class CountryViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Country.objects.prefetch_related('localities', 'country')
    serializer_class = CountrySerializer

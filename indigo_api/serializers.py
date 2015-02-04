from .models import Document
from rest_framework import serializers

class DocumentSerializer(serializers.HyperlinkedModelSerializer):
    body_xml = serializers.CharField()
    publication_date = serializers.DateField()

    class Meta:
        model = Document
        fields = (
                # readonly, url is part of the rest framework
                'id', 'url',

                'uri', 'draft', 'created_at', 'updated_at',
                'title', 'country',
                'publication_date', 'publication_name', 'publication_number',

                # TODO: don't send this back in the listing view, it could be huge
                'body_xml',
                )

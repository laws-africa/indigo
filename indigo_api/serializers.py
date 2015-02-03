from .models import Document
from rest_framework import serializers

class DocumentSerializer(serializers.HyperlinkedModelSerializer):
    body_xml = serializers.CharField()

    class Meta:
        model = Document
        fields = (
                # readonly, url is part of the rest framework
                'id', 'url',
                'uri', 'draft', 'created_at', 'updated_at',
                'title', 'country',
                # TODO: don't send this back in the listing view, it could be huge
                'body_xml',
                )

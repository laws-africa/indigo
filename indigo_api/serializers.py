from .models import Document
from rest_framework import serializers
from rest_framework.reverse import reverse

class DocumentSerializer(serializers.HyperlinkedModelSerializer):
    publication_date = serializers.DateField()
    body_xml_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
                # readonly, url is part of the rest framework
                'id', 'url',

                'uri', 'draft', 'created_at', 'updated_at',
                'title', 'country', 'number', 'nature',
                'publication_date', 'publication_name', 'publication_number',

                # don't include the full body, it could be huge. link to it.
                'body_xml_url'
                )
        read_only_fields = ('number', 'nature', 'body_xml_url')

    def get_body_xml_url(self, doc):
        return reverse('document-body', request=self.context['request'], kwargs={'pk': doc.pk})

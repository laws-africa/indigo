import logging

from django.dispatch import receiver
from rest_framework.reverse import reverse

from indigo_api.signals import document_published
from indigo_slack.slack import send_slack_message


log = logging.getLogger(__name__)


@receiver(document_published)
def doc_published(sender, document, request, **kwargs):
    from indigo_api.serializers import DocumentSerializer

    if request and request.user.is_authenticated():
        serializer = DocumentSerializer(context={'request': request})
        pub_url = serializer.get_published_url(document) + ".html?standalone=1"

        url = reverse('document', request=request, kwargs={'doc_id': document.id})

        country = document.work.country
        fields = [{
            "title": "Country",
            "value": country.name,
            "short": "true",
        }]

        locality = country.work_locality(document.work)
        if locality:
            fields.append({
                "title": "Locality",
                "value": locality.name,
                "short": "true",
            })

        fields.append({
            "title": "Edit in Indigo",
            "value": url,
            "short": "false",
        })

        send_slack_message(
            u"{user} published <{pub_url}|{title}>".format(user=request.user.first_name, title=document.title, url=url, pub_url=pub_url),
            attachments=[{
                "text": document.work.frbr_uri,
                "fallback": document.work.frbr_uri,
                "author_name": "%s %s" % (request.user.first_name, request.user.last_name),
                "title": document.title,
                "title_link": pub_url,
                "color": "good",
                "fields": fields,
            }]
        )

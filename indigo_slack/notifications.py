import logging

from django.dispatch import receiver
from rest_framework.reverse import reverse

from indigo_api.signals import document_published
from indigo_slack.slack import send_slack_message


log = logging.getLogger(__name__)


@receiver(document_published)
def doc_published(sender, document, request, **kwargs):
    if request and request.user.is_authenticated():
        url = reverse('document', request=request, kwargs={'doc_id': document.id})

        country = document.work.country
        fields = [{
            "title": "Country",
            "value": country.name,
            "short": "true",
        }]

        if document.work.locality:
            fields.append({
                "title": "Locality",
                "value": document.work.locality.name,
                "short": "true",
            })

        fields.append({
            "title": "Edit in Indigo",
            "value": url,
            "short": "false",
        })

        send_slack_message(
            u"{user} published <{url}|{title}>".format(user=request.user.first_name, title=document.title, url=url),
            attachments=[{
                "text": document.work.frbr_uri,
                "fallback": document.work.frbr_uri,
                "author_name": "%s %s" % (request.user.first_name, request.user.last_name),
                "title": document.title,
                "title_link": url,
                "color": "good",
                "fields": fields,
            }]
        )

from django.db.models import signals
from django.dispatch import receiver
from actstream.models import Action

from indigo_api.models import Document
from indigo_metrics.models import DailyPlaceMetrics
from indigo_metrics.tasks import update_document_metrics


@receiver(signals.post_save, sender=Action)
def action_created(sender, instance, **kwargs):
    """ Send 'created' action to activity stream
    """
    if kwargs['created']:
        if instance.data and instance.data.get('place_code'):
            DailyPlaceMetrics.record_activity(instance)


@receiver(signals.post_save, sender=Document)
def document_saved(sender, instance, **kwargs):
    """ Update document metrics in the background.
    """
    update_document_metrics(instance.pk)

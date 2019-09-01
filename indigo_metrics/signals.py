from django.db.models import signals
from django.dispatch import receiver
from actstream.models import Action

from indigo_metrics.models import DailyPlaceMetrics


@receiver(signals.post_save, sender=Action)
def action_created(sender, instance, **kwargs):
    """ Send 'created' action to activity stream if new task
    """
    if kwargs['created']:
        if instance.data and instance.data.get('place_code'):
            DailyPlaceMetrics.record_activity(instance)

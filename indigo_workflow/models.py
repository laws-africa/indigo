from django.db import models

from viewflow.models import Process


class ImplicitPlaceProcess(Process):
    """ Process model for implict (rather than explicit) workflow
    tasks that involve a particular place (country or locality).
    """
    country = models.ForeignKey('indigo_app.country', null=False, related_name='list_works_tasks', help_text='Country to list works for')
    locality = models.ForeignKey('indigo_app.Locality', null=True, related_name='list_works_tasks', help_text='Locality to list works for')
    approved = models.BooleanField(default=False)
    notes = models.TextField(null=True, blank=False)

    @property
    def place_name(self):
        s = ''
        if self.locality:
            s = self.locality.name + ", "
        s = s + self.country.name
        return s


class ReviewWorkProcess(Process):
    """ Process for reviewing the details of a particular work.
    """
    work = models.ForeignKey('indigo_api.work', null=False, related_name='review_work_tasks', help_text='Work to review')


class CreatePointInTimeProcess(Process):
    """ Process for creating a new point-in-time version of a particular work.
    """
    work = models.ForeignKey('indigo_api.work', null=False, related_name='create_pit_tasks', help_text='Work to create point in time for')
    date = models.DateField(null=False, blank=False, help_text="Date of the point in time to create")
    language = models.ForeignKey('indigo_app.language', null=False, related_name='+')
    # the amendment may be null for initial imports
    amendment = models.ForeignKey('indigo_api.amendment', null=True, related_name='create_pit_tasks')

    approved = models.BooleanField(default=False)

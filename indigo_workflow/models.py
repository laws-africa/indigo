from django.db import models

from viewflow.models import Process


class ListWorksProcess(Process):
    # TODO: pull in country/locality for easy filtering of tasks?
    country = models.ForeignKey('indigo_app.country', null=False, related_name='list_works_tasks', help_text='Country to list works for')
    locality = models.ForeignKey('indigo_app.Locality', null=True, related_name='list_works_tasks', help_text='Locality to list works for')
    approved = models.BooleanField(default=False)

    @property
    def place_name(self):
        s = ''
        if self.locality:
            s = self.locality.name + ", "
        s = s + self.country.name
        return s

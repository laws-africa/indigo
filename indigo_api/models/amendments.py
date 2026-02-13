from functools import cached_property

from actstream import action
from django.db.models import signals
from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField, transition
from natsort import natsorted


class AmendmentManager(models.Manager):
    def approved(self):
        return self.filter(amending_work__work_in_progress=False, amended_work__work_in_progress=False)


class Amendment(models.Model):
    """ An amendment to a work, performed by an amending work.
    """
    objects = AmendmentManager()

    amended_work = models.ForeignKey("indigo_api.work", on_delete=models.CASCADE, null=False, verbose_name=_("amended work"),
                                     help_text=_("Work being amended"), related_name='amendments')
    amending_work = models.ForeignKey("indigo_api.work", on_delete=models.CASCADE, null=False, verbose_name=_("amending work"),
                                      help_text=_("Work making the amendment"), related_name='amendments_made')
    date = models.DateField(_("date"), null=False, blank=False,
                            help_text=_("Date on which the amendment comes into operation"))
    verb = models.CharField(_("verb"), null=False, blank=True, default="amended", help_text=_("Replace with e.g. 'revised' as needed"))

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    created_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+',
                                        verbose_name=_("created by"))
    updated_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+',
                                        verbose_name=_("updated by"))

    class Meta:
        ordering = ['date']
        verbose_name = _("amendment")
        verbose_name_plural = _("amendments")

    def expressions(self):
        """ The amended work's documents (expressions) at this date.
        """
        return self.amended_work.expressions().filter(expression_date=self.date)

    def can_delete(self):
        return not self.expressions().exists()

    def instruction_languages(self):
        """Languages for which there should be instructions for this amendment."""
        languages = self.amended_work.expression_languages()
        return languages or [self.amended_work.country.primary_language]

    @staticmethod
    def order_further(amendments):
        """ Not always needed and can be expensive.
            Order amendments by their dates; then the date, subtype, and number of their amending works.
            Use natural sorting for the `number` component, as it's a character field but commonly uses integers.

            :param amendments: A queryset of Amendment objects.
            :return: A list of Amendment objects, in the correct order.
        """
        amendments = natsorted(amendments, key=lambda x: x.amending_work.number)
        amendments.sort(key=lambda x: (x.date, x.amending_work.date, x.amending_work.subtype or ''))
        return amendments

    def update_date_for_related(self, old_date):
        # update existing documents to have the new date as their expression date
        for document in self.amended_work.document_set.filter(expression_date=old_date):
            document.change_date(self.date, self.updated_by_user, comment=_('Document date changed with amendment date.'))
        # update any tasks at the old date too
        for task in self.amended_work.tasks.filter(timeline_date=old_date):
            task.change_date(self.date, self.updated_by_user)


@receiver(signals.post_save, sender=Amendment)
def post_save_amendment(sender, instance, created, **kwargs):
    """ When an amendment is created, save any documents already at that date
    to ensure the details of the amendment are stashed correctly in each document.
    """
    if created:
        for doc in instance.amended_work.document_set.filter(expression_date=instance.date):
            # forces call to doc.copy_attributes()
            doc.updated_by_user = instance.created_by_user
            doc.save()

        # Send action to activity stream, as 'created' if a new amendment
        if instance.created_by_user:
            action.send(instance.created_by_user, verb='created', action_object=instance,
                        place_code=instance.amended_work.place.place_code)

    elif instance.updated_by_user:
        action.send(instance.updated_by_user, verb='updated', action_object=instance,
                    place_code=instance.amended_work.place.place_code)

    # propagate copy-on-principal flags from the commenced work, if any
    instance.amended_work.propagate_copy_from_principal_topics()


class AmendmentInstruction(models.Model):
    """ Instructions to apply an amendment to a particular provision (and language) of a work."""
    NEW = 'new'
    APPLIED = 'applied'

    amendment = models.ForeignKey(Amendment, on_delete=models.CASCADE, null=False, related_name="instructions",
                                  verbose_name=_("amendment"))
    language = models.ForeignKey("indigo_api.Language", on_delete=models.CASCADE, null=False, related_name="+")
    state = FSMField(_("state"), default=NEW)
    amending_provision = models.CharField(_("amending provision"), max_length=2048, null=True, blank=True)
    title = models.CharField(_("title"), max_length=4096, null=True, blank=True)
    page_number = models.IntegerField(_("page number"), null=True, blank=True)
    provision_name = models.CharField(_("provision name"), max_length=4096, null=True, blank=True)
    # the eid of the provision to be amended
    provision_id = models.CharField(_("provision id"), max_length=4096, null=True, blank=True)
    amendment_instruction = models.TextField(_("amendment instruction"), null=True, blank=True)

    applied_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+',
                                        verbose_name=_("applied by"))
    applied_at = models.DateTimeField(_("applied at"), null=True, blank=True)
    # actual eid of the amended provision
    amended_provision_id = models.CharField(_("amended provision id"), max_length=4096, null=True, blank=True)
    amended_document = models.ForeignKey("indigo_api.Document", on_delete=models.SET_NULL, null=True, blank=True)
    # the text and xml of the provision after the amendment has been applied, for reference
    amended_text = models.TextField(_("amended text"), null=True, blank=True)
    amended_xml = models.TextField(_("amended xml"), null=True, blank=True)
    # the xml and text of the amended provision once it was saved
    final_amended_text = models.TextField(_("final amended text"), null=True, blank=True)
    final_amended_xml = models.TextField(_("final amended text"), null=True, blank=True)

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)
    created_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+', verbose_name=_("created by"))

    class Meta:
        ordering = ['page_number', 'provision_name']

    @property
    def is_applied(self):
        return self.state == self.APPLIED

    @transition(field=state, source=[NEW], target=APPLIED)
    def apply(self, user):
        self.applied_by_user = user
        self.applied_at = timezone.now()
        self.state = self.APPLIED
        self.save()

    @transition(field=state, source=[APPLIED], target=NEW)
    def unapply(self):
        self.applied_by_user = None
        self.applied_at = None
        self.state = self.NEW
        self.save()

    def determine_provision_id(self):
        """Try to set the provision_id based on provision_name by using the references mechanism to look it up in a
        document suitable for this provision (if any). This is best effort."""
        if self.provision_name:
            for document in self.amendment.amended_work.document_set.filter(expression_date__lte=self.amendment.date).order_by('-expression_date'):
                eid = document.get_portion_eid_by_reference(self.provision_name)
                if eid:
                    self.provision_id = eid
                    return

    @cached_property
    def best_document(self):
        """Get (one of) the best documents for this instruction, which is at this date and with this language."""
        from .documents import Document

        if self.amended_document:
            return self.amended_document

        return Document.objects.undeleted().filter(
            work=self.amendment.amended_work, expression_date=self.amendment.date,
            language=self.language).first()

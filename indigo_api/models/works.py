from copy import deepcopy
from itertools import chain
import logging

from actstream import action
from datetime import datetime
from django.db.models import JSONField, signals, Q
from django.db.models.signals import m2m_changed
from django.db import models, IntegrityError, transaction
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from natsort import natsorted
import reversion.revisions
from reversion.models import Version
from cobalt import FrbrUri, RepealEvent
from treebeard.mp_tree import MP_Node

from indigo.plugins import plugins
from indigo_api.signals import work_approved, work_unapproved
from indigo_api.timeline import TimelineCommencementEvent, describe_single_commencement, get_serialized_timeline, describe_repeal


log = logging.getLogger()


class WorkQuerySet(models.QuerySet):
    def get_for_frbr_uri(self, frbr_uri):
        work = self.filter(frbr_uri=frbr_uri).first()
        if work is None:
            raise ValueError(_("Work for FRBR URI '%(uri)s' doesn't exist") % {"uri": frbr_uri})
        return work


class WorkManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self):
        # defer expensive or unnecessary fields
        return super().get_queryset() \
            .select_related('updated_by_user', 'created_by_user', 'country',
                            'country__country', 'locality', 'publication_document')

    def approved(self):
        return self.exclude(work_in_progress=True)


class TaxonomyTopic(MP_Node):
    name = models.CharField(_("name"), max_length=512, null=False, blank=False,
                            help_text=_("Name of the taxonomy topic"))
    slug = models.SlugField(_("slug"), max_length=4096, null=False, unique=True, blank=False,
                            help_text=_("Unique short name (code) for the topic."))
    description = models.TextField(_("description"), null=True, blank=True,
                                   help_text=_("Description of the topic"))
    public = models.BooleanField(_("public"), default=True)
    project = models.BooleanField(_("project"), default=False)
    copy_from_principal = models.BooleanField(
        _("copy from principal work"), default=False,
        help_text=_("Copy this topic from principal works to works that amend, commence or repeal the principal work.")
    )
    node_order_by = ['name']

    class Meta:
        verbose_name = _("taxonomy topic")
        verbose_name_plural = _("taxonomy topics")

    def __str__(self):
        return self.name

    @property
    def range_space(self):
        # helper for adding space indents in templates
        return range(self.depth)

    @classmethod
    def get_topic(cls, value):
        return cls.objects.filter(slug=value).first()

    def save(self, *args, **kwargs):
        parent = self.get_parent(update=True)
        self.slug = (f"{parent.slug}-" if parent else "") + slugify(self.name)
        super().save(*args, **kwargs)

    def propagate_copy_from_principal(self, works, add):
        """If this topic has copy_from_principal set to True, propagate the topic to related works for the provided
        works. If no works are provided, then propagate to related works for all works that have this topic."""
        if self.copy_from_principal:
            if works is None:
                works = self.works.filter(principal=True).all()

            related = Work.get_incoming_related_works(works)

            if add:
                log.info(f"Adding topic {self} to {len(related)} related works")
                self.works.add(*related)
            else:
                log.info(f"Removing topic {self} from {len(related)} related works")
                self.works.remove(*related)

    @classmethod
    def get_toc_tree(cls, query_dict=None):
        # capture all preserve all filter parameters and add taxonomy_topic
        new_query = None
        if query_dict is not None:
            new_query = query_dict.copy()
            new_query.pop('taxonomy_topic', None)

        def fix_up(item):
            item["title"] = item["data"]["name"]
            if new_query:
                new_query.update({'taxonomy_topic': item['id']})
                item["href"] = f"?{new_query.urlencode()}"
                new_query.pop('taxonomy_topic', None)
            for kid in item.get("children", []):
                fix_up(kid)

        tree = cls.dump_bulk()
        for x in tree:
            fix_up(x)

        return tree

    @classmethod
    def get_public_root_nodes(cls):
        root_nodes = cls.get_root_nodes()
        return root_nodes.filter(public=True)

    @classmethod
    def get_project_root_nodes(cls):
        root_nodes = cls.get_root_nodes()
        return root_nodes.filter(project=True)


class WorkMixin(object):
    """ Support methods that define behaviour for a work, independent of the database model.

    This makes it possible to change the underlying model class for a work, and then mixin
    this functionality.
    """
    _work_uri = None
    _repeal = None

    @property
    def work_uri(self):
        """ The FRBR Work URI as a :class:`FrbrUri` instance that uniquely identifies this work universally. """
        if self._work_uri is None:
            self._work_uri = FrbrUri.parse(self.frbr_uri)
        return self._work_uri

    @property
    def year(self):
        return self.work_uri.date.split('-', 1)[0]

    @property
    def nature(self):
        return self.doctype

    @property
    def repeal(self):
        """ Repeal information for this work, as a :class:`cobalt.RepealEvent` object.
        None if this work hasn't been repealed.
        """
        if self._repeal is None:
            if self.repealed_date:
                if self.repealed_by:
                    self._repeal = RepealEvent(self.repealed_date, self.repealed_by.title, self.repealed_by.frbr_uri)
                else:
                    self._repeal = RepealEvent(self.repealed_date, 'No repealing work', '')
        return self._repeal

    @property
    def place(self):
        return self.locality or self.country

    @property
    def commencement_date(self):
        main = self.main_commencement
        if main:
            return main.date

    @property
    def commencement_note(self):
        main = self.main_commencement
        if main:
            return main.note

    @property
    def commencing_work(self):
        main = self.main_commencement
        if main:
            return main.commencing_work

    def amended(self):
        return self.amendments.exists()

    def most_recent_amendment_year(self):
        latest = self.amendments.order_by('-date').first()
        if latest:
            return latest.date.year

    def amendments_after_date(self, date):
        return self.amendments.filter(date__gt=date)

    def labeled_properties(self):
        props = self.place.settings.work_properties

        return sorted([{
            'label': props[key],
            'key': key,
            'value': val,
        } for key, val in self.properties.items() if val and key in props], key=lambda x: x['label'])

    def numbered_title(self):
        """ Return a formatted title using the number for this work, such as "Act 5 of 2009".
        This usually differs from the short title. May return None.
        """
        plugin = plugins.for_work('work-detail', self)
        if plugin:
            return plugin.work_numbered_title(self)

    def friendly_type(self):
        """ Return a friendly document type for this work, such as "Act" or "By-law".
        """
        plugin = plugins.for_work('work-detail', self)
        if plugin:
            return plugin.work_friendly_type(self)

    def expressions(self):
        """ A queryset of expressions of this work, in ascending expression date order.
        """
        from .documents import Document
        return (
            Document.objects
            .undeleted()
            .no_xml()
            .select_related("language", "language__language")
            .filter(work=self)
            .order_by('expression_date')
        )

    def initial_expressions(self):
        """ Queryset of expressions at initial publication date.
        """
        return self.expressions().filter(expression_date=self.publication_date)

    def possible_expression_dates(self):
        """ Return a list of dicts each describing a possible expression date on a work, in descending date order.
        Each has a date and specifies whether it is an amendment, consolidation, and/or initial expression.
        """
        amendment_dates = [a.date for a in self.amendments.all()]
        consolidation_dates = [c.date for c in self.arbitrary_expression_dates.all()]

        # the initial date is the publication date, or the earliest of the consolidation and commencement dates
        try:
            initial = self.publication_date or min(consolidation_dates + [x for x in [self.commencement_date] if x])
        except ValueError:
            # list was empty
            initial = None

        all_dates = set(amendment_dates + consolidation_dates)
        dates = [
            {'date': date,
             'amendment': date in amendment_dates,
             'consolidation': date in consolidation_dates,
             'initial': date == initial}
            for date in all_dates
        ]

        if initial and initial not in all_dates:
            dates.append({
                'date': initial,
                'initial': True
            })

        dates.sort(key=lambda x: x['date'], reverse=True)
        return dates

    def all_provisions(self):
        # a list of the element ids of the earliest PiT (in whichever language) of a work
        # does not include Schedules as they don't have commencement dates
        first_expression = self.expressions().first()
        if first_expression:
            return first_expression.all_provisions()
        return None

    @cached_property
    def main_commencement(self):
        return self.commencements.filter(main=True).first() if self.pk else None

    def first_commencement_date(self):
        first = self.commencements.first() if self.pk else None
        if first:
            return first.date

    def latest_commencement_date(self):
        latest = self.commencements.order_by('-date').first() if self.pk else None
        if latest:
            return latest.date

    def all_commenceable_provisions(self, date=None):
        """ Returns a list of TOCElement objects that can be commenced.
        Each TOCElement object has a (potentially empty) list of `children`.
        If `date` is provided, only provisions in expressions up to and including that date are included.

        This is a potentially expensive operation across multiple documents, and so intermediate and final
        results are cached.
        """
        from indigo.analysis.toc.base import descend_toc_pre_order, remove_toc_elements

        if getattr(self, '_provision_cache', None) is None:
            # cache the provisions for the various documents because they are expensive to compute
            self._provision_cache = {}
            # cache selected details of the documents we use to build up provisions, in ascending expression date order
            self._docs_for_provisions = list(
                self.expressions()
                    .values('id', 'language_id', 'expression_date')
                    .order_by('expression_date')
                    .all())

        if date:
            documents = [d for d in self._docs_for_provisions if d['expression_date'] <= date]
            if not documents:
                # get the earliest available expression when historical points in time don't exist
                # give it in a list so that it can be sorted below, but not if it's None
                documents = self._docs_for_provisions[:1]
        else:
            # use all expressions
            documents = self._docs_for_provisions

        # ids of documents we need to generate TOCs for
        to_load = [d['id'] for d in documents if d['id'] not in self._provision_cache]
        tocs = {}
        if to_load:
            docs_for_toc = self.expressions().defer(None).filter(pk__in=to_load) \
                .select_related('work', 'work__locality', 'work__country', 'work__country__country')
            for doc in docs_for_toc:
                toc = doc.table_of_contents()
                for p in descend_toc_pre_order(toc):
                    p.element = None
                # explicitly exclude definitions from commenceable provisions
                toc = remove_toc_elements(toc, elements=['definition'])
                tocs[doc.id] = toc

        # within the existing ascending expression date order, sort expressions so that we consider
        # primary language documents first
        documents = sorted(documents, key=lambda d: 0 if d['language_id'] == self.country.primary_language_id else 1)

        # return a list of all provisions to date
        cumulative_provisions = []

        # get a TOC plugin that can be shared across all these documents
        locality = self.locality.code if self.locality else None
        plugin = plugins.for_locale('toc', country=self.country.code, locality=locality, language=self.country.primary_language.code)

        if plugin:
            for i, doc in enumerate(documents):
                # don't do any work if we've already cached the provisions for this doc
                try:
                    cumulative_provisions, cumulative_id_set = self._provision_cache[doc['id']]
                except KeyError:
                    # get the previous document's provisions and id set to build on
                    previous_id = documents[i - 1]['id'] if i > 0 else None
                    cumulative_provisions, cumulative_id_set = self._provision_cache.get(previous_id, ([], set()))
                    # copy these because we'll change them
                    cumulative_provisions = deepcopy(cumulative_provisions)
                    cumulative_id_set = cumulative_id_set.copy()

                    # update them based on the current toc
                    plugin.insert_commenceable_provisions(tocs[doc['id']], cumulative_provisions, cumulative_id_set)

                    # update the cache; provisions and id_set were updated in place
                    self._provision_cache[doc['id']] = (cumulative_provisions, cumulative_id_set)

        # this'll be the last document's cumulative_provisions, or []
        return cumulative_provisions

    def all_uncommenced_provision_ids(self, date=None, return_bool=False):
        """ Returns a (potentially empty) list of the ids of TOCElement objects that haven't yet commenced.
            If `date` is provided, only provisions in expressions up to and including that date are included.
            If `return_bool` is True, returns a boolean instead.
        """
        from indigo.analysis.toc.base import descend_toc_pre_order

        commencements = self.commencements.all()
        # common case: one commencement that covers all provisions
        if any(c.all_provisions for c in commencements):
            return False if return_bool else []

        # commencement.provisions are lists of provision ids
        commenced = [p for c in commencements for p in c.provisions]

        uncommenced = []
        for p in descend_toc_pre_order(self.all_commenceable_provisions(date=date)):
            if p.id not in commenced:
                if return_bool:
                    return True
                uncommenced.append(p.id)

        return False if return_bool else uncommenced

    @property
    def commencements_count(self):
        """ The number of commencement objects, plus one if there are uncommenced provisions, on a work """
        commencements_count = len(self.commencements.all())
        if self.all_uncommenced_provision_ids(return_bool=True):
            commencements_count += 1
        return commencements_count

    @property
    def has_consolidation(self):
        return self.arbitrary_expression_dates.exists()

    def consolidation_note(self):
        if self.has_consolidation:
            return self.consolidation_note_override or self.place.settings.consolidation_note

    def commencement_description(self, friendly_date=True, commencements=None, has_uncommenced_provisions=None):
        """ Returns a TimelineCommencementEvent object describing the commencement status of a work.
            - If there's more than one commencement, OR if some provisions are yet to commence, describe it as 'multiple'.
            - If there are none, describe it as 'uncommenced'.
            - If there's one, AND no uncommenced provisions, describe the single commencement in more detail.

            If specific commencements are passed in, evaluate those rather than all commencements on the work.
            If has_uncommenced_provisions (bool) is passed in, use that rather than checking a single commencement for all_provisions.
            By default, commencement dates are formatted as e.g. '1 January 2023'.
                Passing in friendly_date=False leaves them as e.g. 2023-01-01.
        """
        n_commencements = len(commencements) if commencements is not None else len(self.commencements.all())
        # if the commencement description isn't scoped, has_uncommenced_provisions should be True
        # when there's a single commencement that does not commence all provisions
        # (we only care about whether there are uncommenced provisions when there's a single commencement)
        if has_uncommenced_provisions is None and n_commencements == 1:
            has_uncommenced_provisions = not self.commencements.first().all_provisions

        if n_commencements == 0:
            if self.commenced:
                return TimelineCommencementEvent(subtype='unknown', description=_('Commencement date unknown'))
            return TimelineCommencementEvent(subtype='uncommenced', description=_('Not commenced'))

        # we have 'multiple' commencements if there are more than one,
        # OR if there's only one but it doesn't commence everything
        elif n_commencements > 1 or has_uncommenced_provisions:
            return TimelineCommencementEvent(subtype='multiple', description=_('There are multiple commencements'))

        # single commencement
        commencement = commencements[0] if commencements else self.commencements.first()
        return describe_single_commencement(commencement, with_date=True, friendly_date=friendly_date)

    def commencement_description_internal(self):
        return self.commencement_description(friendly_date=False)

    def commencement_description_external(self):
        return self.commencement_description()

    def repeal_description(self, friendly_date=True):
        return describe_repeal(self, with_date=True, friendly_date=friendly_date)

    def repeal_description_internal(self):
        return self.repeal_description(friendly_date=False)

    def repeal_description_external(self):
        return self.repeal_description(friendly_date=True)

    def get_serialized_timeline(self):
        return get_serialized_timeline(self)


class Work(WorkMixin, models.Model):
    """ A work is an abstract document, such as an act. It has basic metadata and
    allows us to track works that we don't have documents for, and provides a
    logical parent for documents, which are expressions of a work.
    """
    REPEALED = 'repealed'
    REVOKED = 'revoked'
    WITHDRAWN = 'withdrawn'
    LAPSED = 'lapsed'
    RETIRED = 'retired'
    EXPIRED = 'expired'
    REPLACED = 'replaced'
    DISAPPLIED = 'disapplied'
    REPEALED_VERB_CHOICES = (
        (REPEALED, _('repealed')),
        (REVOKED, _('revoked')),
        (WITHDRAWN, _('withdrawn')),
        (LAPSED, _('lapsed')),
        (RETIRED, _('retired')),
        (EXPIRED, _('expired')),
        (REPLACED, _('replaced')),
        (DISAPPLIED, _('disapplied')),
    )

    class Meta:
        permissions = (
            ('review_work', _('Can review work details')),
            ('bulk_add_work', _('Can import works in bulk')),
            ('bulk_export_work', _('Can export works in bulk')),
        )
        verbose_name = _("work")
        verbose_name_plural = _("works")

    frbr_uri = models.CharField(_("FRBR URI"), max_length=512, null=False, blank=False, unique=True,
                                help_text=_("Used globally to identify this work"))
    """ The FRBR Work URI of this work that uniquely identifies it globally """

    title = models.CharField(_("title"), max_length=1024, null=False, blank=False)
    country = models.ForeignKey('indigo_api.Country', null=False, on_delete=models.PROTECT, related_name='works',
                                verbose_name=_("country"))
    locality = models.ForeignKey('indigo_api.Locality', null=True, blank=True, on_delete=models.PROTECT,
                                 related_name='works', verbose_name=_("locality"))

    doctype = models.CharField(_("doctype"), max_length=64, null=False, blank=True, help_text=_("FRBR doctype"))
    subtype = models.CharField(_("subtype"), max_length=512, null=True, blank=True, help_text=_("FRBR subtype"))
    actor = models.CharField(_("actor"), max_length=512, null=True, blank=True, help_text=_("FRBR actor"))
    date = models.CharField(_("date"), max_length=10, null=False, blank=True, help_text=_("FRBR date"))
    number = models.CharField(_("number"), max_length=512, null=False, blank=True, help_text=_("FRBR number"))

    # publication details
    publication_name = models.CharField(_("publication name"), null=True, blank=True, max_length=255,
                                        help_text=_("Original publication's name, e.g. Government Gazette"))
    publication_number = models.CharField(_("publication number"), null=True, blank=True, max_length=255,
                                          help_text=_("Publication's sequence number, eg. gazette number"))
    publication_date = models.DateField(_("publication date"), null=True, blank=True, help_text=_("Date of publication"))

    assent_date = models.DateField(_("assent date"), null=True, blank=True, help_text=_("Date signed by the president"))

    commenced = models.BooleanField(_("commenced"), null=False, default=False,
                                    help_text=_("Has this work commenced? (Date may be unknown)"))

    # repeal information
    repealed_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                    help_text=_("Work that repealed this work"), related_name='repealed_works',
                                    verbose_name=_("repealed by"))
    repealed_date = models.DateField(_("repealed date"), null=True, blank=True, help_text=_("Date of repeal of this work"))
    repealed_verb = models.CharField(_("repealed verb"), null=True, blank=True, max_length=256,
                                     help_text=_("Specify if it should be anything other than 'repealed' (the default)"))
    repealed_note = models.CharField(_("repealed note"), null=True, blank=True, max_length=512,
                                     help_text=_("Optional note giving extra detail about the repeal"))

    # optional parent work
    parent_work = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                    help_text=_("Parent (primary) work for subsidiary legislation"),
                                    related_name='child_works', verbose_name=_("parent (primary) work"))

    principal = models.BooleanField(_("principal"), null=False, default=False,
                                    help_text=_("Principal works are not simply repeals, amendments or commencements,"
                                                " and should have full text content."))
    stub = models.BooleanField(_("stub"), default=False, help_text=_("Stub works do not have content or points in time"))

    # key-value pairs of extra data, using keys for this place from PlaceSettings.work_properties
    properties = JSONField(_("properties"), null=False, blank=True, default=dict)

    taxonomy_topics = models.ManyToManyField(TaxonomyTopic, related_name='works', blank=True, verbose_name=_("taxonomy topics"))

    as_at_date_override = models.DateField(_("as-at date override"), null=True, blank=True,
                                           help_text=_("Date up to which this work was last checked for updates"))
    consolidation_note_override = models.CharField(_("consolidation note override"), max_length=1024, null=True, blank=True,
                                                   help_text=_("Consolidation note about this particular work, to"
                                                               " override any consolidation note for the place"))
    disclaimer = models.CharField(_("disclaimer"), max_length=1024, null=True, blank=True,
                                  help_text=_("Disclaimer text about this work"))

    work_in_progress = models.BooleanField(_("work in progress"), default=True,
                                           help_text=_("Work in progress, to be approved"))

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)
    approved_at = models.DateTimeField(_("approved at"), null=True, blank=True)

    created_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+',
                                        verbose_name=_("created by"))
    updated_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+',
                                        verbose_name=_("updated by"))
    approved_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
                                         verbose_name=_("approved by"))

    objects = WorkManager.from_queryset(WorkQuerySet)()

    @property
    def approved(self):
        return not self.work_in_progress

    @property
    def locality_code(self):
        # Helper to get/set locality using the locality_code, used by the WorkSerializer.
        return self.locality.code

    @locality_code.setter
    def locality_code(self, value):
        if value:
            locality = self.country.localities.filter(code=value).first()
            if not locality:
                raise ValueError(_("No such locality for this country: %(code)s") % {"code": value})
            self.locality = locality
        else:
            self.locality = None

    def clean(self):
        # validate and clean the frbr_uri
        try:
            frbr_uri = FrbrUri.parse(self.frbr_uri).work_uri(work_component=False)
        except ValueError:
            raise ValidationError(_("Invalid FRBR URI"))

        # Assume frbr_uri starts with /akn; `rest` is everything after the country/locality, e.g.
        # in `/akn/za-wc/act/2000/12`, `rest` is `act/2000/12`.
        rest = frbr_uri.split('/', 3)[3]

        # force akn prefix, country and locality codes in frbr uri
        prefix = '/akn/' + self.country.code
        if self.locality:
            prefix = prefix + '-' + self.locality.code

        self.frbr_uri = f'{prefix}/{rest}'.lower()

    def save(self, *args, **kwargs):
        # prevent circular references
        if self.parent_work == self:
            self.parent_work = None

        # a work can be repealed without being 'repealed_by' something, but it needs a repealed_date
        if not self.repealed_date:
            self.repealed_by = None
            self.repealed_verb = None
            self.repealed_note = None
        # if a work is repealed and doesn't have a verb, use the default ('repealed')
        elif not self.repealed_verb:
            self.repealed_verb = self.REPEALED

        self.set_frbr_uri_fields()
        return super(Work, self).save(*args, **kwargs)

    def set_frbr_uri_fields(self):
        # extract FRBR URI fields
        self.doctype = self.work_uri.doctype
        self.subtype = self.work_uri.subtype
        self.actor = self.work_uri.actor
        self.date = self.work_uri.date
        self.number = self.work_uri.number

    def update_documents_at_publication_date(self, old_publication_date, new_publication_date):
        """ Updates the expression dates of all documents at the old publication date to the new one.
        """
        from .documents import Document
        for document in Document.objects.filter(work=self, expression_date=old_publication_date):
            document.expression_date = new_publication_date
            document.save()

    def update_document_titles(self, old_title, new_title):
        """ Updates the titles of all documents that currently have the old title.
        """
        from .documents import Document
        for document in Document.objects.filter(work=self, title=old_title):
            document.title = new_title
            document.save()

    def save_with_revision(self, user, comment=None):
        """ Save this work and create a new revision at the same time.
        """
        with reversion.revisions.create_revision():
            reversion.revisions.set_user(user)
            if comment:
                reversion.revisions.set_comment(comment)
            self.updated_by_user = user
            self.save()

    def can_delete(self):
        return (not self.document_set.undeleted().exists() and
                not self.child_works.exists() and
                not self.repealed_works.exists() and
                not self.commencements_made.exists() and
                not Amendment.objects.filter(Q(amending_work=self) | Q(amended_work=self)).exists())

    def create_expression_at(self, user, date, language=None):
        """ Create a new expression at a particular date.

        This uses an existing document at or before this date as a template, if available.
        """
        from .documents import Document, Attachment

        language = language or self.country.primary_language
        doc = Document(work=self)

        # most recent expression at or before this date
        template = self.document_set \
            .undeleted() \
            .filter(expression_date__lte=date, language=language) \
            .order_by('-expression_date') \
            .first()

        if template:
            doc.title = template.title
            doc.content = template.content

        doc.draft = True
        doc.language = language
        doc.expression_date = date
        doc.created_by_user = user
        doc.save()

        # copy over attachments to new expression
        attachments = Attachment.objects.filter(document=template)
        for attachment in attachments:
            attachment.pk = None
            attachment.document = doc
            attachment.file.save(attachment.filename, attachment.file)
            attachment.save()

        return doc

    def versions(self):
        """ Return a queryset of `reversion.models.Version` objects for
        revisions for this work, most recent first.
        """
        return Version.objects.get_for_object(self).select_related('revision', 'revision__user')

    def as_at_date(self):
        return self.as_at_date_override or self.place.settings.as_at_date

    def approve(self, user, request=None):
        self.work_in_progress = False
        self.approved_by_user = user
        self.approved_at = datetime.now()
        self.save_with_revision(user)
        action.send(user, verb='approved', action_object=self, place_code=self.place.place_code)
        try:
            with transaction.atomic():
                work_approved.send(sender=self.__class__, work=self, request=request)
        except IntegrityError:
            pass

    def unapprove(self, user):
        self.work_in_progress = True
        self.approved_by_user = None
        self.approved_at = None
        self.save_with_revision(user)
        action.send(user, verb='unapproved', action_object=self, place_code=self.place.place_code)
        work_unapproved.send(sender=self.__class__, work=self)

        # unpublish all documents
        for document in self.document_set.published():
            document.draft = True
            document.save_with_revision(user, comment=_("This document was unpublished because its work was unapproved."))

    def has_publication_document(self):
        return PublicationDocument.objects.filter(work=self).exists()

    def public_taxonomy_topics(self):
        # TODO: make this less expensive?
        return [t for t in self.taxonomy_topics.all() if t.get_root().public]

    def get_import_date(self):
        """Return the date at which content should be imported for this work; may be None."""
        import_timeline_dates = [self.publication_date] if self.publication_date else []
        if not import_timeline_dates:
            import_timeline_dates = [self.commencement_date] if self.commencement_date else []
        import_timeline_dates.extend(c.date for c in self.arbitrary_expression_dates.all())
        return max(import_timeline_dates) if import_timeline_dates else None

    def propagate_copy_from_principal_topics(self):
        """Ensure that any copy-from-principal topics on this work are copied to related works."""
        if self.principal:
            for topic in self.taxonomy_topics.filter(copy_from_principal=True):
                topic.propagate_copy_from_principal([self], add=True)

    @cached_property
    def taxonomy_topics_list(self):
        taxonomy_topics = list(self.taxonomy_topics.all())
        paths = [
            topic.path[0:pos]
            for topic in taxonomy_topics
            for pos in range(0, len(topic.path), topic.steplen)[1:]
            if not topic.is_root()
        ]
        topics = list(TaxonomyTopic.objects.filter(path__in=paths).order_by('depth'))
        return [{
            "topic": topic,
            "ancestors": [t for t in topics if topic.path.startswith(t.path)]
        } for topic in taxonomy_topics]

    def __str__(self):
        return '%s (%s)' % (self.frbr_uri, self.title)

    @classmethod
    def get_incoming_related_works(cls, works):
        """ Get a queryset of works that are related to the given works because the related work amends,
        repeals or commences one of the given works.

        Note that the parent/child relationship is ignored.
        """
        if not works:
            return cls.objects.none()

        q = Q(amendments_made__amended_work__in=works)
        q |= Q(repealed_works__in=works)
        q |= Q(commencements_made__commenced_work__in=works)
        return cls.objects.filter(q).order_by().distinct("pk")


@receiver(signals.post_save, sender=Work)
def post_save_work(sender, instance, **kwargs):
    """ Cascade changes to linked documents
    """
    if not kwargs['raw'] and not kwargs['created']:
        # cascade updates to ensure documents
        # pick up changes to inherited attributes
        for doc in instance.document_set.all():
            # forces call to doc.copy_attributes()
            doc.updated_by_user = instance.updated_by_user
            doc.save()

        instance.propagate_copy_from_principal_topics()

    # Send action to activity stream, as 'created' if a new work
    if kwargs['created']:
        if instance.created_by_user:
            action.send(instance.created_by_user, verb='created', action_object=instance,
                        place_code=instance.place.place_code)
    else:
        if instance.updated_by_user:
            action.send(instance.updated_by_user, verb='updated', action_object=instance,
                        place_code=instance.place.place_code)


@receiver(m2m_changed, sender=Work.taxonomy_topics.through)
def taxonomy_topic_copy_from_principal(sender, instance, action, reverse, model, pk_set, **kwargs):
    """ When a topic is added or removed from a work, add or remove it from related works
    if the copy_from_principal flag is set."""
    if action not in ['post_add', 'post_remove']:
        return

    if reverse:
        # topic.works was updated with bulk works
        if not instance.copy_from_principal:
            return

        # get all the principal works that had the topic added or removed
        works = Work.objects.filter(pk__in=pk_set, principal=True)
        if works.exists():
            instance.propagate_copy_from_principal(works, add=action == 'post_add')
    else:
        # the work.taxonomy_topics was updated with bulk topics
        if not instance.principal:
            return

        # get all updated topics that have the copy_from_principal flag set
        topics = TaxonomyTopic.objects.filter(pk__in=pk_set, copy_from_principal=True)
        if topics.exists():
            # update all related works
            for topic in topics:
                topic.propagate_copy_from_principal([instance], add=action == 'post_add')


# version tracking
reversion.revisions.register(Work)


def publication_document_filename(instance, filename):
    return 'work-attachments/%s/publication-document' % (instance.work.id,)


class PublicationDocument(models.Model):
    work = models.OneToOneField(Work, related_name='publication_document', null=False, on_delete=models.CASCADE,
                                verbose_name=_("work"))
    # either file or trusted_url should be provided
    file = models.FileField(_("file"), upload_to=publication_document_filename)
    trusted_url = models.URLField(_("trusted URL"), null=True, blank=True)
    size = models.IntegerField(_("file size"), null=True)
    filename = models.CharField(_("file name"), max_length=255)
    mime_type = models.CharField(_("file MIME type"), max_length=255)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("publication document")
        verbose_name_plural = _("publication documents")

    def build_filename(self):
        # don't include /akn/ from FRBR URI in filename
        return f"{self.work.frbr_uri[5:].replace('/', '-')}-publication-document.pdf"

    def save(self, *args, **kwargs):
        self.filename = self.build_filename()
        return super(PublicationDocument, self).save(*args, **kwargs)


class CommencementManager(models.Manager):
    def approved(self):
        # exclude WIP=True commencing works rather than filtering on WIP=False because commencing_work is optional
        return self.filter(commenced_work__work_in_progress=False).exclude(commencing_work__work_in_progress=True)


class Commencement(models.Model):
    """ The commencement details of (provisions of) a work,
    optionally performed by a commencing work or a provision of the work itself.
    """
    objects = CommencementManager()

    commenced_work = models.ForeignKey(Work, on_delete=models.CASCADE, null=False, verbose_name=_("commenced work"),
                                       help_text=_("Principal work being commenced"), related_name="commencements")
    commencing_work = models.ForeignKey(Work, on_delete=models.SET_NULL, null=True, verbose_name=_("commencing work"),
                                        help_text=_("Work that provides the commencement date for the principal work"),
                                        related_name="commencements_made")
    date = models.DateField(_("date"), null=True, blank=True,
                            help_text=_("Date of the commencement, or null if it is unknown"))
    main = models.BooleanField(_("main"), default=False,
                               help_text=_("This commencement date is the date on which most of the provisions of the"
                                           " commenced work come into force"))
    all_provisions = models.BooleanField(_("all provisions"), default=False,
                                         help_text=_("All provisions of this work commenced on this date"))
    note = models.TextField(_("note"), max_length=1024, blank=True, null=True,
                            help_text=_("Usually a reference to a provision of the commenced work or a commencing work,"
                                        " if there is a commencement but the date is open to interpretation"))

    # list of the element ids of the provisions commenced, e.g. ["sec_2", "sec_4.3.list0.a"]
    provisions = JSONField(_("commenced provisions"), null=False, blank=False, default=list,
                           help_text=_("A list of the element ids of the provisions that come into force with this"
                                       " commencement"))

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    created_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+',
                                        verbose_name=_("created by"))
    updated_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+',
                                        verbose_name=_("updated by"))

    class Meta:
        ordering = ['date']
        unique_together = (('commenced_work', 'commencing_work', 'date'),)
        verbose_name = _("commencement")
        verbose_name_plural = _("commencements")

    def expressions(self):
        """ The commenced work's documents (expressions) at this date.
        """
        return self.commenced_work.expressions().filter(expression_date=self.date)

    def update_commenced_work(self):
        # if a commencement on a work exists, the work cannot be uncommenced
        if not self.commenced_work.commenced:
            self.commenced_work.commenced = True
            self.commenced_work.updated_by_user = self.updated_by_user or self.created_by_user
            self.commenced_work.save()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_commenced_work()


@receiver(signals.post_save, sender=Commencement)
def post_save_commencement(sender, instance, created, **kwargs):
    # Send action to activity stream, as 'created' if a new commencement
    if created:
        if instance.created_by_user:
            action.send(instance.created_by_user, verb='created', action_object=instance,
                        place_code=instance.commenced_work.place.place_code)

    elif instance.updated_by_user:
        action.send(instance.updated_by_user, verb='updated', action_object=instance,
                    place_code=instance.commenced_work.place.place_code)

    # propagate copy-on-principal flags from the commenced work, if any
    instance.commenced_work.propagate_copy_from_principal_topics()


class AmendmentManager(models.Manager):
    def approved(self):
        return self.filter(amending_work__work_in_progress=False, amended_work__work_in_progress=False)


class Amendment(models.Model):
    """ An amendment to a work, performed by an amending work.
    """
    objects = AmendmentManager()

    amended_work = models.ForeignKey(Work, on_delete=models.CASCADE, null=False, verbose_name=_("amended work"),
                                     help_text=_("Work being amended"), related_name='amendments')
    amending_work = models.ForeignKey(Work, on_delete=models.CASCADE, null=False, verbose_name=_("amending work"),
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


class ArbitraryExpressionDate(models.Model):
    """ An arbitrary expression date not tied to an amendment, e.g. a consolidation date.
    """
    date = models.DateField(_("date"), null=False, blank=False, help_text=_("Arbitrary date, e.g. consolidation date"))
    description = models.TextField(_("description"), null=True, blank=True)
    work = models.ForeignKey(Work, on_delete=models.CASCADE, null=False, verbose_name=_("work"),
                             related_name="arbitrary_expression_dates")

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    created_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+',
                                        verbose_name=_("created by"))
    updated_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+',
                                        verbose_name=_("updated by"))

    class Meta:
        unique_together = ('date', 'work')
        ordering = ['date']
        verbose_name = _("arbitrary expression date")
        verbose_name_plural = _("arbitrary expression dates")

    def expressions(self):
        """ The work's documents (expressions) at this date.
        """
        return self.work.expressions().filter(expression_date=self.date)

    def can_delete(self):
        return not self.expressions().exists()

    @property
    def amended_work(self):
        return self.work


@receiver(signals.post_save, sender=ArbitraryExpressionDate)
def post_save_arbitrary_expression_date(sender, instance, **kwargs):
    # Send action to activity stream, as 'created' if a new arbitrary expression date
    if kwargs['created']:
        action.send(instance.created_by_user, verb='created', action_object=instance,
                    place_code=instance.work.place.place_code)
    else:
        action.send(instance.updated_by_user, verb='updated', action_object=instance,
                    place_code=instance.work.place.place_code)


class Subtype(models.Model):
    name = models.CharField(_("name"), max_length=1024, help_text=_("Name of the subtype"))
    abbreviation = models.CharField(_("abbreviation"), max_length=32, unique=True,
                                    help_text=_("Short abbreviation to use in the FRBR URI. No punctuation."))

    # cheap cache for subtypes, to avoid DB lookups
    _cache = {}

    class Meta:
        verbose_name = _("subtype")
        verbose_name_plural = _("subtypes")
        ordering = ('name',)

    def clean(self):
        if self.abbreviation:
            self.abbreviation = self.abbreviation.lower()

    def __str__(self):
        return '%s (%s)' % (self.name, self.abbreviation)

    @classmethod
    def for_abbreviation(cls, abbr):
        if not cls._cache:
            cls._cache = {s.abbreviation: s for s in cls.objects.all()}
        return cls._cache.get(abbr)


@receiver(signals.post_save, sender=Subtype)
def on_subtype_saved(sender, instance, **kwargs):
    # clear the subtype cache
    Subtype._cache = {}


class WorkAlias(models.Model):
    alias = models.CharField(_("alias"), max_length=255, help_text=_("Alias e.g. Penal Code, etc"))
    work = models.ForeignKey(Work, on_delete=models.CASCADE, related_name="aliases", verbose_name=_("work"))

    class Meta:
        unique_together = ('alias', 'work')
        ordering = ('alias',)
        verbose_name = _("work alias")
        verbose_name_plural = _("work aliases")

    def __str__(self):
        return self.alias


class ChapterNumber(models.Model):
    number = models.CharField(_("number"), max_length=32, null=True, blank=True, help_text=_("The Chapter number"))
    name = models.CharField(_("name"), max_length=64, null=False, blank=True, default="chapter", help_text=_("Specify if it should be anything other than 'chapter' (the default)"))
    work = models.ForeignKey(Work, on_delete=models.CASCADE, null=False, verbose_name=_("work"), related_name='chapter_numbers')
    validity_start_date = models.DateField(_("validity start date"), null=True, blank=True, help_text=_("Date from which this Chapter number applied to the work"))
    validity_end_date = models.DateField(_("validity end date"), null=True, blank=True, help_text=_("Date until which this Chapter number applied to the work"))
    revision_name = models.CharField(_("revision name"), max_length=64, null=True, blank=True, help_text=_("Name of the publication in which this Chapter number was assigned to the work"))

    class Meta:
        ordering = ('-validity_start_date',)
        verbose_name = _("chapter number")
        verbose_name_plural = _("chapter numbers")

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = "chapter"
        return super().save(*args, **kwargs)

    def get_name(self):
        """ The preferred way to manage different chapter names is through the work-detail plugin,
            where all the options are given in chapter_names_choices so that their translations can be stored too.
            BaseWorkDetail only has one option, 'chapter' --> _('Chapter').
        """
        plugin = plugins.for_work('work-detail', self.work)
        return plugin.chapter_number_name(self) if plugin else _("Chapter")

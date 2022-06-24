from lxml import etree
from math import ceil
import datetime
import logging

from django.core.exceptions import ObjectDoesNotExist
from django.db import connection, models, transaction
from django.db.models import Sum

from indigo_api.models import PublicationDocument, Country, Document


log = logging.getLogger(__name__)


class WorkMetrics(models.Model):
    work = models.OneToOneField('indigo_api.work', on_delete=models.CASCADE, null=False, related_name='metrics')

    # Depth completeness - expected vs actual expressions
    n_languages = models.IntegerField(null=True, help_text="Number of languages in published documents")
    n_expressions = models.IntegerField(null=True, help_text="Number of published documents")
    n_points_in_time = models.IntegerField(null=True, help_text="Number of recorded points in time")
    n_expected_expressions = models.IntegerField(null=True, help_text="Expected number of published documents")
    p_depth_complete = models.IntegerField(null=True, help_text="Percentage depth complete")

    # Breadth completeness - basic completeness
    p_breadth_complete = models.IntegerField(null=True, help_text="Percentage breadth complete")

    # total percentage complete, a combination of breadth and depth completeness
    p_complete = models.IntegerField(null=True, help_text="Percentage complete")

    # weight lent to depth completeness when calculating total completeness
    DEPTH_WEIGHT = 0.50

    @classmethod
    def calculate(cls, work):
        metrics = WorkMetrics()
        metrics.n_points_in_time = len(work.possible_expression_dates())
        metrics.n_languages = work.document_set.published().values('language').distinct().count() or 1
        # non-stubs should always have at least one expression
        metrics.n_expected_expressions = 0 if work.stub else max(1, metrics.n_points_in_time * metrics.n_languages)
        metrics.n_expressions = work.document_set.published().count()

        # sum up factors towards breadth completeness
        points = [
            # one for existing, so we don't get zero
            1,
            # at least one published expression?
            1 if (work.stub or metrics.n_expressions > 0) else 0
        ]
        # publication document?
        try:
            if work.publication_document:
                points.append(1)
        except PublicationDocument.DoesNotExist:
            points.append(0)
        metrics.p_breadth_complete = int(100.0 * sum(points) / len(points))

        if work.stub:
            metrics.p_depth_complete = 100
        else:
            # TODO: take into account some measure of completeness for the expressions that do exist
            metrics.p_depth_complete = int(100.0 * metrics.n_expressions / metrics.n_expected_expressions)

        metrics.p_complete = int(metrics.p_depth_complete * cls.DEPTH_WEIGHT +
                                 metrics.p_breadth_complete * (1.0 - cls.DEPTH_WEIGHT))

        return metrics

    @classmethod
    def create_or_update(cls, work):
        metrics = cls.calculate(work)

        try:
            existing = cls.objects.get(work=work)
            if existing:
                metrics.id = existing.id
        except cls.DoesNotExist:
            pass

        work.metrics = metrics
        metrics.save()

        return metrics

    @classmethod
    def update_all_work_metrics(cls):
        from indigo_api.models import Work

        log.info('Updating individual work metrics.')
        for work in Work.objects.all():
            cls.create_or_update(work)
        log.info('Work metrics updated')


class DocumentMetrics(models.Model):
    document = models.OneToOneField(Document, on_delete=models.CASCADE, null=False, related_name='metrics')

    n_bytes = models.IntegerField(null=False, default=0)
    n_provisions = models.IntegerField(null=False, default=0)
    n_words = models.IntegerField(null=False, default=0)
    n_pages = models.IntegerField(null=False, default=0)

    @classmethod
    def calculate(cls, document):
        metrics = DocumentMetrics()
        xml = etree.fromstring(document.document_xml)
        n_words = len(' '.join(xml.xpath('//a:*//text()', namespaces={'a': xml.nsmap[None]})).split())

        metrics.n_bytes = len(document.document_xml)
        metrics.n_provisions = len(document.all_provisions())
        metrics.n_words = n_words
        # average of 250 words per page
        metrics.n_pages = ceil(n_words / 250)

        return metrics

    @classmethod
    def create_or_update(cls, doc_id):
        document = Document.objects.get(pk=doc_id)
        metrics = cls.calculate(document)

        try:
            existing = cls.objects.get(document_id=document.pk)
            if existing:
                metrics.id = existing.id
        except cls.DoesNotExist:
            pass

        document.metrics = metrics
        metrics.save()

        return metrics

    @classmethod
    def calculate_for_place(cls, place_code):
        """ Calculates the aggregate DocumentMetrics values for all undeleted documents in a given place.
        """
        country, locality = Country.get_country_locality(place_code)

        return DocumentMetrics.objects\
            .filter(document__work__country=country, document__work__locality=locality, document__deleted=False)\
            .aggregate(n_bytes=Sum('n_bytes'), n_provisions=Sum('n_provisions'), n_words=Sum('n_words'), n_pages=Sum('n_pages'))

    @classmethod
    def calculate_for_works(cls, works):
        """ Calculates the aggregate DocumentMetrics values for all undeleted documents related to a list of works.
        """
        return DocumentMetrics.objects\
            .filter(document__work__in=works, document__deleted=False)\
            .aggregate(n_bytes=Sum('n_bytes'), n_provisions=Sum('n_provisions'), n_words=Sum('n_words'), n_pages=Sum('n_pages'))


class DailyWorkMetrics(models.Model):
    """ Daily summarised work metrics.
    """
    date = models.DateField(null=False, db_index=True)
    place_code = models.CharField(null=False, db_index=True, max_length=20)
    country = models.CharField(null=False, max_length=20)
    locality = models.CharField(null=True, max_length=20)

    n_works = models.IntegerField(null=False)
    n_expressions = models.IntegerField(null=True)
    n_points_in_time = models.IntegerField(null=True)
    n_expected_expressions = models.IntegerField(null=True)
    # number of works for which p_breadth_complete == 100
    n_complete_works = models.IntegerField(null=True)

    p_depth_complete = models.IntegerField(null=True)
    p_breadth_complete = models.IntegerField(null=True)
    p_complete = models.IntegerField(null=True)

    class Meta:
        db_table = 'indigo_metrics_daily_workmetrics'
        unique_together = (("date", "place_code"),)

    @classmethod
    def update_daily_work_metrics(cls, date):
        log.info('Updating aggregate daily work metrics for %s.' % date)
        cls.create_or_update(date)
        log.info('Daily work metrics updated')

    @classmethod
    def create_or_update(cls, date=None):
        date = date or datetime.date.today()

        with transaction.atomic():
            cls.objects.filter(date=date).delete()
            cls.insert(date)

    @classmethod
    def insert(cls, date):
        with connection.cursor() as cursor:
            cursor.execute("""
INSERT INTO
  indigo_metrics_daily_workmetrics(
    date, place_code, country, locality,
    n_works, n_expressions, n_expected_expressions, n_points_in_time, n_complete_works,
    p_depth_complete, p_breadth_complete, p_complete
  )
SELECT
  %s AS date,
  frbr_uri_parts[3] AS place_code,
  SUBSTRING(frbr_uri_parts[3] FROM 1 FOR 2) AS country,
  SUBSTRING(frbr_uri_parts[3] FROM 4) AS locality,
  COUNT(1) AS n_works,
  SUM(n_expressions) AS n_expressions,
  SUM(n_expected_expressions) AS n_expected_expressions,
  SUM(n_points_in_time) AS n_points_in_time,
  -- NOTE: we only consider breadth completeness at the moment
  SUM(CASE WHEN p_breadth_complete = 100 THEN 1 ELSE 0 END) as n_complete_works,
  AVG(p_depth_complete) AS p_depth_complete,
  AVG(p_breadth_complete) AS p_breadth_complete,
  AVG(p_complete) AS p_complete
FROM (
  SELECT
    frbr_uri,
    REGEXP_SPLIT_TO_ARRAY(FRBR_URI, '/') AS frbr_uri_parts,
    n_expressions,
    n_expected_expressions,
    n_points_in_time,
    p_depth_complete,
    p_breadth_complete,
    p_complete
  FROM indigo_metrics_workmetrics wm
  INNER JOIN indigo_api_work w ON w.id = wm.work_id
) AS x
GROUP BY
  date, place_code, country, locality
""", [date])


class DailyPlaceMetrics(models.Model):
    date = models.DateField(null=False, db_index=True)
    place_code = models.CharField(null=False, db_index=True, max_length=20)
    country = models.ForeignKey('indigo_api.Country', null=False, on_delete=models.CASCADE)
    locality = models.ForeignKey('indigo_api.Locality', null=True, on_delete=models.CASCADE)

    n_activities = models.IntegerField(null=False, default=0)

    class Meta:
        db_table = 'indigo_metrics_daily_placemetrics'
        unique_together = (("date", "place_code"),)

    @classmethod
    def record_activity(cls, action):
        place_code = action.data.get('place_code')
        if not place_code:
            return

        try:
            country, locality = Country.get_country_locality(place_code)
        except ObjectDoesNotExist:
            return

        metrics, created = cls.objects.get_or_create(
            date=action.timestamp.date(),
            country=country,
            locality=locality,
            place_code=place_code)

        metrics.n_activities += 1
        metrics.save()

# coding=utf-8
import datetime
import io
import xlsxwriter

from django.http import HttpResponse

from indigo.plugins import plugins
from indigo_api.models import Amendment


class XlsxWriter:
    def __init__(self, country, locality):
        country = country
        locality = locality
        locality_code = locality.code if locality else None
        bulk_creator = plugins.for_locale('bulk-creator', country.code, None, locality_code)
        self.aliases = bulk_creator.aliases
        self.place = locality or country
        self.extra_properties = list(self.place.settings.work_properties.keys())

    def write_full_index(self, workbook, works):
        def get_columns():
            base_columns = ['country', 'locality',
                            'title',
                            'subtype', 'number', 'year',
                            'publication_name', 'publication_number',
                            'assent_date', 'publication_date', 'commencement_date',
                            'stub', 'taxonomy',
                            'primary_work',
                            'commenced_by', 'commenced_on_date',
                            'amended_by', 'amended_on_date',
                            'repealed_by', 'repealed_on_date',
                            'subleg',
                            'commences', 'commences_on_date',
                            'amends', 'amends_on_date',
                            'repeals', 'repeals_on_date',
                            'Ignore (x) or in (✔)',
                            'frbr_uri', 'frbr_uri_title',
                            'comments', 'LINKS ETC (add columns as needed)']

            # add extra properties
            columns = self.extra_properties + base_columns

            # transform aliases backwards
            for alias, meaning in self.aliases:
                if meaning in columns:
                    columns[columns.index(meaning)] = alias

            return columns

        def write_amendment_active(n):
            amendments_active = info.get('amendments_active')
            if amendments_active:
                try:
                    amendment = amendments_active[n]
                    sheet.write(row, columns.index('amends'), uri_title(amendment.amended_work))
                    sheet.write(row, columns.index('amends_on_date'), amendment.date, date_format)
                except IndexError:
                    pass

        def write_amendment_passive(n):
            amendments_passive = info.get('amendments_passive')
            if amendments_passive:
                try:
                    amendment = amendments_passive[n]
                    sheet.write(row, columns.index('amended_by'), uri_title(amendment.amending_work))
                    sheet.write(row, columns.index('amended_on_date'), amendment.date, date_format)
                except IndexError:
                    pass

        def write_commencement_active(n):
            commencements_active = info.get('commencements_active')
            if commencements_active:
                try:
                    commencement = commencements_active[n]
                    sheet.write(row, columns.index('commences'), uri_title(commencement.commenced_work))
                    sheet.write(row, columns.index('commences_on_date'), commencement.date or '(unknown)', date_format)
                except IndexError:
                    pass

        def write_commencement_passive(n):
            commencements_passive = info.get('commencements_passive')
            if commencements_passive:
                try:
                    commencement = commencements_passive[n]
                    # don't rewrite main commencement date if it doesn't have a commencing work
                    if commencement == info.get('work').main_commencement and not commencement.commencing_work:
                        return
                    sheet.write(row, columns.index('commenced_by'), uri_title(commencement.commencing_work))
                    sheet.write(row, columns.index('commenced_on_date'), commencement.date or '(unknown)', date_format)
                except IndexError:
                    pass

        def write_field(field):
            column_number = columns.index(field)
            to_write = None
            # transform aliases
            for alias, meaning in self.aliases:
                if alias == field:
                    field = meaning
                    break

            # what to actually write
            if field in ['title', 'subtype', 'number', 'year',
                         'publication_name', 'publication_number', 'frbr_uri',
                         'assent_date', 'publication_date', 'commencement_date']:
                to_write = getattr(work, field)
            elif field == 'country':
                to_write = work.country.code
            elif field == 'locality':
                to_write = work.locality.code if work.locality else ''
            elif field == 'stub' and work.stub:
                to_write = '✔'
            elif field == 'taxonomy':
                to_write = '; '.join(t.slug for t in work.taxonomies.all())
            elif field == 'primary_work':
                to_write = uri_title(work.parent_work)
            elif field == 'repealed_by':
                to_write = uri_title(work.repealed_by)
            elif field == 'repealed_on_date':
                to_write = work.repealed_date
            elif field == 'subleg':
                to_write = '; '.join(uri_title(child) for child in work.child_works.all())
            elif field == 'Ignore (x) or in (✔)':
                to_write = '✔'
            elif field == 'frbr_uri_title':
                to_write = uri_title(work)

            elif field in self.extra_properties:
                to_write = work.properties.get(field)

            if isinstance(to_write, datetime.date):
                sheet.write(row, column_number, to_write, date_format)
            else:
                sheet.write(row, column_number, to_write)

        def write_repeal_active(n):
            repealed_works = info.get('repeals_active')
            if repealed_works:
                try:
                    repealed_work = repealed_works[n]
                    sheet.write(row, columns.index('repeals'), uri_title(repealed_work))
                    sheet.write(row, columns.index('repeals_on_date'), repealed_work.repealed_date, date_format)
                except IndexError:
                    pass

        date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
        sheet = workbook.add_worksheet('Works')
        columns = get_columns()
        # write the column titles
        for position, title in enumerate(columns):
            sheet.write(0, position, title)

        # gather the works and their related information
        rows = []
        for work in works:
            """ how many rows will we need for this work?
                a minimum of one, plus more if there are multiple commencements / amendments / repeals
                 (but not if there's one of each)
                grab the commencements / amendments / repeals while we're at it
            """
            n_rows = 1
            commencements_passive = work.commencements.all().order_by('date')
            amendments_passive = work.amendments.all().order_by('date')
            commencements_active = work.commencements_made.all().order_by('date')
            amendments_active = work.amendments_made.all().order_by('date')
            repeals_active = work.repealed_works.all().order_by('repealed_date')

            for relation in [commencements_passive, amendments_passive,
                             commencements_active, amendments_active, repeals_active]:
                n_rows += len(relation) - 1 if len(relation) else 0

            info = {
                'work': work,
                'n_rows': n_rows,
                'commencements_passive': commencements_passive,
                'amendments_passive': amendments_passive,
                'commencements_active': commencements_active,
                'amendments_active': amendments_active,
                'repeals_active': repeals_active,
            }

            rows.append(info)

        # write the works
        row = 0
        for info in rows:
            work = info.get('work')
            for n in range(info.get('n_rows')):
                row += 1
                for field in columns:
                    write_field(field)
                write_commencement_passive(n)
                write_amendment_passive(n)
                write_commencement_active(n)
                write_amendment_active(n)
                write_repeal_active(n)

    def generate_xlsx(self, queryset, filename, full_index):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)

        if full_index:
            self.write_full_index(workbook, queryset)
        else:
            write_works(workbook, queryset)
            write_relationships(workbook, queryset)

        workbook.close()
        output.seek(0)

        response = HttpResponse(
            output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="%s"' % filename
        return response


def write_works(workbook, queryset):
    date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
    works_sheet = workbook.add_worksheet('Works')
    works_sheet_columns = ['FRBR URI', 'Place', 'Title', 'Subtype', 'Year',
                           'Number', 'Publication Date', 'Publication Number',
                           'Assent Date', 'Commenced', 'Main Commencement Date',
                           'Repealed Date', 'Parent Work', 'Stub']
    # Write the works sheet column titles
    for position, title in enumerate(works_sheet_columns, 1):
        works_sheet.write(0, position, title)

    for row, work in enumerate(queryset, 1):
        works_sheet.write(row, 0, row)
        works_sheet.write(row, 1, work.frbr_uri)
        works_sheet.write(row, 2, work.place.place_code)
        works_sheet.write(row, 3, work.title)
        works_sheet.write(row, 4, work.subtype)
        works_sheet.write(row, 5, work.year)
        works_sheet.write(row, 6, work.number)
        works_sheet.write(row, 7, work.publication_date, date_format)
        works_sheet.write(row, 8, work.publication_number)
        works_sheet.write(row, 9, work.assent_date, date_format)
        works_sheet.write(row, 10, work.commenced)
        works_sheet.write(row, 11, work.commencement_date, date_format)
        works_sheet.write(row, 12, work.repealed_date, date_format)
        works_sheet.write(row, 13, work.parent_work.frbr_uri if work.parent_work else None)
        works_sheet.write(row, 14, work.stub)


def write_relationships(workbook, queryset):
    date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
    relationships_sheet = workbook.add_worksheet('Relationships')
    relationships_sheet_columns = ['First Work', 'Relationship', 'Second Work', 'Date']

    # write the relationships sheet column titles
    for position, title in enumerate(relationships_sheet_columns, 1):
        relationships_sheet.write(0, position, title)

    row = 1
    for work in queryset:
        family = []

        # parent work
        if work.parent_work:
            family.append({
                'rel': 'subsidiary of',
                'work': work.parent_work.frbr_uri,
                'date': None
            })

        # amended works
        amended = Amendment.objects.filter(amending_work=work).prefetch_related('amended_work').all()
        family = family + [{
            'rel': 'amends',
            'work': a.amended_work.frbr_uri,
            'date': a.date
        } for a in amended]

        # repealed works
        repealed_works = work.repealed_works.all()
        family = family + [{
            'rel': 'repeals',
            'work': r.frbr_uri,
            'date': r.repealed_date
        } for r in repealed_works]

        # commenced works
        family = family + [{
            'rel': 'commences',
            'work': c.commenced_work.frbr_uri,
            'date': c.date
        } for c in work.commencements_made.all()]

        for relationship in family:
            relationships_sheet.write(row, 0, row)
            relationships_sheet.write(row, 1, work.frbr_uri)
            relationships_sheet.write(row, 2, relationship['rel'])
            relationships_sheet.write(row, 3, relationship['work'])
            relationships_sheet.write(row, 4, relationship['date'], date_format)
            row += 1


def uri_title(work=None):
    return f'{work.frbr_uri} - {work.title}' if work else ""

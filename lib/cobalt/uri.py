import re

FRBR_URI_RE = re.compile(r"""^/(?P<country>[a-z]{2})       # country
                              (-(?P<locality>[^/]+))?      # locality code
                              /(?P<doctype>[^/]+)          # document type
                              /((?P<subtype>[^/]+)         # subtype (optional)
                              /((?P<actor>[^/]+)/)?)?      # actor (optional)
                              (?P<date>[0-9]{4}(-[0-9]{2}(-[0-9]{2})?)?)  # date
                              /(?P<number>[^/]+)           # number
                              (/                           # optional expression components
                                (?P<language>[a-z]{3})     # language (eg. eng)
                                (@(?P<expression_date>[^/]*))?           # expression date (eg. @ or @2012-12-22)
                                (/(?P<expression_component>[a-z0-9/]+))?  # expression component (eg. /main or /main/schedule1/tableA)
                                (\.(?P<format>[a-z]))?     # format (eg. .xml, .akn, .html, .pdf)
                              )?$""", re.X)

class FrbrUri(object):
    """
    An FRBR URI parser which understands Akoma Ntoso 3.0 FRBR URIs (IRIs) for works
    and expressions.

    .. seealso::

       http://akresolver.cs.unibo.it/admin/documentation.html
       http://www.akomantoso.org/release-notes/akoma-ntoso-3.0-schema/naming-conventions-1/bungenihelpcenterreferencemanualpage.2008-01-09.1484954524
    """

    default_language = 'eng'

    def __init__(self, country, locality, doctype, subtype, actor, date, number,
            language=None, expression_date=None, expression_component=None, 
            format=None):
        self.country = country
        self.locality = locality
        self.doctype = doctype
        self.subtype = subtype
        self.actor = actor
        self.date = date
        self.number = number

        self.language = language or self.default_language
        self.expression_date = expression_date
        self.expression_component = expression_component
        self.format = format

    def work_uri(self):
        """ String form of the work URI. """
        country = self.country
        if self.locality:
            country = country + "-" + self.locality

        parts = ['', country, self.doctype]

        if self.subtype:
            parts.append(self.subtype)
            if self.actor:
                parts.append(self.actor)
        
        parts += [self.date, self.number]
        return '/'.join(parts)

    def expression_uri(self):
        """ String form of the expression URI. """
        uri = self.work_uri() + "/" + self.language

        if self.expression_date is not None:
            uri = uri + '@' + self.expression_date

        if self.expression_component:
            uri = uri + "/" + self.expression_component

        return uri

    def manifestation_uri(self):
        """ String form of the manifestation URI. """
        uri = self.expression_uri()
        if self.format:
            uri = uri + "." + self.format
        return uri

    def __str__(self):
        return self.work_uri()

    @classmethod
    def parse(cls, s):
        match = FRBR_URI_RE.match(s)
        if match:
            return cls(**match.groupdict())
        else:
            raise ValueError("Invalid FRBR URI: %s" % s)

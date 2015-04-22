import re

FRBR_URI_RE = re.compile(r"""^/(?P<country>[a-z]{2})       # country
                              (-(?P<locality>[^/]+))?      # locality code
                              /(?P<doctype>[^/]+)          # document type
                              /((?P<subtype>[^/]+)         # subtype (optional)
                              /((?P<actor>[^/]+)/)?)?      # actor (optional)
                              (?P<date>[0-9]{4}(-[0-9]{2}(-[0-9]{2})?)?)  # date
                              /(?P<number>[^/]+)           # number
                              (/
                               (                           # either a work component or expression details
                                (                                # optional expression details
                                  (?P<language>[a-z]{3})                    # language (eg. eng)
                                  (@(?P<expression_date>[^/]*))?            # expression date (eg. @ or @2012-12-22)
                                  (/                                        # optional expression component
                                    (?P<expression_component>[^/]+?)?       # expression component (eg. main or schedule1)
                                    (/(?P<expression_subcomponent>[^.]+))?  # expression subcomponent (eg. chapter/1 or section/20)
                                  )?                                        #
                                  (\.(?P<format>[a-z]))?                    # format (eg. .xml, .akn, .html, .pdf)
                                )|                                          #
                                (?P<work_component>[^/]{4,})   # work component
                              ))?$""", re.X)


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
                 work_component=None, language=None, expression_date=None, expression_component=None,
                 expression_subcomponent=None, format=None):
        self.country = country
        self.locality = locality
        self.doctype = doctype
        self.subtype = subtype
        self.actor = actor
        self.date = date
        self.number = number
        self.work_component = work_component

        self.language = language or self.default_language
        self.expression_date = expression_date
        self.expression_component = expression_component
        self.expression_subcomponent = expression_subcomponent
        self.format = format

    def clone(self):
        return FrbrUri(
            self.country,
            self.locality,
            self.doctype,
            self.subtype,
            self.actor,
            self.date,
            self.number,
            self.language,
            self.expression_date,
            self.expression_component,
            self.format,
        )

    def uri(self):
        """ String form of the work URI, excluding the work component, if any. """
        return self.work_uri(work_component=False)

    def work_uri(self, work_component=True):
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

        if work_component and self.work_component:
            parts += [self.work_component]

        return '/'.join(parts)

    def expression_uri(self, work_component=True):
        """ String form of the expression URI. """
        uri = self.work_uri(work_component=False) + "/" + self.language

        if self.expression_date is not None:
            # TODO: support virtual expression date with ":" instead of "@"
            # http://www.akomantoso.org/release-notes/akoma-ntoso-3.0-schema/naming-conventions-1/bungenihelpcenterreferencemanualpage.2008-01-09.1856321727
            uri = uri + '@' + self.expression_date

        # expression component is preferred over a work component
        if self.expression_component:
            uri = uri + "/" + self.expression_component
            if self.expression_subcomponent:
                uri = uri + "/" + self.expression_subcomponent

        # if we have a work component, use it
        elif work_component and self.work_component:
            uri = uri + "/" + self.work_component

        return uri

    def manifestation_uri(self, work_component=True):
        """ String form of the manifestation URI. """
        uri = self.expression_uri()
        if self.format:
            uri = uri + "." + self.format
        return uri

    def __str__(self):
        return self.work_uri()

    @classmethod
    def parse(cls, s):
        s = s.rstrip('/')
        match = FRBR_URI_RE.match(s)
        if match:
            return cls(**match.groupdict())
        else:
            raise ValueError("Invalid FRBR URI: %s" % s)

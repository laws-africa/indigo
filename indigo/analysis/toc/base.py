import re
from lxml.html import _collect_string_content
from django.utils.translation import override, ugettext as _

from indigo.plugins import plugins, LocaleBasedMatcher


# Ensure that these translations are included by makemessages
_('Act')
_('Article')
_('By-law')
_('Chapter')
_('Government Notice')
_('Part')
_('Section')
_('Preface')
_('Preamble')


@plugins.register('toc')
class TOCBuilderBase(LocaleBasedMatcher):
    """ This builds a Table of Contents for an Act.

    A Table of Contents is a tree of :class:`TOCElement` instances, each element
    representing an item of interest in the Table of Contents. Each item
    has attributes useful for presenting a Table of Contents, such as a type
    (chapter, part, etc.), a number, a heading and further child elements.

    The TOC is assembled from certain tags in the document, see ``toc_elements``.

    The Table of Contents can also be used to lookup the XML element corresponding
    to an item in the Table of Contents identified by its subcomponent path.
    This is useful when handling URIs such as ``.../eng/main/section/1`` or
    ``.../eng/main/part/C``. See :meth:`cobalt.act.Act.get_subcomponent`.

    Some components can be uniquely identified by their type and number, such as
    ``Section 2``. Others require context, such as ``Part 2 of Chapter 1``. The
    latter are controlled by ``toc_non_unique_elements``.
    """

    locale = (None, None, None)
    """ The locale this TOC builder is suited for, as ``(country, language, locality)``.
    """

    toc_elements = ['coverpage', 'preface', 'preamble', 'part', 'chapter', 'section', 'conclusions']
    """ Elements we include in the table of contents, without their XML namespace. Subclasses must
    provide this.
    """

    toc_non_unique_components = ['chapter', 'part']
    """ These TOC elements (tag names without namespaces) aren't numbered uniquely throughout the document
    and will need their parent components for context. Subclasses must provide this.
    """

    titles = {}
    """ Dict from toc elements (tag names without namespaces) to functions that take a :class:`TOCElement` instance
    and return a string title for that element.

    Include the special item `default` to handle elements not in the list.
    """

    # eg. schedule1
    component_id_re = re.compile('([^0-9]+)([0-9]+)')

    def table_of_contents_for_document(self, document):
        return self.table_of_contents(document.doc, document.django_language)

    def setup(self):
        self._toc_elements_ns = set('{%s}%s' % (self.act.namespace, s) for s in self.toc_elements)

    def is_toc_element(self, element):
        return element.tag in self._toc_elements_ns

    def table_of_contents(self, act, language):
        """ Get the table of contents of ``act`` as a list of :class:`TOCElement` instances. """
        self.act = act
        self.language = language
        self.setup()

        with override(language):
            return self.build_table_of_contents()

    def build_table_of_contents(self):
        toc = []
        for component, element in self.act.components().iteritems():
            if component != "main":
                # non-main components are items in their own right
                item = self.make_toc_entry(element, component)
                item.children = self.process_elements(component, [element])
                toc += [item]
            else:
                toc += self.process_elements(component, [element])

        return toc

    def process_elements(self, component, elements, parent=None):
        """ Process the list of ``elements`` and their children, and
        return a (potentially empty) set of TOC items.
        """
        items = []
        for e in elements:
            if self.is_toc_element(e):
                item = self.make_toc_entry(e, component, parent=parent)
                item.children = self.process_elements(component, e.iterchildren(), parent=item)
                items.append(item)
            else:
                items += self.process_elements(component, e.iterchildren())
        return items

    def make_toc_entry(self, element, component, parent=None):
        type_ = element.tag.split('}', 1)[-1]
        id_ = element.get('id')

        if type_ == 'doc':
            # component, get the title from the alias
            heading = element.find('./{*}meta//{*}FRBRalias')
            if heading is not None:
                heading = heading.get('value')
            else:
                # eg. schedule1 -> Schedule 1
                m = self.component_id_re.match(component)
                if m:
                    typ, num = m.groups()
                    heading = '%s %s' % (_(typ.capitalize()), num)
                else:
                    heading = _(component.capitalize())
        else:
            try:
                heading = _collect_string_content(element.heading)
            except AttributeError:
                heading = None

        try:
            num = element.num
        except AttributeError:
            num = None

        num = num.text if num else None

        if type_ == "doc":
            subcomponent = None
        else:
            # if we have a chapter/part as a child of a chapter/part, we need to include
            # the parent as context because they aren't unique, eg: part/1/chapter/2
            if type_ in self.toc_non_unique_components and parent and parent.type in self.toc_non_unique_components:
                subcomponent = parent.subcomponent + "/"
            else:
                subcomponent = ""

            # eg. 'preamble' or 'chapter/2'
            subcomponent += type_

            if num:
                subcomponent += '/' + num.strip('.()')

        toc_item = TOCElement(element, component, type_, heading=heading, id_=id_,
                              num=num, subcomponent=subcomponent, parent=parent)
        toc_item.title = self.friendly_title(toc_item)

        return toc_item

    def friendly_title(self, item):
        """ Build a friendly title for this, based on heading names etc.
        """
        if item.type in self.titles:
            return self.titles[item.type](item)

        if 'default' in self.titles:
            return self.titles['default'](item)

        return self.default_title(item)

    def default_title(self, item):
        if item.heading:
            title = item.heading
        else:
            title = _(item.type.capitalize())
            if item.num:
                title += u' ' + item.num

        return title


class TOCElement(object):
    """
    An element in the table of contents of a document, such as a chapter, part or section.

    :ivar children: further TOC elements contained in this one, may be None or empty
    :ivar element: :class:`lxml.objectify.ObjectifiedElement` the XML element of this TOC element
    :ivar heading: heading for this element, excluding the number, may be None
    :ivar title: friendly title of this entry
    :ivar id: XML id string of the node in the document, may be None
    :ivar num: number of this element, as a string, may be None
    :ivar component: number of the component that this item is a part of, as a string
    :ivar subcomponent: name of this subcomponent, used by :meth:`cobalt.act.Act.get_subcomponent`, may be None
    :ivar type: element type, one of: ``chapter, part, section`` etc.
    """

    def __init__(self, element, component, type_, heading=None, id_=None, num=None, subcomponent=None, parent=None, children=None):
        self.element = element
        self.component = component
        self.type = type_
        self.heading = heading
        self.id = id_
        self.num = num
        self.children = children
        self.subcomponent = subcomponent
        self.title = None

    def as_dict(self):
        info = {
            'type': self.type,
            'component': self.component,
            'subcomponent': self.subcomponent,
            'title': self.title,
        }

        if self.heading:
            info['heading'] = self.heading

        if self.num:
            info['num'] = self.num

        if self.id:
            info['id'] = self.id

        if self.children:
            info['children'] = [c.as_dict() for c in self.children]

        return info

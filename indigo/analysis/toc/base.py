import re
from functools import lru_cache

from lxml import etree

from django.utils.translation import override, ugettext as _

from indigo.plugins import plugins, LocaleBasedMatcher


# Ensure that these translations are included by makemessages
from indigo.xmlutils import closest

_('Act')
_('Article')
_('By-law')
_('Chapter')
_('Government Notice')
_('Part')
_('Section')
_('Preface')
_('Preamble')


@lru_cache(maxsize=None)
def type_title(typ, language):
    """ Title for this type of TOC item, translated.

    language is a django language code. It is only used for caching key purposes. It is assumed
    that the django language has been set to this language already.

    This can be called 10,000s of times when building a TOC, but there are only a handful
    of possible item types, so they are cached for performance.
    """
    return _(typ.capitalize())


def descend_toc_pre_order(items):
    # yields each item and then its children, recursively
    for item in items:
        yield item
        for descendant in descend_toc_pre_order(item.children):
            yield descendant


def descend_toc_post_order(items):
    # yields each item's children, recursively, ending with itself
    for item in items:
        for descendant in descend_toc_post_order(item.children):
            yield descendant
        yield item


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
    ``.../eng/main/part/C``.

    Some components can be uniquely identified by their type and number, such as
    ``Section 2``. Others require context, such as ``Part 2 of Chapter 1``. The
    latter are controlled by ``toc_non_unique_elements``.
    """

    locale = (None, None, None)
    """ The locale this TOC builder is suited for, as ``(country, language, locality)``.
    """

    toc_basic_units = ['section']
    """ The basic units for the tradition.
    """

    toc_elements = [
        # top-level
        'coverpage', 'preface', 'preamble', 'conclusions', 'attachment', 'component',
        # hierarchical elements
        'alinea', 'article', 'book', 'chapter', 'clause', 'division', 'indent', 'level', 'list',
        'paragraph', 'part', 'point', 'proviso', 'rule', 'section',
        'subchapter', 'subclause', 'subdivision', 'sublist', 'subparagraph', 'subpart', 'subrule',
        'subsection', 'subtitle', 'title', 'tome', 'transitional',
    ]
    """ Elements we include in the table of contents, without their XML namespace.
        Base includes the following from the from the AKN schema:
        - all `hierarchicalStructure` elements, except:
          - `meta` and `body` are excluded
          - `attachment` and `component` are included individually rather than their plural containers
        - all `ANhier` (hierarchical) elements
        - no block elements.
    """

    toc_deadends = ['meta', 'attachments', 'components', 'embeddedStructure', 'quotedStructure', 'subFlow']
    """ Elements we don't check or recurse into because they contain sub-documents or subflows.
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

    component_elements = ['component', 'attachment']
    """ Elements that are considered components.
    """

    # eg. schedule1
    component_id_re = re.compile('([^0-9]+)([0-9]+)')

    non_commenceable_toplevel_elements = set(['coverpage', 'preface', 'preamble', 'conclusions', 'attachment', 'component'])

    def table_of_contents_for_document(self, document):
        """ Build the table of contents for a document.
        """
        return self.table_of_contents(document.doc, document.django_language)

    def table_of_contents_entry_for_element(self, document, element):
        """ Build the table of contents entry for an element from a document.
        """
        self.setup(document.doc, document.django_language)

        with override(self.language):
            name, component_el = self.determine_component(element)
            # find the first node at or above element, that is a valid TOC element
            element = closest(element, lambda e: self.is_toc_element(e))
            if element is not None:
                return self.make_toc_entry(element, name, self.get_component_id(name, component_el))

    def setup(self, act, language):
        self.act = act
        self.language = language
        self._toc_elements_ns = set(f'{{{self.act.namespace}}}{s}' for s in self.toc_elements)
        self._toc_deadends_ns = set(f'{{{self.act.namespace}}}{s}' for s in self.toc_deadends)
        self.heading_text_path = etree.XPath(".//text()[not(ancestor::a:authorialNote)]", namespaces={'a': self.act.namespace})

    def determine_component(self, element):
        """ Determine the component element which contains +element+.
        """
        ancestors = [element] + list(element.iterancestors())

        # reversed so that we go through components before the main document element,
        # because all components are ancestors of that
        for name, element in reversed(self.act.components().items()):
            if element in ancestors:
                return name, element

        return None, None

    def is_toc_element(self, element):
        return element.tag in self._toc_elements_ns or (
            # AKN 2.0 crossheadings are <hcontainer name="crossheading">
            'crossheading' in self.toc_elements and element.tag.endswith('}hcontainer')
            and element.get('name', None) == 'crossheading')

    def table_of_contents(self, act, language):
        """ Get the table of contents of ``act`` as a list of :class:`TOCElement` instances. """
        self.setup(act, language)

        with override(language):
            return self.build_table_of_contents()

    def build_table_of_contents(self):
        toc = []
        for component, element in self.act.components().items():
            toc += self.process_elements(component, self.get_component_id(component, element), [element])

        return toc

    def get_component_id(self, name, element):
        """ Get an ID for this component element.
        """
        return None if name == 'main' else element.get('eId')

    def process_elements(self, component, component_id, elements, parent=None):
        """ Process the list of ``elements`` and their children, and
        return a (potentially empty) set of TOC items.
        """
        items = []
        for e in elements:
            # don't descend into these elements, which can contain nested documents or other subflows
            if e.tag in self._toc_deadends_ns:
                continue

            if self.is_toc_element(e):
                item = self.make_toc_entry(e, component, component_id, parent=parent)
                item.children = self.process_elements(component, component_id, e.iterchildren(), parent=item)
                items.append(item)
            else:
                items += self.process_elements(component, component_id, e.iterchildren())
        return items

    def make_toc_entry(self, element, component, component_id, parent=None):
        type_ = element.tag.split('}', 1)[-1]
        id_ = element.get('eId')

        # support for crossheadings in AKN 2.0
        if type_ == 'hcontainer' and element.get('name', None) == 'crossheading':
            type_ = 'crossheading'

        try:
            # collect text without descending into authorial notes
            heading = ''.join(self.heading_text_path(element.heading))
        except AttributeError:
            heading = None

        if not heading and type_ in self.component_elements:
            try:
                # try to use the alias from the attachment/component meta attribute
                heading = element.doc.meta.identification.FRBRWork.FRBRalias.get('value')
            except AttributeError:
                pass

            if not heading:
                # try the doc name
                try:
                    heading = element.doc.get('name', '').capitalize()
                except AttributeError:
                    pass

        try:
            num = element.num
        except AttributeError:
            num = None

        num = num.text if num else None

        if type_ in self.component_elements:
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
                              num=num, subcomponent=subcomponent, component_id=component_id,
                              basic_unit=type_ in self.toc_basic_units)
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
            title = type_title(item.type, self.language)
            if item.num:
                title += ' ' + item.num

        return title

    def commenceable_items(self, toc):
        """ Return a list of those items in +toc+ that are considered commenceable.

        By default, these are all the child items in the main component, except
        the preface, preamble and conclusion.
        Only the top-level toc elements are assessed.
        """
        def process(item):
            if item.component == 'main':
                if item.type not in self.non_commenceable_toplevel_elements and item.num:
                    items.append(item)

        items = []
        for entry in toc:
            process(entry)

        return items

    def insert_commenceable_provisions(self, toc, provisions, id_set):
        items = self.commenceable_items(toc)
        self.insert_provisions(provisions, id_set, items)

    def insert_provisions(self, provisions, id_set, items):
        """ Insert provisions from current toc at their correct indexes in `provisions`.
            `provisions` is a list of provisions for a work, usually built up by adding provisions to it
                from each point in time (using this method).
            `id_set` is the current set of ids that have already been added to `provisions`;
                it helps ensure that our list contains only unique provisions.
            `items` is a list of commenceable provisions from the current document's ToC.
        """
        # TODO: allow for structural changes (sections moved into Parts etc)
        # take note of any removed items to compensate for later
        removed_indexes = [i for i, p in enumerate(provisions) if p.id not in [i.id for i in items]]
        for i, item in enumerate(items):
            # We need to insert this provision at the correct position in the work provision list.
            # We also need to identify the right children based on the index.
            # If any provisions from a previous document have been removed in this document
            # (indexes stored in removed_indexes), bump the insertion index up to take them into account.
            for n in removed_indexes:
                if i >= n:
                    i += 1

            if item.id and item.id not in id_set:
                id_set.add(item.id)
                provisions.insert(i, item)

            # look at children and insert any provisions there too (ToC can be deeply nested)
            if item.children:
                try:
                    existing_children = provisions[i].children
                    existing_id_set = set([e.id for e in existing_children])
                except IndexError:
                    # the parent provision didn't exist previously
                    existing_children = []
                    existing_id_set = set()
                self.insert_provisions(existing_children, existing_id_set, item.children)


class TOCElement(object):
    """
    An element in the table of contents of a document, such as a chapter, part or section.

    :ivar children: further TOC elements contained in this one, defaults to empty list
    :ivar component: component name (after the ! in the FRBR URI) of the component that this item is a part of
    :ivar element: :class:`lxml.objectify.ObjectifiedElement` the XML element of this TOC element
    :ivar heading: heading for this element, excluding the number, may be None
    :ivar id: XML id string of the node in the document, may be None
    :ivar num: number of this element, as a string, may be None
    :ivar qualified_id: the id of the element, qualified by the component id (if any)
    :ivar subcomponent: name of this subcomponent, may be None
    :ivar title: friendly title of this entry
    :ivar type: element type, one of: ``chapter, part, section`` etc.
    :ivar basic_unit: boolean, defaults to False.
    """

    def __init__(self, element, component, type_, heading=None, id_=None, num=None, subcomponent=None, children=None, component_id=None, basic_unit=False):
        self.element = element
        self.component = component
        self.type = type_
        self.heading = heading
        self.id = id_
        self.num = num
        self.children = children or []
        self.subcomponent = subcomponent
        self.title = None
        self.qualified_id = id_ if component == 'main' else f"{component_id}/{id_}"
        self.basic_unit = basic_unit

    def as_dict(self):
        return {
            'type': self.type,
            'component': self.component,
            'subcomponent': self.subcomponent,
            'title': self.title,
            'children': [c.as_dict() for c in self.children],
            'basic_unit': self.basic_unit,
            'num': self.num,
            'id': self.id,
            'heading': self.heading,
        }


class BeautifulElement:
    def __init__(self, toc_element):
        self.toc_element = toc_element
        self.num = toc_element.num.strip('.') if toc_element.num else ''
        self.children = [BeautifulElement(c) for c in toc_element.children]
        # info that'll get added at decorate_provisions and elsewhere as booleans
        self.commenced = None
        self.last_node = None
        self.all_descendants_same = None
        self.all_descendants_opposite = None
        self.container = None
        self.full_container = None
        self.visible = None
        self.visible_descendants = None

    def __getattr__(self, item):
        return getattr(self.toc_element, item)


@plugins.register('commencements-beautifier')
class CommencementsBeautifier(LocaleBasedMatcher):
    locale = (None, None, None)
    """ The locale this commencements beautifier is suited for, as ``(country, language, locality)``.
    """

    capitalize_types = ['part', 'chapter']
    """ The types that should be capitalized when beautified for the tradition.
    """

    def __init__(self):
        self.commenced = True
        self.current_run = None
        self.runs = None
        self.previous_in_run = False

    def decorate_provisions(self, provisions, assess_against):
        provisions = [BeautifulElement(p) for p in provisions]
        for p in descend_toc_post_order(provisions):

            # when self.commenced is True, assess_against is the list of commenced provision ids
            # when self.commenced is False, assess_against is the list of uncommenced provision ids
            p.commenced = self.commenced if p.id in assess_against else not self.commenced

            p.last_node = not p.children

            # Do ALL descendants share the same commencement status as the current p?
            # empty list passed to all() returns True
            p.all_descendants_same = all(
                c.commenced == p.commenced and
                (c.all_descendants_same or c.last_node)
                for c in p.children
            ) if p.children else False

            # Do NO descendants share the same commencement status as the current p?
            # empty list passed to all() returns True
            p.all_descendants_opposite = all(
                c.commenced != p.commenced and
                (c.all_descendants_same or c.last_node)
                for c in p.children
            ) if p.children else False

            p.container = any(c.basic_unit or c.container for c in p.children)

            # e.g. Subpart I, which is commenced, contains sections 1 to 3, all of which are fully commenced
            p.full_container = p.container and p.all_descendants_same

        return provisions

    def add_to_run(self, p, run):
        typ = p.type.capitalize() if p.type in self.capitalize_types else p.type
        # start a new run if this type is different
        new_run = typ not in [r['type'] for r in run] if run else False
        run.append({'type': typ, 'num': p.num, 'new_run': new_run})

    def stringify_run(self, run):
        # first (could be only) item, e.g. 'section 1'
        run_str = f"{run[0]['type']} {run[0]['num']}" if run[0]['num'] else run[0]['type']
        # common case: e.g. section 1–5 (all the same type)
        if len(run) > 1 and not any(r['new_run'] for r in run):
            run_str += f"–{run[-1]['num']}"

        # e.g. section 1–3, article 1–2, regulation 1
        elif len(run) > 1:
            # get all of the first group, e.g. section
            first_type = [r for r in run if r['type'] == run[0]['type']]
            run_str += f"–{first_type[-1]['num']}" if len(first_type) > 1 else ''

            # get all e.g. articles, then all e.g. regulations
            for subsequent_type in [r['type'] for r in run if r['new_run']]:
                this_type = [r for r in run if r['type'] == subsequent_type]
                run_str += f", {subsequent_type} {this_type[0]['num']}" if this_type[0]['num'] else f", {subsequent_type}"
                run_str += f"–{this_type[-1]['num']}" if len(this_type) > 1 else ''

        return run_str

    def add_all_basics(self, p):
        """ Adds a description of all basic units in a container to the container's `num`.
        e.g. Part A's `num`: 'A' --> 'A (section 1–3)'
        """
        # get all the basic units in the container, but don't look lower than needed
        basics = []
        def look_for_basics(prov, basics):
            if prov.basic_unit:
                self.add_to_run(prov, basics)
            elif prov.container:
                for c in prov.children:
                    look_for_basics(c, basics)

        # we don't need to check if p itself is a basic unit because it must be a container
        for c in p.children:
            look_for_basics(c, basics)

        p.num += f' ({self.stringify_run(basics)})' if basics else ''

    def stash_current(self):
        if self.current_run:
            self.current_stash.append(self.current_run)
            self.current_run = []

    def add_to_current(self, p, all_basic_units=False):
        if all_basic_units:
            # num becomes more descriptive
            self.add_all_basics(p)
        self.add_to_run(p, self.current_run)

    def end_current(self):
        stash = ', '.join([self.stringify_run(r) for r in self.current_stash]) if self.current_stash else None
        run = self.stringify_run(self.current_run) if self.current_run else None
        if stash or run:
            self.runs.append(', '.join([x for x in [stash, run] if x]))
        self.current_stash = []
        self.current_run = []
        self.previous_in_run = False

    def process_basic_unit(self, p):
        """ Adds the subprovisions that have also (not) commenced to the basic unit's `num`,
        unless the entire provision is (un)commenced.
        e.g. section 2's `num`: '2' --> '2(1), 2(3), 2(4)'
        e.g. section 1's `num`: '1' --> '1(1)(a)(ii), 1(1)(a)(iii), 1(1)(c), 1(2)'
        """
        end_at_next_add = False
        subs_to_add = []

        def add_to_subs(p, prefix):
            # stop drilling down if the subprovision is fully un/commenced or is the last (un/commenced) node
            if p.commenced == self.commenced and (
                    p.last_node or p.all_descendants_same or p.all_descendants_opposite
            ):
                # go no further down, prefix with all parent nums
                subs_to_add.append(prefix + p.num)
            # keep drilling if some descendants are different
            elif not p.all_descendants_same:
                for c in p.children:
                    add_to_subs(c, prefix + p.num)

        if p.children and not p.all_descendants_same:
            # don't continue run if we're giving subprovisions
            end_at_next_add = True
            self.stash_next = True
            # e.g. section 1-5, section 6(1)
            if p.type in [r['type'] for r in self.current_run]:
                self.stash_current()
            for c in p.children:
                add_to_subs(c, p.num)

        p.num = ', '.join(subs_to_add) if subs_to_add else p.num
        self.add_to_current(p)

        if end_at_next_add:
            self.stash_current()
        elif self.stash_next:
            self.stash_current()
            self.stash_next = False

    def process_provision(self, p):
        # start processing?
        if p.commenced == self.commenced or (p.children and not p.all_descendants_same):
            # e.g. a fully un/commenced Chapter or Part: Chapter 1 (sections 1–5)
            if p.full_container:
                self.add_to_current(p, all_basic_units=True)
                self.end_current()

            # e.g. a Chapter that isn't fully un/commenced
            elif p.container:
                # if the id was explicitly given and none of the children will be given: Chapter 1 (in part);
                if p.commenced == self.commenced and p.all_descendants_opposite:
                    old_num = p.num
                    p.num += ' (in part)'
                    self.add_to_current(p)
                    p.num = old_num
                    self.end_current()
                # if we're going to keep going: Chapter 1, Part …
                else:
                    self.add_to_current(p)

            # e.g. section with subsections
            elif p.basic_unit:
                self.process_basic_unit(p)
                # keep track in case the next section isn't included
                self.previous_in_run = True

            # lonely subprovision, e.g. Chapter 1 item (a)
            elif not p.container and p.commenced == self.commenced:
                # TODO: deal with nested lonely subprovisions
                self.add_to_current(p)
                self.previous_in_run = True

            # keep drilling down on partially un/commenced containers
            if not (p.full_container or p.basic_unit) and (
                    not p.all_descendants_opposite or p.commenced != self.commenced
            ):
                for c in p.children:
                    self.process_provision(c)
                # e.g. end of Part A, sections were checked individually
                if p.container:
                    self.end_current()

        # e.g. section 1–3, section 5–8
        elif self.previous_in_run and p.basic_unit:
            self.stash_current()

    def make_beautiful(self, provisions, assess_against):
        self.current_run = []
        self.current_stash = []
        self.runs = []
        self.previous_in_run = False
        self.stash_next = False

        provisions = self.decorate_provisions(provisions, assess_against)

        for p in provisions:
            self.process_provision(p)

        self.end_current()

        return '; '.join(p for p in self.runs)

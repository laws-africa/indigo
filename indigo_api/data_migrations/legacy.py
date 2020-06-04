import re

from indigo_api.data_migrations import AKNMigration


class ScheduleArticleToHcontainer(AKNMigration):
    """ Change from using article as the main schedule container
    to using hcontainer.

    Migrates:

        <mainBody>
          <article id="schedule2">
            <heading>BY-LAWS REPEALED BY SECTION 99</heading>
            <paragraph id="schedule2.paragraph-0">

    to:

        <mainBody>
          <hcontainer id="schedule2" name="schedule">
            <heading>Schedule 2</heading>
            <subeading>BY-LAWS REPEALED BY SECTION 99</subeading>
            <paragraph id="schedule2.paragraph-0">
    """
    def migrate_act(self, act):
        changed = False

        for article in act.root.xpath('//a:mainBody/a:article', namespaces={'a': act.namespace}):
            changed = True

            # change to hcontainer
            article.tag = '{%s}hcontainer' % act.namespace
            article.set('name', 'schedule')

            # make heading a subheading
            try:
                heading = article.heading
                heading.tag = '{%s}subheading' % act.namespace
            except AttributeError:
                pass

            # add a new heading
            alias = article.getparent().getparent().meta.identification.FRBRWork.FRBRalias.get('value')
            heading = act.maker.heading(alias)
            article.insert(0, heading)

        return changed


class FixSignificantWhitespace(AKNMigration):
    """ Strip unnecessary whitespace from p, heading, subheading and listIntroduction
    elements.

    In the past, we pretty-printed our XML which introduced meaningful whitespace. This
    migration removes it.
    """
    def migrate_document(self, document):
        xml = self.strip_whitespace(document.document_xml)
        if xml != document.document_xml:
            document.reset_xml(xml, from_model=True)
            return True

    def strip_whitespace(self, xml):
        opening = re.compile(r'<(p|heading|subheading|listIntroduction)>\n\s+<')
        xml = opening.sub('<\\1><', xml)

        closing = re.compile(r'\s*\n\s+</(p|heading|subheading|listIntroduction)>')
        xml = closing.sub('</\\1>', xml)

        return xml

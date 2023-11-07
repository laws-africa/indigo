from django.core.management import BaseCommand
from django.utils.text import slugify
from indigo_api.models import TaxonomyTopic, Workflow

import logging

log = logging.getLogger(__name__)


def get_or_create_topic(name, parent=None, description=None):
    slug = f'{parent.slug}-{slugify(name)}' if parent else f'{slugify(name)}'
    topic = TaxonomyTopic.objects.filter(slug=slug).first()
    if topic:
        log.info(f'Got topic {topic}')
        if description:
            log.warning(f'Description not added; topic already existed')
    else:
        if parent:
            topic = TaxonomyTopic.add_child(parent, name=name, description=description)
            log.info(f'Added topic child: {topic} under {parent}')
        else:
            topic = TaxonomyTopic.add_root(name=name, description=description)
            log.info(f'Added topic root: {topic}')

    return topic


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # get or create 'Projects' topic root
        projects_root = get_or_create_topic('Projects')

        # get or create priority children: High, Medium, Low
        high_priority = get_or_create_topic('Priority: High', parent=projects_root)
        medium_priority = get_or_create_topic('Priority: Medium', parent=projects_root)
        low_priority = get_or_create_topic('Priority: Low', parent=projects_root)

        for project in Workflow.objects.all():
            place = f'{project.country.country.name}, {project.locality.name}' if project.locality else project.country.country.name
            log.info(f'\nProcessing {project.title} in {place}')
            # scope project title to place
            new_title = f'{place} – {project.title}'
            priority_root = high_priority if project.priority else low_priority
            project_taxonomy = get_or_create_topic(new_title, parent=priority_root, description=project.description)

            # add project taxonomy to all related works
            for task in project.tasks.all():
                if task.work:
                    task.work.taxonomy_topics.add(project_taxonomy)

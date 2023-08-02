from django.core.management import BaseCommand
from indigo_api.models import TaxonomyTopic, TaxonomyVocabulary, Work
from django.utils.text import slugify
from treebeard.exceptions import NodeAlreadySaved
from psycopg2 import IntegrityError

import logging

log = logging.getLogger(__name__)

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for t in TaxonomyVocabulary.objects.all().iterator():
            root = TaxonomyTopic.add_root(name=t.title)
            log.info(f"Created root node {root}")
            for vocabulary in t.topics.all():

                if vocabulary.level_1:
                    log.info(f"Creating child node {vocabulary.level_1}")
                    slug = slugify(f"{root.slug}-{vocabulary.level_1}")
                    child = TaxonomyTopic.objects.filter(slug=slug).first()
                    if child:
                        log.info(f"Found existing node {child}")
                    else:
                        child = TaxonomyTopic.add_child(root, name=vocabulary.level_1)

                    if vocabulary.level_2:
                        log.info(f"Creating child node {vocabulary.level_2}")
                        child = TaxonomyTopic.add_child(child, name=vocabulary.level_2)

                    for work in vocabulary.works.all():
                        log.info(f"Adding work {work} to {child}")
                        work.taxonomy_topics.add(child)

from nose.tools import assert_equal, assert_not_equal
from rest_framework.test import APITestCase
from django.contrib.auth.models import User, Permission, ContentType
from django.test.utils import override_settings

from indigo_api.models import Work, ProvisionTaxonomyTopic
from indigo_app.tests.utils import TEST_STORAGES


@override_settings(STORAGES=TEST_STORAGES)
class WorkAPITest(APITestCase):
    fixtures = ['languages_data', 'countries', 'user', 'editor', 'taxonomy_topics', 'work', 'drafts', 'published']

    def setUp(self):
        self.client.login(username='email@example.com', password='password')

    def test_prevent_delete(self):
        work = Work.objects.get(pk=7)

        self.assertRedirects(self.client.post('/works%s/delete' % work.frbr_uri), '/works%s/edit/' % work.frbr_uri)

        # delete linked documents
        work.expressions().delete()

        # now can delete
        self.assertRedirects(self.client.post('/works%s/delete' % work.frbr_uri), '/places/za')

    def test_filters(self):
        response = self.client.get('/api/works?country=za')
        assert_equal(response.status_code, 200)
        assert_not_equal(len(response.data['results']), 0)

        response = self.client.get('/api/works?country=xy')
        assert_equal(response.status_code, 200)
        assert_equal(response.data['results'], [])

    def test_provision_taxonomy_topics(self):
        user = User.objects.get(username='email@example.com')
        content_type = ContentType.objects.get_for_model(ProvisionTaxonomyTopic)
        user.user_permissions.add(*Permission.objects.filter(
            content_type=content_type,
            codename__in=[
                'view_provisiontaxonomytopic',
                'add_provisiontaxonomytopic',
            ],
        ))

        other_work = Work.objects.get(pk=2)
        ProvisionTaxonomyTopic.objects.create(
            work=other_work,
            taxonomy_topic_id=2,
            provision_eid='sec_99',
        )

        response = self.client.post('/api/works/1/provision-taxonomy-topics', {
            'provision_eid': 'sec_1',
            'taxonomy_topic': 'lawsafrica-subject-areas-money-and-business',
        }, format='json')
        assert_equal(response.status_code, 201)
        assert_equal(response.data['provision_eid'], 'sec_1')
        assert_equal(response.data['taxonomy_topic'], 'lawsafrica-subject-areas-money-and-business')

        provision_topic = ProvisionTaxonomyTopic.objects.get(pk=response.data['id'])
        assert_equal(provision_topic.work_id, 1)

        response = self.client.get('/api/works/1/provision-taxonomy-topics')
        assert_equal(response.status_code, 200)
        assert_equal(response.data['count'], 1)
        assert_equal(response.data['results'][0]['provision_eid'], 'sec_1')
        assert_equal(response.data['results'][0]['taxonomy_topic'], 'lawsafrica-subject-areas-money-and-business')

import re

import django
from django.urls import get_resolver
from django.test import testcases

from indigo_app.views.base import AbstractAuthedIndigoView


class AuthedUrlsTest(testcases.TestCase):
    non_authed_urls = r"""
robots\.txt\Z
help\Z
terms\Z
\Z

accounts/social/connections/\Z
accounts/social/signup/\Z
accounts/social/login/error/\Z
accounts/social/login/cancelled/\Z
accounts/password/reset/key/done/\Z
accounts/password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$
accounts/password/reset/done/\Z
accounts/password/reset/\Z
accounts/confirm-email/(?P<key>[-:\w]+)/$
accounts/confirm\-email/\Z
accounts/email/\Z
accounts/inactive/\Z
accounts/password/set/\Z
accounts/password/change/\Z
accounts/logout/\Z
accounts/login/\Z
accounts/signup/\Z

resolver/(?P<path>.+)$
resolver/((?P<authorities>[\w,.-]+)/)?resolve(?P<frbr_uri>/.*)$

api/$
api/documents/(?P<document_id>[0-9]+)/analysis/mark\-up\-italics\Z
api/documents/(?P<document_id>[0-9]+)/analysis/link\-references\Z
api/documents/(?P<document_id>[0-9]+)/analysis/link\-terms\Z
api/documents/(?P<document_id>[0-9]+)/static/(?P<filename>.+)\Z
api/documents/(?P<document_id>[0-9]+)/render/coverpage\Z
api/documents/(?P<document_id>[0-9]+)/parse\Z
api/documents/(?P<document_id>[0-9]+)/diff\Z
api/documents/(?P<document_id>[0-9]+)/media/(?P<filename>.*)$
api/publications/(?P<country>[a-z]{2})(-(?P<locality>[^/]+))?/find$
""".split()

    def setUp(self):
        # version 2.2.25 changed the regexes for URLs, so account for the old format
        if django.VERSION < (2, 2, 25):
            self.non_authed_urls = [re.sub(r'\\Z$', '$', x) for x in self.non_authed_urls]

    def test_urls_have_auth(self):
        """ This test checks that all URLs, except those explicitly whitelisted, inherit from the
        AbstractAuthedIndigoView class, which requires authentication.
        """
        entries = [[k, v[1]] for k, v in get_resolver().reverse_dict.items()]

        for view, url in entries:
            # different python versions have slightly different regex string formats, so normalize them
            url = url.replace('\\/', '/')

            view_class = getattr(view, 'view_class', None)
            if view_class:
                if AbstractAuthedIndigoView not in view_class.__mro__ and url not in self.non_authed_urls:
                    # NOTE: if your view is failing this test either add it to the list of urls that are expected
                    #       not to require authentication, or ensure it inherits from AbstractAuthedIndigoView
                    self.fail(f'The view for {url} does not have AbstractAuthedIndigoView as an ancestor. Are you'
                              ' sure it does not require authentication?')

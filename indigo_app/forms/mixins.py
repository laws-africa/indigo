import urllib.parse


class FormAsUrlMixin:
    """Adds a helper method to serialise the submitted form data (uncleaned) as a URL query string. This is useful for
    pagination links.
    """
    def data_as_url(self):
        # only keep keeps that were cleaned
        data = [(k, v) for k, v in self.data.lists() if k in self.cleaned_data]
        return urllib.parse.urlencode(data, True, encoding='utf-8')

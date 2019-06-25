from indigo_content_api.tests.v1.test_countries_api import CountriesAPIV1Test


class CountriesAPIV2Test(CountriesAPIV1Test):
    fixtures = ['countries', 'user']
    api_path = '/api/v2'

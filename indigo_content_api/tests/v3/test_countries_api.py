from indigo_content_api.tests.v2.test_countries_api import CountriesAPIV2Test


class CountriesAPIV3Test(CountriesAPIV2Test):
    api_path = '/api/v3'

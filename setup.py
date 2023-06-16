from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

with open(path.join(here, 'VERSION')) as f:
    version = f.read().strip()


setup(
    name='indigo',
    version=version,
    description='A Django application for publishing legislation using Akoma Ntoso',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/laws-africa/indigo',

    # Author details
    author='Laws.Africa',
    author_email='greg@laws.africa',

    # See https://pypi.org/classifiers/
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: Django :: 3.2',
        'Intended Audience :: Legal Industry',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
    ],

    packages=find_packages(exclude=['docs']),
    include_package_data=True,

    python_requires='~=3.7',
    install_requires=[
        'django>=3.2,<4',
        'boto3>=1.7',
        'cobalt>=6.1',
        'cssutils>=2.3.0',
        'django-ckeditor>=5.8',
        'dj-database-url>=0.3.0',
        'django-activity-stream>=0.10.0',
        'django-allauth>=0.48.0',
        'django-background-tasks>=1.2.5',
        'django-compressor>=3.1',
        'django-cors-headers>=3.11.0',
        'django-countries-plus<=2.0.0',
        'django-jsonfield>=1.4.1',
        'django-jsonfield-compat>=0.4.4',
        'django-filter==2.4.0',
        'django-fsm>=2.6.0',
        'django-languages-plus>=1.1.1',
        'django-pipeline>=1.6.11',
        'django-recaptcha>=1.4.0,<2.0.0',
        'django-reversion>=3.0.9',
        'django-sass-processor>=1.1',
        'django-sass-processor-dart-sass>=0.0.1',
        'django-storages>=1.12.3',
        'django-templated-email>=2.3.0',
        'djangorestframework-xml>=1.3.0',
        'djangorestframework>=3.11.0,<3.12.0',  # v3.12.0: The authtoken model no longer exposes
                                                # the pk in the admin URL. [#7341]
        'bluebell @ git+https://github.com/laws-africa/bluebell@9f790556fdab05fed66bceb9b24af4c0ed4807c9',
        'docpipe @ git+https://github.com/laws-africa/docpipe@7c33ed68b0d8dd1723204b87cdf0ac1d5696124f',
        'EbookLib>=0.15',
        'google-api-python-client>=1.7.9',
        'iso8601>=0.1',
        'jsonpatch>=1.23',
        'lxml>=3.4.1',
        'mammoth>=1.4.4',
        'natsort>=8.3',
        'requests>=2',
        'unicodecsv>=0.14.1',
        'whitenoise>=5.3.0',
        'django-contrib-comments>=1.9.1',
        'XlsxWriter>=1.2.6',
        # unreleased version of xmldiff that allows us to ignore attributes when diffing
        'xmldiff @ git+https://github.com/Shoobx/xmldiff@6980256b10ffa41b5ab80716e63a608f587126db#egg=xmldiff',
        'sentry-sdk>=1.16.0',

        # for indigo_social
        'pillow>=5.2.0',
        'pinax-badges>=2.0.3',
    ],
    extras_require={
        'dev': [
            'nose',
            'flake8',
            'django-nose>=1.4.4',
            'mock>=1.3.0',
        ],
        'test': [
            'nose',
            'flake8',
            'django-nose>=1.4.4',
            'mock>=1.3.0',
            'coveralls',
            'django-webtest>=1.9.4',
            'dotmap>=1.3.8',
            'sheet2dict==0.1.1'
        ],
        'docs': [
            'psycopg2',
        ],
    },
)
